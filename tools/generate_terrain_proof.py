#!/usr/bin/env python3
"""Deterministic seamless grass/soil terrain atlas — MACRO variation pass.

Architecture preserved:
- Match Corners masks 0..15 at (mask%4, mask/4)
- Shared edge profiles / wraparound borders (seam contract)
- Variants keep identical border pixels; interiors may differ

Atlas layout 12×4 (192×64):
  cols 0–3, rows 0–3 : primary masks 0..15
  cols 4–7, row 0    : grass macro (light, dark, sparse, dense)
  cols 4–7, row 1    : soil macro (base-style, dark, clumps, pebbles)
  cols 8–11          : edge/corner visual variants (same terrain bits + same borders)
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/art/outdoor/terrain_proof"
DOCS = ROOT / "docs/art_tests"
TILE = 16
SEED = 20260801
ATLAS_COLS = 12
ATLAS_ROWS = 4

# Calm grass palette — mid green + muted dark + warm yellow-green accents only
G_BASE = (68, 108, 46)
G_DARK = (54, 88, 36)
G_MID = (62, 100, 42)
G_WARM = (82, 118, 48)  # yellow-green fleck only
G_LIGHT = (78, 122, 54)
G_DEEP = (46, 76, 32)

# Warm packed loam — not orange sand
S_BASE = (108, 74, 46)
S_DARK = (86, 56, 34)
S_MID = (98, 66, 40)
S_LIFT = (116, 82, 52)
S_CLUMP = (74, 48, 30)
S_PEBBLE = (96, 90, 82)
S_PEBBLE2 = (84, 80, 74)
S_ROOT = (120, 92, 56)

FRINGE = (52, 86, 34)
FRINGE2 = (60, 96, 40)
SOIL_EDGE = (78, 50, 30)

TL, TR, BR, BL = 1, 2, 4, 8


def _h(*parts: int) -> int:
	n = SEED
	for p in parts:
		n = (n ^ (p * 374761393)) & 0xFFFFFFFF
		n = (n * 1664525 + 1013904223) & 0xFFFFFFFF
	return n


def _put(px, ox: int, oy: int, x: int, y: int, c: tuple[int, int, int]) -> None:
	if 0 <= x < TILE and 0 <= y < TILE:
		px[ox + x, oy + y] = (*c, 255)


def _fill(px, ox: int, oy: int, c: tuple[int, int, int], pad: int = 0) -> None:
	for y in range(pad, TILE - pad):
		for x in range(pad, TILE - pad):
			px[ox + x, oy + y] = (*c, 255)


def _soft_flecks(px, ox: int, oy: int, salt: int, colors: list, chance_mod: int, pad: int = 1) -> None:
	"""Sparse intentional flecks — not per-pixel noise."""
	for y in range(pad, TILE - pad):
		for x in range(pad, TILE - pad):
			v = _h(x, y, salt)
			if (v % chance_mod) == 0:
				_put(px, ox, oy, x, y, colors[v % len(colors)])


def paint_grass_base(px, ox: int, oy: int, salt: int = 11) -> None:
	"""Calm seamless grass — soft texture, minimal repeating motif."""
	_fill(px, ox, oy, G_BASE)
	# Soft low-freq shade blobs (large, few)
	for p in range(2):
		cx = 4 + (_h(salt, 1 + p) % 8)
		cy = 4 + (_h(salt, 2 + p) % 8)
		for dy in range(-2, 3):
			for dx in range(-2, 3):
				if abs(dx) + abs(dy) <= 3:
					_put(px, ox, oy, cx + dx, cy + dy, G_MID if (dx + dy) % 2 == 0 else G_DARK)
	_soft_flecks(px, ox, oy, salt, [G_DARK, G_WARM], chance_mod=23, pad=1)
	# Lock wraparound borders
	for y in range(TILE):
		px[ox + TILE - 1, oy + y] = px[ox + 0, oy + y]
	for x in range(TILE):
		px[ox + x, oy + TILE - 1] = px[ox + x, oy + 0]


def paint_grass_macro(px, ox: int, oy: int, kind: str, salt: int) -> None:
	"""Macro interiors only (caller copies borders from base). kind: light|dark|sparse|dense."""
	pad = 2
	if kind == "light":
		_fill(px, ox, oy, G_LIGHT, pad=pad)
		# Soft pale patches
		for p in range(3):
			cx = 3 + (_h(salt, p) % 10)
			cy = 3 + (_h(salt, 10 + p) % 10)
			for dy in range(-1, 2):
				for dx in range(-1, 2):
					_put(px, ox, oy, cx + dx, cy + dy, G_WARM if abs(dx) + abs(dy) < 2 else G_LIGHT)
		_soft_flecks(px, ox, oy, salt, [G_BASE, G_WARM], 19, pad)
	elif kind == "dark":
		_fill(px, ox, oy, G_DARK, pad=pad)
		for p in range(3):
			cx = 3 + (_h(salt, p) % 10)
			cy = 3 + (_h(salt, 20 + p) % 10)
			for dy in range(-2, 3):
				for dx in range(-2, 3):
					if abs(dx) + abs(dy) <= 2:
						_put(px, ox, oy, cx + dx, cy + dy, G_DEEP)
		_soft_flecks(px, ox, oy, salt, [G_MID, G_BASE], 17, pad)
	elif kind == "sparse":
		_fill(px, ox, oy, G_BASE, pad=pad)
		# Open feel: few dark dots only
		for p in range(4):
			_put(px, ox, oy, 4 + (_h(salt, p) % 8), 4 + (_h(salt, 30 + p) % 8), G_DARK)
		# One short blade
		bx, by = 7, 9
		_put(px, ox, oy, bx, by, G_WARM)
		_put(px, ox, oy, bx, by - 1, G_LIGHT)
	else:  # dense
		_fill(px, ox, oy, G_MID, pad=pad)
		for p in range(8):
			cx = 3 + (_h(salt, 40 + p) % 10)
			cy = 3 + (_h(salt, 50 + p) % 10)
			_put(px, ox, oy, cx, cy, G_DARK)
			_put(px, ox, oy, cx, cy - 1, G_WARM if p % 2 == 0 else G_LIGHT)
			_put(px, ox, oy, cx + 1, cy, G_DEEP if p % 3 == 0 else G_DARK)
		for p in range(3):
			cx = 4 + (_h(salt, 60 + p) % 8)
			cy = 5 + (_h(salt, 70 + p) % 6)
			for dy in range(0, 3):
				for dx in range(0, 3):
					_put(px, ox, oy, cx + dx, cy + dy, G_DARK)


def paint_soil_base(px, ox: int, oy: int, salt: int = 29) -> None:
	_fill(px, ox, oy, S_BASE)
	for p in range(2):
		cx = 4 + (_h(salt, 1 + p) % 8)
		cy = 4 + (_h(salt, 2 + p) % 8)
		for dy in range(-2, 3):
			for dx in range(-2, 3):
				if abs(dx) + abs(dy) <= 2:
					_put(px, ox, oy, cx + dx, cy + dy, S_MID)
	_soft_flecks(px, ox, oy, salt, [S_DARK, S_LIFT], 29, pad=1)
	for y in range(TILE):
		px[ox + TILE - 1, oy + y] = px[ox + 0, oy + y]
	for x in range(TILE):
		px[ox + x, oy + TILE - 1] = px[ox + x, oy + 0]


def paint_soil_macro(px, ox: int, oy: int, kind: str, salt: int) -> None:
	"""kind: normal|dark|clumps|pebbles — interiors only."""
	pad = 2
	if kind == "normal":
		_fill(px, ox, oy, S_BASE, pad=pad)
		_soft_flecks(px, ox, oy, salt, [S_MID, S_DARK], 21, pad)
		for p in range(2):
			cx = 4 + (_h(salt, p) % 8)
			cy = 4 + (_h(salt, 5 + p) % 8)
			_put(px, ox, oy, cx, cy, S_DARK)
			_put(px, ox, oy, cx + 1, cy, S_MID)
	elif kind == "dark":
		_fill(px, ox, oy, S_DARK, pad=pad)
		for p in range(3):
			cx = 3 + (_h(salt, p) % 10)
			cy = 3 + (_h(salt, 10 + p) % 10)
			for dy in range(-2, 3):
				for dx in range(-2, 3):
					if abs(dx) + abs(dy) <= 2:
						_put(px, ox, oy, cx + dx, cy + dy, S_CLUMP)
		_soft_flecks(px, ox, oy, salt, [S_MID, S_BASE], 19, pad)
	elif kind == "clumps":
		_fill(px, ox, oy, S_BASE, pad=pad)
		spots = [(5, 5), (10, 7), (7, 11), (11, 10), (4, 9)]
		for i, (cx, cy) in enumerate(spots):
			_put(px, ox, oy, cx, cy, S_CLUMP)
			_put(px, ox, oy, cx + 1, cy, S_CLUMP)
			_put(px, ox, oy, cx, cy + 1, S_DARK)
			if i % 2 == 0:
				_put(px, ox, oy, cx + 1, cy + 1, S_MID)
	else:  # pebbles + roots
		_fill(px, ox, oy, S_MID, pad=pad)
		for cx, cy in ((5, 6), (9, 5), (7, 10), (11, 9), (6, 12)):
			_put(px, ox, oy, cx, cy, S_PEBBLE if (cx + cy) % 2 == 0 else S_PEBBLE2)
		# dry root fiber
		_put(px, ox, oy, 4, 8, S_ROOT)
		_put(px, ox, oy, 5, 8, S_ROOT)
		_put(px, ox, oy, 6, 7, S_ROOT)
		_put(px, ox, oy, 8, 11, S_ROOT)
		_put(px, ox, oy, 9, 10, (110, 84, 50))


_BASE_GRASS: list[list[tuple[int, int, int]]] | None = None
_BASE_SOIL: list[list[tuple[int, int, int]]] | None = None


def base_grass() -> list[list[tuple[int, int, int]]]:
	global _BASE_GRASS
	if _BASE_GRASS is None:
		tmp = Image.new("RGBA", (TILE, TILE))
		px = tmp.load()
		paint_grass_base(px, 0, 0, 11)
		_BASE_GRASS = [[px[x, y][:3] for x in range(TILE)] for y in range(TILE)]
	return _BASE_GRASS


def base_soil() -> list[list[tuple[int, int, int]]]:
	global _BASE_SOIL
	if _BASE_SOIL is None:
		tmp = Image.new("RGBA", (TILE, TILE))
		px = tmp.load()
		paint_soil_base(px, 0, 0, 29)
		_BASE_SOIL = [[px[x, y][:3] for x in range(TILE)] for y in range(TILE)]
	return _BASE_SOIL


def build_edge_profiles() -> dict[tuple[bool, bool], list[tuple[int, int, int]]]:
	g = base_grass()
	s = base_soil()
	profiles: dict[tuple[bool, bool], list[tuple[int, int, int]]] = {}
	profiles[(False, False)] = [g[0][x] for x in range(TILE)]
	profiles[(True, True)] = [s[0][x] for x in range(TILE)]

	# Fixed connection slots — richer fringe but locked indices
	gs: list[tuple[int, int, int]] = []
	for i in range(TILE):
		if i <= 4:
			gs.append(g[0][i])
		elif i == 5:
			gs.append(FRINGE2)
		elif i in (6, 7):
			gs.append(FRINGE)
		elif i == 8:
			gs.append(SOIL_EDGE)
		else:
			gs.append(s[0][i])
	profiles[(False, True)] = gs

	sg: list[tuple[int, int, int]] = []
	for i in range(TILE):
		if i <= 5:
			sg.append(s[0][i])
		elif i == 6:
			sg.append(SOIL_EDGE)
		elif i == 7:
			sg.append(SOIL_EDGE)
		elif i == 8:
			sg.append(FRINGE)
		elif i == 9:
			sg.append(FRINGE2)
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


def paint_transition_interior(px, ox: int, oy: int, mask: int, variant: int = 0) -> None:
	"""Interior fringe variation by variant id; borders applied separately."""
	g = base_grass()
	s = base_soil()
	# Shift fringe thresholds / blade density by variant
	lo = 0.36 + (variant % 3) * 0.02
	hi = 0.56 + (variant % 3) * 0.02
	blade_mod = 3 + (variant % 4)
	gap_mod = 11 + variant * 2
	for y in range(TILE):
		for x in range(TILE):
			f = bilinear_soil(mask, float(x), float(y))
			h = _h(mask, x, y, variant)
			if f >= hi:
				c = s[y][x]
				if hi <= f < hi + 0.12:
					c = SOIL_EDGE if (h & 3) != 0 else s[y][x]
					if variant >= 1 and (h % 5) == 0:
						c = S_DARK
			elif f <= lo:
				c = g[y][x]
			else:
				band = (f - lo) / max(0.01, hi - lo)
				# Rare fringe gap
				if (h % gap_mod) == 0 and 0.4 < band < 0.7:
					c = SOIL_EDGE if band > 0.55 else s[y][x]
				elif band < 0.28:
					c = g[y][x]
					if (h % blade_mod) == 0:
						c = G_WARM
				elif band < 0.50:
					# blade length variation
					c = FRINGE2 if (h & 1) == 0 else FRINGE
					if (h % (blade_mod + 1)) == 0:
						c = G_LIGHT
				elif band < 0.72:
					c = FRINGE
					if (h % 5) == variant % 5:
						c = G_WARM  # 1–2px protrusion feel
				else:
					c = SOIL_EDGE if (h & 1) == 0 else s[y][x]
					if (h % 7) == 0:
						c = FRINGE
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


def draw_mask(px, ox: int, oy: int, mask: int, variant: int = 0) -> None:
	if mask == 0:
		paint_grass_base(px, ox, oy, 11)
	elif mask == 15:
		paint_soil_base(px, ox, oy, 29)
	else:
		paint_transition_interior(px, ox, oy, mask, variant=variant)
	apply_shared_edges(px, ox, oy, mask)


def copy_border(px, sox: int, soy: int, dox: int, doy: int) -> None:
	for i in range(TILE):
		px[dox + i, doy + 0] = px[sox + i, soy + 0]
		px[dox + i, doy + 15] = px[sox + i, soy + 15]
		px[dox + 0, doy + i] = px[sox + 0, soy + i]
		px[dox + 15, doy + i] = px[sox + 15, soy + i]


def copy_full(px, sox: int, soy: int, dox: int, doy: int) -> None:
	for y in range(TILE):
		for x in range(TILE):
			px[dox + x, doy + y] = px[sox + x, soy + y]


def make_ground() -> Image.Image:
	im = Image.new("RGBA", (ATLAS_COLS * TILE, ATLAS_ROWS * TILE), (0, 0, 0, 255))
	px = im.load()

	# Primary 16 masks
	for mask in range(16):
		draw_mask(px, (mask % 4) * TILE, (mask // 4) * TILE, mask, variant=0)

	# Grass macro variants (cols 4–7, row 0) — borders from mask 0
	kinds_g = ("light", "dark", "sparse", "dense")
	for vi, kind in enumerate(kinds_g):
		ox, oy = (4 + vi) * TILE, 0
		draw_mask(px, ox, oy, 0)
		paint_grass_macro(px, ox, oy, kind, salt=100 + vi * 17)
		copy_border(px, 0, 0, ox, oy)

	# Soil macro variants (cols 4–7, row 1)
	kinds_s = ("normal", "dark", "clumps", "pebbles")
	for vi, kind in enumerate(kinds_s):
		ox, oy = (4 + vi) * TILE, TILE
		draw_mask(px, ox, oy, 15)
		paint_soil_macro(px, ox, oy, kind, salt=200 + vi * 19)
		copy_border(px, 3 * TILE, 3 * TILE, ox, oy)

	# Edge visual variants — same mask bits, same borders, different interiors
	# Straight edges: 12, 3, 6, 9 — 3 variants each at cols 8–10
	straight = [
		(12, 0),  # row 0 of variant strip uses y offsets below
		(3, 1),
		(6, 2),
		(9, 3),
	]
	for mask, row in straight:
		primary = ((mask % 4) * TILE, (mask // 4) * TILE)
		for vi in range(3):
			ox, oy = (8 + vi) * TILE, row * TILE
			draw_mask(px, ox, oy, mask, variant=vi + 1)
			copy_border(px, primary[0], primary[1], ox, oy)

	# Corner variants: masks 1,2,4,8 — 2 variants each in remaining cells of row via col 11 + reuse
	# Place at (11,0)=mask1 v1, (11,1)=mask2 v1, (11,2)=mask4 v1, (11,3)=mask8 v1
	# Second corner variants overwrite? Use primary redraw at unused — also paint variant 2 into
	# the fourth straight slot isn't available. Put second corner variants by replacing
	# one straight's 3rd slot? Better: put corner v1 at col11, and corner v2 interiors into
	# cells that were filler — draw into (8-10 already used). Expand: use col11 only for corners v1.
	# For second corner variant, re-use probability on primary + one alt: draw alts into
	# positions that tests don't require as grass/soil.
	corners = [(1, 0), (2, 1), (4, 2), (8, 3)]
	for mask, row in corners:
		primary = ((mask % 4) * TILE, (mask // 4) * TILE)
		ox, oy = 11 * TILE, row * TILE
		draw_mask(px, ox, oy, mask, variant=1)
		copy_border(px, primary[0], primary[1], ox, oy)

	# Second corner variants: paint into cols 4-7 rows 2-3 (were unused copies)
	corners2 = [(1, 4, 2), (2, 5, 2), (4, 6, 2), (8, 7, 2), (1, 4, 3), (2, 5, 3), (4, 6, 3), (8, 7, 3)]
	# Actually rows 2-3 cols 4-7 = 8 cells: two variants for each of 4 corners
	corner_slots = [
		(1, 4, 2, 1), (1, 5, 2, 2),
		(2, 6, 2, 1), (2, 7, 2, 2),
		(4, 4, 3, 1), (4, 5, 3, 2),
		(8, 6, 3, 1), (8, 7, 3, 2),
	]
	for mask, col, row, var in corner_slots:
		primary = ((mask % 4) * TILE, (mask // 4) * TILE)
		ox, oy = col * TILE, row * TILE
		draw_mask(px, ox, oy, mask, variant=var)
		copy_border(px, primary[0], primary[1], ox, oy)

	# Opaque
	for y in range(im.height):
		for x in range(im.width):
			r, g, b, _a = px[x, y]
			px[x, y] = (r, g, b, 255)
	return im


def put(px, x: int, y: int, rgba: tuple[int, int, int, int]) -> None:
	if 0 <= x < TILE and 0 <= y < TILE:
		px[x, y] = rgba


def make_decor() -> Image.Image:
	"""Readable overlays at game scale — tufts/flowers larger than 1px."""
	n = 16
	im = Image.new("RGBA", (n * TILE, TILE), (0, 0, 0, 0))
	cells = [Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0)) for _ in range(n)]

	def blade_tuft(p, x0: int, h: int = 5) -> None:
		for i in range(h):
			put(p, x0, 14 - i, (*((G_DEEP, G_DARK, G_MID, G_WARM, G_LIGHT)[min(i, 4)]), 255))
		put(p, x0 - 1, 12, (*G_DARK, 255))
		put(p, x0 + 1, 13, (*G_MID, 255))

	# 0–2: three distinct grass tufts (tall enough to read)
	p = cells[0].load()
	blade_tuft(p, 8, 6)

	p = cells[1].load()
	blade_tuft(p, 6, 5)
	blade_tuft(p, 10, 4)

	p = cells[2].load()
	blade_tuft(p, 5, 5)
	blade_tuft(p, 8, 7)
	blade_tuft(p, 11, 4)

	# 3: clover
	p = cells[3].load()
	for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)):
		put(p, 8 + dx, 11 + dy, (*G_MID, 255))
	put(p, 8, 11, (52, 128, 56, 255))
	put(p, 7, 10, (52, 128, 56, 255))
	put(p, 9, 10, (48, 120, 52, 255))

	# 4–5: white flowers (readable cluster)
	p = cells[4].load()
	put(p, 7, 13, (*G_DARK, 255))
	for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1), (0, 1)):
		put(p, 7 + dx, 11 + dy, (220, 220, 210, 255))
	put(p, 7, 11, (200, 200, 120, 255))

	p = cells[5].load()
	for cx in (5, 10):
		put(p, cx, 13, (*G_DARK, 255))
		for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1)):
			put(p, cx + dx, 11 + dy, (216, 216, 206, 255))

	# 6: yellow flowers
	p = cells[6].load()
	put(p, 8, 13, (*G_MID, 255))
	for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1), (1, -1)):
		put(p, 8 + dx, 11 + dy, (200, 168, 44, 255))
	put(p, 8, 11, (188, 140, 36, 255))

	# 7: dark low-veg patch (readable blob)
	p = cells[7].load()
	for dy in range(0, 4):
		for dx in range(0, 5):
			put(p, 6 + dx, 10 + dy, (*G_DEEP, 255))
	put(p, 8, 9, (*G_DARK, 255))
	put(p, 9, 10, (*G_MID, 255))

	# 8: pebble group (soil decor)
	p = cells[8].load()
	put(p, 6, 12, (*S_PEBBLE, 255))
	put(p, 7, 12, (*S_PEBBLE2, 255))
	put(p, 8, 11, (*S_PEBBLE, 255))
	put(p, 9, 13, (*S_PEBBLE2, 255))
	put(p, 7, 11, (78, 74, 68, 255))

	# 9–10: earth clumps
	p = cells[9].load()
	for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (2, 0)):
		put(p, 6 + dx, 11 + dy, (*S_CLUMP, 255))
	put(p, 7, 10, (*S_DARK, 255))

	p = cells[10].load()
	for dx, dy in ((0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
		put(p, 9 + dx, 12 + dy, (*S_CLUMP, 255))

	# 11: dry root
	p = cells[11].load()
	put(p, 4, 12, (*S_ROOT, 255))
	put(p, 5, 12, (112, 86, 52, 255))
	put(p, 6, 11, (*S_ROOT, 255))
	put(p, 7, 11, (108, 82, 48, 255))
	put(p, 8, 10, (*S_ROOT, 255))
	put(p, 9, 10, (100, 76, 46, 255))

	# 12: dark soil patch
	p = cells[12].load()
	for dy in range(0, 3):
		for dx in range(0, 4):
			put(p, 6 + dx, 11 + dy, (*S_DARK, 255))
	put(p, 7, 10, (*S_CLUMP, 255))

	# 13: sprout
	p = cells[13].load()
	put(p, 8, 13, (*S_DARK, 255))
	put(p, 8, 12, (*G_MID, 255))
	put(p, 8, 11, (*G_WARM, 255))
	put(p, 7, 11, (*G_LIGHT, 255))
	put(p, 9, 12, (*G_DARK, 255))

	# 14–15: extra blade / tiny flower
	p = cells[14].load()
	blade_tuft(p, 8, 4)

	p = cells[15].load()
	put(p, 8, 12, (*G_DARK, 255))
	for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, -1)):
		put(p, 8 + dx, 10 + dy, (210, 210, 200, 255))

	for i, cell in enumerate(cells):
		im.paste(cell, (i * TILE, 0), cell)
	return im


def write_zoom_crops(ground: Image.Image) -> None:
	DOCS.mkdir(parents=True, exist_ok=True)

	def zoom_field(col: int, row: int, name: str, variants: list[tuple[int, int]] | None = None) -> None:
		field = Image.new("RGBA", (TILE * 3, TILE * 3))
		if variants is None:
			cell = ground.crop((col * TILE, row * TILE, (col + 1) * TILE, (row + 1) * TILE))
			for yy in range(3):
				for xx in range(3):
					field.paste(cell, (xx * TILE, yy * TILE))
		else:
			# show mix of macros
			idx = 0
			for yy in range(3):
				for xx in range(3):
					c, r = variants[idx % len(variants)]
					cell = ground.crop((c * TILE, r * TILE, (c + 1) * TILE, (r + 1) * TILE))
					field.paste(cell, (xx * TILE, yy * TILE))
					idx += 1
		field.resize((field.width * 4, field.height * 4), Image.NEAREST).save(DOCS / f"terrain_macro_{name}_x4.png")

	zoom_field(0, 0, "grass", [(0, 0), (4, 0), (5, 0), (0, 0), (6, 0), (7, 0), (4, 0), (0, 0), (5, 0)])
	zoom_field(3, 3, "soil", [(3, 3), (4, 1), (5, 1), (6, 1), (3, 3), (7, 1), (4, 1), (5, 1), (3, 3)])
	# edge: primary + variants of mask 12
	edge = Image.new("RGBA", (TILE * 3, TILE))
	for i, (c, r) in enumerate([(0, 3), (8, 0), (9, 0)]):
		cell = ground.crop((c * TILE, r * TILE, (c + 1) * TILE, (r + 1) * TILE))
		edge.paste(cell, (i * TILE, 0))
	edge.resize((edge.width * 6, edge.height * 6), Image.NEAREST).save(DOCS / "terrain_macro_edge_x4.png")
	print("wrote macro x4 crops")


def write_comparison(before_scene: Path, after_scene: Path, out: Path) -> None:
	if not before_scene.exists() or not after_scene.exists():
		print("skip comparison (missing scene shots)")
		return
	a = Image.open(before_scene).convert("RGBA")
	b = Image.open(after_scene).convert("RGBA")
	h = max(a.height, b.height)
	w = a.width + b.width + 8
	canvas = Image.new("RGBA", (w, h), (20, 20, 24, 255))
	canvas.paste(a, (0, 0))
	canvas.paste(b, (a.width + 8, 0))
	draw = ImageDraw.Draw(canvas)
	draw.rectangle([0, 0, a.width, 22], fill=(0, 0, 0, 180))
	draw.rectangle([a.width + 8, 0, w, 22], fill=(0, 0, 0, 180))
	draw.text((8, 4), "BEFORE", fill=(255, 255, 255, 255))
	draw.text((a.width + 16, 4), "AFTER (macro)", fill=(255, 255, 255, 255))
	canvas.save(out)
	print("wrote", out)


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
