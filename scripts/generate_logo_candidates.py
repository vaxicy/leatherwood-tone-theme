"""Leatherwood Tone Theme - code-drawn logo candidates.

Concept: olive-green leather + wood / growth-ring grain ("leatherwood").
Everything is drawn with Pillow at 4x supersampling (numpy only feeds the
grain + growth-ring textures) so previews stay crisp; the olive palette is
read straight from manifest.json so the logo can never drift from the theme.

Every candidate ends up as a rounded-square badge with transparent corners,
matching the other themes in this collection.

Run from the project root:
    python3 scripts/generate_logo_candidates.py

Output: store-assets/icon-candidates/
    candidate-NN-<slug>.png       512px preview (RGBA)
    candidate-NN-<slug>-128.png   final-size check (size a Chrome theme needs)
    contact-sheet.png             every candidate + 128 / 64px legibility check
"""

import json
import math
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

SS = 4                       # supersample factor
PREVIEW = 512                # preview canvas
FINAL = 128                  # the only size a Chrome theme icon needs
SMALL = 64                   # small-size legibility check
CORNER = 0.23                # corner radius of the badge, as a share of the side
DEST = "store-assets/icon-candidates"


# ----------------------------------------------------------------- palette
def _manifest_colors():
    with open("manifest.json", encoding="utf-8") as fh:
        return json.load(fh)["theme"]["colors"]


_MC = _manifest_colors()


def MC(key):
    return tuple(_MC[key])


OLIVE_DEEP = MC("toolbar")               # 71, 76, 36
OLIVE = MC("frame")                      # 108, 113, 16
OLIVE_LT = MC("button_background")       # 159, 165, 64
OLIVE_PALE = MC("bookmark_text")         # 192, 193, 164
CREAM = MC("tab_text")                   # 240, 240, 234

# warm leather / bark accents - the theme has no brown slot, these are the
# tanned-leather half of "leatherwood" and stay in the same muted family.
BARK = (88, 60, 34)
BARK_LT = (140, 102, 60)
PATCH = (156, 115, 68)
TAN = (176, 143, 100)


def blend(a, b, t):
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


# ----------------------------------------------------------------- textures
def _noise(h, w, scale, seed, blur=1.2):
    """Smooth 0..1 noise field, generated small and upscaled."""
    rnd = np.random.default_rng(seed)
    sh, sw = max(4, h // scale), max(4, w // scale)
    small = rnd.random((sh, sw)).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8), "L")
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(img, dtype=np.float32) / 255.0


def grain(img, seed=1, amount=9.0, scale=12):
    """Additive leather grain - mean brightness (hence the colour) is kept."""
    h, w = img.height, img.width
    arr = np.asarray(img, dtype=np.float32)
    smooth = _noise(h, w, scale, seed) - 0.5
    speck = np.random.default_rng(seed + 977).normal(0.0, 1.0, (h, w)).astype(np.float32)
    delta = (smooth * 1.7 + speck * 0.85) * amount
    arr = np.clip(arr + delta[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def wood_lines(img, color, seed=1, strength=0.42, period=0.03, warp=2.6, axis="y"):
    """Growth-ring lines: wavy sine bands, softened by low-frequency noise."""
    h, w = img.height, img.width
    arr = np.asarray(img, dtype=np.float32)
    bend = _noise(h, w, 40, seed, blur=h * 0.01)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u = yy if axis == "y" else xx
    phase = u / (period * h) + (bend - 0.5) * warp
    mask = np.clip(np.sin(phase * 2 * math.pi), 0.0, None) ** 1.6 * strength
    out = arr * (1 - mask[..., None]) + np.array(color, np.float32) * mask[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


# ----------------------------------------------------------------- masks
def circle_mask(S, cx, cy, r):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    return m


def ring_mask(S, cx, cy, r, width):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], outline=255, width=width)
    return m


def rrect_mask(S, box, radius):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=radius, fill=255)
    return m


def leaf_mask(S, cx, cy, hw, hh, angle=0.0):
    """Pointed-oval leaf: the lens where two circles overlap."""
    d = (hh ** 2 - hw ** 2) / (2 * hw)
    r = hw + d
    m = ImageChops.darker(circle_mask(S, cx - d, cy, r), circle_mask(S, cx + d, cy, r))
    if angle:
        m = m.rotate(angle, resample=Image.BICUBIC, center=(cx, cy))
    return m


def paint(img, color, mask):
    img.paste(Image.new("RGB", img.size, color), (0, 0), mask)


def badge(img, S):
    """Clip the finished square to the rounded badge silhouette."""
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1],
                                           radius=CORNER * S, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


# ----------------------------------------------------------------- stitching
def rrect_path(box, radius, step=3.0):
    x0, y0, x1, y1 = box
    pts = []
    corners = [((x0 + radius, y0 + radius), 180, 270),
               ((x1 - radius, y0 + radius), 270, 360),
               ((x1 - radius, y1 - radius), 0, 90),
               ((x0 + radius, y1 - radius), 90, 180)]
    for (cx, cy), a0, a1 in corners:
        n = max(3, int(math.pi * radius / 2 / step))
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return pts


def circle_path(cx, cy, r, step=3.0):
    n = max(24, int(2 * math.pi * r / step))
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]


def stitch_along(draw, pts, spacing, length, color, width, step=2.5):
    """Sewing-machine stitches crossing the given path."""
    fine = []
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / step))
        for k in range(n):
            t = k / n
            fine.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    fine.append(pts[-1])

    acc = 0.0
    due = spacing * 0.5
    for i in range(1, len(fine)):
        (x0, y0), (x1, y1) = fine[i - 1], fine[i]
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg < 1e-6:
            continue
        acc += seg
        if acc >= due:
            tx, ty = (x1 - x0) / seg, (y1 - y0) / seg
            nx, ny = -ty, tx
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            draw.line([(mx - nx * length / 2, my - ny * length / 2),
                       (mx + nx * length / 2, my + ny * length / 2)],
                      fill=color, width=width)
            due = acc + spacing


def dashed_line(draw, x0, x1, y, dash, gap, color, width):
    x = x0
    while x < x1:
        draw.line([(x, y), (min(x + dash, x1), y)], fill=color, width=width)
        x += dash + gap


# ----------------------------------------------------------------- candidates
def c01_growth_rings(S):
    """Cross-section of a log: growth rings inside a bark rim."""
    img = Image.new("RGB", (S, S), CREAM)
    c = S / 2
    R = 0.372 * S
    body = Image.new("RGB", (S, S), OLIVE)
    body = wood_lines(body, OLIVE_DEEP, seed=11, strength=0.30, period=0.02, warp=2.0)
    body = grain(body, seed=12, amount=11)
    img.paste(body, (0, 0), circle_mask(S, c, c, R))

    d = ImageDraw.Draw(img)
    d.ellipse([c - R, c - R, c + R, c + R], outline=BARK, width=int(0.038 * S))
    rings = [(0.320, OLIVE_PALE), (0.262, OLIVE_LT), (0.204, OLIVE_PALE),
             (0.146, OLIVE_LT), (0.088, OLIVE_PALE)]
    for rad, col in rings:
        d.ellipse([c - rad * S, c - rad * S, c + rad * S, c + rad * S],
                  outline=col, width=int(0.0125 * S))
    paint(img, BARK_LT, circle_mask(S, c, c, 0.044 * S))
    return badge(grain(img, seed=13, amount=6), S)


def c02_leather_patch(S):
    """Tanned-leather patch, hand-sewn, with a pressed growth ring."""
    img = Image.new("RGB", (S, S), BARK)
    box = [0.175 * S, 0.175 * S, 0.825 * S, 0.825 * S]
    radius = 0.155 * S
    mask = rrect_mask(S, box, radius)

    patch = grain(Image.new("RGB", (S, S), PATCH), seed=21, amount=16, scale=9)
    patch = wood_lines(patch, BARK, seed=22, strength=0.16, period=0.09, warp=2.2)
    img.paste(patch, (0, 0), mask)

    d = ImageDraw.Draw(img)
    inset = 0.040 * S
    path = rrect_path([box[0] + inset, box[1] + inset, box[2] - inset, box[3] - inset],
                      radius - inset * 0.55)
    stitch_along(d, path, spacing=0.036 * S, length=0.020 * S,
                 color=CREAM, width=int(0.0072 * S))

    c = S / 2
    for rad, wd in ((0.158, 0.016), (0.104, 0.014)):
        d.ellipse([c - rad * S, c - rad * S, c + rad * S, c + rad * S],
                  outline=OLIVE_PALE, width=int(wd * S))
    paint(img, OLIVE, circle_mask(S, c, c, 0.054 * S))
    return badge(grain(img, seed=23, amount=5), S)


def c03_leaf_grain(S):
    """Olive leaf pressed into a grained board."""
    img = Image.new("RGB", (S, S), CREAM)
    box = [0.135 * S, 0.135 * S, 0.865 * S, 0.865 * S]
    mask = rrect_mask(S, box, 0.165 * S)

    base = grain(Image.new("RGB", (S, S), OLIVE_DEEP), seed=31, amount=12)
    base = wood_lines(base, OLIVE_LT, seed=32, strength=0.38, period=0.078, warp=0.9)
    img.paste(base, (0, 0), mask)

    c = S / 2
    lm = leaf_mask(S, c, c, 0.128 * S, 0.250 * S)
    leaf = grain(Image.new("RGB", (S, S), OLIVE_LT), seed=33, amount=10, scale=8)
    img.paste(leaf, (0, 0), lm)

    d = ImageDraw.Draw(img)
    d.line([(c, c - 0.220 * S), (c, c + 0.220 * S)], fill=OLIVE_PALE, width=int(0.014 * S))
    for i in range(4):
        y = c - 0.135 * S + i * 0.087 * S
        span = 0.074 * S * (1.0 - abs(i - 1.4) / 4.4)
        d.line([(c, y), (c - span, y + 0.045 * S)], fill=OLIVE_PALE, width=int(0.0095 * S))
        d.line([(c, y), (c + span, y + 0.045 * S)], fill=OLIVE_PALE, width=int(0.0095 * S))
    return badge(grain(img, seed=34, amount=5), S)


def c04_stacked_slabs(S):
    """Three stacked slats: olive wood, stitched leather, dark wood."""
    img = Image.new("RGB", (S, S), OLIVE_DEEP)
    h = 0.155 * S
    gap = 0.050 * S
    total = 3 * h + 2 * gap
    top = (S - total) / 2
    left = 0.185 * S
    width = S - 2 * left
    specs = [(OLIVE_LT, OLIVE_PALE, 41), (BARK_LT, BARK, 42), (OLIVE, OLIVE_LT, 43)]

    for i, (fill, line, seed) in enumerate(specs):
        y0 = top + i * (h + gap)
        mask = rrect_mask(S, [left, y0, left + width, y0 + h], h / 2)
        slab = grain(Image.new("RGB", (S, S), fill), seed=seed, amount=13, scale=10)
        slab = wood_lines(slab, blend(fill, line, 0.9), seed=seed + 100,
                          strength=0.30, period=0.019, warp=2.4)
        img.paste(slab, (0, 0), mask)

    d = ImageDraw.Draw(img)
    y_mid = top + h + gap
    for y in (y_mid + 0.030 * S, y_mid + h - 0.030 * S):
        dashed_line(d, left + 0.055 * S, left + width - 0.055 * S, y,
                    dash=0.020 * S, gap=0.016 * S, color=CREAM, width=int(0.0072 * S))
    return badge(grain(img, seed=44, amount=6), S)


def c05_stitched_circle(S):
    """Round leather badge: rim stitching around a ring core."""
    img = Image.new("RGB", (S, S), CREAM)
    c = S / 2
    R = 0.360 * S
    disc = Image.new("RGB", (S, S), OLIVE)
    disc = wood_lines(disc, OLIVE_DEEP, seed=51, strength=0.26, period=0.021, warp=2.2)
    disc = grain(disc, seed=52, amount=12)
    img.paste(disc, (0, 0), circle_mask(S, c, c, R))

    d = ImageDraw.Draw(img)
    stitch_along(d, circle_path(c, c, 0.312 * S), spacing=0.040 * S,
                 length=0.021 * S, color=CREAM, width=int(0.0068 * S))
    paint(img, OLIVE_DEEP, circle_mask(S, c, c, 0.185 * S))
    d.ellipse([c - 0.132 * S, c - 0.132 * S, c + 0.132 * S, c + 0.132 * S],
              outline=OLIVE_PALE, width=int(0.016 * S))
    paint(img, BARK_LT, circle_mask(S, c, c, 0.052 * S))
    return badge(grain(img, seed=53, amount=6), S)


def c06_twin_rings(S):
    """Two interlocking rings: olive wood meeting tanned leather."""
    img = Image.new("RGB", (S, S), OLIVE_DEEP)
    c = S / 2
    cy = c
    r = 0.212 * S
    w = int(0.072 * S)
    x1, x2 = c - 0.088 * S, c + 0.088 * S

    left = ring_mask(S, x1, cy, r, w)
    right = ring_mask(S, x2, cy, r, w)
    paint(img, OLIVE_LT, left)
    paint(img, TAN, right)
    paint(img, blend(OLIVE_LT, TAN, 0.5), ImageChops.darker(left, right))
    return badge(grain(img, seed=61, amount=6), S)


CANDIDATES = [
    ("01-growth-rings", "growth rings", c01_growth_rings),
    ("02-leather-patch", "leather patch", c02_leather_patch),
    ("03-leaf-grain", "leaf on grain", c03_leaf_grain),
    ("04-stacked-slabs", "stacked slabs", c04_stacked_slabs),
    ("05-stitched-circle", "stitched circle", c05_stitched_circle),
    ("06-twin-rings", "twin rings", c06_twin_rings),
]


# ----------------------------------------------------------------- rendering
def render(fn, size):
    return fn(size * SS).resize((size, size), Image.LANCZOS)


def load_font(size):
    for name in ("segoeui.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(items):
    cols = 3
    cell_w, cell_h = 340, 350
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, (slug, label, big, mid, small) in enumerate(items):
        x = (i % cols) * cell_w
        y = (i // cols) * cell_h
        d.rounded_rectangle([x + 10, y + 10, x + cell_w - 10, y + cell_h - 10],
                            radius=16, fill=(236, 235, 228), outline=(219, 217, 207))
        sheet.paste(big.resize((232, 232), Image.LANCZOS), (x + 24, y + 24),
                    big.resize((232, 232), Image.LANCZOS))
        sheet.paste(mid, (x + 272, y + 24), mid)
        sheet.paste(small, (x + 272, y + 168), small)
        d.text((x + 24, y + 272), f"{i + 1}. {label}", fill=(48, 46, 36), font=load_font(19))
        d.text((x + 24, y + 300), slug, fill=(150, 148, 138), font=load_font(14))
        d.text((x + 272, y + 240), "128", fill=(150, 148, 138), font=load_font(13))
        d.text((x + 272, y + 208), "512\u2192", fill=(200, 198, 190), font=load_font(11))
    return sheet


def main():
    if not os.path.exists("manifest.json"):
        raise SystemExit("run this from the project root (manifest.json not found)")
    os.makedirs(DEST, exist_ok=True)
    items = []
    for slug, label, fn in CANDIDATES:
        img = render(fn, PREVIEW)
        img.save(os.path.join(DEST, f"candidate-{slug}.png"))
        final = render(fn, FINAL)          # straight from the supersampled draw
        final.save(os.path.join(DEST, f"candidate-{slug}-{FINAL}.png"))
        items.append((slug, label, img, final,
                      img.resize((SMALL, SMALL), Image.LANCZOS)))
        print(f"wrote candidate-{slug}.png / candidate-{slug}-{FINAL}.png")

    sheet = contact_sheet(items)
    sheet.save(os.path.join(DEST, "contact-sheet.png"))
    print(f"wrote contact-sheet.png ({sheet.width}x{sheet.height})")
    print(f"\n{len(CANDIDATES)} candidates in {os.path.abspath(DEST)}")


if __name__ == "__main__":
    main()
