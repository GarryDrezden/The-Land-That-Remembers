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
MAP_H = 32
GROUND_W = MAP_W * TILE
GROUND_H = MAP_H * TILE

GRASS_A = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/grass_16.png"
GRASS_B = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/grass_16_b.png"
DIRT_A = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/dirt_16.png"
DIRT_B = ROOT / "assets/art/outdoor/texture_proof_v1/terrain/dirt_16_b.png"
HOUSE_SRC = UPLOAD / "houses" / "main_house_v1.png"
## Integer nearest downsample after crop; door ~32px vs hero ~23px (~71%).
HOUSE_PIXEL_DIV = 4
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

    # Path mask: gate (bottom) → door (¾ house door is slightly left of center).
    # Gate ~(20,29), door approach ~(18–20, 15–16)
    path_cells: set[tuple[int, int]] = set()
    for y in range(15, 30):
        for dx in (-1, 0, 1):
            path_cells.add((19 + dx, y))
    for y in range(24, 30):
        for dx in (-2, 2):
            path_cells.add((19 + dx, y))
    for y in range(15, 21):
        for dx in (-2, -1, 0, 1, 2):
            path_cells.add((19 + dx, y))
    for y in range(17, 23):
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


def prepare_main_house() -> dict:
    """Key black BG from upload house, crop, integer nearest downsample for VS01."""
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
    crop.save(OUT / "main_house_v1_source_crop.png")
    disp = crop.resize(
        (crop.width // HOUSE_PIXEL_DIV, crop.height // HOUSE_PIXEL_DIV),
        Image.NEAREST,
    )
    disp.save(OUT / "main_house_v1.png")
    dx0, dy0, dx1, dy1 = [c // HOUSE_PIXEL_DIV for c in HOUSE_DOOR_CROP]
    meta = {
        "source": "upload/houses/main_house_v1.png",
        "runtime": "assets/art/outdoor/yard_vs01/main_house_v1.png",
        "source_crop": "assets/art/outdoor/yard_vs01/main_house_v1_source_crop.png",
        "pixel_div": HOUSE_PIXEL_DIV,
        "crop_size": list(crop.size),
        "display_size": list(disp.size),
        "door_rect_display": {"x0": dx0, "y0": dy0, "x1": dx1, "y1": dy1},
        "notes": [
            "main_house_v1.png is the approved base exterior for the childhood home.",
            "Original stays permanently in upload/houses/.",
            "Runtime uses keyed crop + integer nearest downsample only (no blur).",
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
