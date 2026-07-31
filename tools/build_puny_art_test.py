#!/usr/bin/env python3
"""One-shot builder for isolated Puny World yard art test.

Crops ONLY from assets/external/punyworld_overworld.png.
Does not touch gameplay scenes. Does not pull Kenney/generated props.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "assets" / "external" / "punyworld_overworld.png"
OUT = ROOT / "assets" / "art" / "outdoor" / "puny_world"
PREVIEW_DIR = ROOT / "docs" / "art_tests"
SCALE = 3  # integer display scale
TILE = 16
MAP_W, MAP_H = 20, 14  # tiles — one screen fragment


def crop_tile(im: Image.Image, c: int, r: int, w: int = 1, h: int = 1) -> Image.Image:
	box = (c * TILE, r * TILE, (c + w) * TILE, (r + h) * TILE)
	return im.crop(box)


def save_png(img: Image.Image, path: Path) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	img.save(path)


def write_import(path: Path) -> None:
	"""Godot 4 nearest-neighbor import sidecar."""
	rel = path.as_posix()
	text = f"""[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://art_test_{path.stem}"
path="res://.godot/imported/{path.name}-{path.stem}.ctex"
metadata={{
"vram_texture": false
}}

[deps]

source_file="res://{path.relative_to(ROOT).as_posix()}"
dest_files=["res://.godot/imported/{path.name}-{path.stem}.ctex"]

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=false
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/fix_alpha_border=false
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=0
"""
	# Simpler: let Godot reimport; we only need filter_nearest in project via
	# default Texture2D. Write minimal import with nearest filter.
	text = f"""[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="res://{path.relative_to(ROOT).as_posix()}"

[params]

compress/mode=0
mipmaps/generate=false
process/fix_alpha_border=false
detect_3d/compress_to=0
"""
	path.with_suffix(path.suffix + ".import").write_text(text, encoding="utf-8")


def build_ground(im: Image.Image) -> tuple[Image.Image, dict]:
	"""Compose warm dirt clearing + grass transitions + pond from Puny tiles."""
	# Tile atlas picks (col, row)
	G = (0, 0)  # solid grass
	G2 = (0, 1)  # grass flecks
	D = (8, 1)  # warm dirt
	# Transitions (dirt center / grass edge) — approximate organic clearing
	# Using common edge tiles from rows 0-2
	TL = (4, 0)
	T = (5, 0)
	TR = (6, 0)
	L = (3, 1)
	R = (6, 1)
	BL = (4, 2)
	B = (5, 2)
	BR = (6, 2)

	# Coherent rounded pond block from sheet (cols 7-9, rows 10-12)
	pond_tiles = {
		(0, 0): (7, 10),
		(1, 0): (8, 10),
		(2, 0): (9, 10),
		(0, 1): (7, 11),
		(1, 1): (8, 11),
		(2, 1): (9, 11),
		(0, 2): (7, 12),
		(1, 2): (8, 12),
		(2, 2): (9, 12),
	}

	# Map codes: 'G','G2','D', edges, 'P' pond relative
	grid = [["G"] * MAP_W for _ in range(MAP_H)]

	# Dirt clearing (yard feel) center-left
	for y in range(3, 11):
		for x in range(2, 12):
			grid[y][x] = "D"
	# Soften with edge markers
	for x in range(2, 12):
		grid[3][x] = "T"
		grid[10][x] = "B"
	for y in range(3, 11):
		grid[y][2] = "L"
		grid[y][11] = "R"
	grid[3][2] = "TL"
	grid[3][11] = "TR"
	grid[10][2] = "BL"
	grid[10][11] = "BR"

	# Grass fleck variation outside
	for y in range(MAP_H):
		for x in range(MAP_W):
			if grid[y][x] == "G" and (x + y * 3) % 5 == 0:
				grid[y][x] = "G2"

	# Pond bottom-right of clearing
	pond_origin = (13, 7)
	for py in range(3):
		for px in range(3):
			grid[pond_origin[1] + py][pond_origin[0] + px] = f"P{px}{py}"

	lookup = {
		"G": G,
		"G2": G2,
		"D": D,
		"TL": TL,
		"T": T,
		"TR": TR,
		"L": L,
		"R": R,
		"BL": BL,
		"B": B,
		"BR": BR,
	}

	ground = Image.new("RGBA", (MAP_W * TILE, MAP_H * TILE), (0, 0, 0, 0))
	for y in range(MAP_H):
		for x in range(MAP_W):
			code = grid[y][x]
			if code.startswith("P"):
				px, py = int(code[1]), int(code[2])
				tc, tr = pond_tiles[(px, py)]
			else:
				tc, tr = lookup[code]
			ground.paste(crop_tile(im, tc, tr), (x * TILE, y * TILE))

	meta = {"map_w": MAP_W, "map_h": MAP_H, "tile": TILE, "pond_origin": pond_origin}
	return ground, meta


def extract_props(im: Image.Image) -> dict[str, Path]:
	"""Named crops used by the scene. Coordinates verified against sheet."""
	specs = {
		# obstacles / vegetation (resource nodes)
		"rock": (0, 26, 1, 1),
		"pebbles": (1, 26, 1, 1),
		"tree": (3, 26, 1, 1),
		"tree_fruit": (2, 26, 1, 1),
		"tree_b": (0, 27, 1, 1),
		"bush": (3, 27, 1, 1),
		"weed_a": (1, 27, 1, 1),
		"weed_b": (0, 28, 1, 1),
		"weed_c": (1, 28, 1, 1),
		"weed_d": (1, 29, 1, 1),
		"pine": (0, 29, 1, 1),
		"stump": (1, 31, 1, 1),
		# house fragment — 32×32 wooden cottage (fantasy village; not Soviet shed)
		"house": (7, 26, 2, 2),
		"house_alt": (9, 26, 2, 2),
		# fence scrap for yard density
		"fence": (4, 31, 2, 1),
		"well": (4, 30, 1, 1),
		# water center variants (for subtle pond shimmer loop)
		"water_0": (8, 11, 1, 1),
		"water_1": (18, 11, 1, 1),
		"water_2": (19, 11, 1, 1),
	}
	paths: dict[str, Path] = {}
	for name, (c, r, w, h) in specs.items():
		img = crop_tile(im, c, r, w, h)
		path = OUT / "props" / f"{name}.png"
		save_png(img, path)
		paths[name] = path
	return paths


def compose_preview(ground: Image.Image, props: dict[str, Path], layout: list[dict]) -> Image.Image:
	"""Offline screenshot-quality render at integer ×3 — no Godot required for still."""
	base = ground.resize((ground.width * SCALE, ground.height * SCALE), Image.NEAREST)
	canvas = Image.new("RGBA", base.size, (0, 0, 0, 255))
	canvas.paste(base, (0, 0))
	for item in layout:
		if item.get("skip_preview"):
			continue
		name = item["sprite"]
		img = Image.open(props[name]).convert("RGBA")
		img = img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)
		# item x,y are in tile-space top-left pixels of map
		px = int(item["x"] * SCALE)
		py = int(item["y"] * SCALE)
		canvas.alpha_composite(img, (px, py))
	return canvas


def main() -> None:
	assert SHEET.exists(), f"missing {SHEET}"
	# clean previous preview junk
	preview_junk = ROOT / "assets" / "art" / "outdoor" / "_puny_preview"
	if preview_junk.exists():
		import shutil

		shutil.rmtree(preview_junk)

	OUT.mkdir(parents=True, exist_ok=True)
	im = Image.open(SHEET).convert("RGBA")

	ground, meta = build_ground(im)
	ground_path = OUT / "yard_art_test_ground.png"
	save_png(ground, ground_path)

	props = extract_props(im)

	# Natural yard fragment layout (pixel coords in 16px tile space)
	layout = [
		{"id": "house", "sprite": "house", "x": 40, "y": 24},
		{"id": "fence_1", "sprite": "fence", "x": 24, "y": 56},
		{"id": "well", "sprite": "well", "x": 88, "y": 40},
		{"id": "tree_1", "sprite": "tree", "x": 8, "y": 48},
		{"id": "tree_2", "sprite": "tree_fruit", "x": 168, "y": 40},
		{"id": "tree_3", "sprite": "tree_b", "x": 248, "y": 88},
		{"id": "pine_corner", "sprite": "pine", "x": 280, "y": 24},
		{"id": "bush_1", "sprite": "bush", "x": 112, "y": 72},
		{"id": "bush_2", "sprite": "bush", "x": 176, "y": 128},
		{"id": "bush_3", "sprite": "bush", "x": 48, "y": 128},
		{"id": "weed_1", "sprite": "weed_a", "x": 64, "y": 80},
		{"id": "weed_2", "sprite": "weed_c", "x": 96, "y": 96},
		{"id": "weed_3", "sprite": "weed_d", "x": 128, "y": 84},
		{"id": "weed_4", "sprite": "weed_a", "x": 152, "y": 112},
		{"id": "weed_5", "sprite": "weed_c", "x": 56, "y": 112},
		{"id": "rock_1", "sprite": "rock", "x": 112, "y": 120},
		{"id": "pebbles_1", "sprite": "pebbles", "x": 136, "y": 108},
		{"id": "stump_1", "sprite": "stump", "x": 160, "y": 72},
		{"id": "clear_weed", "sprite": "weed_b", "x": 80, "y": 92, "clearable": True},
	]

	# Gaps (honest):
	gaps = {
		"character": "Puny World Overworld sheet has no player/NPC walk frames. Companion pack 'Puny Characters' exists but was NOT added (single-pack rule).",
		"log": "No fallen-log / timber prop found in overworld sheet resource nodes.",
		"weathered_house": "Only bright fantasy cottages / thatch / stone castle pieces — no weathered Soviet shed / childhood-home vernacular.",
		"messy_weeds": "Plants are tidy tufts/flowers/crops, not unkempt overgrowth piles.",
	}

	preview = compose_preview(ground, props, layout)
	PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
	shot = PREVIEW_DIR / "yard_art_test_puny_world.png"
	save_png(preview, shot)

	# Also draw a note strip under preview for docs (separate file without note for clean shot)
	note = preview.copy()
	# clean shot already saved; annotated optional
	ann = Image.new("RGBA", (preview.width, preview.height + 72), (18, 16, 14, 255))
	ann.paste(preview, (0, 0))
	draw = ImageDraw.Draw(ann)
	draw.text(
		(8, preview.height + 8),
		"ART TEST — Puny World only | scale x3 | NO character in pack | NO log prop",
		fill=(240, 220, 180, 255),
	)
	save_png(ann, PREVIEW_DIR / "yard_art_test_puny_world_annotated.png")

	manifest = {
		"source_sheet": "assets/external/punyworld_overworld.png",
		"license": "CC0 (Shade / OpenGameArt)",
		"scale": SCALE,
		"tile": TILE,
		"ground": str(ground_path.relative_to(ROOT)).replace("\\", "/"),
		"props": {k: str(v.relative_to(ROOT)).replace("\\", "/") for k, v in props.items()},
		"layout": layout,
		"gaps": gaps,
		"preview": str(shot.relative_to(ROOT)).replace("\\", "/"),
		"meta": meta,
	}
	(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
	(OUT / "README.txt").write_text(
		"Slices and composed ground for isolated art test only.\n"
		"Source: punyworld_overworld.png (CC0).\n"
		"Do not mix with Kenney or project-generated sprites here.\n",
		encoding="utf-8",
	)
	print("built", OUT)
	print("preview", shot)
	print("GAPS:", json.dumps(gaps, ensure_ascii=False, indent=2))


if __name__ == "__main__":
	main()
