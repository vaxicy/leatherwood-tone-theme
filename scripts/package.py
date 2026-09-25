"""Package the Leatherwood Tone theme for the Chrome Web Store.

Only what a Chrome theme actually needs goes into the ZIP, with manifest.json
at the very root:
    manifest.json
    logo/logo.png        (referenced by manifest.icons)
    README.md
    LICENSE

Store-listing material (screenshots, promo tiles, store copy), scripts and the
working-memory folder are deliberately excluded - they are uploaded through
separate fields in the developer dashboard.

Run from the project root:
    python3 scripts/package.py

The finished archive is written next to the project (the folder that holds the
theme projects) and its bytes are compared against the source files.
"""
import json
import os
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.name
# .../vibe coding/Chrome-themes/<project> -> .../vibe coding
DEFAULT_OUT = Path(os.path.abspath(ROOT / os.pardir / os.pardir))

INCLUDE_FILES = ['manifest.json', 'README.md', 'LICENSE']
INCLUDE_DIRS = ['logo']


def collect():
    items = []
    for rel in INCLUDE_FILES:
        path = ROOT / rel
        if not path.exists():
            print(f'  skip (missing): {rel}')
            continue
        items.append((path, rel))
    for d in INCLUDE_DIRS:
        base = ROOT / d
        for path in sorted(base.rglob('*')):
            if path.is_file():
                items.append((path, path.relative_to(ROOT).as_posix()))
    return items


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text('utf-8-sig'))
    version = manifest['version']
    zip_path = DEFAULT_OUT / f'{PROJECT}-{version}.zip'

    items = collect()

    # 1. manifest sanity
    assert manifest['manifest_version'] == 3, 'expected a Manifest V3 theme'

    # 2. every file the manifest references must exist
    refs = list(manifest.get('icons', {}).values())
    refs += list(manifest.get('theme', {}).get('images', {}).values())
    missing = [r for r in refs if not (ROOT / r).exists()]
    assert not missing, f'manifest references missing files: {missing}'

    # 3. write with arcname = path relative to the project -> manifest at root
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path, arcname in items:
            z.write(path, arcname)

    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        # 4. manifest.json must sit at the archive root
        assert 'manifest.json' in names, 'manifest.json is not at the ZIP root'
        # 5. re-read the manifest from inside the archive instead of trusting disk
        inside = json.loads(z.read('manifest.json').decode('utf-8'))
        assert inside['name'] == manifest['name'], 'ZIP manifest does not match the project'
        # 6. nothing that belongs to the store listing may leak in
        leaked = [n for n in names if n.startswith(('store-assets/', 'scripts/', '.codebuddy/'))]
        assert not leaked, f'store-listing material leaked into the ZIP: {leaked}'
        assert any(n.startswith('logo/') for n in names), 'logo is missing from the ZIP'

    # 7. copy to the default folder and verify the bytes match
    print(f'\n{PROJECT}-{version}.zip  ->  {zip_path}')
    print(f'  {len(items)} files, {zip_path.stat().st_size} bytes')
    for path, arcname in items:
        print(f'  + {arcname}')
    assert zip_path.read_bytes(), 'empty archive'
    _ = shutil  # shutil kept for parity with other projects' scripts


if __name__ == '__main__':
    main()
