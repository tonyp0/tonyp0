"""The hangar manifest: a flight-board table under the FLEET HANGAR card."""
import datetime as dt
from urllib.parse import quote

from cards import repo_status

# language -> (badge colour, simple-icons logo, logo colour)
LANGS = {
    "Python": ("3776AB", "python", "white"),
    "Swift": ("F05138", "swift", "white"),
    "Jupyter Notebook": ("F37626", "jupyter", "white"),
    "JavaScript": ("F7DF1E", "javascript", "black"),
    "TypeScript": ("3178C6", "typescript", "white"),
    "Java": ("ED8B00", "openjdk", "white"),
    "Kotlin": ("7F52FF", "kotlin", "white"),
    "C++": ("00599C", "cplusplus", "white"),
    "C": ("A8B9CC", "c", "black"),
    "C#": ("512BD4", "dotnet", "white"),
    "Go": ("00ADD8", "go", "white"),
    "Rust": ("000000", "rust", "white"),
    "HTML": ("E34F26", "html5", "white"),
    "CSS": ("1572B6", "css3", "white"),
    "Shell": ("4EAA25", "gnubash", "white"),
    "Dart": ("0175C2", "dart", "white"),
}

STATUS = {  # label, colour, plain-text fallback
    "LIVE": ("● LIVE", "13846c"),
    "WARM": ("◐ WARM", "b26a00"),
    "GROUNDED": ("○ GROUNDED", "3a4c5e"),
}


def _shield_text(s):
    return quote(s.replace("-", "--").replace("_", "__"), safe="")


def badge(text, color, logo=None, logo_color="white"):
    url = f"https://img.shields.io/badge/{_shield_text(text)}-{color}?style=flat-square"
    if logo:
        url += f"&logo={logo}&logoColor={logo_color}"
    return f'<img src="{url}" alt="{text}"/>'


def ago(date, today):
    days = (dt.date.fromisoformat(today) - dt.date.fromisoformat(date)).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 14:
        return f"{days}d ago"
    if days < 60:
        return f"{days // 7}w ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def manifest_block(data, notes=None):
    notes = notes or {}
    today = data["today"]
    repos = sorted(data["repos"], key=lambda r: r["pushed"], reverse=True)
    stats = [repo_status(r, today) for r in repos]
    live = stats.count("LIVE")

    rows = ["| # | AIRFRAME | POWERPLANT | STATUS | LAST SORTIE | BRIEFING |",
            "|:-:|:--|:-:|:-:|:-:|:--|"]
    for i, (r, st) in enumerate(zip(repos, stats), 1):
        lang = r["lang"]
        if lang:
            color, logo, lc = LANGS.get(lang, ("26384a", None, "white"))
            lang_cell = badge(lang, color, logo, lc)
        else:
            lang_cell = "—"
        label, color = STATUS[st]
        stars = f" ★{r['stars']}" if r["stars"] else ""
        note = (notes.get(r["name"]) or r["desc"] or "—").replace("|", "\\|")
        rows.append(f"| `{i:02d}` | **[{r['name']}]({r['url']})**{stars} | {lang_cell} | {badge(label, color)} "
                    f"| `{ago(r['pushed'], today)}` | {note} |")

    return (
        "<details>\n"
        f"<summary><b>🛩️ OPEN THE HANGAR MANIFEST</b> · {len(repos)} airframes · {live} in the air</summary>\n\n"
        + "\n".join(rows)
        + "\n\n<sub>🟢 LIVE: pushed in the last 14 days · 🟠 WARM: last 60 days · ⚪ GROUNDED: older · "
          "sorted by most recent sortie</sub>\n\n</details>"
    )
