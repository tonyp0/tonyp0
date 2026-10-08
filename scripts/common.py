"""Shared drawing helpers for the flight-ops profile cards."""
from xml.sax.saxutils import escape as _escape

W = 900
FONT = "Menlo, Consolas, 'DejaVu Sans Mono', 'Courier New', monospace"

PALETTES = {
    "dark": dict(
        bg="#0a0f14", panel="#0f1720", grid="#16212c", line="#26384a",
        text="#d3dee8", dim="#7a8c9e", faint="#3a4c5e",
        accent="#2ee6b8", accent_soft="#13846c", amber="#ffb340", red="#ff5f56",
        portrait="#8fdcc7",
        levels=["#131e28", "#0d4d43", "#0f7d68", "#18ad8c", "#3ff5c8"],
    ),
    "light": dict(
        bg="#f6f8fa", panel="#ffffff", grid="#e7edf2", line="#c5d1dc",
        text="#1d2733", dim="#5d6d7d", faint="#a9b7c4",
        accent="#00866b", accent_soft="#7fd3be", amber="#b26a00", red="#d03b3b",
        portrait="#1d2733",
        levels=["#e4eaf0", "#b3e8da", "#64cfb2", "#1fa184", "#0a6650"],
    ),
}


def esc(s):
    return _escape(str(s), {'"': "&quot;"})


def trunc(s, n):
    s = str(s)
    return s if len(s) <= n else s[: max(1, n - 1)] + "…"


def svg_open(w, h, p, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{esc(FONT)}" role="img" aria-label="{esc(label)}">\n'
        "<style>.still{display:none}"
        "@media (prefers-reduced-motion: reduce){.fx{display:none}.still{display:inline}}</style>\n"
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="6" fill="{p["bg"]}" stroke="{p["line"]}"/>\n'
        + brackets(w, h, p)
    )


def brackets(w, h, p, inset=8, size=12):
    a = p["accent"]
    out = []
    for x, y, dx, dy in [(inset, inset, 1, 1), (w - inset, inset, -1, 1),
                         (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)]:
        out.append(f'<path d="M{x},{y + dy*size} L{x},{y} L{x + dx*size},{y}" '
                   f'fill="none" stroke="{a}" stroke-width="2"/>')
    return "\n".join(out) + "\n"


def header(p, title, subtitle, right_top="", right_bottom="", status_dot=True):
    out = [
        f'<text x="28" y="36" font-size="16" font-weight="bold" fill="{p["accent"]}">// {esc(title)}</text>',
        f'<text x="28" y="53" font-size="9.5" letter-spacing="1.5" fill="{p["dim"]}">{esc(subtitle)}</text>',
    ]
    if right_top:
        out.append(f'<text x="872" y="34" font-size="11" text-anchor="end" fill="{p["text"]}">{esc(right_top)}</text>')
    if right_bottom:
        out.append(f'<text x="872" y="52" font-size="9" letter-spacing="1" text-anchor="end" fill="{p["dim"]}">{esc(right_bottom)}</text>')
        if status_dot:
            x = 872 - len(right_bottom) * 6.9 - 10
            out.append(f'<circle cx="{x:.1f}" cy="49" r="3" fill="{p["accent"]}">'
                       f'<animate attributeName="opacity" values="1;0.2;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    out.append(f'<line x1="28" y1="66" x2="872" y2="66" stroke="{p["line"]}"/>')
    return "\n".join(out) + "\n"


def stat_strip(p, items, y, x0=28, width=844):
    step = width / len(items)
    out = []
    for i, (value, label) in enumerate(items):
        x = x0 + i * step
        out.append(f'<rect x="{x:.1f}" y="{y}" width="3" height="30" fill="{p["accent"]}"/>')
        out.append(f'<text x="{x+11:.1f}" y="{y+18}" font-size="21" font-weight="bold" fill="{p["text"]}">{esc(value)}</text>')
        out.append(f'<text x="{x+11:.1f}" y="{y+31}" font-size="8.5" letter-spacing="1.2" fill="{p["dim"]}">{esc(label.upper())}</text>')
    return "\n".join(out) + "\n"


def footer(p, w, h, code):
    return (f'<text x="{w-28}" y="{h-15}" font-size="8.5" letter-spacing="1.5" text-anchor="end" '
            f'fill="{p["dim"]}">{esc(code)}</text>\n')


def drone(p, cx, cy, s, color, spin=True, light=None):
    """Top-down quadcopter centred on (cx, cy); s = arm half-span."""
    r = s * 0.42
    out = [f'<g>']
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+dx*s:.1f}" y2="{cy+dy*s:.1f}" stroke="{color}" stroke-width="{max(1.5, s/9):.1f}"/>')
    for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        rx, ry = cx + dx * s, cy + dy * s
        out.append(f'<circle cx="{rx:.1f}" cy="{ry:.1f}" r="{r:.1f}" fill="{color}" fill-opacity="0.08" stroke="{color}" stroke-width="1"/>')
        blade = (f'<line x1="{rx - r*0.9:.1f}" y1="{ry:.1f}" x2="{rx + r*0.9:.1f}" y2="{ry:.1f}" '
                 f'stroke="{color}" stroke-width="1.6" stroke-linecap="round">')
        if spin:
            blade += (f'<animateTransform attributeName="transform" type="rotate" '
                      f'from="0 {rx:.1f} {ry:.1f}" to="{360 if dx*dy > 0 else -360} {rx:.1f} {ry:.1f}" '
                      f'dur="0.22s" repeatCount="indefinite"/>')
        out.append(blade + "</line>")
    b = s * 0.42
    out.append(f'<rect x="{cx-b:.1f}" y="{cy-b*0.75:.1f}" width="{2*b:.1f}" height="{1.5*b:.1f}" rx="{b*0.35:.1f}" '
               f'fill="{p["panel"]}" stroke="{color}" stroke-width="1.4"/>')
    if light:
        out.append(f'<circle cx="{cx}" cy="{cy - b*0.2:.1f}" r="{max(1.6, s/10):.1f}" fill="{light}">'
                   f'<animate attributeName="opacity" values="1;0.15;1" dur="1.2s" repeatCount="indefinite"/></circle>')
    out.append("</g>")
    return "\n".join(out)


def fmt_num(n):
    n = int(n)
    if n >= 10000:
        return f"{n/1000:.1f}k"
    return f"{n:,}"


def fmt_size(kb):
    kb = kb or 0
    if kb >= 1024 * 1024:
        return f"{kb/1024/1024:.1f} GB"
    if kb >= 1024:
        return f"{kb/1024:.1f} MB"
    return f"{kb} KB"
