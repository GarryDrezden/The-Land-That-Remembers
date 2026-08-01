#!/usr/bin/env python3
"""Deterministic seamless grass/soil terrain atlas (16×16, margin=0, separation=0).

Visual pass: richer interiors + fringe, while preserving shared edge profiles
and wraparound borders (seam contract / test_terrain_atlas.py).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/art/outdoor/terrain_proof"
TILE = 16
SEED = 20260801

# Close greens — differ by detail, not whole-tile hue
GRASS = [
	(70, 112, 48),   # base
	(66, 106, 44),   # darker soft
	(76, 118, 52),   # lighter fleck
	(62, 100, 42),   # soft shadow patch
]
SOIL = [
	(114, 80, 50),   # warm packed earth
	(104, 72, 44),   # darker clump base
	(122, 88, 56),   # lighter dry spot
	(96, 66, 40),    # deep shadow
]
FRINGE = (58, 92, 38)       # grass overhang shade
SOIL_EDGE = (88, 60, 36)    # darker earth under fringe
PEBBLE = (102, 96, 88)
PEBBLE2 = (90, 86, 80)
CLUMP = (86, 58, 34)
ROOT_FIBER = (130, 100, 62)

TL, TR, BR, BL = 1, 2, 4, 8


def _h(*parts: int) -> int:
	n = SEED
	for p in parts:
		n = (n ^ (p * 374761393)) & 0xFFFFFFFF
		n = (n * 1664525 + 1013904223) & 0xFFFFFFFF
	return n


def grass_c(i: int) -> tuple[int, int, int]:
	return GRASS[i % 4]


def soil_c(i: int) -> tuple[int, int, int]:
	return SOIL[i % 4]


def _put(px, ox: int, oy: int, x: int, y: int, c: tuple[int, int, int]) -> None:
	if 0 <= x < TILE and 0 <= y < TILE:
		px[ox + x, oy + y] = (*c, 255)


def _stamp_cluster(px, ox: int, oy: int, cx: int, cy: int, color: tuple[int, int, int], n: int, salt: int) -> None:
	"""Stamp 2–4 connected pixels around cx,cy (interior-safe caller)."""
	_put(px, ox, oy, cx, cy, color)
	dirs = ((1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1))
	for i in range(max(1, n - 1)):
		d = dirs[(_h(salt, cx, cy, i) >> 3) % len(dirs)]
		_put(px, ox, oy, cx + d[0], cy + d[1], color)


def paint_grass_surface(px, ox: int, oy: int, salt: int, style: int = 0, inner_only: bool = False) -> None:
	"""style 0=base, 1=A more flecks, 2=B darker patches, 3=C sparse blades."""
	# Fill base
	for y in range(TILE):
		for x in range(TILE):
			if inner_only and (x < 2 or y < 2 or x > 13 or y > 13):
				continue
			v = _h(x, y, salt)
			c = GRASS[0]
			# Soft shade banding — rare, clustered feel via shared hash
			if (v % 29) == 0:
				c = GRASS[1]
			elif (v % 37) == 0:
				c = GRASS[2]
			px[ox + x, oy + y] = (*c, 255)

	# Interior-only details (never on outer 2px ring for variants; base then wrap-locked)
	x0, x1 = (2, 13) if inner_only else (1, 14)
	y0, y1 = (2, 13) if inner_only else (1, 14)

	# Soft dark patches
	patch_n = 1 + (style == 2)
	for p in range(patch_n):
		cx = 3 + (_h(salt, 10 + p) % 10)
		cy = 3 + (_h(salt, 20 + p) % 10)
		_stamp_cluster(px, ox, oy, cx, cy, GRASS[3], 3, salt + p)

	# Small 2–4 px fleck groups
	flecks = 2 + style  # A more flecks
	for p in range(flecks):
		cx = 3 + (_h(salt, 30 + p) % 10)
		cy = 3 + (_h(salt, 40 + p) % 10)
		_stamp_cluster(px, ox, oy, cx, cy, GRASS[2 if p % 2 == 0 else 1], 2 + (p % 2), salt + 50 + p)

	# Short blades (2px), rare
	blade_n = 1 if style == 0 else (2 if style != 3 else 3)
	for p in range(blade_n):
		bx = 3 + (_h(salt, 60 + p) % 10)
		by = 4 + (_h(salt, 70 + p) % 8)
		_put(px, ox, oy, bx, by, GRASS[2])
		_put(px, ox, oy, bx, by - 1, GRASS[0])
		if style == 3 and (_h(salt, p) & 1):
			_put(px, ox, oy, bx - 1, by - 1, GRASS[1])

	if not inner_only:
		for y in range(TILE):
			px[ox + TILE - 1, oy + y] = px[ox + 0, oy + y]
		for x in range(TILE):
			px[ox + x, oy + TILE - 1] = px[ox + x, oy + 0]


def paint_soil_surface(px, ox: int, oy: int, salt: int, style: int = 0, inner_only: bool = False) -> None:
	for y in range(TILE):
		for x in range(TILE):
			if inner_only and (x < 2 or y < 2 or x > 13 or y > 13):
				continue
			v = _h(x, y, salt + 7)
			c = SOIL[0]
			if (v % 31) == 0:
				c = SOIL[1]
			elif (v % 43) == 0:
				c = SOIL[2]
			px[ox + x, oy + y] = (*c, 255)

	# Darker soft patches
	for p in range(1 + (style > 0)):
		cx = 3 + (_h(salt, 80 + p) % 10)
		cy = 3 + (_h(salt, 90 + p) % 10)
		_stamp_cluster(px, ox, oy, cx, cy, SOIL[3], 3, salt + 100 + p)

	# Clumps
	for p in range(1 + style):
		cx = 4 + (_h(salt, 110 + p) % 8)
		cy = 4 + (_h(salt, 120 + p) % 8)
		_put(px, ox, oy, cx, cy, CLUMP)
		if (_h(salt, p) & 1):
			_put(px, ox, oy, cx + 1, cy, CLUMP)

	# Pebbles
	for p in range(1 + (style == 2)):
		cx = 4 + (_h(salt, 130 + p) % 8)
		cy = 4 + (_h(salt, 140 + p) % 8)
		_put(px, ox, oy, cx, cy, PEBBLE if p % 2 == 0 else PEBBLE2)

	# Dry root fiber (1–3 px diagonal), rare
	if style >= 1 or (_h(salt, 9) % 3) == 0:
		rx = 5 + (_h(salt, 150) % 6)
		ry = 6 + (_h(salt, 160) % 5)
		_put(px, ox, oy, rx, ry, ROOT_FIBER)
		_put(px, ox, oy, rx + 1, ry, ROOT_FIBER)
		if style >= 2:
			_put(px, ox, oy, rx + 2, ry - 1, ROOT_FIBER)

	if not inner_only:
		for y in range(TILE):
			px[ox + TILE - 1, oy + y] = px[ox + 0, oy + y]
		for x in range(TILE):
			px[ox + x, oy + TILE - 1] = px[ox + x, oy + 0]


def paint_seamless_surface(px, ox: int, oy: int, is_soil: bool, salt: int, inner_only: bool = False, style: int = 0) -> None:
	if is_soil:
		paint_soil_surface(px, ox, oy, salt, style=style, inner_only=inner_only)
	else:
		paint_grass_surface(px, ox, oy, salt, style=style, inner_only=inner_only)


_BASE_GRASS: list[list[tuple[int, int, int]]] | None = None
_BASE_SOIL: list[list[tuple[int, int, int]]] | None = None


def base_grass() -> list[list[tuple[int, int, int]]]:
	global _BASE_GRASS
	if _BASE_GRASS is None:
		tmp = Image.new("RGBA", (TILE, TILE))
		px = tmp.load()
		paint_grass_surface(px, 0, 0, salt=11, style=0)
		_BASE_GRASS = [[px[x, y][:3] for x in range(TILE)] for y in range(TILE)]
	return _BASE_GRASS


def base_soil() -> list[list[tuple[int, int, int]]]:
	global _BASE_SOIL
	if _BASE_SOIL is None:
		tmp = Image.new("RGBA", (TILE, TILE))
		px = tmp.load()
		paint_soil_surface(px, 0, 0, salt=29, style=0)
		_BASE_SOIL = [[px[x, y][:3] for x in range(TILE)] for y in range(TILE)]
	return _BASE_SOIL


def build_edge_profiles() -> dict[tuple[bool, bool], list[tuple[int, int, int]]]:
	"""Shared side profiles — identical bytes for identical corner pairs (seam contract)."""
	g = base_grass()
	s = base_soil()
	profiles: dict[tuple[bool, bool], list[tuple[int, int, int]]] = {}
	profiles[(False, False)] = [g[0][x] for x in range(TILE)]
	profiles[(True, True)] = [s[0][x] for x in range(TILE)]

	# GS: grass → soil with 1–3px fringe, fixed connection points
	gs: list[tuple[int, int, int]] = []
	for i in range(TILE):
		if i <= 4:
			gs.append(g[0][i])
		elif i == 5:
			gs.append(g[1][i])  # protruding blade
		elif i == 6:
			gs.append(FRINGE)
		elif i == 7:
			gs.append(SOIL_EDGE)  # darker earth under fringe
		else:
			gs.append(s[0][i])
	profiles[(False, True)] = gs

	sg: list[tuple[int, int, int]] = []
	for i in range(TILE):
		if i <= 7:
			sg.append(s[0][i] if i <= 6 else SOIL_EDGE)
		elif i == 8:
			sg.append(FRINGE)
		elif i == 9:
			sg.append(g[1][i])
		else:
			sg.append(g[0][i])
	profiles[(True, False)] = sg
	return profiles


EDGE = build_edge_profiles()


def corner_soil(mask: int, bit: int) -> bool:
	return bool(mask & bit)


def bilinear_soil(mask: int, x: float, y: float) -> float:
	u = x / 15.0
	v = y / 15.0
	tl = 1.0 if corner_soil(mask, TL) else 0.0
	tr = 1.0 if corner_soil(mask, TR) else 0.0
	bl = 1.0 if corner_soil(mask, BL) else 0.0
	br = 1.0 if corner_soil(mask, BR) else 0.0
	return (
		tl * (1 - u) * (1 - v)
		+ tr * u * (1 - v)
		+ bl * (1 - u) * v
		+ br * u * v
	)


def paint_transition_interior(px, ox: int, oy: int, mask: int) -> None:
	"""Interior transition with 1–3px grass fringe; edges overwritten by shared profiles."""
	g = base_grass()
	s = base_soil()
	for y in range(TILE):
		for x in range(TILE):
			f = bilinear_soil(mask, float(x), float(y))
			h = _h(mask, x, y)
			if f >= 0.55:
				c = s[y][x]
				# darker soil just under fringe band
				if 0.55 <= f < 0.68:
					c = SOIL_EDGE if (h & 3) != 0 else s[y][x]
			elif f <= 0.42:
				c = g[y][x]
			else:
				# fringe band 1–3px: grass overhang / blades into soil
				band = (f - 0.42) / 0.13  # 0..1 across fringe
				if band < 0.35:
					c = g[y][x]
					if (h % 5) == 0:
						c = GRASS[2]
				elif band < 0.65:
					c = FRINGE if (h & 1) == 0 else GRASS[1]
				else:
					c = SOIL_EDGE if (h & 2) == 0 else s[y][x]
					# occasional blade tip into soil
					if (h % 7) == 0:
						c = GRASS[2]
			px[ox + x, oy + y] = (*c, 255)


def apply_shared_edges(px, ox: int, oy: int, mask: int) -> None:
	tl = corner_soil(mask, TL)
	tr = corner_soil(mask, TR)
	br = corner_soil(mask, BR)
	bl = corner_soil(mask, BL)
	g = base_grass()
	s = base_soil()

	top = EDGE[(tl, tr)]
	bot = EDGE[(bl, br)]

	def vert_profile(a: bool, b: bool) -> list[tuple[int, int, int]]:
		if a == b:
			src = s if a else g
			return [src[y][0] for y in range(TILE)]
		return EDGE[(a, b)]

	left = vert_profile(tl, bl)
	right = vert_profile(tr, br)

	for i in range(TILE):
		px[ox + i, oy + 0] = (*top[i], 255)
		px[ox + i, oy + 15] = (*bot[i], 255)
		px[ox + 0, oy + i] = (*left[i], 255)
		px[ox + 15, oy + i] = (*right[i], 255)

	if mask == 0:
		for i in range(TILE):
			px[ox + i, oy + 0] = (*g[0][i], 255)
			px[ox + i, oy + 15] = (*g[15][i], 255)
			px[ox + 0, oy + i] = (*g[i][0], 255)
			px[ox + 15, oy + i] = (*g[i][15], 255)
	elif mask == 15:
		for i in range(TILE):
			px[ox + i, oy + 0] = (*s[0][i], 255)
			px[ox + i, oy + 15] = (*s[15][i], 255)
			px[ox + 0, oy + i] = (*s[i][0], 255)
			px[ox + 15, oy + i] = (*s[i][15], 255)


def draw_mask(px, ox: int, oy: int, mask: int) -> None:
	if mask == 0:
		paint_grass_surface(px, ox, oy, salt=11, style=0)
	elif mask == 15:
		paint_soil_surface(px, ox, oy, salt=29, style=0)
	else:
		paint_transition_interior(px, ox, oy, mask)
	apply_shared_edges(px, ox, oy, mask)


def copy_border(px, sox: int, soy: int, dox: int, doy: int) -> None:
	for i in range(TILE):
		px[dox + i, doy + 0] = px[sox + i, soy + 0]
		px[dox + i, doy + 15] = px[sox + i, soy + 15]
		px[dox + 0, doy + i] = px[sox + 0, soy + i]
		px[dox + 15, doy + i] = px[sox + 15, soy + i]


def make_ground() -> Image.Image:
	cols, rows = 8, 4
	im = Image.new("RGBA", (cols * TILE, rows * TILE), (0, 0, 0, 255))
	px = im.load()

	for mask in range(16):
		draw_mask(px, (mask % 4) * TILE, (mask // 4) * TILE, mask)

	# Grass variants A/B/C (+ keep 4th mild unused visually same borders)
	# col4=A(style1), col5=B(style2), col6=C(style3), col7=extra mild
	for vi, style in enumerate((1, 2, 3, 1)):
		ox, oy = (4 + vi) * TILE, 0
		draw_mask(px, ox, oy, 0)
		paint_grass_surface(px, ox, oy, salt=100 + vi * 13, style=style, inner_only=True)
		copy_border(px, 0, 0, ox, oy)

	for vi, style in enumerate((1, 2, 3, 1)):
		ox, oy = (4 + vi) * TILE, TILE
		draw_mask(px, ox, oy, 15)
		paint_soil_surface(px, ox, oy, salt=200 + vi * 17, style=style, inner_only=True)
		copy_border(px, 3 * TILE, 3 * TILE, ox, oy)

	for row in (2, 3):
		for col in range(4, 8):
			ox, oy = col * TILE, row * TILE
			draw_mask(px, ox, oy, 0)
			copy_border(px, 0, 0, ox, oy)

	for y in range(im.height):
		for x in range(im.width):
			r, g, b, _a = px[x, y]
			px[x, y] = (r, g, b, 255)
	return im


def put(px, x: int, y: int, rgba: tuple[int, int, int, int]) -> None:
	if 0 <= x < TILE and 0 <= y < TILE:
		px[x, y] = rgba


def make_decor() -> Image.Image:
	"""Transparent overlays only — denser readable tufts/flowers/pebbles/twig."""
	im = Image.new("RGBA", (8 * TILE, TILE), (0, 0, 0, 0))
	cells = [Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0)) for _ in range(8)]

	# 0: single tuft
	p = cells[0].load()
	put(p, 7, 13, (*GRASS[3], 255))
	put(p, 7, 12, (*GRASS[0], 255))
	put(p, 7, 11, (*GRASS[2], 255))
	put(p, 6, 10, (*GRASS[1], 255))
	put(p, 8, 12, (*GRASS[1], 255))

	# 1: double tuft
	p = cells[1].load()
	for x, tip in ((5, 10), (9, 9)):
		put(p, x, 13, (*GRASS[3], 255))
		put(p, x, 12, (*GRASS[0], 255))
		put(p, x, 11, (*GRASS[2], 255))
		put(p, x + (1 if x == 5 else -1), tip, (*GRASS[1], 255))

	# 2: clover / leaf
	p = cells[2].load()
	for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1)):
		put(p, 8 + dx, 11 + dy, (*GRASS[0], 255))
	put(p, 8, 11, (56, 132, 58, 255))

	# 3: white flower accent
	p = cells[3].load()
	put(p, 6, 11, (*GRASS[1], 255))
	put(p, 6, 10, (214, 214, 204, 255))
	put(p, 5, 10, (214, 214, 204, 255))
	put(p, 7, 10, (214, 214, 204, 255))
	put(p, 6, 9, (200, 200, 190, 255))

	# 4: yellow flower
	p = cells[4].load()
	put(p, 9, 12, (*GRASS[0], 255))
	put(p, 9, 11, (198, 168, 48, 255))
	put(p, 8, 11, (198, 168, 48, 255))
	put(p, 10, 11, (188, 158, 42, 255))

	# 5: pebble group
	p = cells[5].load()
	put(p, 6, 12, (*PEBBLE, 255))
	put(p, 7, 12, (*PEBBLE2, 255))
	put(p, 8, 11, (*PEBBLE, 255))
	put(p, 10, 13, (*PEBBLE2, 255))

	# 6: dry twig
	p = cells[6].load()
	put(p, 4, 12, (*ROOT_FIBER, 255))
	put(p, 5, 12, (120, 92, 56, 255))
	put(p, 6, 11, (*ROOT_FIBER, 255))
	put(p, 7, 11, (110, 84, 50, 255))
	put(p, 8, 10, (*ROOT_FIBER, 255))

	# 7: dark grass speck
	p = cells[7].load()
	for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 1)):
		put(p, 8 + dx, 12 + dy, (*GRASS[3], 255))

	for i, cell in enumerate(cells):
		im.paste(cell, (i * TILE, 0), cell)
	return im


def write_zoom_crops(ground: Image.Image) -> None:
	"""Export ×4 crops for docs from atlas (grass / soil / transition)."""
	docs = ROOT / "docs/art_tests"
	docs.mkdir(parents=True, exist_ok=True)

	def zoom_cell(col: int, row: int, name: str) -> None:
		cell = ground.crop((col * TILE, row * TILE, (col + 1) * TILE, (row + 1) * TILE))
		# 3×3 of same cell for grass/soil field feel
		if name in ("grass", "soil"):
			field = Image.new("RGBA", (TILE * 3, TILE * 3))
			for yy in range(3):
				for xx in range(3):
					field.paste(cell, (xx * TILE, yy * TILE))
			field.resize((field.width * 4, field.height * 4), Image.NEAREST).save(docs / f"terrain_visual_{name}_x4.png")
		else:
			cell.resize((TILE * 8, TILE * 8), Image.NEAREST).save(docs / f"terrain_visual_{name}_x4.png")

	zoom_cell(0, 0, "grass")
	zoom_cell(3, 3, "soil")
	# transition: top edge mask (grass N / soil S) ≈ mask with TL=TR=0 BL=BR=1 → bits 8+4=12
	zoom_cell(0, 3, "border")  # mask 12 at col0 row3
	print("wrote visual x4 crops")


def main() -> None:
	OUT.mkdir(parents=True, exist_ok=True)
	global _BASE_GRASS, _BASE_SOIL, EDGE
	_BASE_GRASS = None
	_BASE_SOIL = None
	EDGE = build_edge_profiles()
	ground = make_ground()
	decor = make_decor()
	gp = OUT / "terrain_ground.png"
	dp = OUT / "terrain_decor.png"
	ground.save(gp)
	decor.save(dp)
	write_zoom_crops(ground)
	print("wrote", gp, ground.size)
	print("wrote", dp, decor.size)


if __name__ == "__main__":
	main()
