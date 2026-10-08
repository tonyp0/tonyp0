"""The four flight-ops cards: PILOT ID, TERRAIN SURVEY, FLEET HANGAR, MISSION LOG."""
import base64
import datetime as dt
import io
import math

from common import (W, brackets, drone, esc, fmt_num, fmt_size, footer, header,
                    stat_strip, svg_open, trunc)

TAG = "TP0"


# ───────────────────────── portrait ─────────────────────────

def portrait_png(path, crop, size, p, mode):
    """Dither a photo to 1-bit and tint it, returning a base64 PNG (transparent background)."""
    from PIL import Image, ImageEnhance, ImageOps

    im = Image.open(path).convert("L")
    w, h = im.size
    if crop:
        x0, y0, x1, y1 = crop
        im = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    else:  # centre square
        s = min(w, h)
        im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2))
    im = im.resize((size, size), Image.LANCZOS)
    im = ImageEnhance.Contrast(ImageOps.autocontrast(im, cutoff=3)).enhance(1.4)
    bits = im.convert("1")  # Floyd–Steinberg
    # dark mode lights up bright pixels; light mode inks in dark pixels; both read as a positive image
    lit = bits.point(lambda v: 255 if (v and mode == "dark") or (not v and mode == "light") else 0)
    ink = tuple(int(p["portrait"][i:i + 2], 16) for i in (1, 3, 5))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(ink + (255,), mask=lit)
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


# ───────────────────────── 01 PILOT ID ─────────────────────────

def pilot_id(data, prof, p, mode, portrait_b64=None):
    h = 340
    s = [svg_open(W, h, p, f"Pilot ID card for {prof['callsign']}: {prof['rows'][0]['value']}")]

    # window chrome
    s.append(f'<text x="26" y="29" font-size="11" fill="{p["red"]}">●</text>'
             f'<text x="40" y="29" font-size="11" fill="{p["amber"]}">●</text>'
             f'<text x="54" y="29" font-size="11" fill="{p["accent"]}">●</text>')
    s.append(f'<text x="74" y="28" font-size="11" fill="{p["dim"]}">{esc(data["login"])}@github: ~/hangar/preflight</text>')
    s.append(f'<text x="872" y="28" font-size="9" letter-spacing="1.5" text-anchor="end" fill="{p["dim"]}">UPLINK</text>')
    for i in range(4):
        s.append(f'<rect x="{800 + i*6}" y="{26 - (i+1)*2.5:.1f}" width="4" height="{(i+1)*2.5:.1f}" fill="{p["accent"]}">'
                 f'<animate attributeName="opacity" values="1;1;0.25;1" dur="2.4s" begin="{i*0.15:.2f}s" repeatCount="indefinite"/></rect>')
    s.append(f'<line x1="20" y1="40" x2="880" y2="40" stroke="{p["line"]}"/>')

    # camera feed
    px, py, ps = 28, 56, 236
    s.append(f'<rect x="{px}" y="{py}" width="{ps}" height="{ps}" fill="{p["panel"]}" stroke="{p["line"]}"/>')
    if portrait_b64:
        s.append(f'<image x="{px}" y="{py}" width="{ps}" height="{ps}" style="image-rendering:pixelated" '
                 f'href="data:image/png;base64,{portrait_b64}"/>')
    else:
        s.append(drone(p, px + ps / 2, py + ps / 2, 44, p["accent"], spin=True, light=p["red"]))
    cx, cy = px + ps / 2, py + ps / 2
    s.append(f'<g stroke="{p["accent"]}" fill="none" opacity="0.85">')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="96" stroke-dasharray="3 9" stroke-width="1.2">'
             f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" dur="30s" repeatCount="indefinite"/></circle>')
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        s.append(f'<line x1="{cx + dx*104}" y1="{cy + dy*104}" x2="{cx + dx*114}" y2="{cy + dy*114}" stroke-width="1.5"/>')
    s.append("</g>")
    s.append(brackets_box(p, px, py, ps, ps))
    s.append(f'<rect x="{px+6}" y="{py+6}" width="58" height="13" fill="{p["bg"]}" opacity="0.8"/>'
             f'<text x="{px+10}" y="{py+16}" font-size="8.5" letter-spacing="1" fill="{p["accent"]}">CAM-01</text>')
    s.append(f'<rect x="{px+ps-50}" y="{py+6}" width="44" height="13" fill="{p["bg"]}" opacity="0.8"/>'
             f'<circle cx="{px+ps-42}" cy="{py+12.5}" r="3" fill="{p["red"]}">'
             f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></circle>'
             f'<text x="{px+ps-35}" y="{py+16}" font-size="8.5" letter-spacing="1" fill="{p["red"]}">REC</text>')
    s.append(f'<rect x="{px+6}" y="{py+ps-19}" width="{ps-12}" height="13" fill="{p["bg"]}" opacity="0.8"/>'
             f'<text x="{px+10}" y="{py+ps-9}" font-size="8.5" letter-spacing="1" fill="{p["accent"]}">GIMBAL -12°</text>'
             f'<text x="{px+ps-10}" y="{py+ps-9}" font-size="8.5" letter-spacing="1" text-anchor="end" fill="{p["accent"]}">PILOT · {esc(prof["callsign"])}</text>')
    s.append(f'<rect class="fx" x="{px}" y="{py}" width="{ps}" height="2" fill="{p["accent"]}" opacity="0.45">'
             f'<animate attributeName="y" values="{py};{py+ps-2};{py}" dur="5s" repeatCount="indefinite"/></rect>')

    # preflight readout
    tx = 296
    s.append(f'<text x="{tx}" y="74" font-size="13" font-weight="bold" fill="{p["accent"]}">'
             f'$ ./preflight --pilot {esc(prof["callsign"].lower())} <tspan>█'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/>'
             f'</tspan></text>')
    s.append(f'<line x1="{tx}" y1="86" x2="872" y2="86" stroke="{p["line"]}" stroke-dasharray="2 4"/>')

    rows = list(prof["rows"])
    telemetry = (f"Repos {len(data['repos'])} · Stars {sum(r['stars'] for r in data['repos'])} · "
                 f"Followers {data['followers']} · {fmt_num(data['year_total'])} contribs this year")
    rows.append(dict(label="TELEMETRY", value=telemetry))
    y = 110
    for i, row in enumerate(rows[:9]):
        t = 0.35 + i * 0.22
        total = t + 0.3
        anim = (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{t/total:.3f};1" '
                f'dur="{total:.2f}s" fill="freeze"/>')
        s.append(f'<g>{anim}'
                 f'<text x="{tx}" y="{y}" font-size="9.5" letter-spacing="1.2" fill="{p["dim"]}">{esc(row["label"].upper())}</text>'
                 f'<text x="{tx+104}" y="{y}" font-size="11.5" fill="{p["text"]}">{esc(trunc(row["value"], 57))}</text>'
                 f'<text x="872" y="{y}" font-size="9.5" text-anchor="end" fill="{p["accent"]}">[ OK ]</text></g>')
        y += 22
    t = 0.35 + len(rows[:9]) * 0.22
    s.append(f'<g><animate attributeName="opacity" values="0;0;1" keyTimes="0;{t/(t+0.4):.3f};1" dur="{t+0.4:.2f}s" fill="freeze"/>'
             f'<text x="{tx}" y="{y + 8}" font-size="11" font-weight="bold" letter-spacing="1.5" fill="{p["accent"]}">'
             f'ALL SYSTEMS NOMINAL · CLEARED FOR TAKEOFF</text></g>')

    s.append(footer(p, W, h, f"{TAG} // 01 · PILOT ID"))
    s.append("</svg>")
    return "\n".join(s)


def brackets_box(p, x, y, w, h, size=10):
    a = p["accent"]
    out = []
    for cx, cy, dx, dy in [(x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)]:
        out.append(f'<path d="M{cx - dx*3},{cy + dy*size} L{cx - dx*3},{cy - dy*3} L{cx + dx*size},{cy - dy*3}" '
                   f'fill="none" stroke="{a}" stroke-width="2"/>')
    return "\n".join(out)


# ───────────────────────── 02 TERRAIN SURVEY ─────────────────────────

def calendar_stats(weeks, today):
    days = [d for w in weeks for d in w if d["date"] <= today]
    counts = [d["count"] for d in days]
    t = dt.date.fromisoformat(today)
    week_start = str(t - dt.timedelta(days=(t.weekday() + 1) % 7))
    cur = 0
    i = len(counts) - 1
    if counts and counts[-1] == 0:
        i -= 1  # today not logged yet doesn't break the streak
    while i >= 0 and counts[i] > 0:
        cur += 1
        i -= 1
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    peak = max(days, key=lambda d: d["count"]) if days else dict(date=today, count=0)
    return dict(
        today=counts[-1] if counts else 0,
        week=sum(d["count"] for d in days if d["date"] >= week_start),
        last30=sum(counts[-30:]),
        year=sum(counts),
        streak=cur, longest=longest, peak=peak,
    )


def level(c, mx):
    if c == 0:
        return 0
    q = c / max(mx, 1)
    return 1 if q < 0.25 else 2 if q < 0.5 else 3 if q < 0.75 else 4


def terrain(data, prof, p, mode):
    h = 350
    st = calendar_stats(data["weeks"], data["today"])
    peak = st["peak"]
    pdate = dt.date.fromisoformat(peak["date"])
    s = [svg_open(W, h, p, f"Terrain survey: {st['year']} contributions in the last year, "
                         f"current streak {st['streak']} days, longest {st['longest']} days")]
    s.append(header(p, "TERRAIN SURVEY", "52 WEEKS OF COMMITS, MAPPED FROM ABOVE",
                    f"PEAK {peak['count']} · {pdate.strftime('%b %d').upper()}", "SURVEY STATUS: ACTIVE"))
    s.append(stat_strip(p, [
        (st["today"], "Today"), (st["week"], "This week"), (st["last30"], "Last 30 days"),
        (fmt_num(st["year"]), "Last year"), (f"{st['streak']}d", "Current streak"),
        (f"{st['longest']}d", "Longest streak")], 80))

    weeks = data["weeks"]
    n = len(weeks)
    cell, gap = 13, 3
    pitch = cell + gap
    gw = n * pitch - gap
    gx = 28 + (844 - gw) / 2
    gy = 168
    lane = gy - 20
    mx = max((d["count"] for w in weeks for d in w), default=1)

    x_start, x_end, dur = gx - 40, gx + gw + 40, 12.0
    s.append(f'<line x1="{gx}" y1="{lane}" x2="{gx+gw}" y2="{lane}" stroke="{p["line"]}" stroke-dasharray="1 5"/>')

    for i, w in enumerate(weeks):
        x = gx + i * pitch
        t = (x + cell / 2 - x_start) / (x_end - x_start) * dur
        tot = t + 0.35
        anim = (f'<animate attributeName="opacity" values="0.22;0.22;1" keyTimes="0;{t/tot:.3f};1" '
                f'dur="{tot:.2f}s" fill="freeze"/>')
        cells = []
        for d in w:
            r = dt.date.fromisoformat(d["date"]).weekday()
            row = (r + 1) % 7
            y = gy + row * pitch
            lv = level(d["count"], mx)
            title = f'<title>{d["count"]} on {d["date"]}</title>'
            cells.append(f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{p["levels"][lv]}">{title}</rect>')
        s.append(f'<g>{anim}{"".join(cells)}</g>')

        # month label at the first week containing the 1st
        for d in w:
            if d["date"].endswith("-01") or (i == 0 and d is w[0]):
                if i < n - 2 and x < 872 - 5 * 12 - 30 - 70:
                    lbl = dt.date.fromisoformat(d["date"]).strftime("%b").upper()
                    s.append(f'<text x="{x:.1f}" y="{gy + 7*pitch + 12}" font-size="9" fill="{p["dim"]}">{lbl}</text>')
                break

    # peak marker + today outline
    for i, w in enumerate(weeks):
        for d in w:
            row = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7
            x, y = gx + i * pitch, gy + row * pitch
            if d is peak or (d["date"] == peak["date"]):
                s.append(f'<circle cx="{x+cell/2:.1f}" cy="{y+cell/2}" r="9" fill="none" stroke="{p["amber"]}" stroke-width="1.5">'
                         f'<animate attributeName="r" values="7;13;7" dur="2s" repeatCount="indefinite"/>'
                         f'<animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite"/></circle>')
            if d["date"] == data["today"]:
                s.append(f'<rect x="{x-1.5:.1f}" y="{y-1.5}" width="{cell+3}" height="{cell+3}" rx="3" fill="none" stroke="{p["accent"]}" stroke-width="1.5"/>')

    # survey drone + scan beam
    beam_h = gy + 7 * pitch - lane
    craft = (f'<polygon points="-5,4 5,4 11,{beam_h} -11,{beam_h}" fill="{p["accent"]}" opacity="0.13"/>'
             f'<line x1="-11" y1="{beam_h}" x2="11" y2="{beam_h}" stroke="{p["accent"]}" stroke-width="1.5" opacity="0.7"/>'
             + drone(p, 0, 0, 11, p["accent"], spin=True, light=p["red"]))
    s.append(f'<g class="fx">{craft}<animateMotion path="M{x_start:.1f},{lane} L{x_end:.1f},{lane}" '
             f'dur="{dur}s" repeatCount="indefinite"/></g>')
    s.append(f'<g class="still" transform="translate({gx + gw - 6:.1f},{lane})">{drone(p, 0, 0, 11, p["accent"], spin=False)}</g>')

    # legend
    ly = gy + 7 * pitch + 12
    lx = 872 - 5 * 12 - 30
    s.append(f'<text x="{lx - 6}" y="{ly}" font-size="8.5" text-anchor="end" fill="{p["dim"]}">FLAT</text>')
    for k in range(5):
        s.append(f'<rect x="{lx + k*12}" y="{ly - 8}" width="9" height="9" rx="1.5" fill="{p["levels"][k]}"/>')
    s.append(f'<text x="{lx + 60 + 2}" y="{ly}" font-size="8.5" fill="{p["dim"]}">PEAKS</text>')

    s.append(f'<text x="28" y="{h-15}" font-size="8.5" letter-spacing="1" fill="{p["dim"]}">'
             f'SURVEYED {esc(data["today"])}</text>')
    s.append(footer(p, W, h, f"{TAG} // 02 · TERRAIN · {n} WK"))
    s.append("</svg>")
    return "\n".join(s)


# ───────────────────────── 03 FLEET HANGAR ─────────────────────────

def repo_status(r, today):
    age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(r["pushed"])).days
    return "LIVE" if age <= 14 else "WARM" if age <= 60 else "GROUNDED"


def hangar_repos(data, limit=8):
    repos = sorted(data["repos"], key=lambda r: r["pushed"], reverse=True)[:limit]
    return sorted(repos, key=lambda r: r["created"])


def hangar(data, prof, p, mode):
    h = 320
    repos = hangar_repos(data)
    today = data["today"]
    stats = [repo_status(r, today) for r in repos]
    s = [svg_open(W, h, p, f"Fleet hangar: {len(repos)} repositories shown as drones; "
                         f"{stats.count('LIVE')} live, {stats.count('WARM')} warm, {stats.count('GROUNDED')} grounded")]
    s.append(header(p, "FLEET HANGAR", "EVERY REPO IS AN AIRFRAME · PARKED BY BUILD DATE",
                    f"{len(data['repos'])} AIRFRAMES",
                    f"{stats.count('LIVE')} LIVE · {stats.count('WARM')} WARM · {stats.count('GROUNDED')} GROUNDED"))
    if not repos:
        s.append(f'<text x="450" y="180" font-size="12" text-anchor="middle" fill="{p["dim"]}">HANGAR EMPTY · NO PUBLIC REPOS YET</text>')
    n = max(len(repos), 1)
    bay = 844 / n
    pad_y, ground = 214, 224
    sizes = [math.log10(max(r["size_kb"], 10)) for r in repos]
    lo, hi = (min(sizes), max(sizes)) if sizes else (1, 2)
    s.append(f'<line x1="28" y1="{ground}" x2="872" y2="{ground}" stroke="{p["line"]}" stroke-width="1.5"/>')
    chars = int(bay / 6.8)
    prev_year = None
    for i, (r, stt, sz) in enumerate(zip(repos, stats, sizes)):
        cx = 28 + bay * i + bay / 2
        if i:
            s.append(f'<line x1="{28 + bay*i:.1f}" y1="84" x2="{28 + bay*i:.1f}" y2="{ground}" stroke="{p["grid"]}" stroke-dasharray="3 5"/>')
        year = r["created"][:4]
        if year != prev_year:
            s.append(f'<text x="{28 + bay*i + 5:.1f}" y="{ground - 4}" font-size="8" fill="{p["accent"]}">{year}</text>')
            prev_year = year
        arm = 14 + (sz - lo) / max(hi - lo, 0.01) * 16
        color = p["accent"] if stt == "LIVE" else p["amber"] if stt == "WARM" else p["faint"]
        s.append(f'<ellipse cx="{cx:.1f}" cy="{pad_y}" rx="{min(bay*0.36, 50):.1f}" ry="6" fill="none" stroke="{p["line"]}"/>'
                 f'<text x="{cx:.1f}" y="{pad_y + 3}" font-size="7" text-anchor="middle" fill="{p["faint"]}">H</text>')
        if stt == "LIVE":
            hover = pad_y - arm - 52
            wash = "".join(
                f'<line x1="{cx + dx:.1f}" y1="{hover + arm + 10:.1f}" x2="{cx + dx*1.6:.1f}" y2="{pad_y - 10}" '
                f'stroke="{color}" stroke-dasharray="2 5" opacity="0.5">'
                f'<animate attributeName="stroke-dashoffset" values="14;0" dur="0.7s" repeatCount="indefinite"/></line>'
                for dx in (-arm * 0.6, 0, arm * 0.6))
            s.append(f'<g class="fx">{wash}</g>')
            s.append(f'<g>{drone(p, round(cx, 1), round(hover, 1), round(arm, 1), color, spin=True, light=p["accent"])}'
                     f'<animateTransform attributeName="transform" type="translate" values="0,0;0,-6;0,0" '
                     f'dur="{2.2 + i*0.17:.2f}s" repeatCount="indefinite"/></g>')
        else:
            light = p["amber"] if stt == "WARM" else None
            s.append(drone(p, round(cx, 1), round(pad_y - arm * 0.55 - 6, 1), round(arm, 1), color, spin=False, light=light))
        nc = p["accent"] if stt == "LIVE" else p["text"]
        s.append(f'<a href="{esc(r["url"])}"><text x="{cx:.1f}" y="{ground + 20}" font-size="11" font-weight="bold" '
                 f'text-anchor="middle" fill="{nc}">{esc(trunc(r["name"], chars - 1))}</text></a>')
        s.append(f'<text x="{cx:.1f}" y="{ground + 35}" font-size="8.5" text-anchor="middle" fill="{p["dim"]}">'
                 f'{esc(trunc((r["lang"] or "—") + " · " + fmt_size(r["size_kb"]), chars + 3))}</text>')
        star = f" · ★{r['stars']}" if r["stars"] else ""
        s.append(f'<text x="{cx:.1f}" y="{ground + 49}" font-size="8.5" text-anchor="middle" fill="{color if stt != "GROUNDED" else p["dim"]}">'
                 f'{stt} · {r["pushed"][5:]}{star}</text>')
    s.append(f'<text x="28" y="{h-15}" font-size="8.5" letter-spacing="1" fill="{p["dim"]}">'
             f'LIVE = PUSHED ≤14D · WARM ≤60D · DRONE SIZE = REPO SIZE</text>')
    s.append(footer(p, W, h, f"{TAG} // 03 · HANGAR · REPOS"))
    s.append("</svg>")
    return "\n".join(s)


# ───────────────────────── 04 MISSION LOG ─────────────────────────

def _smooth_path(pts):
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def _plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def month_lines(m, width=30):
    lines = []
    repos = [r for r in m["commit_repos"] if r["commits"]]
    if m["commits"]:
        lines.append(("main", f"› {_plural(m['commits'], 'commit')} · {_plural(len(repos), 'repo')}"))
        for r in repos[:2]:
            lines.append(("sub", f"  {r['name']} — {r['commits']}"))
        if len(repos) > 2:
            lines.append(("sub", f"  +{len(repos) - 2} more"))
    if m["created"]:
        lines.append(("main", f"› Launched {_plural(len(m['created']), 'new repo')}"))
        for r in m["created"][:2]:
            lines.append(("sub", f"  {r['name']} · {r['lang'] or '—'}"))
    if m["prs"]:
        lines.append(("main", f"› {_plural(m['prs'], 'pull request')} opened"))
    if not lines:
        lines.append(("sub", "› Grounded · no logged sorties"))
    return [(k, trunc(t, width)) for k, t in lines[:7]]


def mission_log(data, prof, p, mode):
    h = 480
    months = data["months"]
    commits = sum(m["commits"] for m in months)
    active = len({r["name"] for m in months for r in m["commit_repos"] if r["commits"]})
    created = sum(len(m["created"]) for m in months)
    prs = sum(m["prs"] for m in months)
    first = dt.date.fromisoformat(months[0]["month"] + "-01")
    s = [svg_open(W, h, p, f"Mission log: {commits} commits across {active} repositories over the last "
                         f"{len(months)} months")]
    s.append(header(p, "MISSION LOG", f"LAST {len(months)} MONTHS OF FLIGHT",
                    f"SINCE {first.strftime('%b %Y').upper()}", "SORTIE IN PROGRESS"))
    s.append(stat_strip(p, [(commits, "Commits"), (active, "Active repos"), (created, "Repos launched"),
                            (prs, "Pull requests")], 80, width=640))

    # altitude grid
    top, base = 140, 300
    for k, frac in enumerate([0, 0.33, 0.66, 1.0]):
        y = base - frac * (base - top)
        s.append(f'<line x1="60" y1="{y:.1f}" x2="872" y2="{y:.1f}" stroke="{p["grid"]}"/>')
    s.append(f'<text x="28" y="{top + 4}" font-size="8" fill="{p["dim"]}">ALT</text>'
             f'<text x="28" y="{base + 3}" font-size="8" fill="{p["dim"]}">GND</text>')

    mx = max([m["commits"] for m in months] + [1])
    xs = [140 + i * (872 - 140 - 70) / max(len(months) - 1, 1) for i in range(len(months))]
    pts = [(60, base)] + [(x, base - 10 - (m["commits"] / mx) * (base - top - 20)) for x, m in zip(xs, months)]
    path = _smooth_path(pts)
    s.append(f'<rect x="44" y="{base - 3}" width="32" height="6" fill="none" stroke="{p["line"]}"/>'
             f'<text x="60" y="{base + 16}" font-size="8" text-anchor="middle" fill="{p["dim"]}">LAUNCH</text>')
    s.append(f'<path d="{path}" fill="none" stroke="{p["accent"]}" stroke-width="1.6" stroke-dasharray="6 5">'
             f'<animate attributeName="stroke-dashoffset" values="22;0" dur="1.2s" repeatCount="indefinite"/></path>')

    panel_w, gap, py = 202, 12, 322
    for i, ((x, y), m) in enumerate(zip(pts[1:], months)):
        cur = i == len(months) - 1
        mdate = dt.date.fromisoformat(m["month"] + "-01")
        col = p["amber"] if cur else p["accent"]
        pxc = 28 + i * (panel_w + gap) + panel_w / 2
        s.append(f'<path d="M{x:.1f},{y + 8:.1f} L{pxc:.1f},{py}" stroke="{p["faint"]}" stroke-dasharray="1 4" fill="none"/>')
        s.append(f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{p["bg"]}" stroke="{col}" stroke-width="1.5" '
                 f'transform="rotate(45 {x:.1f} {y:.1f})"/>')
        if cur:
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="none" stroke="{col}">'
                     f'<animate attributeName="r" values="8;18;8" dur="2s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values="1;0;1" dur="2s" repeatCount="indefinite"/></circle>')
        s.append(f'<text x="{x:.1f}" y="{y - 14:.1f}" font-size="9" letter-spacing="1" text-anchor="middle" fill="{col}">'
                 f'{mdate.strftime("%b").upper()} · {m["commits"]}{" · NOW" if cur else ""}</text>')

        # log panel
        x0 = 28 + i * (panel_w + gap)
        s.append(f'<rect x="{x0}" y="{py}" width="{panel_w}" height="128" rx="5" fill="{p["panel"]}" '
                 f'stroke="{col if cur else p["line"]}" stroke-width="{1.5 if cur else 1}"/>')
        s.append(f'<text x="{x0 + 12}" y="{py + 20}" font-size="11" font-weight="bold" fill="{p["text"]}">'
                 f'<tspan fill="{col}">◆</tspan> {mdate.strftime("%B %Y").upper()}</text>')
        if cur:
            s.append(f'<text x="{x0 + panel_w - 10}" y="{py + 20}" font-size="7.5" letter-spacing="1" text-anchor="end" fill="{col}">CURRENT</text>')
        ly = py + 40
        for kind, text in month_lines(m):
            s.append(f'<text x="{x0 + 12}" y="{ly}" font-size="9.5" fill="{p["text"] if kind == "main" else p["dim"]}" '
                     f'xml:space="preserve">{esc(text)}</text>')
            ly += 13.5

    craft = drone(p, 0, 0, 9, p["accent"], spin=True, light=p["red"])
    s.append(f'<g class="fx">{craft}<animateMotion path="{path}" dur="9s" repeatCount="indefinite"/></g>')
    lx, ly = pts[-1]
    s.append(f'<g class="still" transform="translate({lx:.1f},{ly - 22:.1f})">{drone(p, 0, 0, 9, p["accent"], spin=False)}</g>')

    s.append(footer(p, W, h, f"{TAG} // 04 · MISSION LOG · {len(months)} MO"))
    s.append("</svg>")
    return "\n".join(s)
