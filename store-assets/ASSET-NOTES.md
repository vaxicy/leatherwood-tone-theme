# Assets

Four English deliverables, all rendered from one headless-Chromium source (`scripts/generate-references.py`):

| File | Size | Content |
|------|------|---------|
| `screenshots/en/screenshot-1-browser.png` | 1280x800 | Full-window mockup of the themed browser |
| `screenshots/en/screenshot-2-introduction.png` | 1280x800 | Theme intro with the 2x2 colour cards |
| `promo/440x280.png` | 440x280 | Brand tile |
| `promo/1400x560.png` | 1400x560 | Marquee with a scaled window preview |

Plus the single theme icon `logo/logo.png` (128x128) and the store copy in `store-description.txt`.

## Calibration

The window mockup is authored in the pixel space of real maximized Chrome (1080x675) and rasterised at a matching device scale factor, so the 1280x800 store shot stays crisp instead of being upscaled. Theme-controlled surfaces (frame, toolbar, active tab, bookmark bar, omnibox, new-tab page, text, links) are read from `manifest.json` at render time.

Elements Chrome paints itself are literals, because this is a dark palette and Chrome decides them:

| Element | Value | Note |
|---|---|---|
| Google mark on the new tab page | `#E8EAED` | `ntp_logo_alternate` makes Chrome paint the mark in a single light neutral tone derived from the new-tab background; it is not the four-colour brand logo |
| New tab search pill | `#FFFFFF` with dark text `#3C4043` | Chrome renders the search box light on this dark page |
| Plus / mic glyphs in the search pill | `#5F6368` | Chrome's dark-surface tone; the Lens glyph keeps its brand colours |
| Shortcut tiles | `#FFFFFF` (Chrome Web Store), `#3C4043` (add shortcut) | The round tiles are rendered by the page, not the theme |
| `Images` row and shortcut labels | `#9AA0A6` | Chrome's standard dark-surface tone |
| Omnibox outline | `#9AA0A6` | Chrome's own outline on the dark toolbar |
| `Customize Chrome` pill | `#202124` / `#A8C7FA` | Rendered by the page, not the theme |
| Window glyphs | `#E1E1D5` | Light glyphs on the olive frame, matching the theme's icon tone |

These dark-surface values are shared with the other dark themes in this collection. If a real installed-Chrome capture of this theme shows a different tone, update the `LOGO_TINT` / `NSEARCH_*` / `SHORT_*` constants at the top of the composer and re-render all four assets.

The page backdrop behind `screenshot-2` and the marquee is **`ntp_background` darkened to 35% (`#0D0C07`)**, not `ntp_background` itself. The dark tone is derived from the theme so it still feels native, but sits clearly below every swatch — otherwise the `Night Wood` card and the window's own new-tab area would merge into the page. The composer asserts the backdrop never equals a swatch colour.

## Logo

`logo/logo.png` is the single 128px icon a Chrome theme ships, taken from candidate 05 of `store-assets/icon-candidates/` (`candidate-05-stitched-circle.png`): a stitched olive-leather badge over a wood-ring core. It lives in its own `logo/` folder so it is easy to find when uploading, and `manifest.json` references only that one file.

## Store copy

`store-description.txt` is the detailed description field (short, English, factual — palette and solid-colour character only, no promotional wording).

## Regenerating

    python3 scripts/generate-logo.py             # re-draws the 128px logo
    python3 scripts/generate-store-assets.py     # screenshots + promo tiles

The composer renders all four assets in one pass; change the styling in the script and re-run instead of editing a PNG.
