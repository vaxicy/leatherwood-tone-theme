"""Compose every Leatherwood Tone store asset from one HTML/CSS source.

The window is authored in a real maximized-Chrome pixel space (1080x675) and
scaled once per output:
  screenshot-1  1280x800  device scale 1.18519 (1080 -> 1280, 675 -> 800)
  promo wide    scaled preview of the same window, trimmed so the frame fits

Theme-controlled colours come from manifest.json (single source of truth).
Chrome-owned UI tones (new-tab Google mark, search pill, shortcut labels,
omnibox outline, Customize pill) are literals because Chrome paints them
itself; see store-assets/ASSET-NOTES.md for where each value comes from.

Run from the project root:
    python3 scripts/generate-references.py
"""
import base64
import json
import os
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)                 # keep every write on an ASCII-relative path
OUT = Path('store-assets/references')
OUT.mkdir(parents=True, exist_ok=True)

C = json.loads(Path('manifest.json').read_text('utf-8-sig'))['theme']['colors']


def darken(rgb, k):
    return [int(round(c * k)) for c in rgb]


# Page backdrop for the info sheet and the marquee. It must NOT equal any colour
# shown as a swatch, or that card merges into the page - ntp_background IS a
# swatch here, so derive a clearly darker tone from it instead.
C['backdrop'] = darken(C['ntp_background'], 0.35)


def color(k):
    return '#%02X%02X%02X' % tuple(C[k])


# ---------------------------------------------------------------------------
# UI tones NOT controlled by the theme (Chrome paints them itself).
# Dark-surface values shared with the other dark themes in this collection
# (see store-assets/ASSET-NOTES.md).
# ---------------------------------------------------------------------------
LOGO_TINT = '#E8EAED'        # ntp_logo_alternate tone Chrome paints on a dark NTP
SEARCH_TEXT = '#9AA0A6'      # shortcut labels / new-tab header
OMNI_BORDER = '#9AA0A6'      # omnibox outline on the dark toolbar
NSEARCH_BG = '#FFFFFF'       # new-tab search pill: Chrome renders it light here
NSEARCH_TEXT = '#3C4043'     # placeholder inside the light search pill
NSEARCH_ICON = '#5F6368'     # plus / mic glyphs inside the search pill
SHORTCUT_TILE = '#FFFFFF'    # favicon tiles (YouTube / Chrome Web Store)
SHORTCUT_ADD = '#3C4043'     # "Add shortcut" circle
PILL_BG = '#202124'          # Customize Chrome pill
PILL_FG = '#A8C7FA'
WIN_BTN = '#E1E1D5'          # window glyphs on the olive frame
G_RED, G_BLUE, G_YELLOW, G_GREEN = '#EA4335', '#4285F4', '#FBBC05', '#34A853'

VARS = f""":root{{
  --frame:{color('frame')};
  --bar:{color('toolbar')};
  --ntp:{color('ntp_background')};
  --ob:{color('omnibox_background')};
  --tabtx:{color('tab_text')};
  --tabtx2:{color('tab_background_text')};
  --bmtext:{color('bookmark_text')};
  --icon:{color('toolbar_button_icon')};
  --link:{color('ntp_link')};
  --ntptext:{color('ntp_text')};
  --backdrop:{color('backdrop')};
  --logoc:{LOGO_TINT};
  --ui:{SEARCH_TEXT};
  --soft:{color('bookmark_text')};
  --shortcut:{SHORTCUT_TILE};
  --shortcutadd:{SHORTCUT_ADD};
  --omnib:{OMNI_BORDER};
  --wbtn:{WIN_BTN};
}}"""

CSS = VARS + """
*{box-sizing:border-box}
body{margin:0;overflow:hidden;font-family:Arial,'Helvetica Neue',sans-serif;background:var(--backdrop);color:var(--ntptext)}
.window{width:1080px;height:675px;background:var(--ntp);position:relative;overflow:hidden;display:flex;flex-direction:column}
.row{display:flex;align-items:center;flex:0 0 auto}
svg{display:block}

/* ---- tab strip (frame colour) ---- */
.tabstrip{height:32px;background:var(--frame);display:flex;align-items:flex-end;padding-left:33px}
.chev{position:absolute;left:14px;top:13px}
.tab{width:176px;height:27px;border-radius:9px 9px 0 0;margin-right:7px;padding:0 10px 0 30px;display:flex;align-items:center;
     font-size:11.5px;color:var(--tabtx2);position:relative;outline:1px solid rgba(255,255,255,.14);outline-offset:-1px}
.tab.on{background:var(--bar);outline:0;color:var(--tabtx)}
.tab i{position:absolute;left:11px;top:8px;width:12px;height:12px;line-height:0}
.tab .t{flex:1 1 auto;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tab .x{flex:0 0 auto;margin-left:6px;opacity:.8}
.tab .x svg{margin:0}
.newtab{width:20px;height:20px;margin:0 0 4px 8px;display:flex;align-items:center;justify-content:center}
.wbtns{margin-left:auto;margin-bottom:9px;margin-right:12px;display:flex;gap:24px}

/* ---- toolbar ---- */
.toolbar{height:32px;background:var(--bar);display:flex;align-items:center;gap:16px;padding:0 14px}
.nav{display:flex;gap:15px;align-items:center}
.omni{flex:1;height:27px;border:2px solid var(--omnib);border-radius:14px;background:var(--ob);display:flex;align-items:center;
      padding:0 6px 0 11px;gap:9px;font-size:12.5px;color:var(--ntptext)}
.omni .ph{flex:1;white-space:nowrap;overflow:hidden}
.tools{display:flex;gap:16px;align-items:center}

/* ---- bookmark bar ---- */
.bookmarks{height:32px;background:var(--bar);display:flex;align-items:center;gap:19px;padding:0 14px;font-size:11.5px;color:var(--bmtext)}
.bookmarks .sep{width:1px;height:14px;background:rgba(240,240,234,.16)}
.bm{display:flex;align-items:center;gap:6px}

/* ---- new tab page ---- */
.ntp{flex:1;position:relative;background:var(--ntp)}
.gtop{position:absolute;top:13px;right:12px;display:flex;align-items:center;gap:16px;font-size:12.5px;color:var(--ui)}
.glogo{position:absolute;top:86.5px;left:0;right:0;text-align:center;font-family:'Google Sans','Product Sans',Arial,sans-serif;
       font-size:66px;font-weight:500;letter-spacing:-2.8px;color:var(--logoc);line-height:1}
.nsearch{position:absolute;top:187px;left:50%;margin-left:-264px;width:529px;height:44px;border-radius:22px;background:var(--shortcut);
         box-shadow:0 1px 6px rgba(0,0,0,.42);display:flex;align-items:center;gap:13px;padding:0 14px 0 20px}
.nsearch .ph{flex:1;font-size:15px;color:#3C4043;white-space:nowrap;overflow:hidden}
.shortcuts{position:absolute;top:251px;left:0;right:0;display:flex;justify-content:center;gap:8px}
.shortcut{width:78px;text-align:center;font-size:12px;color:var(--ui)}
.shortcut .circle{width:33px;height:33px;border-radius:50%;background:var(--shortcut);margin:0 auto 14px;display:flex;align-items:center;justify-content:center}
.shortcut .circle.add{background:var(--shortcutadd)}
.shortcut .lbl{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.customize{position:absolute;right:10px;bottom:10px;height:26px;border-radius:13px;background:#202124;color:#A8C7FA;
           display:flex;align-items:center;gap:6px;padding:0 12px;font-size:11.5px}

/* ---- promo: 440x280 brand tile ---- */
.tile{width:440px;height:280px;background:var(--frame);position:relative;overflow:hidden;text-align:center}
.tile img{width:78px;height:78px;display:block;margin:24px auto 0}
.tile h1{font-family:Georgia,serif;font-weight:normal;font-size:36px;margin:12px 0 0;color:var(--ntptext)}
.tile .kicker{font-size:13px;letter-spacing:5px;margin-top:8px;color:#E9EBD2}
.tile p{font-size:14px;margin:17px 0 0;color:#E9EBD2}
.tile:after{content:'';position:absolute;left:0;right:0;bottom:0;height:14px;background:var(--link)}

/* ---- promo: 1400x560 marquee ---- */
.marquee{width:1400px;height:560px;background:var(--backdrop);position:relative;overflow:hidden;text-align:center;
         border-top:8px solid var(--link)}
.marquee h1{font-family:Georgia,serif;font-weight:normal;font-size:47px;margin:26px 0 0;color:var(--ntptext)}
.marquee p{font-size:17px;margin:9px 0 0;color:var(--ui)}
.marquee .frame{position:absolute;top:139px;left:300px;width:800px;height:370px;overflow:hidden;border:2px solid var(--frame);
                border-radius:16px;box-shadow:0 0 0 1px rgba(240,240,234,.06),0 16px 44px rgba(0,0,0,.7)}
.marquee .frame .window{transform:scale(.740741);transform-origin:top left}

/* ---- screenshot 2: palette card ---- */
.intro{width:1280px;height:800px;background:var(--backdrop);padding:66px 74px}
.intro .kicker{font-size:12px;letter-spacing:4px;color:var(--ui)}
.intro h1{font-family:Georgia,serif;font-weight:normal;font-size:54px;margin:16px 0 0;color:var(--ntptext)}
.intro .lead{font-size:21px;margin:14px 0 0;color:var(--soft)}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:38px}
.card{height:196px;border-radius:18px;padding:30px;display:flex;flex-direction:column;justify-content:flex-end}
.card strong{font-size:28px}
.card span{font-size:16.5px;margin-top:10px}
.intro .chips{font-size:16px;margin-top:32px;color:var(--ui)}
"""


# ----------------------------------------------------------------- glyphs
def g_mark(size):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 48 48">'
            f'<path fill="{G_RED}" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>'
            f'<path fill="{G_BLUE}" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>'
            f'<path fill="{G_YELLOW}" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>'
            f'<path fill="{G_GREEN}" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>')


def pinwheel(size):
    """Four-colour circular mark (Chrome / Chrome Web Store glyph)."""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<circle cx="12" cy="12" r="11" fill="#FFFFFF"/>'
            f'<path d="M12 1a11 11 0 0 1 9.53 5.5L12 12z" fill="{G_RED}"/>'
            f'<path d="M21.53 6.5A11 11 0 0 1 12 23L12 12z" fill="{G_GREEN}"/>'
            f'<path d="M12 23A11 11 0 0 1 2.47 17.5L12 12z" fill="{G_YELLOW}"/>'
            f'<circle cx="12" cy="12" r="5" fill="{G_BLUE}"/><circle cx="12" cy="12" r="2.1" fill="#FFFFFF"/></svg>')


def apps(size, fill):
    dots = ''.join(f'<circle cx="{3 + 9 * (i % 3)}" cy="{3 + 9 * (i // 3)}" r="2.6"/>' for i in range(9))
    return f'<svg width="{size}" height="{size}" viewBox="0 0 30 30" fill="{fill}">{dots}</svg>'


def mic(size, fill):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<rect x="9" y="2" width="6" height="11" rx="3" fill="{fill}"/>'
            f'<path d="M5 11v1a7 7 0 0 0 14 0v-1" fill="none" stroke="{fill}" stroke-width="2"/>'
            f'<path d="M12 19v3" stroke="{fill}" stroke-width="2"/></svg>')


def plus(size, fill):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<path d="M12 5v14M5 12h14" stroke="{fill}" stroke-width="2.3" stroke-linecap="round"/></svg>')


def magnifier(size, fill):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<circle cx="10" cy="10" r="6.4" fill="none" stroke="{fill}" stroke-width="2.2"/>'
            f'<path d="M15 15l5.6 5.6" stroke="{fill}" stroke-width="2.2" stroke-linecap="round"/></svg>')


def lens(size):
    """Google Lens glyph (Chrome renders it in brand colour on the search pill)."""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<rect x="2" y="2" width="20" height="20" rx="6" fill="#FFFFFF"/>'
            f'<path d="M4 10a8 8 0 0 1 16 0z" fill="{G_BLUE}"/>'
            f'<path d="M20 10a8 8 0 0 1-8 8z" fill="{G_RED}"/>'
            f'<path d="M12 18a8 8 0 0 1-8-8z" fill="{G_YELLOW}"/>'
            f'<circle cx="12" cy="10" r="3.1" fill="{G_GREEN}"/>'
            f'<circle cx="12" cy="10" r="1.3" fill="#FFFFFF"/></svg>')


def favicon(kind, size=12):
    if kind == 'leaf':
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
                f'<path d="M19 4c0 8-5.4 13-13 13 0-8 5.4-13 13-13z" fill="#9FA540"/>'
                f'<path d="M6 17C10 13 13.5 10.5 17 8" stroke="#242214" stroke-width="1.6" fill="none"/></svg>')
    if kind == 'wood':
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
                f'<circle cx="12" cy="12" r="10" fill="#B08F64"/>'
                f'<circle cx="12" cy="12" r="6.2" fill="none" stroke="#6B512F" stroke-width="1.4"/>'
                f'<circle cx="12" cy="12" r="2.6" fill="none" stroke="#6B512F" stroke-width="1.4"/></svg>')
    if kind == 'chrome':
        return pinwheel(size)
    return ''


def win_buttons():
    g = f'stroke="{WIN_BTN}" stroke-width="1.5" stroke-linecap="round" fill="none"'
    return ('<div class="wbtns">'
            f'<svg width="10" height="10" viewBox="0 0 12 12"><path d="M1.2 6h9.6" {g}/></svg>'
            f'<svg width="10" height="10" viewBox="0 0 12 12"><rect x="1.8" y="1.8" width="8.4" height="8.4" rx="2" {g}/></svg>'
            f'<svg width="10" height="10" viewBox="0 0 12 12"><path d="M2.2 2.2l7.6 7.6M9.8 2.2L2.2 9.8" {g}/></svg>'
            '</div>')


def nav_icons():
    g = f'stroke="{color("toolbar_button_icon")}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    return ('<div class="nav">'
            f'<svg width="16" height="16" viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7" {g}/></svg>'
            f'<svg width="16" height="16" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" {g}/></svg>'
            f'<svg width="16" height="16" viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.6-5.9" {g}/><path d="M20 3.6V7h-3.4" {g}/></svg>'
            f'<svg width="16" height="16" viewBox="0 0 24 24"><path d="M4 11l8-7 8 7v8.5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1z" {g}/></svg>'
            '</div>')


def tab(title, kind, active=False):
    cls = 'tab on' if active else 'tab'
    return (f'<div class="{cls}"><i>{favicon(kind, 12)}</i>'
            f'<span class="t">{title}</span>'
            f'<span class="x"><svg width="9" height="9" viewBox="0 0 12 12">'
            f'<path d="M2 2l8 8M10 2l-8 8" stroke="{color("tab_background_text")}" stroke-width="1.6" stroke-linecap="round"/></svg></span></div>')


def folder(size=12):
    g = f'stroke="{color("bookmark_text")}" stroke-width="1.5" stroke-linejoin="round" fill="none"'
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'<path d="M3 7.5h6l2 2.5h10v8.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 18.5z" {g}/></svg>')


def bookmarks():
    kids = ''.join(f'<div class="bm">{folder()}{name}</div>'
                   for name in ('Craft', 'Wood', 'Notes', 'Shop', 'Docs', 'Dev'))
    return ('<div class="bookmarks">' + apps(13, color('bookmark_text'))
            + '<div class="sep"></div>' + kids + '</div>')


def window(height=675):
    tabs = (('Leather & Wood Care', 'leaf'),
            ('Woodworking Weekly', 'wood'),
            ('New Tab', 'chrome'))
    strip = ('<div class="tabstrip">'
             f'<div class="chev"><svg width="11" height="11" viewBox="0 0 24 24">'
             f'<path d="M6 10l6 6 6-6" stroke="{color("tab_text")}" stroke-width="2.4" fill="none" stroke-linecap="round"/></svg></div>'
             + ''.join(tab(t, k, i == 2) for i, (t, k) in enumerate(tabs))
             + f'<div class="newtab">{plus(13, color("toolbar_button_icon"))}</div>'
             + win_buttons() + '</div>')
    omni = ('<div class="omni">' + g_mark(14) + '<span class="ph"></span>'
            + magnifier(13, SEARCH_TEXT) + '</div>')
    dots = ''.join(f'<circle cx="12" cy="{5 + 7 * i}" r="1.7" fill="{color("toolbar_button_icon")}"/>' for i in range(3))
    icon = color('toolbar_button_icon')
    puzzle = (f'<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="{icon}" stroke-width="1.6" stroke-linejoin="round">'
              f'<path d="M10 4.6a2 2 0 1 1 4 0V6h3.4v3.4H19a2 2 0 1 1 0 4h-1.6V17H14v1.4a2 2 0 1 1-4 0V17H6.6v-3.6H5a2 2 0 1 1 0-4h1.6V6H10z"/></svg>')
    kebab = ('<div class="tools">'
             f'<svg width="15" height="15" viewBox="0 0 24 24"><path d="M12 3.6l2.5 5.6 6.1.5-4.6 4 1.4 6-5.4-3.2-5.4 3.2 1.4-6-4.6-4 6.1-.5z" fill="none" stroke="{icon}" stroke-width="1.6" stroke-linejoin="round"/></svg>'
             + puzzle
             + f'<svg width="15" height="15" viewBox="0 0 24 24">{dots}</svg>'
             '</div>')
    toolbar = '<div class="toolbar">' + nav_icons() + omni + kebab + '</div>'
    glogo = '<div class="glogo">Google</div>'
    nsearch = ('<div class="nsearch">' + plus(20, NSEARCH_ICON)
               + '<span class="ph">Search Google or type a URL</span>'
               + mic(17, NSEARCH_ICON) + lens(19) + '</div>')
    short = ('<div class="shortcuts">'
             f'<div class="shortcut"><div class="circle">{pinwheel(17)}</div><div class="lbl">Web Store</div></div>'
             f'<div class="shortcut"><div class="circle">{favicon("wood", 17)}</div><div class="lbl">Woodcraft</div></div>'
             f'<div class="shortcut"><div class="circle add">{plus(15, "#E8EAED")}</div><div class="lbl">Add shortcut</div></div>'
             '</div>')
    customize = ('<div class="customize">'
                 f'<svg width="12" height="12" viewBox="0 0 24 24"><path d="M4 20l4.2-1.1L20 7.1 16.9 4 5.1 15.8z" fill="none" stroke="{PILL_FG}" stroke-width="2" stroke-linejoin="round"/></svg>'
                 'Customize Chrome</div>')
    ntp = f'<div class="ntp">{gtop()}{glogo}{nsearch}{short}{customize}</div>'
    return f'<div class="window" style="height:{height}px">' + strip + toolbar + bookmarks() + ntp + '</div>'


def gtop():
    return '<div class="gtop"><span>Images</span>' + apps(13, SEARCH_TEXT) + '</div>'


LOGO_URI = 'data:image/png;base64,' + base64.b64encode(Path('logo/logo.png').read_bytes()).decode()

tile = ('<div class="tile">' + f'<img src="{LOGO_URI}" alt="Leatherwood Tone logo">'
        + '<h1>Leatherwood</h1><div class="kicker">CHROME THEME</div>'
        + '<p>Earthy olive wood for a calmer browser.</p></div>')
marquee = ('<div class="marquee"><h1>Leatherwood Tone Theme</h1>'
           '<p>Olive green, deep wood and one pale reed accent.</p>'
           + '<div class="frame">' + window(height=500) + '</div></div>')

PALETTE = [
    ('Olive Frame', 'frame', 'Window frame & tab strip', 'ntp_text'),
    ('Deep Olive', 'toolbar', 'Toolbar, bookmarks & active tab', 'ntp_text'),
    ('Night Wood', 'ntp_background', 'New tab background', 'ntp_text'),
    ('Pale Reed', 'ntp_link', 'Accent & links', 'ntp_background'),
]
assert all(tuple(C['backdrop']) != tuple(C[k]) for _n, k, _r, _f in PALETTE), \
    'page backdrop must not equal a swatch colour'
cards = ''.join(
    f'<div class="card" style="background:{color(k)};color:{color(fg)};border:1px solid rgba(240,240,234,.18)">'
    f'<strong>{name}</strong><span>{color(k)} · {role}</span></div>' for name, k, role, fg in PALETTE)
intro = ('<div class="intro"><div class="kicker">AN EARTHY, DARK PALETTE</div><h1>Leatherwood Tone Theme</h1>'
         '<p class="lead">Olive green, deep wood and one pale reed accent.</p><div class="cards">' + cards + '</div>'
         '<p class="chips">Solid colors · Dark interface · No wallpaper · Tuned for contrast</p></div>')


def page(body):
    return '<!doctype html><html lang="en"><meta charset="utf-8"><style>' + CSS + '</style><body>' + body + '</body></html>'


# name, output size, design size. The browser window is authored at 1080x675
# (real capture pixel space) and rasterised at a matching device scale factor
# so the 1280x800 store shot stays crisp instead of being upscaled.
JOBS = [
    ('screenshot-1-browser', 1280, 800, 1080, 675, window(675)),
    ('screenshot-2-introduction', 1280, 800, 1280, 800, intro),
    ('promo-440x280', 440, 280, 440, 280, tile),
    ('promo-1400x560', 1400, 560, 1400, 560, marquee),
]

with sync_playwright() as p:
    engine = p.chromium.launch(headless=True)
    for name, w, h, dw, dh, body in JOBS:
        dsf = w / dw
        html = page(body)
        (OUT / f'{name}.html').write_text(html, 'utf-8')
        sheet = engine.new_page(device_scale_factor=dsf, viewport={'width': dw, 'height': dh})
        sheet.set_content(html)
        sheet.screenshot(path=str(OUT / f'{name}.png'))
        sheet.close()
        destination = Path('store-assets') / ('promo' if name.startswith('promo-') else 'screenshots/en') / (
            name.removeprefix('promo-') + '.png')
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_suffix('.new.png')
        with Image.open(OUT / f'{name}.png') as img:
            out = img.convert('RGB')
            if out.size != (w, h):
                print(f'  resampling {name} {out.size} -> {(w, h)}')
                out = out.resize((w, h), Image.LANCZOS)
            assert out.size == (w, h), f'{name}: got {out.size}, expected {(w, h)}'
            out.save(temp)
        temp.replace(destination)
        print(f'Rendered {name} {w}x{h}')
    engine.close()
