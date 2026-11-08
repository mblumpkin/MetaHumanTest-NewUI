"""
make_ui_textures.py
===================

Builds every PNG texture the IHPC (Avatar Injury Prevention) UI needs, using the
assets exported from the Figma file "Avatar Injury Prevention Program".

Run from the project root:
    python -I Tools/FigmaUI/make_ui_textures.py

Input : SourceArt/Figma/Original/   (raw files downloaded from Figma)
Output: SourceArt/Figma/UE/         (PNG files ready to import into Unreal)

Why a script?
  * Unreal cannot import SVG files, so the small vector icons from Figma
    (toggle, chevrons, zoom) are rasterised here from their exact SVG numbers.
  * The video-card art in Figma has the text baked into the picture. The UI needs
    the text to come from data, so this script rebuilds a text-free card
    background from the original pixels.
  * Anyone on the team can re-run it after the Figma file changes.

Every icon is rendered at 4x its Figma size so it stays sharp on high-DPI screens.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "SourceArt", "Figma", "Original")
OUT = os.path.join(ROOT, "SourceArt", "Figma", "UE")

ICON_SCALE = 4      # final pixels per Figma pixel
SUPERSAMPLE = 8     # draw this much bigger, then shrink, for smooth (anti-aliased) edges


# ---------------------------------------------------------------------------
# Small drawing helpers
# ---------------------------------------------------------------------------

def new_canvas(w, h):
    """Transparent canvas big enough to draw a w x h (Figma px) icon supersampled."""
    k = ICON_SCALE * SUPERSAMPLE
    return Image.new("RGBA", (round(w * k), round(h * k)), (0, 0, 0, 0)), k


def finish(img, w, h, name):
    """Shrink the supersampled canvas to 4x size and save it."""
    final = img.resize((round(w * ICON_SCALE), round(h * ICON_SCALE)), Image.LANCZOS)
    path = os.path.join(OUT, name)
    final.save(path)
    print("wrote", os.path.relpath(path, ROOT), final.size)


def rgba(hex_color, opacity=1.0):
    """'#RRGGBB' + opacity (0..1) -> (r, g, b, a) tuple."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return (r, g, b, round(255 * opacity))


def layer(base, draw_fn):
    """Draw on a separate transparent layer, then alpha-composite it onto base.
    This reproduces how Figma stacks semi-transparent shapes."""
    top = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(top))
    return Image.alpha_composite(base, top)


def stroke_polyline(draw, pts, k, width, color):
    """Polyline with round caps and round joins (SVG stroke-linecap/linejoin=round)."""
    scaled = [(x * k, y * k) for x, y in pts]
    w = width * k
    draw.line(scaled, fill=color, width=round(w))
    r = w / 2
    for x, y in scaled:  # round caps + joins
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


# ---------------------------------------------------------------------------
# 1. Toggle switch (Figma "Component 4", 38 x 20)
# ---------------------------------------------------------------------------

def make_toggle(name, track_hex, track_opacity, knob_cx, knob_opacity):
    img, k = new_canvas(38, 20)
    # <rect width="38" height="20" rx="10" fill=track>
    img = layer(img, lambda d: d.rounded_rectangle([0, 0, 38 * k, 20 * k], radius=10 * k,
                                                   fill=rgba(track_hex, track_opacity)))
    # <circle cx=knob_cx cy="10" r="8.5" fill="white">
    img = layer(img, lambda d: d.ellipse([(knob_cx - 8.5) * k, 1.5 * k, (knob_cx + 8.5) * k, 18.5 * k],
                                         fill=rgba("#FFFFFF", knob_opacity)))
    finish(img, 38, 20, name)


# ---------------------------------------------------------------------------
# 2. Chevrons
# ---------------------------------------------------------------------------

def make_small_chevron():
    """Accordion chevron (Figma vector 15 x 9.52635, stroke 2, white).
    The SVG path points UP; the DOWN version is a vertical flip."""
    w, h = 15, 9.52635
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    stroke_polyline(d, [(1.00003, 8.52632), (7.15793, 1), (14, 8.52632)], k, 2, rgba("#FFFFFF"))
    finish(img, w, h, "T_IHPC_Chevron_Up.png")
    finish(img.transpose(Image.FLIP_TOP_BOTTOM), w, h, "T_IHPC_Chevron_Down.png")


def make_header_chevron(name_up, name_down, hex_color):
    """Header toggle chevron (Figma 'Vector 2', 27 x 12, stroke 5)."""
    w, h = 27.0006, 12.0003
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    stroke_polyline(d, [(2.50032, 9.5), (13.5003, 2.5), (24.5003, 9.5)], k, 5, rgba(hex_color))
    finish(img, w, h, name_up)
    if name_down:
        finish(img.transpose(Image.FLIP_TOP_BOTTOM), w, h, name_down)


# ---------------------------------------------------------------------------
# 3. Zoom icon (Figma 'Vector', 20 x 19, stroke 2, white)
# ---------------------------------------------------------------------------

def make_zoom():
    w, h = 20, 19
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    white = rgba("#FFFFFF")
    # magnifier ring: centre (8.92, 9.107), radii 7.92 x 8.107
    cx, cy, rx, ry = 8.92, 9.107, 7.92, 8.107
    ring = [(cx + rx * math.cos(t), cy + ry * math.sin(t))
            for t in np.linspace(0, 2 * math.pi, 181)]
    stroke_polyline(d, ring, k, 2, white)
    stroke_polyline(d, [(5.32, 9.10699), (12.52, 9.10699)], k, 2, white)   # plus: horizontal
    stroke_polyline(d, [(8.92, 5.422), (8.92, 12.792)], k, 2, white)       # plus: vertical
    stroke_polyline(d, [(15.0789, 14.4069), (19, 18)], k, 2, white)        # handle
    finish(img, w, h, "T_IHPC_Zoom.png")


# ---------------------------------------------------------------------------
# 4. Raster icons supplied as PNG in Figma (just resized)
# ---------------------------------------------------------------------------

def resize_png(src_name, figma_w, figma_h, out_name):
    im = Image.open(os.path.join(SRC, src_name)).convert("RGBA")
    im = im.resize((figma_w * ICON_SCALE, figma_h * ICON_SCALE), Image.LANCZOS)
    path = os.path.join(OUT, out_name)
    im.save(path)
    print("wrote", os.path.relpath(path, ROOT), im.size)


# ---------------------------------------------------------------------------
# 5. Gradients that UMG cannot draw by itself
# ---------------------------------------------------------------------------

def make_title_glow():
    """Glow behind the title text: Figma linear-gradient, colour rgb(211,216,169),
    alpha 0 at 12.5%, 0.35 at 51.923%, 0 at 89.904% (576 x 54 in Figma)."""
    w, h = 512, 8
    stops = [(0.0, 0.0), (0.125, 0.0), (0.51923, 0.35), (0.89904, 0.0), (1.0, 0.0)]
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = 211, 216, 169
    xs = np.linspace(0, 1, w)
    alpha = np.interp(xs, [s[0] for s in stops], [s[1] for s in stops])
    arr[..., 3] = (alpha * 255).round().astype(np.uint8)[None, :]
    path = os.path.join(OUT, "T_IHPC_TitleGlow.png")
    Image.fromarray(arr).save(path)
    print("wrote", os.path.relpath(path, ROOT), (w, h))


def make_drop_shadow():
    """Shadow under the title bar / nav bar: CSS box-shadow 0 7px 6.3px rgba(0,0,0,0.25).
    One column of pixels: row d = d pixels below the bar's bottom edge."""
    rows = 24
    sigma = 6.3 / 2.0  # CSS blur radius = 2 x standard deviation
    arr = np.zeros((rows, 4, 4), dtype=np.uint8)
    for d in range(rows):
        # Fraction of the offset shadow still covering this row after the blur.
        coverage = 0.5 * math.erfc((d + 0.5 - 7.0) / (sigma * math.sqrt(2)))
        arr[d, :, 3] = round(255 * 0.25 * coverage)
    path = os.path.join(OUT, "T_IHPC_DropShadow.png")
    Image.fromarray(arr).save(path)
    print("wrote", os.path.relpath(path, ROOT), (4, rows))


# ---------------------------------------------------------------------------
# 6. Text-free video card background
# ---------------------------------------------------------------------------

def make_video_card_background():
    """The Figma 'videos row' uses one picture (video_cards.png) that holds three
    finished cards, text included. Rebuild one card with no text and no white
    severity tick, so Unreal can draw the title/date/time/tick from data.

    Measured from the picture (pixels in video_cards.png):
      card 1 x 49-724, card 2 x 1029-1704, card 3 x 2009-2684, all y 44-311
      white tick: 8 px wide, rows 45-82 (card 1 x_rel 114-121, card 3 x_rel 592-599)
      severity bar: rows 57-70, body: rows 71-311
      text starts at x_rel ~237, so x_rel >= 232 is plain left-to-right gradient
    """
    src = np.array(Image.open(os.path.join(SRC, "video_cards.png")).convert("RGBA")).astype(np.int32)
    top, bottom = 44, 311
    card1 = src[top:bottom + 1, 49:725].copy()
    card3 = src[top:bottom + 1, 2009:2685].copy()

    out = card3.copy()                                      # icon panel + bar from card 3
    out[:, 586:606] = card1[:, 586:606]                    # remove card 3's tick using card 1 pixels

    # Remove the text: every text-free row of the body is identical, so copy one
    # clean row (y=280 in the source) down the whole body, keeping the alpha
    # (which holds the rounded bottom corners).
    clean_row = 280 - top
    body_top = 71 - top
    for x in range(232, out.shape[1]):
        col = clean_row
        # near the rounded right corner, borrow the colour from the nearest solid column
        sx = x
        while out[col, sx, 3] < 255 and sx > 232:
            sx -= 1
        out[body_top:, x, :3] = out[col, sx, :3]

    img = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    path = os.path.join(OUT, "T_IHPC_VideoCard_BG.png")
    img.save(path)
    print("wrote", os.path.relpath(path, ROOT), img.size)


# ---------------------------------------------------------------------------
# 7. Playback / timeline bar (Figma layer "ihpc ui (1)ee 1" on frame "iPad Pro 12.9" - 1")
# ---------------------------------------------------------------------------

# Bounding boxes (x0, y0, x1, y1, inclusive) of each glossy button inside timeline_raw_1.png.
# That picture is 3146 x 306 = 3x the 1048 x 102 Figma layer. Measured from its alpha channel.
TIMELINE_BUTTONS = {
    "T_IHPC_TL_Record":      (61, 84, 197, 220),
    "T_IHPC_TL_Restart":     (227, 65, 400, 238),
    "T_IHPC_TL_Pause":       (430, 54, 624, 248),
    "T_IHPC_TL_SlowDown":    (651, 87, 788, 223),
    "T_IHPC_TL_SpeedUp":     (2396, 81, 2533, 218),
    "T_IHPC_TL_Play":        (2562, 54, 2756, 248),
    "T_IHPC_TL_FastForward": (2782, 68, 2950, 235),
    "T_IHPC_TL_Bookmark":    (2975, 84, 3111, 220),
}


def make_timeline_assets():
    """Cuts the buttons and the slider knob out of the Figma timeline picture, and draws the
    orange marker dot. The track itself is drawn by Unreal (two rounded bars), because its
    dark/light split has to move with the animation."""
    src = Image.open(os.path.join(SRC, "timeline_raw_1.png")).convert("RGBA")

    # Buttons: exact crops (each button is separate, so the crop has a transparent background).
    for name, (x0, y0, x1, y1) in TIMELINE_BUTTONS.items():
        crop = src.crop((x0, y0, x1 + 1, y1 + 1))
        path = os.path.join(OUT, name + ".png")
        crop.save(path)
        print("wrote", os.path.relpath(path, ROOT), crop.size)

    # Knob: centre (1661.5, 148), radius 64.5 px in the 3x picture (43 px across in Figma).
    # It sits on top of the track, so cut a circle out (everything outside -> transparent).
    cx, cy, r = 1661.5, 148.0, 64.6
    box = (int(cx - r - 1), int(cy - r - 1), int(cx + r + 2), int(cy + r + 2))
    knob = np.array(src.crop(box)).astype(np.float32)
    h, w = knob.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx + box[0] + 0.5 - cx) ** 2 + (yy + box[1] + 0.5 - cy) ** 2)
    coverage = np.clip(r - dist + 0.5, 0.0, 1.0)            # 1 inside, 0 outside, smooth 1 px edge
    knob[..., 3] = knob[..., 3] * coverage
    path = os.path.join(OUT, "T_IHPC_TL_Thumb.png")
    Image.fromarray(knob.clip(0, 255).astype(np.uint8)).save(path)
    print("wrote", os.path.relpath(path, ROOT), (w, h))

    # Marker: white ring 19 px across with an orange (#EB8D71) dot 13.67 px across (Figma px).
    img, k = new_canvas(19, 19)
    img = layer(img, lambda d: d.ellipse([0, 0, 19 * k, 19 * k], fill=rgba("#FFFFFF")))
    o = (19 - 13.67) / 2
    img = layer(img, lambda d: d.ellipse([o * k, o * k, (19 - o) * k, (19 - o) * k], fill=rgba("#EB8D71")))
    finish(img, 19, 19, "T_IHPC_TL_Marker.png")


# ---------------------------------------------------------------------------
# 8. Layer switcher / opacity buttons (Figma layers "ihpc ui rttd 2" + "Rectangle 24" on frame "iPad Pro 12.9" - 1")
# ---------------------------------------------------------------------------
# layers_f1_raw_1.png = the original picture used on frame 1 (Body selected),
# layers_f4_raw_1.png = the same component on frame 4 (Muscles selected).
# Both are 853 x 320 = 4.586x the 186 x 70 Figma layer. Each circle is 46 Figma px across.
# Nobody drew "Skeleton selected" in Figma, so it is built here from the other pictures.
# "Rectangle 24" (the pill behind the buttons) is a plain colour (#1D3C55 at 26 %, corner radius 35.5),
# so Unreal draws it as a rounded box - no texture needed.

LAYER_CIRCLE_X = {"Body": 158, "Muscles": 428, "Skeleton": 698}   # circle centres (x) in the 4.586x picture
LAYER_CIRCLE_TOP = 48            # crop rows 48..261 -> circle centre y = 155 (measured: circle spans y 50..259)
LAYER_CROP = 214                 # crop size (the circle is 211 px across, plus a 1-2 px margin)
LAYER_BADGE = (770.0, 80.5, 40.5)  # orange badge on the skeleton circle: centre x, y and radius incl. white ring + edge
LAYER_OFF_BG_BLUE = 227          # blue channel of the flat light-blue inside of an unselected circle (175, 203, 227)
LAYER_ICON_BLUE = 85             # blue channel of the navy icon lines on an unselected circle (24, 60, 85)


def _layer_crop(picture, name):
    x = LAYER_CIRCLE_X[name] - LAYER_CROP // 2
    return picture[LAYER_CIRCLE_TOP:LAYER_CIRCLE_TOP + LAYER_CROP, x:x + LAYER_CROP].copy()


def _save_rgba(arr, name):
    path = os.path.join(OUT, name)
    Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8)).save(path)
    print("wrote", os.path.relpath(path, ROOT), (arr.shape[1], arr.shape[0]))


def _diffuse_fill(img, mask, iterations=600):
    """Fills the masked pixels by repeatedly averaging their 4 neighbours. On a smooth gradient
    (the inside of the selected circle) this paints over thin lines without leaving a trace."""
    out = img.copy()
    out[mask] = img[~mask].mean(axis=0)
    for _ in range(iterations):
        avg = (np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 4.0
        out[mask] = avg[mask]
    return out


def _icon_alpha(unselected_crop):
    """How much of each pixel is icon (0..1), read from an UNSELECTED circle: there the icon is navy
    lines on a flat light-blue fill, so the blue channel tells how much icon covers the pixel."""
    n = unselected_crop.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    inside = np.hypot(xx + 0.5 - n / 2, yy + 0.5 - n / 2) < 85     # inside the inner ring only
    alpha = (LAYER_OFF_BG_BLUE - unselected_crop[..., 2]) / float(LAYER_OFF_BG_BLUE - LAYER_ICON_BLUE)
    return np.clip(alpha, 0.0, 1.0) * inside


def _grow(mask, pixels):
    """Make a yes/no mask a few pixels bigger (so anti-aliased edges are included)."""
    out = mask.copy()
    for _ in range(pixels):
        out = out | np.roll(out, 1, 0) | np.roll(out, -1, 0) | np.roll(out, 1, 1) | np.roll(out, -1, 1)
    return out


def make_layer_switcher_assets():
    """Six circle buttons (Body / Muscles / Skeleton, each selected = '_On' and unselected = '_Off')
    and the orange badge, as separate textures so Unreal can swap them when a layer is picked."""
    f1 = np.array(Image.open(os.path.join(SRC, "layers_f1_raw_1.png")).convert("RGBA")).astype(np.float32)
    f4 = np.array(Image.open(os.path.join(SRC, "layers_f4_raw_1.png")).convert("RGBA")).astype(np.float32)

    body_on, body_off = _layer_crop(f1, "Body"), _layer_crop(f4, "Body")
    muscles_on, muscles_off = _layer_crop(f4, "Muscles"), _layer_crop(f1, "Muscles")
    skeleton_off = _layer_crop(f1, "Skeleton")

    # 1. Skeleton (unselected) without the badge: the badge sits on the top-right of the rim, so those
    #    pixels are borrowed from another unselected circle (the rims are identical). The badge becomes
    #    its own widget, so it can be shown / hidden (e.g. "something new to look at").
    n = LAYER_CROP
    yy, xx = np.mgrid[0:n, 0:n]
    bx = LAYER_BADGE[0] - (LAYER_CIRCLE_X["Skeleton"] - n // 2)
    by = LAYER_BADGE[1] - LAYER_CIRCLE_TOP
    under_badge = np.hypot(xx + 0.5 - bx, yy + 0.5 - by) < LAYER_BADGE[2]
    skeleton_lines = (skeleton_off[..., 2] < 200) & (skeleton_off[..., 0] < 120) & (skeleton_off[..., 3] > 200)
    replace = under_badge & ~_grow(skeleton_lines, 2)
    skeleton_off[replace] = body_off[replace]

    # 2. An empty "selected" circle: the body and muscles icons are in different places, so where one
    #    circle has icon lines the other usually has clean background. Where both have lines,
    #    the gap is painted over from the surrounding gradient.
    body_lines = _grow(_icon_alpha(body_off) > 0.02, 3)
    muscle_lines = _grow(_icon_alpha(muscles_off) > 0.02, 3)
    empty_on = body_on.copy()
    empty_on[body_lines] = muscles_on[body_lines]
    empty_on = _diffuse_fill(empty_on, body_lines & muscle_lines)

    # 3. Selected = white icon on the dark glossy circle. The icon shape comes from the unselected picture.
    def selected_from(unselected):
        a = _icon_alpha(unselected)[..., None]
        out = empty_on.copy()
        out[..., :3] = empty_on[..., :3] * (1 - a) + 255.0 * a
        return out

    skeleton_on = selected_from(skeleton_off)

    # Check: rebuilding "Body selected" the same way should match Figma's real one.
    diff = np.abs(selected_from(body_off)[..., :3] - body_on[..., :3])
    print("layer switcher: rebuilt Body_On vs Figma, mean difference %.2f / 255" % diff.mean())

    for name, arr in [("Body_On", body_on), ("Body_Off", body_off),
                      ("Muscles_On", muscles_on), ("Muscles_Off", muscles_off),
                      ("Skeleton_On", skeleton_on), ("Skeleton_Off", skeleton_off)]:
        _save_rgba(arr, "T_IHPC_LS_%s.png" % name)

    # 4. Badge: white ring 16.8 px across with an orange (#EB8D71) dot 13.1 px across (Figma px).
    img, k = new_canvas(16.8, 16.8)
    img = layer(img, lambda d: d.ellipse([0, 0, 16.8 * k, 16.8 * k], fill=rgba("#FFFFFF")))
    o = (16.8 - 13.1) / 2
    img = layer(img, lambda d: d.ellipse([o * k, o * k, (16.8 - o) * k, (16.8 - o) * k], fill=rgba("#EB8D71")))
    finish(img, 16.8, 16.8, "T_IHPC_LS_Badge.png")


# ---------------------------------------------------------------------------
# 10. Close "X" for the tab panels (not in Figma - drawn in the same style as the header chevron)
# ---------------------------------------------------------------------------

def make_close_icon():
    """White X, 16 x 16 Figma px, stroke 2.6 with round caps (same rounded-stroke look as the
    header chevron / zoom icon). Sits on a navy circle button drawn by Unreal."""
    w = h = 16.0
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    m = 2.6 / 2 + 0.5                       # keep the round caps inside the canvas
    stroke_polyline(d, [(m, m), (w - m, h - m)], k, 2.6, rgba("#FFFFFF"))
    stroke_polyline(d, [(w - m, m), (m, h - m)], k, 2.6, rgba("#FFFFFF"))
    finish(img, w, h, "T_IHPC_Close.png")


# ---------------------------------------------------------------------------
# 9. Clean edges: "bleed" the colour into the invisible pixels (runs on every PNG at the end)
# ---------------------------------------------------------------------------
# A fully transparent pixel still stores a colour. Figma exports store WHITE there (our drawn icons store black).
# Unreal shrinks UI textures (mipmaps) and blends neighbouring pixels (trilinear filtering) WITHOUT weighting by
# transparency, so that hidden white/black leaks into the visible edge: dark glossy buttons get a light, ragged
# rim and white icons a dark one - it reads as "pixelated edges" when the button is drawn small.
# Fix: give every invisible pixel the colour of the nearest visible edge. Alpha is not changed, so the picture
# looks identical at full size; only the blending at the edges becomes clean.

def bleed_transparent_edges(path):
    img = np.array(Image.open(path).convert("RGBA")).astype(np.float32)
    alpha = img[..., 3] / 255.0
    known = alpha > 0
    if known.all() or not known.any():
        return
    rgb = img[..., :3].copy()
    weight = alpha.copy()                      # how much each known pixel counts (edge pixels count less)
    filled = known.copy()
    while not filled.all():
        acc = np.zeros_like(rgb)
        wsum = np.zeros_like(weight)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                w = np.roll(np.roll(weight * filled, dy, 0), dx, 1)
                acc += np.roll(np.roll(rgb, dy, 0), dx, 1) * w[..., None]
                wsum += w
        grow = ~filled & (wsum > 0)
        if not grow.any():
            break
        rgb[grow] = acc[grow] / wsum[grow][..., None]
        weight[grow] = 1.0
        filled |= grow
    img[..., :3] = np.where(known[..., None], img[..., :3], rgb)
    Image.fromarray(np.clip(np.round(img), 0, 255).astype(np.uint8)).save(path)


def bleed_all_outputs():
    names = sorted(f for f in os.listdir(OUT) if f.lower().endswith(".png"))
    for name in names:
        bleed_transparent_edges(os.path.join(OUT, name))
    print("clean edges (colour bled into transparent pixels):", len(names), "textures")


def main():
    os.makedirs(OUT, exist_ok=True)
    make_layer_switcher_assets()
    make_timeline_assets()
    make_toggle("T_IHPC_Toggle_Off.png", "#D9D9D9", 0.20, 10.5, 0.65)
    make_toggle("T_IHPC_Toggle_On.png", "#B3CA7F", 0.76, 27.5, 0.75)
    make_small_chevron()
    make_header_chevron("T_IHPC_HeaderChevron_Up.png", "T_IHPC_HeaderChevron_Down.png", "#FFFFFF")
    make_header_chevron("T_IHPC_HeaderChevron_Up_Blue.png", None, "#245983")
    make_zoom()
    resize_png("download_icon.png", 30, 30, "T_IHPC_Download.png")
    resize_png("inspect_code.png", 33, 33, "T_IHPC_InspectCode.png")
    make_title_glow()
    make_drop_shadow()
    make_video_card_background()
    make_close_icon()
    bleed_all_outputs()        # must be last: fixes the edges of every texture made above


if __name__ == "__main__":
    main()
