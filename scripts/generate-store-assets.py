"""Entry point for every Leatherwood Tone store asset.

Renders the two 1280x800 screenshots and the two promo tiles via
generate-references.py, then validates the single 128px logo.

Run from the project root:
    python3 scripts/generate-store-assets.py
"""
import os
import runpy
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)

runpy.run_path('scripts/generate-references.py', run_name='__main__')

with Image.open('logo/logo.png') as logo:
    assert logo.size == (128, 128), f'logo must be 128x128, got {logo.size}'
    assert logo.mode == 'RGBA', f'logo must keep transparent corners, got {logo.mode}'

for rel in ('store-assets/screenshots/en/screenshot-1-browser.png',
            'store-assets/screenshots/en/screenshot-2-introduction.png',
            'store-assets/promo/440x280.png',
            'store-assets/promo/1400x560.png'):
    with Image.open(rel) as img:
        assert img.mode == 'RGB', f'{rel} must be flattened RGB, got {img.mode}'

print('Logo validated: logo/logo.png (128x128 RGBA, single size)')
print('All four store assets rendered and verified')
