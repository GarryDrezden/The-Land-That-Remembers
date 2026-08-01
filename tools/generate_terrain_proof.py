#!/usr/bin/env python3
"""Deterministic seamless grass/soil terrain atlas (16×16, margin=0, separation=0).

Outputs:
  assets/art/outdoor/terrain_proof/terrain_ground.png
  assets/art/outdoor/terrain_proof/terrain_decor.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/art/outdoor/terrain_proof"
TILE = 16
SEED = 20260801

GRASS = [(72, 114, 50), (70, 111, 49), (74, 116, 51), (71, 113, 49)]
SOIL = [(116, 82, 52), (110, 78, 49), (122, 86, 55), (108, 76, 48)]
FRINGE = (64, 96, 42)
PEBBLE = (96, 90, 82)
CLUMP = (92, 64, 40)

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


def seamless_value(x: int, y: int, salt: int) -> int:
	"""Low-frequency periodic value noise on a 16×16 torus (no harsh hash grid)."""
	# Sample continuous coords in [0,16)
	fx = (x + 0.5) % TILE
	fy = (y + 0.5) % TILE
	x0 = int(fx) % TILE
	y0 = int(fy) % TILE
	x1 = (x0 + 1) % TILE
	y1 = (y0 + 1) % TILE
	tx = fx - int(fx)
	ty = fy - int(fy)
	# smoothstep
	tx = tx * tx * (3 - 2 * tx)
	ty = ty * ty * (3 - 2 * ty)

	def corner(ix: int, iy: int) -> float:
		return (_h(ix, iy, salt) & 0xFFFF) / 65535.0

	v00 = corner(x0, y0)
	v10 = corner(x1, y0)
	v01 = corner(x0, y1)
	v11 = corner(x1, y1)
	v0 = v00 * (1 - tx) + v10 * tx
	v1 = v01 * (1 - tx) + v11 * tx
	v = v0 * (1 - ty) + v1 * ty
	# second octave, lower weight
	v2 = ((_h((x * 3) % TILE, (y * 5) % TILE, salt + 91) & 0xFFFF) / 65535.0) * 0.25
	return int((v * 0.75 + v2) * 65535) & 0xFFFF


def paint_seamless_surface(px, ox: int, oy: int, is_soil: bool, salt: int, inner_only: bool = False) -> None:
	"""Nearly flat wraparound surface — no per-tile motif (avoids polka-dot grid)."""
	base = SOIL[0] if is_soil else GRASS[0]
	alt = SOIL[1] if is_soil else GRASS[1]
	alt2 = SOIL[2] if is_soil else GRASS[2]
	for y in range(TILE):
		for x in range(TILE):
			if inner_only and (x < 2 or y < 2 or x > 13 or y > 13):
				continue
			# Sparse flecks only; density low so tiled field reads as one cloth
			v = _h(x % TILE, y % TILE, salt)
			c = base
			if (v % 23) == 0:
				c = alt
			elif (v % 41) == 0:
				c = alt2
			if is_soil and 4 <= x <= 11 and 4 <= y <= 11:
				if (v % 97) == 0:
					c = CLUMP
				elif (v % 131) == 0:
					c = PEBBLE
			px[ox + x, oy + y] = (*c, 255)
	if not inner_only:
		# Wrap edges after fill so abutting identical tiles share exact edge pixels
		for y in range(TILE):
			px[ox + TILE - 1, oy + y] = px[ox + 0, oy + y]
		for x in range(TILE):
			px[ox + x, oy + TILE - 1] = px[ox + x, oy + 0]


# Cache base wraparound tiles for edge profiles GG/SS
_BASE_GRASS: list[list[tuple[int, int, int]]] | None = None
_BASE_SOIL: list[list[tuple[int, int, int]]] | None = None


def base_grass() -> list[list[tuple[int, int, int]]]:
	global _BASE_GRASS
	if _BASE_GRASS is None:
		tmp = Image.new("RGBA", (TILE, TILE))
		px = tmp.load()
		paint_seamless_surface(px, 0, 0, False, salt=11)
		_BASE_GRASS = [[px[x, y][:3] for x in range(TILE)] for y in range(TILE)]
	return _BASE_GRASS


def base_soil() -> list[list[tuple[int, int, int]]]:
	global _BASE_SOIL
	if _BASE_SOIL is None:
		tmp = Image.new("RGBA", (TILE, TILE))
		px = tmp.load()
		paint_seamless_surface(px, 0, 0, True, salt=29)
		_BASE_SOIL = [[px[x, y][:3] for x in range(TILE)] for y in range(TILE)]
	return _BASE_SOIL


def build_edge_profiles() -> dict[tuple[bool, bool], list[tuple[int, int, int]]]:
	"""Edge profiles keyed by (start_corner_soil, end_corner_soil).

	GG/SS use the actual wraparound base tile edges so full tiles have no frame.
	GS/SG use a fixed shared transition so neighboring masks seam-match.
	"""
	g = base_grass()
	s = base_soil()
	profiles: dict[tuple[bool, bool], list[tuple[int, int, int]]] = {}

	# Horizontal-style profiles (indexed by x along an edge). Vertical edges reuse
	# the same arrays with the same corner pair — critical for seam contract.
	profiles[(False, False)] = [g[0][x] for x in range(TILE)]  # top row of grass
	profiles[(True, True)] = [s[0][x] for x in range(TILE)]

	gs: list[tuple[int, int, int]] = []
	for i in range(TILE):
		if i <= 5:
			gs.append(g[0][i])
		elif i in (6, 8):
			gs.append(FRINGE)
		elif i == 7:
			gs.append(g[1][i])
		else:
			gs.append(s[0][i])
	profiles[(False, True)] = gs

	sg: list[tuple[int, int, int]] = []
	for i in range(TILE):
		if i <= 6:
			sg.append(s[0][i])
		elif i == 7:
			sg.append(FRINGE)
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
	g = base_grass()
	s = base_soil()
	for y in range(TILE):
		for x in range(TILE):
			f = bilinear_soil(mask, float(x), float(y))
			if f >= 0.5:
				c = s[y][x]
				# Soft fringe only 1px into soil, rare
				if 0.48 <= f < 0.56 and (_h(mask, x, y) & 7) == 0:
					c = FRINGE
			else:
				c = g[y][x]
				if 0.44 < f <= 0.52 and (_h(mask, x, y) & 7) == 1:
					c = grass_c(2)
			px[ox + x, oy + y] = (*c, 255)


def apply_shared_edges(px, ox: int, oy: int, mask: int) -> None:
	tl = corner_soil(mask, TL)
	tr = corner_soil(mask, TR)
	br = corner_soil(mask, BR)
	bl = corner_soil(mask, BL)

	# Horizontal edges use top-row-style profiles
	top = EDGE[(tl, tr)]
	bot = EDGE[(bl, br)]
	# Vertical edges: for GG/SS use left column of base (wraparound);
	# for transitions use the same GS/SG sequence so left/right seams match.
	g = base_grass()
	s = base_soil()

	def vert_profile(a: bool, b: bool) -> list[tuple[int, int, int]]:
		if a == b:
			src = s if a else g
			return [src[y][0] for y in range(TILE)]
		# reuse horizontal GS/SG sequence (identical bytes for same corner pair)
		return EDGE[(a, b)]

	left = vert_profile(tl, bl)
	right = vert_profile(tr, br)

	for i in range(TILE):
		px[ox + i, oy + 0] = (*top[i], 255)
		px[ox + i, oy + 15] = (*bot[i], 255)
		px[ox + 0, oy + i] = (*left[i], 255)
		px[ox + 15, oy + i] = (*right[i], 255)

	# For full grass/soil, also lock opposite wrap edges from base so tile self-tiles
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
		paint_seamless_surface(px, ox, oy, False, salt=11)
	elif mask == 15:
		paint_seamless_surface(px, ox, oy, True, salt=29)
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

	# Grass variants: unique inner, identical border to mask 0
	for vi in range(4):
		ox, oy = (4 + vi) * TILE, 0
		draw_mask(px, ox, oy, 0)
		paint_seamless_surface(px, ox, oy, False, salt=100 + vi * 13, inner_only=True)
		copy_border(px, 0, 0, ox, oy)

	# Soil variants
	for vi in range(4):
		ox, oy = (4 + vi) * TILE, TILE
		draw_mask(px, ox, oy, 15)
		paint_seamless_surface(px, ox, oy, True, salt=200 + vi * 17, inner_only=True)
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
	im = Image.new("RGBA", (8 * TILE, TILE), (0, 0, 0, 0))
	cells = [Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0)) for _ in range(8)]

	p = cells[0].load()
	put(p, 7, 12, (*GRASS[2], 255))
	put(p, 7, 11, (*GRASS[0], 255))
	put(p, 7, 10, (*GRASS[1], 255))
	put(p, 6, 9, (*GRASS[2], 255))

	p = cells[1].load()
	put(p, 5, 12, (*GRASS[1], 255))
	put(p, 5, 11, (*GRASS[0], 255))
	put(p, 5, 10, (*GRASS[2], 255))
	put(p, 9, 12, (*GRASS[0], 255))
	put(p, 9, 11, (*GRASS[2], 255))
	put(p, 10, 10, (*GRASS[1], 255))

	p = cells[2].load()
	for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
		put(p, 8 + dx, 10 + dy, (*GRASS[0], 255))
	put(p, 8, 10, (58, 140, 62, 255))

	p = cells[3].load()
	put(p, 5, 9, (*GRASS[1], 255))
	put(p, 5, 8, (210, 210, 200, 255))
	put(p, 10, 11, (*GRASS[0], 255))
	put(p, 10, 10, (205, 205, 195, 255))

	p = cells[4].load()
	put(p, 7, 10, (*GRASS[2], 255))
	put(p, 7, 9, (200, 170, 50, 255))
	put(p, 11, 12, (*GRASS[1], 255))
	put(p, 11, 11, (190, 160, 45, 255))

	p = cells[5].load()
	put(p, 6, 11, (*PEBBLE, 255))
	put(p, 7, 11, (100, 96, 90, 255))
	put(p, 10, 12, (92, 88, 82, 255))

	p = cells[6].load()
	put(p, 4, 11, (120, 92, 58, 255))
	put(p, 5, 11, (110, 84, 52, 255))
	put(p, 6, 10, (120, 92, 58, 255))
	put(p, 7, 10, (100, 76, 48, 255))

	p = cells[7].load()
	for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0)):
		put(p, 8 + dx, 11 + dy, (*FRINGE, 255))

	for i, cell in enumerate(cells):
		im.paste(cell, (i * TILE, 0), cell)
	return im


def main() -> None:
	OUT.mkdir(parents=True, exist_ok=True)
	# Reset caches if re-imported
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
	print("wrote", gp, ground.size)
	print("wrote", dp, decor.size)


if __name__ == "__main__":
	main()
