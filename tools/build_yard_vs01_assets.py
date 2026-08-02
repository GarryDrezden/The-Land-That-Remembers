#!/usr/bin/env python3
"""
Bake VS01 yard runtime assets for childhood-home outdoor candidate.

- Does not modify upload/ originals (copies selected props).
- Prepares approved main_house_v1 (key black BG, crop, nearest to ~288px wide).
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
## Long rural plot (~25–30 sotka feel): moderate width, extends south.
MAP_W = 44
MAP_H = 84
## Extra grass around the playable plate so camera offset/zoom never shows void.
GROUND_PAD_TILES = 8
GROUND_W = (MAP_W + GROUND_PAD_TILES * 2) * TILE
GROUND_H = (MAP_H + GROUND_PAD_TILES * 2) * TILE

GRASS_A = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/grass_16.png"
GRASS_B = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/grass_16_b.png"
DIRT_A = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/dirt_16.png"
DIRT_B = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/dirt_16_b.png"
HOUSE_SRC = UPLOAD / "houses" / "main_house_v1.png"
## Runtime width target (nearest). Height follows crop aspect (~151 for 288).
HOUSE_TARGET_W = 288
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
    # Orchard candidates — Fruit_tree* as apple/pear stand-ins; Broken as diseased.
    "fruit_apple_a.png": UPLOAD / "trees-pixel-art/PNG/Assets_separately/Trees/Fruit_tree1.png",
    "fruit_apple_b.png": UPLOAD / "trees-pixel-art/PNG/Assets_separately/Trees/Fruit_tree2.png",
    "fruit_pear.png": UPLOAD / "trees-pixel-art/PNG/Assets_separately/Trees/Fruit_tree3.png",
    "fruit_dead.png": UPLOAD / "trees-pixel-art/PNG/Assets_separately/Trees/Broken_tree4.png",
    "berry_currant.png": UPLOAD / "bushes-pixel-art/PNG/Assets/Bush_simple1_1.png",
    "berry_gooseberry.png": UPLOAD / "bushes-pixel-art/PNG/Assets/Bush_simple2_1.png",
    "berry_raspberry.png": UPLOAD / "bushes-pixel-art/PNG/Assets/Bush_simple1_2.png",
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
    """Legacy partial shed — kept for bake compatibility; scene uses UtilityShed."""
    im = Image.new("RGBA", (48, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(4, 18), (24, 6), (44, 18), (44, 38), (4, 38)], fill=(80, 60, 42, 255))
    d.rectangle((6, 18, 42, 38), fill=(74, 54, 38, 255), outline=(48, 34, 24, 255))
    d.rectangle((18, 24, 30, 38), fill=(52, 38, 28, 255))
    return im


def draw_garage() -> Image.Image:
    """Blockout — large wood garage / woodshed."""
    im = Image.new("RGBA", (72, 52), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(2, 22), (36, 4), (70, 22), (70, 50), (2, 50)], fill=(92, 70, 48, 255))
    d.rectangle((4, 22, 68, 50), fill=(78, 58, 40, 255), outline=(48, 34, 24, 255))
    d.rectangle((10, 28, 34, 50), fill=(42, 32, 24, 255))  # open bay
    d.rectangle((40, 30, 62, 48), fill=(70, 52, 36, 255), outline=(40, 28, 20, 255))
    for y in (34, 40, 46):
        d.line((42, y, 60, y), fill=(54, 38, 26, 255))
    return im


def draw_utility_shed() -> Image.Image:
    """Blockout — single utility shed (left of utility yard)."""
    im = Image.new("RGBA", (52, 44), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(4, 18), (26, 4), (48, 18), (48, 42), (4, 42)], fill=(86, 64, 44, 255))
    d.rectangle((6, 18, 46, 42), fill=(74, 54, 38, 255), outline=(46, 32, 22, 255))
    d.rectangle((20, 26, 32, 42), fill=(50, 36, 26, 255))
    d.rectangle((10, 22, 18, 30), fill=(120, 140, 150, 255), outline=(60, 70, 80, 255))
    return im


def draw_doghouse() -> Image.Image:
    im = Image.new("RGBA", (24, 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(2, 12), (12, 2), (22, 12), (22, 20), (2, 20)], fill=(96, 72, 48, 255))
    d.rectangle((3, 12, 21, 20), fill=(82, 60, 40, 255), outline=(50, 36, 24, 255))
    d.ellipse((8, 13, 16, 20), fill=(40, 30, 22, 255))
    return im


def draw_outhouse() -> Image.Image:
    im = Image.new("RGBA", (22, 34), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(2, 10), (11, 2), (20, 10), (20, 32), (2, 32)], fill=(88, 68, 46, 255))
    d.rectangle((3, 10, 19, 32), fill=(76, 56, 38, 255), outline=(48, 34, 22, 255))
    d.rectangle((7, 16, 15, 32), fill=(52, 38, 28, 255))
    d.ellipse((9, 20, 13, 24), fill=(30, 22, 16, 255))
    return im


def draw_pond() -> Image.Image:
    im = Image.new("RGBA", (64, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 6, 62, 38), fill=(48, 78, 92, 255), outline=(36, 56, 64, 255))
    d.ellipse((10, 12, 50, 32), fill=(56, 96, 110, 255))
    d.ellipse((18, 16, 34, 24), fill=(70, 120, 130, 180))
    # reed hints
    for x in (6, 12, 52, 58):
        d.line((x, 20, x - 1, 8), fill=(50, 90, 40, 255))
    return im


def draw_ruined_bathhouse() -> Image.Image:
    im = Image.new("RGBA", (56, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(4, 16), (28, 4), (52, 16), (52, 38), (4, 38)], fill=(70, 58, 50, 255))
    d.rectangle((6, 16, 50, 38), fill=(64, 52, 44, 255), outline=(40, 32, 28, 255))
    # collapsed roof notch
    d.polygon([(20, 16), (28, 8), (40, 16)], fill=(0, 0, 0, 0))
    d.rectangle((18, 22, 30, 38), fill=(36, 28, 24, 255))
    d.rectangle((34, 20, 44, 28), fill=(90, 90, 70, 120))  # broken window
    return im


def draw_greenhouse() -> Image.Image:
    im = Image.new("RGBA", (48, 36), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(2, 16), (24, 2), (46, 16), (46, 34), (2, 34)], fill=(140, 170, 150, 200))
    d.rectangle((4, 16, 44, 34), fill=(120, 160, 140, 180), outline=(70, 90, 80, 255))
    for x in range(8, 44, 8):
        d.line((x, 16, x, 34), fill=(80, 100, 90, 255))
    d.line((4, 24, 44, 24), fill=(80, 100, 90, 255))
    return im


def draw_compost() -> Image.Image:
    im = Image.new("RGBA", (28, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((2, 6, 26, 18), fill=(64, 48, 32, 255), outline=(40, 30, 20, 255))
    d.ellipse((4, 4, 24, 14), fill=(72, 58, 36, 255))
    d.ellipse((8, 6, 16, 12), fill=(50, 70, 36, 255))
    return im


def draw_fence_rail_broken() -> Image.Image:
    im = Image.new("RGBA", (16, 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 2, 7, 4), fill=(78, 56, 38, 255))
    d.rectangle((10, 1, 15, 3), fill=(68, 48, 32, 255))
    return im


def draw_fence_post_lean() -> Image.Image:
    im = Image.new("RGBA", (12, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(2, 0), (6, 0), (10, 18), (5, 18)], fill=(72, 52, 34, 255))
    return im


def bake_homestead_structures() -> dict:
    struct = OUT / "structures"
    struct.mkdir(parents=True, exist_ok=True)
    makers = {
        "garage.png": draw_garage,
        "utility_shed.png": draw_utility_shed,
        "doghouse.png": draw_doghouse,
        "outhouse.png": draw_outhouse,
        "pond.png": draw_pond,
        "ruined_bathhouse.png": draw_ruined_bathhouse,
        "greenhouse.png": draw_greenhouse,
        "compost.png": draw_compost,
        "fence_rail_broken.png": draw_fence_rail_broken,
        "fence_post_lean.png": draw_fence_post_lean,
    }
    meta = {}
    for name, fn in makers.items():
        im = fn()
        im.save(struct / name)
        meta[name] = {"kind": "blockout", "size": list(im.size)}
    return meta


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
    pad = GROUND_PAD_TILES
    full_w = MAP_W + pad * 2
    full_h = MAP_H + pad * 2

    # Grass fill including camera bleed pad outside the playable plate.
    for ty in range(full_h):
        for tx in range(full_w):
            tile = grass_tiles[(tx * 3 + ty * 5) % 2]
            ground.paste(tile, (tx * TILE, ty * TILE))

    # Path: house front → utility → orchard (stops before far blockage).
    path_cells: set[tuple[int, int]] = set()
    for y in range(13, 50):
        for dx in (-1, 0, 1):
            path_cells.add((20 + dx, y))
    for y in range(13, 22):
        for dx in (-2, -1, 0, 1, 2):
            path_cells.add((20 + dx, y))
    for y in range(22, 36):
        for dx in (-2, 2):
            if (20 + dx + y) % 3 == 0:
                path_cells.add((20 + dx, y))
    # Soft orchard wander (no ladder/arms)
    for y in range(36, 48):
        wobble = 1 if (y // 3) % 2 == 0 else -1
        path_cells.add((20 + wobble, y))
        path_cells.add((20, y))
    # Near-yard side path to well / shed
    for y in range(16, 24):
        for x in range(14, 18):
            if (x + y) % 3 != 0:
                path_cells.add((x, y))

    for tx, ty in path_cells:
        if 0 <= tx < MAP_W and 0 <= ty < MAP_H:
            tile = dirt_tiles[(tx + ty) % 2]
            ground.paste(tile, ((tx + pad) * TILE, (ty + pad) * TILE))

    # Zone character tints (playable plate only) — soft, not hard rectangles.
    overlay = Image.new("RGBA", (GROUND_W, GROUND_H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    ox0 = pad * TILE
    oy0 = pad * TILE

    def band(y0: int, y1: int, rgba: tuple[int, int, int, int]) -> None:
        od.rectangle(
            (ox0, oy0 + y0 * TILE, ox0 + MAP_W * TILE, oy0 + y1 * TILE),
            fill=rgba,
        )

    # Street edge / north — slightly darker
    band(0, 7, (18, 30, 14, 26))
    # Side overgrowth near fences
    od.rectangle((ox0, oy0, ox0 + 8 * TILE, oy0 + MAP_H * TILE), fill=(20, 40, 16, 30))
    od.rectangle(
        (ox0 + 36 * TILE, oy0, ox0 + MAP_W * TILE, oy0 + MAP_H * TILE),
        fill=(20, 40, 16, 30),
    )
    # Utility — mild
    band(22, 34, (28, 36, 18, 16))
    # Orchard — cooler green
    band(34, 50, (16, 42, 28, 22))
    # Future garden — warmer wild grass + faint old bed scars
    band(50, 66, (40, 48, 18, 28))
    for bx, by, bw, bh in (
        (12, 54, 6, 3),
        (20, 56, 7, 3),
        (28, 53, 5, 4),
        (14, 60, 8, 2),
    ):
        od.rectangle(
            (
                ox0 + bx * TILE,
                oy0 + by * TILE,
                ox0 + (bx + bw) * TILE,
                oy0 + (by + bh) * TILE,
            ),
            fill=(70, 55, 30, 40),
        )
    # Far overgrown — deepest
    band(66, MAP_H, (12, 28, 14, 40))

    ground = Image.alpha_composite(ground, overlay)
    return ground


def _is_usable_house_sample(r: int, g: int, b: int) -> bool:
    """Reject keyed-black leftovers and bright grass-like neighbors."""
    s = r + g + b
    if r <= 14 and g <= 14 and b <= 14 and s <= 36:
        return False
    if g > r + 28 and g > b + 18 and s > 180:
        return False
    if s > 520:
        return False
    return True


def _sample_house_fill(
    arr: list[tuple[int, int, int, int]], w: int, h: int, x: int, y: int
) -> tuple[int, int, int, int]:
    """Nearest wood/roof/deep-shadow sample — never pure black."""
    best = None
    best_score = 10**9
    for radius in range(1, 14):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if abs(dx) != radius and abs(dy) != radius:
                    continue
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= w or ny >= h:
                    continue
                pr, pg, pb, pa = arr[ny * w + nx]
                if pa < 220 or not _is_usable_house_sample(pr, pg, pb):
                    continue
                score = dx * dx + dy * dy + (0 if dy < 0 else 4)
                if score < best_score:
                    best_score = score
                    best = (pr, pg, pb, 255)
        if best is not None:
            break
    return best if best is not None else (58, 42, 32, 255)


def _clean_house_alpha(im: Image.Image) -> Image.Image:
    """Close real holes + binary soft alpha without expanding the silhouette.

    - Does NOT grow roof thickness into rectangular under-eave slabs.
    - Does NOT fill exterior notches that are part of the open silhouette.
    - Only fills enclosed interior holes and tiny 1–2px column leaks.
    """
    from collections import deque

    arr = list(im.getdata())
    w, h = im.size

    def idx(x: int, y: int) -> int:
        return y * w + x

    def is_opaque(x: int, y: int, thr: int = 200) -> bool:
        return 0 <= x < w and 0 <= y < h and arr[idx(x, y)][3] >= thr

    # Edge-adjacent keyed-black fringe → transparent (keep interior dark wood).
    stripped = 0
    for y in range(h):
        for x in range(w):
            i = idx(x, y)
            r, g, b, a = arr[i]
            if a < 8 or not (r <= 14 and g <= 14 and b <= 14):
                continue
            edge = any(
                nx < 0
                or ny < 0
                or nx >= w
                or ny >= h
                or arr[idx(nx, ny)][3] < 8
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                for nx, ny in ((x + dx, y + dy),)
                if not (dx == 0 and dy == 0)
            )
            if edge:
                arr[i] = (0, 0, 0, 0)
                stripped += 1

    exterior = [False] * (w * h)
    q: deque[tuple[int, int]] = deque()

    def try_ext(x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= w or y >= h:
            return
        i = idx(x, y)
        if exterior[i] or arr[i][3] >= 200:
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

    # Enclosed holes only (never exterior notches under eaves).
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
    max_hole = max(24, (w * h) // 2000)
    for y in range(h):
        for x in range(w):
            i = idx(x, y)
            if arr[i][3] >= 200 or exterior[i]:
                continue
            cid = hole_label[i]
            if cid >= 0 and comp_size[cid] <= max_hole:
                arr[i] = _sample_house_fill(arr, w, h, x, y)
                filled += 1

    # Tiny column leaks (1–5px) between roof above and wall below — no thick slabs.
    max_gap = 5
    for y in range(2, h - 2):
        for x in range(w):
            i = idx(x, y)
            if arr[i][3] >= 200:
                continue
            above_y = None
            for dy in range(1, 14):
                if y - dy < 0:
                    break
                if is_opaque(x, y - dy, 200):
                    above_y = y - dy
                    break
            if above_y is None:
                continue
            below_y = None
            for dy in range(1, 14):
                if y + dy >= h:
                    break
                if is_opaque(x, y + dy, 200):
                    below_y = y + dy
                    break
            if below_y is None:
                continue
            if (below_y - above_y - 1) <= max_gap:
                arr[i] = _sample_house_fill(arr, w, h, x, y)
                filled += 1

    # Under-eave seal: only narrow leaks between roof (above) and wall (below),
    # or thin flanked gaps — never mass-fill exterior silhouette.
    eave_sealed = 0
    for y in range(3, h - 2):
        for x in range(1, w - 1):
            i = idx(x, y)
            r, g, b, a = arr[i]
            grassish = a >= 40 and g > r + 22 and g > b + 14 and (r + g + b) > 140
            if a >= 200 and not grassish:
                continue
            # Must sit under non-grass opaque roof within 6px.
            roof_dy = None
            for dy in range(1, 7):
                if y - dy < 0:
                    break
                if not is_opaque(x, y - dy, 220):
                    continue
                pr, pg, pb, _pa = arr[idx(x, y - dy)]
                if pg > pr + 28 and pg > pb + 18:
                    continue
                roof_dy = dy
                break
            if roof_dy is None:
                continue
            # Prefer true under-eave: wall/mass below within 8px.
            wall_below = False
            for dy in range(1, 9):
                if y + dy >= h:
                    break
                if is_opaque(x, y + dy, 200):
                    pr, pg, pb, _pa = arr[idx(x, y + dy)]
                    if not (pg > pr + 28 and pg > pb + 18):
                        wall_below = True
                        break
            left_ok = is_opaque(x - 1, y, 200) or is_opaque(x - 2, y, 200)
            right_ok = is_opaque(x + 1, y, 200) or is_opaque(x + 2, y, 200)
            flanked_both = left_ok and right_ok
            if not wall_below and not flanked_both:
                continue
            # Exterior pixels only if flanked on both sides (1–2px leak).
            if exterior[i] and not flanked_both:
                continue
            arr[i] = _sample_house_fill(arr, w, h, x, y)
            eave_sealed += 1
            filled += 1

    # Binary alpha: exterior soft → clear; interior soft → solid wood sample.
    soft_cleared = 0
    soft_solid = 0
    for y in range(h):
        for x in range(w):
            i = idx(x, y)
            r, g, b, a = arr[i]
            if a == 0 or a == 255:
                continue
            if exterior[i] or a < 128:
                arr[i] = (0, 0, 0, 0)
                soft_cleared += 1
                continue
            if _is_usable_house_sample(r, g, b):
                arr[i] = (r, g, b, 255)
            else:
                arr[i] = _sample_house_fill(arr, w, h, x, y)
            soft_solid += 1

    out = Image.new("RGBA", (w, h))
    out.putdata(arr)
    print(
        f"House alpha clean: fringe={stripped}, holes={filled}, "
        f"eave_seal={eave_sealed}, soft_clear={soft_cleared}, soft_solid={soft_solid}"
    )
    return out


def _lift_near_black_shadows(im: Image.Image) -> Image.Image:
    """Replace crushed near-black opaque pixels with sampled wood/deep shadow.

    Keeps silhouette; avoids rectangular black stubs reading as bake artifacts.
    """
    arr = list(im.getdata())
    w, h = im.size
    lifted = 0
    for y in range(h):
        for x in range(w):
            i = y * w + x
            r, g, b, a = arr[i]
            if a < 200:
                continue
            if max(r, g, b) < 22 or r + g + b < 50:
                # Prefer a slightly brighter usable neighbor than pure black.
                best = None
                best_score = 10**9
                for radius in range(1, 16):
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            if abs(dx) != radius and abs(dy) != radius:
                                continue
                            nx, ny = x + dx, y + dy
                            if nx < 0 or ny < 0 or nx >= w or ny >= h:
                                continue
                            pr, pg, pb, pa = arr[ny * w + nx]
                            if pa < 220 or not _is_usable_house_sample(pr, pg, pb):
                                continue
                            if pr + pg + pb < 55:
                                continue
                            score = dx * dx + dy * dy
                            if score < best_score:
                                best_score = score
                                best = (pr, pg, pb, 255)
                    if best is not None:
                        break
                arr[i] = best if best is not None else (58, 42, 32, 255)
                lifted += 1
    out = Image.new("RGBA", (w, h))
    out.putdata(arr)
    print(f"House near-black lift: {lifted} pixels")
    return out


def prepare_main_house() -> dict:
    """Key black BG, crop, conservative alpha clean, nearest resize to ~288px wide."""
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
    crop = _clean_house_alpha(crop)
    crop.save(OUT / "main_house_v1_source_crop.png")

    disp_w = HOUSE_TARGET_W
    disp_h = max(1, int(round(crop.height * (disp_w / float(crop.width)))))
    disp = crop.resize((disp_w, disp_h), Image.NEAREST)
    # Downsample can reopen 1px holes / soft edges — clean again, still no slabs.
    disp = _clean_house_alpha(disp)
    disp = _lift_near_black_shadows(disp)
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
        "target_width": HOUSE_TARGET_W,
        "crop_size": list(crop.size),
        "display_size": list(disp.size),
        "door_rect_display": {"x0": dx0, "y0": dy0, "x1": dx1, "y1": dy1},
        "notes": [
            "main_house_v1.png is the approved base exterior for the childhood home.",
            "Original stays permanently in upload/houses/.",
            "Runtime: key black BG, conservative alpha clean, nearest resize to ~288px wide.",
            "No display_scale shrink; node/sprite scale stays Vector2.ONE.",
        ],
    }
    (OUT / "main_house_v1.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("House runtime", disp.size, "door", meta["door_rect_display"])
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
        if name.startswith("tree") or name.startswith("fruit_"):
            im = nearest_fit(im, 64, 80)
        elif name.startswith("bush") or name.startswith("berry_"):
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

    struct_meta = bake_homestead_structures()
    prop_meta = copy_props()
    house_meta = prepare_main_house()

    manifest = {
        "version": 3,
        "generated": date.today().isoformat(),
        "tile": TILE,
        "map_tiles": [MAP_W, MAP_H],
        "map_px": [GROUND_W, GROUND_H],
        "notes": [
            "VS01 childhood homestead — long plot 44x84 tiles.",
            "Approved exterior: upload/houses/main_house_v1.png → main_house_v1.png.",
            "Homestead structures are separate blockout sprites under structures/.",
            "upload/ originals are never modified in place.",
        ],
        "props": prop_meta,
        "structures": struct_meta,
        "house": house_meta,
        "ground": "ground.png",
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Yard VS01 assets ->", OUT)


if __name__ == "__main__":
    process()
