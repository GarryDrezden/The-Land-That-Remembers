#!/usr/bin/env python3
"""Process AI-generated outdoor test sheets into transparent game assets.

Sources stay untouched in generated_test/source/.
Outputs go to generated_test/processed/.

Honest constraints:
- Sheets have opaque black backgrounds (no native alpha).
- Layout is irregular — no blind hframes/vframes except player band grid.
- Terrain is chunk-based, not a clean 16x16 tileset → ground is baked for the art test.
"""
from __future__ import annotations

import json
import random
import shutil
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/art/outdoor/generated_test/source"
OUT = ROOT / "assets/art/outdoor/generated_test/processed"
AUDIT = ROOT / "docs/art_tests/generated_test_v2_audit.json"

BLACK_THR = 18
ALPHA_SOFT = 40


def is_bg_rgb(r: int, g: int, b: int) -> bool:
	return r <= BLACK_THR and g <= BLACK_THR and b <= BLACK_THR


def remove_black_bg(im: Image.Image) -> Image.Image:
	"""Remove only background reachable from image borders (keeps dark interior pixels)."""
	im = im.convert("RGBA")
	w, h = im.size
	px = im.load()
	is_dark = [[False] * w for _ in range(h)]
	for y in range(h):
		for x in range(w):
			r, g, b, _a = px[x, y]
			if r <= BLACK_THR and g <= BLACK_THR and b <= BLACK_THR:
				is_dark[y][x] = True
	q: deque[tuple[int, int]] = deque()
	seen = [[False] * w for _ in range(h)]
	for x in range(w):
		for y in (0, h - 1):
			if is_dark[y][x] and not seen[y][x]:
				seen[y][x] = True
				q.append((x, y))
	for y in range(h):
		for x in (0, w - 1):
			if is_dark[y][x] and not seen[y][x]:
				seen[y][x] = True
				q.append((x, y))
	while q:
		x, y = q.popleft()
		px[x, y] = (0, 0, 0, 0)
		for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
			if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and is_dark[ny][nx]:
				seen[ny][nx] = True
				q.append((nx, ny))
	# Kill soft fringe only when adjacent to already-transparent bg
	for y in range(h):
		for x in range(w):
			r, g, b, a = px[x, y]
			if a == 0:
				continue
			if r <= ALPHA_SOFT and g <= ALPHA_SOFT and b <= ALPHA_SOFT:
				for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
					if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] == 0:
						px[x, y] = (0, 0, 0, 0)
						break
	return im


def connected_components(im: Image.Image, min_pixels: int = 80) -> list[tuple[int, int, int, int]]:
	w, h = im.size
	px = im.load()
	seen = [[False] * w for _ in range(h)]
	boxes: list[tuple[int, int, int, int, int]] = []

	def opaque(x: int, y: int) -> bool:
		return px[x, y][3] > 20

	for y in range(h):
		for x in range(w):
			if seen[y][x] or not opaque(x, y):
				continue
			q = deque([(x, y)])
			seen[y][x] = True
			minx = maxx = x
			miny = maxy = y
			count = 0
			while q:
				cx, cy = q.popleft()
				count += 1
				minx = min(minx, cx)
				maxx = max(maxx, cx)
				miny = min(miny, cy)
				maxy = max(maxy, cy)
				for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
					if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and opaque(nx, ny):
						seen[ny][nx] = True
						q.append((nx, ny))
			if count >= min_pixels:
				boxes.append((minx, miny, maxx + 1, maxy + 1, count))
	boxes.sort(key=lambda b: (b[1], b[0]))
	return [(a, b, c, d) for a, b, c, d, _ in boxes]


def crop_box(im: Image.Image, box: tuple[int, int, int, int], pad: int = 1) -> Image.Image:
	x0, y0, x1, y1 = box
	x0 = max(0, x0 - pad)
	y0 = max(0, y0 - pad)
	x1 = min(im.width, x1 + pad)
	y1 = min(im.height, y1 + pad)
	return im.crop((x0, y0, x1, y1))


def save(im: Image.Image, path: Path) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	im.save(path)


def mean_rgb(im: Image.Image) -> tuple[float, float, float]:
	px = list(im.getdata())
	vals = [p for p in px if p[3] > 20]
	if not vals:
		return (0.0, 0.0, 0.0)
	n = len(vals)
	return (sum(p[0] for p in vals) / n, sum(p[1] for p in vals) / n, sum(p[2] for p in vals) / n)


def clear_dir(path: Path) -> None:
	if path.exists():
		shutil.rmtree(path)
	path.mkdir(parents=True, exist_ok=True)


def process_player() -> dict:
	"""Slice by measured row/col content bands — not connected components."""
	src = SRC / "player_sheet.png"
	im = remove_black_bg(Image.open(src))
	save(im, OUT / "_cleaned" / "player_sheet.png")

	# Measured from opaque projections on source sheet (1024x682).
	row_bands = [(39, 182), (224, 354), (395, 524), (560, 672)]
	col_bands = [(227, 303), (374, 450), (545, 624), (705, 783), (860, 939)]

	raw_frames: list[Image.Image] = []
	opaque_counts: list[int] = []
	for ry0, ry1 in row_bands:
		for cx0, cx1 in col_bands:
			cell = im.crop((cx0, ry0, cx1, ry1))
			# Tight crop to opaque content inside cell
			bbox = cell.getbbox()
			if bbox is None:
				raw_frames.append(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
				opaque_counts.append(0)
				continue
			piece = cell.crop(bbox)
			raw_frames.append(piece)
			opaque_counts.append(sum(1 for p in piece.getdata() if p[3] > 20))

	max_w = max(f.width for f in raw_frames)
	max_h = max(f.height for f in raw_frames)
	# Prefer a stable canvas near measured character size
	max_w = max(max_w, 76)
	max_h = max(max_h, 130)

	frames_out: list[str] = []
	clear_dir(OUT / "player")
	for i, f in enumerate(raw_frames):
		canvas = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
		ox = (max_w - f.width) // 2
		oy = max_h - f.height  # feet anchored
		canvas.paste(f, (ox, oy), f)
		path = OUT / "player" / f"frame_{i:02d}.png"
		save(canvas, path)
		frames_out.append(path.relative_to(ROOT).as_posix())

	# Contact sheet for audit
	cols, rows = 5, 4
	sheet = Image.new("RGBA", (cols * (max_w + 4), rows * (max_h + 4)), (30, 30, 30, 255))
	d = ImageDraw.Draw(sheet)
	for i, rel in enumerate(frames_out):
		fr = Image.open(ROOT / rel)
		x = (i % cols) * (max_w + 4) + 2
		y = (i // cols) * (max_h + 4) + 2
		sheet.paste(fr, (x, y), fr)
		d.text((x, y), str(i), fill=(255, 0, 255, 255))
	save(sheet, ROOT / "docs/art_tests/player_frames_v2_contact.png")

	# Direction map (sheet: row0 down+up, rows1-3 right walks). Left = flip in engine.
	anims = {
		"idle_down": [0],
		"walk_down": [0, 1],
		"idle_up": [2],
		"walk_up": [2, 3, 4],
		"idle_right": [5],
		"walk_right": [5, 6, 7, 8, 9],
		"idle_left": [5],  # flip
		"walk_left": [5, 6, 7, 8, 9],  # flip
		"walk_right_alt_a": [10, 11, 12, 13, 14],
		"walk_right_alt_b": [15, 16, 17, 18, 19],
	}

	return {
		"frame_size": [max_w, max_h],
		"frames": frames_out,
		"count": len(frames_out),
		"opaque_counts": opaque_counts,
		"anims": anims,
		"row_bands": row_bands,
		"col_bands": col_bands,
		"note": "Left = horizontal flip of right. Extra right walk rows kept as alt cycles.",
	}


def process_vegetation() -> dict:
	im = remove_black_bg(Image.open(SRC / "vegetation_obstacles.png"))
	save(im, OUT / "_cleaned" / "vegetation_obstacles.png")
	clear_dir(OUT / "vegetation")
	# Keep obstacles vegetation-related separate from terrain props
	boxes = connected_components(im, min_pixels=250)
	meta = []
	for i, box in enumerate(boxes):
		piece = crop_box(im, box)
		if piece.width > im.width * 0.95 and piece.height > im.height * 0.95:
			continue
		path = OUT / "vegetation" / f"veg_{i:02d}.png"
		save(piece, path)
		meta.append(
			{
				"file": path.relative_to(ROOT).as_posix(),
				"box": list(box),
				"size": [piece.width, piece.height],
				"area": piece.width * piece.height,
				"mean": [round(c, 1) for c in mean_rgb(piece)],
			}
		)

	# Named picks by height / width heuristics from sheet layout
	by_h = sorted(meta, key=lambda m: m["size"][1], reverse=True)
	oak = by_h[0]["file"] if by_h else None
	birch = by_h[1]["file"] if len(by_h) > 1 else None
	# Third tallest is short spruce/pine candidate on this sheet (~141px)
	spruce = by_h[2]["file"] if len(by_h) > 2 else None

	# Copy named roles
	named = {}
	for role, src_rel in (("oak", oak), ("birch", birch), ("spruce", spruce)):
		if not src_rel:
			continue
		dest = OUT / "vegetation" / f"tree_{role}.png"
		Image.open(ROOT / src_rel).save(dest)
		named[role] = dest.relative_to(ROOT).as_posix()

	# Bushes: mid area, wider than tall-ish green blobs height 80-120
	bushes = []
	for m in sorted(meta, key=lambda x: -x["area"]):
		w, h = m["size"]
		if 70 <= h <= 120 and 90 <= w <= 250 and m["mean"][1] > m["mean"][0]:
			bushes.append(m["file"])
		if len(bushes) >= 6:
			break
	for i, rel in enumerate(bushes):
		dest = OUT / "vegetation" / f"bush_{i:02d}.png"
		Image.open(ROOT / rel).save(dest)

	# Weeds: tall thin or small green
	weeds = []
	for m in meta:
		w, h = m["size"]
		if 20 <= w <= 100 and 40 <= h <= 120 and m["mean"][1] >= m["mean"][0]:
			weeds.append(m["file"])
	weeds = weeds[:10]
	for i, rel in enumerate(weeds):
		dest = OUT / "vegetation" / f"weed_{i:02d}.png"
		Image.open(ROOT / rel).save(dest)

	return {
		"count": len(meta),
		"named_trees": named,
		"bushes": [f"assets/art/outdoor/generated_test/processed/vegetation/bush_{i:02d}.png" for i in range(len(bushes))],
		"weeds": [f"assets/art/outdoor/generated_test/processed/vegetation/weed_{i:02d}.png" for i in range(len(weeds))],
		"all": meta,
		"issue": "Spruce on source sheet is much shorter than oak/birch (~141px vs ~300px).",
	}


def process_obstacles_from_veg(veg_meta: dict) -> dict:
	clear_dir(OUT / "obstacles")
	# From vegetation sheet: rocks / logs / stumps by gray/brown + aspect
	meta = veg_meta.get("all", [])
	rocks, logs, stumps = [], [], []
	for m in meta:
		w, h = m["size"]
		r, g, b = m["mean"]
		rel = m["file"]
		# gray rocks
		if abs(r - g) < 20 and abs(g - b) < 25 and 40 < r < 160 and h < 120 and w < 280:
			rocks.append(rel)
		# long logs
		elif w > h * 1.8 and w > 150 and h < 100 and r > 80:
			logs.append(rel)
		# stump-like
		elif 50 <= w <= 160 and 50 <= h <= 110 and r > g and r > 90:
			stumps.append(rel)

	out = {"rocks": [], "logs": [], "stumps": []}
	for i, rel in enumerate(rocks[:10]):
		dest = OUT / "obstacles" / f"rock_{i:02d}.png"
		Image.open(ROOT / rel).save(dest)
		out["rocks"].append(dest.relative_to(ROOT).as_posix())
	for i, rel in enumerate(logs[:6]):
		dest = OUT / "obstacles" / f"log_{i:02d}.png"
		Image.open(ROOT / rel).save(dest)
		out["logs"].append(dest.relative_to(ROOT).as_posix())
	for i, rel in enumerate(stumps[:6]):
		dest = OUT / "obstacles" / f"stump_{i:02d}.png"
		Image.open(ROOT / rel).save(dest)
		out["stumps"].append(dest.relative_to(ROOT).as_posix())
	return out


def process_house() -> dict:
	im = remove_black_bg(Image.open(SRC / "house_modules.png"))
	save(im, OUT / "_cleaned" / "house_modules.png")
	clear_dir(OUT / "buildings")
	boxes = connected_components(im, min_pixels=200)
	meta = []
	for i, box in enumerate(boxes):
		piece = crop_box(im, box)
		if piece.width > im.width * 0.95:
			continue
		path = OUT / "buildings" / f"part_{i:02d}.png"
		save(piece, path)
		meta.append({"file": path.relative_to(ROOT).as_posix(), "size": [piece.width, piece.height]})
	meta_sorted = sorted(meta, key=lambda m: m["size"][0] * m["size"][1], reverse=True)
	house = None
	if meta_sorted:
		house_path = OUT / "buildings" / "house_main.png"
		Image.open(ROOT / meta_sorted[0]["file"]).save(house_path)
		house = house_path.relative_to(ROOT).as_posix()
	# fences / stairs — mid-sized horizontal pieces
	extras = []
	for m in meta_sorted[1:]:
		w, h = m["size"]
		if 40 <= h <= 100 and 80 <= w <= 350:
			extras.append(m["file"])
		if len(extras) >= 8:
			break
	for i, rel in enumerate(extras):
		dest = OUT / "buildings" / f"prop_{i:02d}.png"
		Image.open(ROOT / rel).save(dest)
	return {
		"house": house,
		"props": [f"assets/art/outdoor/generated_test/processed/buildings/prop_{i:02d}.png" for i in range(len(extras))],
		"count": len(meta),
	}


def process_terrain() -> dict:
	im = remove_black_bg(Image.open(SRC / "terrain_water_rocks_weeds.png"))
	save(im, OUT / "_cleaned" / "terrain_water_rocks_weeds.png")
	clear_dir(OUT / "terrain")
	clear_dir(OUT / "water")
	# Also pull small weeds/rocks from this sheet into obstacles
	boxes = connected_components(im, min_pixels=120)
	dirt, grass, water, shores, props = [], [], [], [], []
	for i, box in enumerate(boxes):
		piece = crop_box(im, box)
		w, h = piece.size
		if w > im.width * 0.9:
			continue
		r, g, b = mean_rgb(piece)
		area = w * h
		entry = {"file": None, "size": [w, h], "mean": [round(r, 1), round(g, 1), round(b, 1)], "area": area}
		# water: cyan/teal
		if b > r + 15 and g > r + 5 and area > 800:
			path = OUT / "water" / f"water_{len(water):02d}.png"
			save(piece, path)
			entry["file"] = path.relative_to(ROOT).as_posix()
			water.append(entry)
		# dirt brown tiles
		elif r > 140 and r > b + 40 and 45 <= w <= 95 and 45 <= h <= 95:
			path = OUT / "terrain" / f"dirt_{len(dirt):02d}.png"
			save(piece, path)
			entry["file"] = path.relative_to(ROOT).as_posix()
			dirt.append(entry)
		# grassy / transition
		elif g > r and area > 1500:
			path = OUT / "terrain" / f"grass_{len(grass):02d}.png"
			save(piece, path)
			entry["file"] = path.relative_to(ROOT).as_posix()
			grass.append(entry)
		elif area > 2000 and (g > 90 or r > 100):
			path = OUT / "terrain" / f"shore_{len(shores):02d}.png"
			save(piece, path)
			entry["file"] = path.relative_to(ROOT).as_posix()
			shores.append(entry)
		elif 80 < area < 8000:
			path = OUT / "obstacles" / f"terrain_detail_{len(props):02d}.png"
			path.parent.mkdir(parents=True, exist_ok=True)
			save(piece, path)
			entry["file"] = path.relative_to(ROOT).as_posix()
			props.append(entry)

	# Bake large ground for art test (no clean seamless 16px grass tile on sheet)
	map_w, map_h = 2048, 1536
	ground = Image.new("RGBA", (map_w, map_h), (0, 0, 0, 0))
	base_green = (86, 118, 52, 255)
	# subtle noise base
	rnd = random.Random(42)
	px = ground.load()
	for y in range(map_h):
		for x in range(map_w):
			j = rnd.randint(-8, 8)
			px[x, y] = (base_green[0] + j, base_green[1] + j // 2, base_green[2] + j // 3, 255)

	def stamp(pieces: list[dict], count: int, scale_jitter: bool = True) -> None:
		if not pieces:
			return
		for _ in range(count):
			src_im = Image.open(ROOT / pieces[rnd.randint(0, len(pieces) - 1)]["file"])
			if scale_jitter and src_im.width > 40:
				# keep nearest, no fractional downscale that blurs
				pass
			x = rnd.randint(-40, map_w - 20)
			y = rnd.randint(-40, map_h - 20)
			ground.alpha_composite(src_im, (x, y))

	stamp(grass, 220)
	stamp(dirt, 40)
	# winding dirt path (parametric)
	if dirt:
		path_tile = Image.open(ROOT / dirt[0]["file"])
		for t in range(0, 360):
			# two winding paths
			x1 = int(180 + t * 4.2 + 40 * __import__("math").sin(t * 0.08))
			y1 = int(520 + 90 * __import__("math").sin(t * 0.05))
			x2 = int(900 + 35 * __import__("math").sin(t * 0.07))
			y2 = int(200 + t * 3.1)
			for x, y in ((x1, y1), (x2, y2)):
				if -50 < x < map_w and -50 < y < map_h:
					ground.alpha_composite(path_tile, (x - path_tile.width // 2, y - path_tile.height // 2))
					# thicken
					ground.alpha_composite(path_tile, (x - path_tile.width // 2 + 20, y - path_tile.height // 2 + 8))

	ground_path = OUT / "terrain" / "ground_baked.png"
	save(ground, ground_path)

	# Pond bake: irregular water body assembled from water chunks + shore stamps
	pond = Image.new("RGBA", (520, 360), (0, 0, 0, 0))
	# soft elliptical water base using average water color
	if water:
		wr, wg, wb = water[0]["mean"]
	else:
		wr, wg, wb = (45, 145, 130)
	ppx = pond.load()
	cx, cy = 260, 180
	for y in range(360):
		for x in range(520):
			nx = (x - cx) / 210.0
			ny = (y - cy) / 140.0
			# irregular ellipse
			n = (nx * nx + ny * ny) + 0.15 * __import__("math").sin(x * 0.07) * __import__("math").cos(y * 0.09)
			if n < 1.0:
				j = rnd.randint(-10, 10)
				ppx[x, y] = (int(wr + j), int(wg + j // 2), int(wb + j // 2), 255)
	for _ in range(35):
		if not water:
			break
		chunk = Image.open(ROOT / water[rnd.randint(0, len(water) - 1)]["file"])
		pond.alpha_composite(chunk, (rnd.randint(20, 360), rnd.randint(20, 240)))
	for _ in range(25):
		if not shores:
			break
		chunk = Image.open(ROOT / shores[rnd.randint(0, len(shores) - 1)]["file"])
		# place near edges
		side = rnd.randint(0, 3)
		if side == 0:
			pos = (rnd.randint(0, 400), rnd.randint(0, 40))
		elif side == 1:
			pos = (rnd.randint(0, 400), rnd.randint(280, 320))
		elif side == 2:
			pos = (rnd.randint(0, 40), rnd.randint(0, 280))
		else:
			pos = (rnd.randint(400, 450), rnd.randint(0, 280))
		pond.alpha_composite(chunk, pos)
	pond_path = OUT / "water" / "pond_baked.png"
	save(pond, pond_path)

	return {
		"dirt_count": len(dirt),
		"grass_count": len(grass),
		"water_count": len(water),
		"shore_count": len(shores),
		"ground_baked": ground_path.relative_to(ROOT).as_posix(),
		"pond_baked": pond_path.relative_to(ROOT).as_posix(),
		"dirt": [d["file"] for d in dirt[:12]],
		"water": [w["file"] for w in water],
		"shores": [s["file"] for s in shores[:12]],
		"grass": [g["file"] for g in grass[:12]],
		"limitation": (
			"No clean seamless 16x16 grass/water tileset on source sheet. "
			"Art test uses baked ground + pond assembled from extracted chunks "
			"(temporary; not production tilemap)."
		),
	}


def main() -> None:
	OUT.mkdir(parents=True, exist_ok=True)
	(OUT / "_cleaned").mkdir(parents=True, exist_ok=True)
	(OUT / "_reference").mkdir(parents=True, exist_ok=True)

	# Reference only — do not slice into gameplay tiles
	ref = SRC / "composition_reference.png"
	if ref.exists():
		save(Image.open(ref), OUT / "_reference" / "composition_reference.png")

	player = process_player()
	veg = process_vegetation()
	obs = process_obstacles_from_veg(veg)
	house = process_house()
	terrain = process_terrain()

	# Clearable picks
	clearables = []
	for group, blocking in (
		(veg.get("weeds", [])[:3], False),
		(obs.get("rocks", [])[:2], True),
		(obs.get("logs", [])[:1] + obs.get("stumps", [])[:1], True),
	):
		for rel in group:
			clearables.append({"path": rel, "blocking": blocking})

	manifest = {
		"pixel_filter": "nearest",
		"map_size_px": [2048, 1536],
		"tile_px": 16,
		"camera_zoom": 2,
		"player_spawn": [980, 780],
		"player": {
			"frames": player["frames"],
			"frame_size": player["frame_size"],
			"anims": player["anims"],
			"fps_walk": 8,
			"move_speed": 110.0,
		},
		"ground": terrain["ground_baked"],
		"pond": {
			"texture": terrain["pond_baked"],
			"position": [420, 620],
			"temporary_bake": True,
		},
		"house": {
			"texture": house["house"],
			"position": [1280, 280],
		},
		"trees": [
			{"id": "oak", "texture": veg["named_trees"].get("oak"), "position": [620, 420]},
			{"id": "birch", "texture": veg["named_trees"].get("birch"), "position": [1580, 900]},
			{"id": "spruce", "texture": veg["named_trees"].get("spruce"), "position": [380, 980]},
		],
		"bushes": veg.get("bushes", []),
		"weeds": veg.get("weeds", []),
		"rocks": obs.get("rocks", []),
		"logs": obs.get("logs", []),
		"stumps": obs.get("stumps", []),
		"building_props": house.get("props", []),
		"clearables": clearables,
		"layout_clusters": [
			# irregular groups — positions relative to map
			{"kind": "bush", "positions": [[700, 500], [740, 530], [680, 560]]},
			{"kind": "weed", "positions": [[860, 700], [890, 720], [840, 740], [910, 690], [880, 760]]},
			{"kind": "rock", "positions": [[500, 880], [530, 900], [510, 920]]},
			{"kind": "rock", "positions": [[1100, 1000], [1130, 1020]]},
			{"kind": "log", "positions": [[1450, 700]]},
			{"kind": "stump", "positions": [[760, 980], [1500, 500]]},
			{"kind": "weed", "positions": [[1350, 850], [1380, 870], [1320, 890]]},
			{"kind": "bush", "positions": [[400, 700], [1600, 600]]},
		],
		"interactive_clearables": [
			{"id": "clear_weed", "kind": "weed", "path_index": 0, "position": [920, 820], "blocking": False},
			{"id": "clear_rock", "kind": "rock", "path_index": 0, "position": [1050, 860], "blocking": True},
			{"id": "clear_log", "kind": "log", "path_index": 0, "position": [880, 940], "blocking": True},
		],
		"notes": [
			terrain["limitation"],
			veg.get("issue", ""),
			"Player sheet had no left-facing frames; engine flips right.",
			"Status: candidate generated outdoor pack — art test v2 (not production-final).",
		],
	}

	audit = {
		"status": "candidate generated outdoor pack — art test v2",
		"source_issues": {
			"all_sprite_sheets": "Opaque black (#000) background, zero native transparency. Soft dark fringe keyed out.",
			"not_uniform_grid": "Vegetation/house/terrain not safe for blind hframes/vframes; CC + manual role picks.",
			"player_grid": "Player usable via measured 4x5 content bands (not equal cell size, but separable).",
			"composition_reference": "Mood reference only — not used as gameplay texture.",
			"terrain_tileset": "No production-ready seamless grass/water 16px set; baked ground/pond for art test.",
			"spruce_scale": "Spruce extraction much shorter than oak/birch on source sheet.",
			"object_bases": "Trees/house include baked dirt islands under feet — may look like patches on ground.",
		},
		"player": player,
		"vegetation": {"named_trees": veg.get("named_trees"), "issue": veg.get("issue"), "count": veg.get("count")},
		"obstacles": obs,
		"house": house,
		"terrain": {
			"dirt_count": terrain["dirt_count"],
			"grass_count": terrain["grass_count"],
			"water_count": terrain["water_count"],
			"limitation": terrain["limitation"],
		},
	}

	AUDIT.parent.mkdir(parents=True, exist_ok=True)
	AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
	(OUT / "scene_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
	print("processed ->", OUT)
	print("player frames", player["count"], "opaque", player["opaque_counts"])
	print("trees", veg.get("named_trees"))
	print("ground", terrain["ground_baked"])
	print("manifest", OUT / "scene_manifest.json")


if __name__ == "__main__":
	main()
