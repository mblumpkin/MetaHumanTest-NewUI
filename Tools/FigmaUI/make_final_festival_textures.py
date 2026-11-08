"""
make_final_festival_textures.py
===============================

Builds the PNG textures for the FINAL FESTIVAL redesign of the IHPC UI (Figma file
"Avatar Injury Prevention Program", page "FINAL FESTIVAL", 2026-11-08): the side bar that
replaced the drop-down nav bar, the side panels, the assistant (BOT) chat window and the
reset-view button.

Run from the project root (after make_ui_textures.py, which makes the older textures):
    python -I Tools/FigmaUI/make_final_festival_textures.py

Inputs
  Icons/                                  high-quality side bar icons supplied with the redesign (211 x 211):
                                          "<Name>.png" = frosted glass circle, "Active <Name>.png" = selected look
  SourceArt/Figma/Original/v2_FinalFestival/   assets downloaded from the FINAL FESTIVAL page
Output
  SourceArt/Figma/UE/T_IHPC_*.png         (same folder as the older textures; imported by ue_import_textures.py)

Every drawn icon is rendered at 4x its Figma size (like make_ui_textures.py), the Icons pictures are used at their
full 211 px (drawn at 55 px in Unreal), and every output gets the clean-edge fix (bleed_transparent_edges).
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

# Re-use the helpers of the original texture script (same folder). -I does not add the script folder to sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_ui_textures import (ROOT, SRC, OUT, ICON_SCALE, new_canvas, finish, rgba,   # noqa: E402
                              stroke_polyline, bleed_transparent_edges)

ICONS = os.path.join(ROOT, "Icons")
SRC2 = os.path.join(SRC, "v2_FinalFestival")

WRITTEN = []   # every PNG this script makes (only these get the edge fix, the older ones are left alone)


def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path)
    WRITTEN.append(path)
    print("wrote", os.path.relpath(path, ROOT), img.size)


def finish_tracked(img, w, h, name):
    finish(img, w, h, name)
    WRITTEN.append(os.path.join(OUT, name))


# ---------------------------------------------------------------------------
# 1. Side bar buttons (Icons folder): normal + selected look for every tab and layer button
# ---------------------------------------------------------------------------

SIDEBAR_ICONS = {
    # output name               normal picture          selected picture
    "T_IHPC_SB_Skin":           ("Skin.png",            "Active Skin.png"),
    "T_IHPC_SB_Muscles":        ("Muscles.png",         "Active Muscle.png"),
    "T_IHPC_SB_Skeleton":       ("Skeleton.png",        "Active Skeleton.png"),
    "T_IHPC_SB_Activity":       ("Activity.png",        "Active Activity.png"),
    "T_IHPC_SB_PoseEstimation": ("Pose Estimation.png", "Active Pose Estimation.png"),
    "T_IHPC_SB_Graph":          ("Graph.png",           "Active Graph.png"),
    "T_IHPC_SB_Timeline":       ("Timeline.png",        "Active Timeline.png"),
    "T_IHPC_SB_SavedVideos":    ("Saved Videos.png",    "Active Saved Videos.png"),
    "T_IHPC_SB_Settings":       ("Settings.png",        "Active Settings.png"),
    "T_IHPC_SB_Button":         ("Button.png",          "Active Button.png"),   # empty circles (chevron, X, send)
}


def make_sidebar_icons():
    for out_name, (normal, active) in SIDEBAR_ICONS.items():
        save(Image.open(os.path.join(ICONS, normal)).convert("RGBA"), out_name + ".png")
        save(Image.open(os.path.join(ICONS, active)).convert("RGBA"), out_name + "_Active.png")


# ---------------------------------------------------------------------------
# 2. Side bar chevron (Figma "rty" in "Group 30": 24 x 8 path, stroke 5, round caps / joins, white)
# ---------------------------------------------------------------------------

def make_sidebar_chevron():
    w, h = 29.0005, 13.0003                     # SVG canvas incl. the stroke
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    stroke_polyline(d, [(2.50027, 10.5), (14.5003, 2.5), (26.5003, 10.5)], k, 5, rgba("#FFFFFF"))
    finish_tracked(img, w, h, "T_IHPC_SB_Chevron_Up.png")                                # expanded: click = collapse
    finish_tracked(img.transpose(Image.FLIP_TOP_BOTTOM), w, h, "T_IHPC_SB_Chevron_Down.png")  # collapsed: click = expand


# ---------------------------------------------------------------------------
# 3. Assistant avatar (Figma "ihpc ui fe-05 1", object-cover in a 69 px circle)
# ---------------------------------------------------------------------------

def make_bot_avatar():
    src = Image.open(os.path.join(SRC2, "bot_avatar.png")).convert("RGBA")
    side = min(src.size)
    left, top = (src.width - side) // 2, (src.height - side) // 2
    square = src.crop((left, top, left + side, top + side))
    size = 69 * ICON_SCALE                      # 276
    square = square.resize((size, size), Image.LANCZOS)
    # Anti-aliased circle mask (drawn 8x bigger, then shrunk).
    big = Image.new("L", (size * 8, size * 8), 0)
    ImageDraw.Draw(big).ellipse([0, 0, size * 8 - 1, size * 8 - 1], fill=255)
    mask = big.resize((size, size), Image.LANCZOS)
    alpha = np.minimum(np.array(square.getchannel("A")), np.array(mask))
    square.putalpha(Image.fromarray(alpha.astype(np.uint8)))
    save(square, "T_IHPC_Bot.png")


# ---------------------------------------------------------------------------
# 4. Small white vector icons
# ---------------------------------------------------------------------------

def make_panel_close_x():
    """Side panel close X (Figma "Group 31": two strokes, 12.59 x 13, stroke 2, round caps)."""
    w, h = 12.5927, 13.0002
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    stroke_polyline(d, [(1, 1), (11.5927, 12.0002)], k, 2, rgba("#FFFFFF"))
    stroke_polyline(d, [(11.5927, 1), (1, 12.0002)], k, 2, rgba("#FFFFFF"))
    finish_tracked(img, w, h, "T_IHPC_PanelClose_X.png")


def make_graph_bookmark():
    """Graph card bookmark icon (Figma "Vector 17": 15 x 16 canvas, stroke 2, round joins)."""
    w, h = 15, 16
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    pts = [(7.74074, 8), (1, 15), (1, 1), (14, 1), (14, 15), (7.74074, 8)]
    stroke_polyline(d, pts, k, 2, rgba("#FFFFFF"))
    finish_tracked(img, w, h, "T_IHPC_GraphBookmark.png")


def make_graph_zoom():
    """Graph card zoom icon (Figma "Vector": 19 x 16 canvas, stroke 2, round caps) - flatter than the old one."""
    w, h = 19, 16
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    white = rgba("#FFFFFF")
    cx, cy, rx, ry = 8.48, 7.67635, 7.48, 6.67635
    ring = [(cx + rx * math.cos(t), cy + ry * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 181)]
    stroke_polyline(d, ring, k, 2, white)
    stroke_polyline(d, [(5.08, 7.67635), (11.88, 7.67635)], k, 2, white)     # plus: horizontal
    stroke_polyline(d, [(8.48, 4.64164), (8.48, 10.7111)], k, 2, white)      # plus: vertical
    stroke_polyline(d, [(14.2967, 12.041), (18, 15)], k, 2, white)           # handle
    finish_tracked(img, w, h, "T_IHPC_GraphZoom.png")


def make_accordion_chevrons():
    """Graphs panel header chevron (Figma "Vector 3" / "Vector 10": 14.36 x 9.16 canvas, stroke 2)."""
    w, h = 14.3637, 9.15793
    img, k = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    stroke_polyline(d, [(1.00003, 8.1579), (6.85649, 1), (13.3637, 8.1579)], k, 2, rgba("#FFFFFF"))
    finish_tracked(img, w, h, "T_IHPC_AccChevron_Up.png")
    finish_tracked(img.transpose(Image.FLIP_TOP_BOTTOM), w, h, "T_IHPC_AccChevron_Down.png")


# ---------------------------------------------------------------------------
# 5. Raster icons supplied as PNG in Figma
# ---------------------------------------------------------------------------

def make_chat_send():
    """Send arrow (Figma "ihpc ui (1) 5ad": an 18 x 20 window onto a 3-icon sprite sheet; it shows the filled arrow).
    Window in Figma: image 444.44% x 230.43% of the box, shifted -294.44% / -65.22% -> sprite pixels below."""
    src = Image.open(os.path.join(SRC2, "send_icon_sprite.png")).convert("RGBA")
    sx = src.width / (18 * 4.4444)               # sprite pixels per Figma px
    sy = src.height / (20 * 2.3043)
    box = (round(18 * 2.9444 * sx), round(20 * 0.6522 * sy), round(18 * 3.9444 * sx), round(20 * 1.6522 * sy))
    icon = src.crop(box).resize((18 * ICON_SCALE, 20 * ICON_SCALE), Image.LANCZOS)
    save(icon, "T_IHPC_ChatSend.png")


def make_reset_icon():
    """Reset view arrow (Figma frame 17 "ihpc ui (1) 6": 30.18 x 32.63, white)."""
    src = Image.open(os.path.join(SRC2, "reset_icon_raw.png")).convert("RGBA")
    save(src.resize((round(30.18 * ICON_SCALE), round(32.63 * ICON_SCALE)), Image.LANCZOS), "T_IHPC_ResetView.png")


# ---------------------------------------------------------------------------
# 6. Action card picture (Figma frame 19 "Rectangle 101-110" + "Rectangle 105-110")
# ---------------------------------------------------------------------------

def make_action_card():
    """269 x 147, radius 14: the mannequin picture (object-cover) with the Figma gradient on top
    (rgb(211,216,169), alpha 0 at the top -> 0.53 at the bottom). The label is a real text widget."""
    w, h, radius = 269, 147, 14
    W, H = w * ICON_SCALE, h * ICON_SCALE       # 1076 x 588
    src = Image.open(os.path.join(SRC2, "action_card_raw_1.png")).convert("RGBA")
    scale = max(W / src.width, H / src.height)  # object-cover
    resized = src.resize((math.ceil(src.width * scale), math.ceil(src.height * scale)), Image.LANCZOS)
    left, top = (resized.width - W) // 2, (resized.height - H) // 2
    card = np.array(resized.crop((left, top, left + W, top + H))).astype(np.float32)
    card[..., 3] = 255.0

    # Gradient overlay, alpha-composited like Figma.
    a = np.linspace(0.0, 0.53, H)[:, None]
    for c, v in enumerate((211, 216, 169)):
        card[..., c] = card[..., c] * (1 - a) + v * a

    # Rounded corners (anti-aliased mask).
    big = Image.new("L", (W * 4, H * 4), 0)
    ImageDraw.Draw(big).rounded_rectangle([0, 0, W * 4 - 1, H * 4 - 1], radius=radius * ICON_SCALE * 4, fill=255)
    card[..., 3] = np.array(big.resize((W, H), Image.LANCZOS)).astype(np.float32)
    save(Image.fromarray(np.clip(np.round(card), 0, 255).astype(np.uint8)), "T_IHPC_ActionCard.png")


# ---------------------------------------------------------------------------
# 7. Side panel shadow (Figma "Rectangle 31": box-shadow 0 7px 6.3px rgba(0,0,0,0.25), on the panel's right edge)
# ---------------------------------------------------------------------------

def make_side_panel_shadow():
    """One row of pixels: column d = d pixels to the right of the panel's edge (same maths as the title bar's
    T_IHPC_DropShadow, turned sideways because the Figma frame is drawn rotated)."""
    cols = 24
    sigma = 6.3 / 2.0
    arr = np.zeros((4, cols, 4), dtype=np.uint8)
    for d in range(cols):
        coverage = 0.5 * math.erfc((d + 0.5 - 7.0) / (sigma * math.sqrt(2)))
        arr[:, d, 3] = round(255 * 0.25 * coverage)
    save(Image.fromarray(arr), "T_IHPC_DropShadowRight.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    make_sidebar_icons()
    make_sidebar_chevron()
    make_bot_avatar()
    make_panel_close_x()
    make_graph_bookmark()
    make_graph_zoom()
    make_accordion_chevrons()
    make_chat_send()
    make_reset_icon()
    make_action_card()
    make_side_panel_shadow()
    for path in WRITTEN:                        # must be last: clean edges on every texture made above
        bleed_transparent_edges(path)
    print("clean edges:", len(WRITTEN), "textures")
    # The list ue_import_textures.py needs to import only these (see its import_textures(only=...)).
    print("IMPORT_LIST =", sorted(os.path.splitext(os.path.basename(p))[0] for p in WRITTEN))


if __name__ == "__main__":
    main()
