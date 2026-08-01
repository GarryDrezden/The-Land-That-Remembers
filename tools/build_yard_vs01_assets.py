#!/usr/bin/env python3
"""
Bake VS01 yard runtime assets for childhood-home outdoor candidate.

- Does not modify upload/ originals (copies selected props).
- Prepares approved main_house_v1 (key black BG, crop, integer nearest ÷4).
- Bakes a cohesive grass + dirt-path ground plate.
- Keeps props near the hero scale bible (16px tile, ~23px hero display).
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "art" / "outdoor" / "yard_vs01"
UPLOAD = ROOT / "upload"

TILE = 16
MAP_W = 40
MAP_H = 34
GROUND_W = MAP_W * TILE
GROUND_H = MAP_H * TILE

GRASS_A = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/grass_16.png"
GRASS_B = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/grass_16_b.png"
DIRT_A = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/dirt_16.png"
DIRT_B = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/dirt_16_b.png"
HOUSE_SRC = UPLOAD / "houses" / "main_house_v1.png"
## Integer nearest downsample after crop; door ~32px vs hero ~23px (~71%).
HOUSE_PIXEL_DIV = 4
## Extra nearest shrink after ÷4 so the house fits the start frame with air (~12%).
HOUSE_DISPLAY_SCALE = 0.88
# Manual door rect on keyed crop (x0,y0,x1,y1) — verified visually.
HOUSE_DOOR_CROP = (430, 338, 478, 468)

PROP_COPY = {
    "rock_sm.png": UPLOAD
    / "rocks-and-stones-top-down-pixel-art/PNG/Objects_separately/Rock1_5_no_shadow.png",
    "rock_md.png": UPLOAD
    / "rocks-and-stones-top-down-pixel-art/PNG/Objects_separately/Rock2_4_no_shadow.png",
    "rock_lg.png": UPLOAD
    / "rocks-and-stones-top-down-pixel-art/PNG/Objects_separately/Rock3_3_no_shadow.png",
    "bush_sm.png": UPLOAD / "bushes-pixel-art/PNG/Assets/Bush_simple1_3.png",
    "bush_md.png": UPLOAD / "bushes-pixel-art/PNG/Assets/Bush_simple1_2.png",
    "bush_overgrown.png": UPLOAD / "bushes-pixel-art/PNG/Assets/Bush_simple2_2.png",
    "tree_a.png": UPLOAD / "trees-pixel-art/PNG/Assets_separately/Trees/Tree2.png",
    "tree_b.png": UPLOAD / "trees-pixel-art/PNG/Assets_separately/Trees/Moss_tree2.png",
    "tree_c.png": UPLOAD / "trees-pixel-art/PNG/Assets_separately/Trees/Broken_tree4.png",
}


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def nearest_fit(im: Image.Image, max_w: int, max_h: int) -> Image.Image:
    w, h = im.size
    if w <= max_w and h <= max_h:
        return im
    scale = min(max_w / w, max_h / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return im.resize((nw, nh), Image.NEAREST)


def draw_izba() -> Image.Image:
    """Temporary old Russian wooden house — top-down/¾, weathered, not cute."""
    w, h = 144, 112
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()

    def put(x: int, y: int, c: tuple[int, int, int, int]) -> None:
        if 0 <= x < w and 0 <= y < h:
            px[x, y] = c

    def fill_rect(x0, y0, x1, y1, c) -> None:
        for y in range(y0, y1):
            for x in range(x0, x1):
                put(x, y, c)

    # Roof (weathered grey-brown shingles / boards)
    roof_base = (78, 62, 48, 255)
    roof_dark = (58, 46, 36, 255)
    roof_edge = (42, 34, 28, 255)
    # Simple gable silhouette
    for y in range(0, 44):
        half = int((44 - y) * 1.55)
        cx = w // 2 + (1 if y % 7 == 0 else 0)  # slight crooked ridge
        for x in range(cx - half, cx + half + 1):
            shade = roof_dark if ((x + y * 3) % 5 == 0) else roof_base
            if y < 3 or abs(x - (cx - half)) < 2 or abs(x - (cx + half)) < 2:
                shade = roof_edge
            put(x, y, shade)
        # ridge board
        put(cx, y, roof_edge)

    # Walls — darkened log planks (weathered izba, not cottage pastel)
    wall_y0, wall_y1 = 40, 100
    wall_x0, wall_x1 = 18, 126
    for y in range(wall_y0, wall_y1):
        row = (y - wall_y0) // 5
        for x in range(wall_x0, wall_x1):
            base = (74, 54, 38, 255) if row % 2 == 0 else (62, 46, 32, 255)
            if (x + row * 5) % 13 == 0:
                base = (48, 34, 24, 255)  # weathered streak
            if (x + y) % 29 == 0:
                base = (88, 70, 48, 255)  # dry board highlight
            if x in (wall_x0, wall_x1 - 1) or y in (wall_y0, wall_y1 - 1):
                base = (40, 28, 20, 255)
            put(x, y, base)
            # log groove
            if (y - wall_y0) % 5 == 4:
                put(x, y, (44, 30, 20, 255))
            # end notches
            if x in (wall_x0 + 1, wall_x1 - 2) and (y - wall_y0) % 5 < 2:
                put(x, y, (52, 36, 24, 255))

    # Foundation / sill
    fill_rect(16, 98, 128, 106, (70, 66, 60, 255))
    fill_rect(18, 100, 126, 104, (88, 82, 72, 255))

    # Windows (old, small, slightly crooked)
    def window(x0, y0, ww=14, hh=12, skew=0) -> None:
        fill_rect(x0, y0, x0 + ww, y0 + hh, (36, 42, 48, 255))
        fill_rect(x0 + 1, y0 + 1, x0 + ww - 1, y0 + hh - 1, (55, 72, 78, 255))
        # cross frame
        for x in range(x0, x0 + ww):
            put(x, y0 + hh // 2 + skew, (40, 32, 24, 255))
        for y in range(y0, y0 + hh):
            put(x0 + ww // 2, y, (40, 32, 24, 255))
        # frame
        for x in range(x0 - 1, x0 + ww + 1):
            put(x, y0 - 1, (50, 38, 28, 255))
            put(x, y0 + hh, (50, 38, 28, 255))
        for y in range(y0, y0 + hh):
            put(x0 - 1, y, (50, 38, 28, 255))
            put(x0 + ww, y, (50, 38, 28, 255))

    window(34, 58, skew=0)
    window(96, 56, skew=1)

    # Door (south facade — obvious goal)
    dx0, dy0, dw, dh = 62, 68, 20, 34
    fill_rect(dx0, dy0, dx0 + dw, dy0 + dh, (56, 40, 28, 255))
    for y in range(dy0, dy0 + dh):
        for x in range(dx0, dx0 + dw):
            if (x + y) % 6 == 0:
                put(x, y, (46, 32, 22, 255))
    for x in range(dx0 - 1, dx0 + dw + 1):
        put(x, dy0 - 1, (40, 28, 20, 255))
        put(x, dy0 + dh, (40, 28, 20, 255))
    for y in range(dy0, dy0 + dh):
        put(dx0 - 1, y, (40, 28, 20, 255))
        put(dx0 + dw, y, (40, 28, 20, 255))
    put(dx0 + dw - 4, dy0 + dh // 2, (120, 100, 60, 255))  # handle

    # Small crooked chimney
    fill_rect(98, 18, 110, 42, (72, 68, 64, 255))
    fill_rect(96, 16, 112, 20, (58, 54, 50, 255))

    # Porch step
    fill_rect(58, 102, 86, 108, (84, 72, 56, 255))
    return im


def draw_fence_post() -> Image.Image:
    im = Image.new("RGBA", (8, 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((2, 0, 5, 17), fill=(72, 52, 34, 255))
    d.rectangle((1, 1, 6, 3), fill=(58, 42, 28, 255))
    d.point((3, 5), fill=(48, 34, 22, 255))
    return im


def draw_fence_rail() -> Image.Image:
    im = Image.new("RGBA", (16, 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 1, 15, 3), fill=(78, 56, 38, 255))
    d.rectangle((0, 3, 15, 4), fill=(58, 42, 28, 255))
    return im


def draw_gate() -> Image.Image:
    im = Image.new("RGBA", (36, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 3, 19), fill=(70, 50, 34, 255))
    d.rectangle((32, 0, 35, 19), fill=(70, 50, 34, 255))
    d.rectangle((3, 4, 32, 6), fill=(82, 60, 40, 255))
    d.rectangle((3, 12, 32, 14), fill=(82, 60, 40, 255))
    return im


def draw_well() -> Image.Image:
    """Secondary prop — old stone well, ~knee-to-waist vs hero."""
    im = Image.new("RGBA", (28, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 14, 25, 30), fill=(90, 90, 92, 255), outline=(55, 55, 58, 255))
    d.ellipse((6, 17, 21, 27), fill=(40, 48, 55, 255))
    d.rectangle((4, 4, 7, 18), fill=(78, 56, 38, 255))
    d.rectangle((20, 4, 23, 18), fill=(78, 56, 38, 255))
    d.rectangle((4, 3, 23, 6), fill=(68, 48, 32, 255))
    return im


def draw_woodpile() -> Image.Image:
    im = Image.new("RGBA", (32, 18), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, y in enumerate((10, 6, 2)):
        d.rectangle((2 + i, y, 28 - i, y + 4), fill=(86, 60, 38, 255), outline=(54, 38, 24, 255))
    return im


def draw_shed_corner() -> Image.Image:
    """Hint of old outbuilding — partial shed corner."""
    im = Image.new("RGBA", (48, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(4, 18), (24, 6), (44, 18), (44, 38), (4, 38)], fill=(80, 60, 42, 255))
    d.rectangle((6, 18, 42, 38), fill=(74, 54, 38, 255), outline=(48, 34, 24, 255))
    d.rectangle((18, 24, 30, 38), fill=(52, 38, 28, 255))
    return im


def draw_stump() -> Image.Image:
    im = Image.new("RGBA", (20, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((1, 4, 18, 15), fill=(78, 56, 36, 255), outline=(48, 34, 22, 255))
    d.ellipse((4, 6, 15, 12), fill=(96, 74, 50, 255))
    d.arc((5, 7, 14, 11), 0, 180, fill=(60, 44, 28, 255))
    return im


def draw_log() -> Image.Image:
    im = Image.new("RGBA", (36, 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 2, 10, 11), fill=(90, 68, 44, 255), outline=(50, 36, 24, 255))
    d.rectangle((5, 2, 30, 10), fill=(82, 58, 38, 255))
    d.ellipse((26, 2, 35, 11), fill=(70, 50, 34, 255), outline=(50, 36, 24, 255))
    return im


def draw_weed(seed: int = 0) -> Image.Image:
    im = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cols = [(70, 110, 48, 255), (58, 92, 40, 255), (84, 120, 52, 255)]
    for i in range(5):
        x = 2 + (i * 2 + seed) % 8
        d.line((6, 10, x, 2 + (i + seed) % 4), fill=cols[(i + seed) % 3], width=1)
    return im


def bake_ground() -> Image.Image:
    grass_tiles = [load_rgba(GRASS_A), load_rgba(GRASS_B)]
    dirt_tiles = [load_rgba(DIRT_A), load_rgba(DIRT_B)]
    ground = Image.new("RGBA", (GROUND_W, GROUND_H), (0, 0, 0, 255))

    # Grass fill with slight variation
    for ty in range(MAP_H):
        for tx in range(MAP_W):
            tile = grass_tiles[(tx * 3 + ty * 5) % 2]
            ground.paste(tile, (tx * TILE, ty * TILE))

    # Path mask: south gate → house door (house feet ~tile y=13.6).
    path_cells: set[tuple[int, int]] = set()
    for y in range(13, 33):
        for dx in (-1, 0, 1):
            path_cells.add((19 + dx, y))
    for y in range(26, 33):
        for dx in (-2, 2):
            path_cells.add((19 + dx, y))
    for y in range(13, 20):
        for dx in (-2, -1, 0, 1, 2):
            path_cells.add((19 + dx, y))
    for y in range(16, 24):
        for x in range(14, 18):
            if (x + y) % 3 != 0:
                path_cells.add((x, y))

    for tx, ty in path_cells:
        if 0 <= tx < MAP_W and 0 <= ty < MAP_H:
            tile = dirt_tiles[(tx + ty) % 2]
            # soft edge: mix some grass edges by only pasting dirt
            ground.paste(tile, (tx * TILE, ty * TILE))

    # Darker overgrown tint on side bands
    overlay = Image.new("RGBA", (GROUND_W, GROUND_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle((0, 0, 10 * TILE, GROUND_H), fill=(20, 40, 16, 28))
    od.rectangle((30 * TILE, 0, GROUND_W, GROUND_H), fill=(20, 40, 16, 28))
    od.rectangle((0, 0, GROUND_W, 6 * TILE), fill=(18, 30, 14, 22))
    ground = Image.alpha_composite(ground, overlay)
    return ground


def _fill_under_eave_gaps(im: Image.Image) -> Image.Image:
    """Close small under-roof silhouette notches only (no ground fill under house).

    Restricts edits to the upper roof/wall band so the open yard under the
    foundation stays transparent. Original upload file is never modified.
    """
    from collections import deque

    arr = list(im.getdata())
    w, h = im.size
    # Upper ~70%: roof + under-eave line. Keep lower foundation/yard open.
    roof_band_y1 = int(h * 0.72)

    def idx(x: int, y: int) -> int:
        return y * w + x

    def alpha_at(x: int, y: int) -> int:
        return arr[idx(x, y)][3]

    def is_opaque(x: int, y: int, thr: int = 200) -> bool:
        return 0 <= x < w and 0 <= y < h and alpha_at(x, y) >= thr

    exterior = [False] * (w * h)
    q: deque[tuple[int, int]] = deque()

    def try_ext(x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= w or y >= h:
            return
        i = idx(x, y)
        if exterior[i] or is_opaque(x, y, 200):
            return
        exterior[i] = True
        q.append((x, y))

    for x in range(w):
        try_ext(x, 0)
        try_ext(x, h - 1)
    for y in range(h):
        try_ext(0, y)
        try_ext(w - 1, y)
    while q:
        x, y = q.popleft()
        try_ext(x + 1, y)
        try_ext(x - 1, y)
        try_ext(x, y + 1)
        try_ext(x, y - 1)

    def nearest_fill(x: int, y: int) -> tuple[int, int, int, int]:
        best = None
        best_d = 10**9
        for r in range(1, 14):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if abs(dx) != r and abs(dy) != r:
                        continue
                    nx, ny = x + dx, y + dy
                    if not is_opaque(nx, ny, 220):
                        continue
                    pr, pg, pb, _pa = arr[idx(nx, ny)]
                    if pr + pg + pb > 400:
                        continue
                    d = dx * dx + dy * dy
                    score = d + (pr + pg + pb) * 0.01
                    if score < best_d:
                        best_d = score
                        best = (pr, pg, pb, 255)
            if best is not None:
                break
        return best if best is not None else (42, 30, 22, 255)

    def has_opaque_band(x0: int, x1: int, y0: int, y1: int) -> bool:
        for yy in range(max(0, y0), min(h, y1)):
            for xx in range(max(0, x0), min(w, x1)):
                if is_opaque(xx, yy, 200):
                    return True
        return False

    # Component size for enclosed holes — only fill tiny pockets.
    hole_label = [-1] * (w * h)
    comp_size: list[int] = []
    for y in range(h):
        for x in range(w):
            i = idx(x, y)
            if hole_label[i] != -1 or exterior[i] or is_opaque(x, y, 200):
                continue
            cid = len(comp_size)
            stack = [(x, y)]
            hole_label[i] = cid
            size = 0
            while stack:
                cx, cy = stack.pop()
                size += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if nx < 0 or ny < 0 or nx >= w or ny >= h:
                        continue
                    ni = idx(nx, ny)
                    if hole_label[ni] != -1 or exterior[ni] or is_opaque(nx, ny, 200):
                        continue
                    hole_label[ni] = cid
                    stack.append((nx, ny))
            comp_size.append(size)

    filled = 0
    max_hole = max(48, (w * h) // 800)
    for y in range(roof_band_y1):
        for x in range(w):
            i = idx(x, y)
            a = arr[i][3]
            if a < 200 and not exterior[i]:
                cid = hole_label[i]
                if cid >= 0 and comp_size[cid] <= max_hole:
                    arr[i] = nearest_fill(x, y)
                    filled += 1

    # Morphological close on roof band: fill exterior pixels tightly surrounded
    # by house (under-eave jags) without painting open sky/yard.
    for _pass in range(3):
        pending: list[tuple[int, int]] = []
        for y in range(1, roof_band_y1):
            for x in range(1, w - 1):
                i = idx(x, y)
                if arr[i][3] >= 200 or not exterior[i]:
                    continue
                opaque_n = sum(
                    1
                    for dy in (-1, 0, 1)
                    for dx in (-1, 0, 1)
                    if not (dx == 0 and dy == 0) and is_opaque(x + dx, y + dy, 200)
                )
                col_gap = is_opaque(x, y - 1, 200) and is_opaque(x, y + 1, 200)
                if opaque_n >= 5 or (col_gap and opaque_n >= 3):
                    pending.append((x, y))
        for x, y in pending:
            arr[idx(x, y)] = nearest_fill(x, y)
            filled += 1
            exterior[idx(x, y)] = False

    # Fill ¾-view under-eave pockets: roof above + wall on one side.
    # These stay exterior-connected (open sideways) but read as holes over grass.
    for y in range(2, roof_band_y1):
        for x in range(2, w - 2):
            i = idx(x, y)
            if arr[i][3] >= 200 or not exterior[i]:
                continue
            above = has_opaque_band(x - 1, x + 2, y - 22, y)
            if not above:
                continue
            left = has_opaque_band(x - 26, x, y - 4, y + 10)
            right = has_opaque_band(x + 1, x + 27, y - 4, y + 10)
            if not (left or right):
                continue
            near = any(
                is_opaque(x + dx, y + dy, 200)
                for dy in range(-6, 7)
                for dx in range(-6, 7)
            )
            if not near:
                continue
            inward = left if x > w * 0.5 else right
            if not inward:
                continue
            arr[i] = nearest_fill(x, y)
            exterior[i] = False
            filled += 1

    # Explicit column-sandwich gaps (roof above + wall below in same column).
    for y in range(2, roof_band_y1):
        for x in range(w):
            i = idx(x, y)
            if arr[i][3] >= 200:
                continue
            above = any(is_opaque(x, y - dy, 200) for dy in range(1, 16) if y - dy >= 0)
            below = any(is_opaque(x, y + dy, 200) for dy in range(1, 16) if y + dy < h)
            if above and below:
                arr[i] = nearest_fill(x, y)
                exterior[i] = False
                filled += 1

    # Harden soft fringe in roof band.
    for y in range(roof_band_y1):
        for x in range(w):
            i = idx(x, y)
            a = arr[i][3]
            if a == 0 or a >= 230:
                continue
            opaque_n = sum(
                1
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if not (dx == 0 and dy == 0) and is_opaque(x + dx, y + dy, 220)
            )
            if opaque_n >= 5 and has_opaque_band(x, x + 1, y - 8, y):
                r, g, b, _ = arr[i]
                arr[i] = nearest_fill(x, y) if r + g + b < 8 else (r, g, b, 255)
                filled += 1

    out = Image.new("RGBA", (w, h))
    out.putdata(arr)
    print(f"House gap fill: {filled} pixels closed (roof band only)")
    return out


def _fill_display_eave_gaps(im: Image.Image) -> Image.Image:
    """Aggressive close of thin under-eave leaks at final display resolution."""
    arr = list(im.getdata())
    w, h = im.size
    y_max = int(h * 0.78)

    def idx(x: int, y: int) -> int:
        return y * w + x

    def opaque(x: int, y: int) -> bool:
        return 0 <= x < w and 0 <= y < h and arr[idx(x, y)][3] >= 200

    def sample(x: int, y: int) -> tuple[int, int, int, int]:
        for r in range(1, 12):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if abs(dx) != r and abs(dy) != r:
                        continue
                    nx, ny = x + dx, y + dy
                    if opaque(nx, ny):
                        pr, pg, pb, _ = arr[idx(nx, ny)]
                        if pr + pg + pb < 420:
                            return (pr, pg, pb, 255)
        return (38, 28, 20, 255)

    filled = 0
    for _pass in range(4):
        pending: list[tuple[int, int]] = []
        for y in range(1, y_max):
            for x in range(w):
                if arr[idx(x, y)][3] >= 200:
                    continue
                above = any(opaque(x, y - dy) for dy in range(1, 18))
                below = any(opaque(x, y + dy) for dy in range(1, 18))
                n = sum(
                    1
                    for dy in (-1, 0, 1)
                    for dx in (-1, 0, 1)
                    if not (dx == 0 and dy == 0) and opaque(x + dx, y + dy)
                )
                if (above and below) or n >= 4:
                    pending.append((x, y))
        for x, y in pending:
            arr[idx(x, y)] = sample(x, y)
            filled += 1
    out = Image.new("RGBA", (w, h))
    out.putdata(arr)
    print(f"House display eave close: {filled} pixels")
    return out


def prepare_main_house() -> dict:
    """Key black BG from upload house, crop, fill eave gaps, nearest downsample for VS01."""
    from collections import deque

    if not HOUSE_SRC.exists():
        raise SystemExit(f"Missing approved house: {HOUSE_SRC}")

    im = load_rgba(HOUSE_SRC)
    w, h = im.size
    px = im.load()
    visited = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def is_bg(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        return a < 8 or (r <= 20 and g <= 20 and b <= 20)

    def try_enq(x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            return
        if not is_bg(x, y):
            return
        visited[y][x] = True
        q.append((x, y))

    for x in range(w):
        try_enq(x, 0)
        try_enq(x, h - 1)
    for y in range(h):
        try_enq(0, y)
        try_enq(w - 1, y)
    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        try_enq(x + 1, y)
        try_enq(x - 1, y)
        try_enq(x, y + 1)
        try_enq(x, y - 1)

    bb = im.getbbox()
    if bb is None:
        raise SystemExit("House became fully transparent after keying")
    pad = 2
    crop = im.crop(
        (
            max(0, bb[0] - pad),
            max(0, bb[1] - pad),
            min(w, bb[2] + pad),
            min(h, bb[3] + pad),
        )
    )
    # Close under-eave grass leaks before downsample so gaps stay filled.
    crop = _fill_under_eave_gaps(crop)
    crop.save(OUT / "main_house_v1_source_crop.png")

    base_w = crop.width // HOUSE_PIXEL_DIV
    base_h = crop.height // HOUSE_PIXEL_DIV
    disp_w = max(1, int(round(base_w * HOUSE_DISPLAY_SCALE)))
    disp_h = max(1, int(round(base_h * HOUSE_DISPLAY_SCALE)))
    disp = crop.resize((disp_w, disp_h), Image.NEAREST)
    # Second + third pass at display size: nearest downsample reopens thin eave gaps.
    disp = _fill_under_eave_gaps(disp)
    disp = _fill_display_eave_gaps(disp)
    disp.save(OUT / "main_house_v1.png")

    sx = disp_w / float(crop.width)
    sy = disp_h / float(crop.height)
    dx0 = int(HOUSE_DOOR_CROP[0] * sx)
    dy0 = int(HOUSE_DOOR_CROP[1] * sy)
    dx1 = int(HOUSE_DOOR_CROP[2] * sx)
    dy1 = int(HOUSE_DOOR_CROP[3] * sy)
    meta = {
        "source": "upload/houses/main_house_v1.png",
        "runtime": "assets/art/outdoor/yard_vs01/main_house_v1.png",
        "source_crop": "assets/art/outdoor/yard_vs01/main_house_v1_source_crop.png",
        "pixel_div": HOUSE_PIXEL_DIV,
        "display_scale": HOUSE_DISPLAY_SCALE,
        "crop_size": list(crop.size),
        "display_size": list(disp.size),
        "door_rect_display": {"x0": dx0, "y0": dy0, "x1": dx1, "y1": dy1},
        "notes": [
            "main_house_v1.png is the approved base exterior for the childhood home.",
            "Original stays permanently in upload/houses/.",
            "Runtime: key black BG, fill under-eave gaps, nearest ÷4, then ~10% nearest shrink.",
        ],
    }
    (OUT / "main_house_v1.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("House runtime", disp.size, "door", meta["door_rect_display"], "scale", HOUSE_DISPLAY_SCALE)
    return meta


def copy_props() -> dict:
    props_dir = OUT / "props"
    props_dir.mkdir(parents=True, exist_ok=True)
    meta = {}
    for name, src in PROP_COPY.items():
        if not src.exists():
            raise SystemExit(f"Missing prop source: {src}")
        im = load_rgba(src)
        # Cap oversized trees/bushes to scale bible
        if name.startswith("tree"):
            im = nearest_fit(im, 64, 80)
        elif name.startswith("bush"):
            im = nearest_fit(im, 32, 28)
        elif name.startswith("rock_lg"):
            im = nearest_fit(im, 28, 24)
        elif name.startswith("rock_md"):
            im = nearest_fit(im, 22, 20)
        elif name.startswith("rock_sm"):
            im = nearest_fit(im, 14, 14)
        dst = props_dir / name
        im.save(dst)
        meta[name] = {"source": str(src.relative_to(ROOT)).replace("\\", "/"), "size": list(im.size)}
    return meta


def process() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / "props").mkdir()

    ground = bake_ground()
    ground.save(OUT / "ground.png")

    izba = draw_izba()
    izba.save(OUT / "house_izba_placeholder.png")

    draw_fence_post().save(OUT / "fence_post.png")
    draw_fence_rail().save(OUT / "fence_rail.png")
    draw_gate().save(OUT / "gate.png")
    draw_well().save(OUT / "well.png")
    draw_woodpile().save(OUT / "woodpile.png")
    draw_shed_corner().save(OUT / "shed_corner.png")
    draw_stump().save(OUT / "stump.png")
    draw_log().save(OUT / "log.png")
    draw_weed(0).save(OUT / "weed_a.png")
    draw_weed(2).save(OUT / "weed_b.png")
    # Keep old placeholder for reference, but approved house is main_house_v1.
    draw_izba().save(OUT / "house_izba_placeholder.png")

    prop_meta = copy_props()
    house_meta = prepare_main_house()

    manifest = {
        "version": 2,
        "generated": date.today().isoformat(),
        "tile": TILE,
        "map_tiles": [MAP_W, MAP_H],
        "map_px": [GROUND_W, GROUND_H],
        "notes": [
            "VS01 yard around approved PixelLab hero scale.",
            "Approved exterior: upload/houses/main_house_v1.png → main_house_v1.png.",
            "Oversized fairy props intentionally omitted.",
            "upload/ originals are never modified in place.",
        ],
        "props": prop_meta,
        "house": house_meta,
        "ground": "ground.png",
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Yard VS01 assets ->", OUT)


if __name__ == "__main__":
    process()
