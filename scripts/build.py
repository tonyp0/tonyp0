"""Render every profile card (dark + light) and refresh the README repo manifest.

Usage:
  GH_TOKEN=... python scripts/build.py            # live data
  python scripts/build.py --sample                # made-up data, no token needed
"""
import argparse
import os
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cards import hangar, hangar_repos, mission_log, pilot_id, portrait_png, repo_status, terrain  # noqa: E402
from common import PALETTES  # noqa: E402
from fetch import fetch  # noqa: E402
from manifest import manifest_block  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="render with made-up data")
    ap.add_argument("--login", default=os.environ.get("GH_LOGIN", "tonyp0"))
    ap.add_argument("--out", default=str(ROOT))
    args = ap.parse_args()

    prof = tomllib.loads((ROOT / "profile.toml").read_text())
    data = fetch(args.login, sample=args.sample)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    photo = ROOT / prof.get("portrait", "assets/portrait.jpg")
    for mode, p in PALETTES.items():
        pic = None
        if photo.exists():
            pic = portrait_png(photo, prof.get("portrait_crop"), 236, p, mode)
        cards = {
            "pilot_id": pilot_id(data, prof, p, mode, pic),
            "terrain": terrain(data, prof, p, mode),
            "hangar": hangar(data, prof, p, mode),
            "mission_log": mission_log(data, prof, p, mode),
        }
        for name, svg in cards.items():
            (out / f"{name}_{mode}.svg").write_text(svg, encoding="utf-8")

    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        block = manifest_block(data, prof.get("repo_notes"))
        new = re.sub(r"(<!-- manifest:start -->).*?(<!-- manifest:end -->)",
                     lambda m: f"{m.group(1)}\n{block}\n{m.group(2)}",
                     text, flags=re.S)
        if new != text and not args.sample:
            readme.write_text(new, encoding="utf-8")
        elif args.sample:
            (out / "README.sample.md").write_text(new, encoding="utf-8")
    print(f"Rendered {len(PALETTES) * 4} cards for {data['login']} → {out}")


if __name__ == "__main__":
    main()
