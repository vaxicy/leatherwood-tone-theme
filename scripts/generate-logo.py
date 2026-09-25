"""Leatherwood Tone Theme - final logo.

Draws the chosen candidate (05 "stitched circle") straight at the only size a
Chrome theme icon needs, reusing the shared drawing code, so the logo and the
candidate sheet can never drift apart.

Run from the project root:
    python3 scripts/generate-logo.py

Output: logo/logo.png  (128x128 RGBA, transparent corners)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_logo_candidates import FINAL, c05_stitched_circle, render  # noqa: E402

DEST = os.path.join("logo", "logo.png")


def main():
    if not os.path.exists("manifest.json"):
        raise SystemExit("run this from the project root (manifest.json not found)")
    os.makedirs("logo", exist_ok=True)
    render(c05_stitched_circle, FINAL).save(DEST)
    print(f"wrote {DEST} ({FINAL}x{FINAL})")


if __name__ == "__main__":
    main()
