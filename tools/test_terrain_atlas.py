#!/usr/bin/env python3
"""Validate seamless terrain_proof atlases. Exit nonzero on failure."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GROUND = ROOT / "assets/art/outdoor/terrain_proof/terrain_ground.png"
DECOR = ROOT / "assets/art/outdoor/terrain_proof/terrain_decor.png"
TILE = 16


class Failed(Exception):
	pass


def check(cond: bool, msg: str) -> None:
	if not cond:
		raise Failed(msg)


def cell(im: Image.Image, col: int, row: int) -> Image.Image:
	return im.crop((col * TILE, row * TILE, (col + 1) * TILE, (row + 1) * TILE))


def border_pixels(tile: Image.Image) -> tuple[list, list, list, list]:
	px = tile.load()
	top = [px[x, 0] for x in range(TILE)]
	bot = [px[x, TILE - 1] for x in range(TILE)]
	left = [px[0, y] for y in range(TILE)]
	right = [px[TILE - 1, y] for y in range(TILE)]
	return top, bot, left, right


def main() -> int:
	errors: list[str] = []

	def fail(msg: str) -> None:
		errors.append(msg)
		print("FAIL:", msg)

	try:
		check(GROUND.exists(), f"missing {GROUND}")
		check(DECOR.exists(), f"missing {DECOR}")
		ground = Image.open(GROUND).convert("RGBA")
		decor = Image.open(DECOR).convert("RGBA")

		check(ground.width % TILE == 0, f"ground width {ground.width} not multiple of 16")
		check(ground.height % TILE == 0, f"ground height {ground.height} not multiple of 16")
		check(decor.width % TILE == 0, f"decor width {decor.width} not multiple of 16")
		check(decor.height % TILE == 0, f"decor height {decor.height} not multiple of 16")

		# No gaps in atlas: continuous packed grid (implicit by size / 16)
		cols = ground.width // TILE
		rows = ground.height // TILE
		check(cols >= 8 and rows >= 4, f"ground atlas too small {cols}x{rows}")

		# Ground fully opaque
		gpx = ground.load()
		for y in range(ground.height):
			for x in range(ground.width):
				_r, _g, _b, a = gpx[x, y]
				if a < 255:
					fail(f"ground transparent at {x},{y} a={a}")
					raise Failed("abort opaque scan")

		# Decor has real alpha
		dpx = decor.load()
		trans = sum(1 for y in range(decor.height) for x in range(decor.width) if dpx[x, y][3] < 8)
		opaque = sum(1 for y in range(decor.height) for x in range(decor.width) if dpx[x, y][3] > 200)
		check(trans > 0, "decor has no transparent pixels")
		check(opaque > 0, "decor has no opaque pixels")

		# No near-white seam pixels on ground
		for y in range(ground.height):
			for x in range(ground.width):
				r, g, b, _a = gpx[x, y]
				if r > 240 and g > 240 and b > 240:
					fail(f"near-white ground pixel at {x},{y}")

		# 16 masks present (first 4×4)
		for mask in range(16):
			col, row = mask % 4, mask // 4
			t = cell(ground, col, row)
			check(t.size == (TILE, TILE), f"mask {mask} bad size")

		# Grass variants share borders with mask 0
		base = cell(ground, 0, 0)
		bt, bb, bl, br = border_pixels(base)
		for vi in range(4):
			v = cell(ground, 4 + vi, 0)
			vt, vb, vl, vr = border_pixels(v)
			check(vt == bt and vb == bb and vl == bl and vr == br, f"grass variant {vi} border mismatch")

		# Full grass tile must wrap: right edge == left edge, bottom == top
		g0 = cell(ground, 0, 0)
		gt, gb, gl, gr = border_pixels(g0)
		check(gl == gr, "grass base left/right edges must match for wraparound")
		check(gt == gb, "grass base top/bottom edges must match for wraparound")
		s15 = cell(ground, 3, 3)
		st, sb, sl, sr = border_pixels(s15)
		check(sl == sr, "soil base left/right edges must match for wraparound")
		check(st == sb, "soil base top/bottom edges must match for wraparound")

		# Soil variants share borders with mask 15
		for vi in range(4):
			v = cell(ground, 4 + vi, 1)
			vt, vb, vl, vr = border_pixels(v)
			check(vt == st and vb == sb and vl == sl and vr == sr, f"soil variant {vi} border mismatch")

		# Seam contract: compatible horizontal neighbors have matching vertical edges
		# For masks A and B side by side: A.TR==B.TL and A.BR==B.BL ⇒ A.right == B.left
		def corners(m: int) -> tuple[bool, bool, bool, bool]:
			return bool(m & 1), bool(m & 2), bool(m & 4), bool(m & 8)  # TL TR BR BL

		for a in range(16):
			for b in range(16):
				atl, atr, abr, abl = corners(a)
				btl, btr, bbr, bbl = corners(b)
				# horizontal neighbor
				if atr == btl and abr == bbl:
					ta = cell(ground, a % 4, a // 4)
					tb = cell(ground, b % 4, b // 4)
					_at, _ab, _al, ar = border_pixels(ta)
					_bt, _bb, bl2, _br = border_pixels(tb)
					if ar != bl2:
						fail(f"H-seam mismatch masks {a}->{b}")
				# vertical neighbor
				if abl == btl and abr == btr:
					ta = cell(ground, a % 4, a // 4)
					tb = cell(ground, b % 4, b // 4)
					_at, abot, _al, _ar = border_pixels(ta)
					btop, _bb, _bl, _br = border_pixels(tb)
					if abot != btop:
						fail(f"V-seam mismatch masks {a}->{b}")

		if errors:
			print(f"{len(errors)} failure(s)")
			return 1
		print("OK: terrain atlas checks passed")
		return 0
	except Failed as e:
		print("FAIL:", e)
		return 1


if __name__ == "__main__":
	sys.exit(main())
