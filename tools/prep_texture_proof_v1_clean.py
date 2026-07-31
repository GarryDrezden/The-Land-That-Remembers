#!/usr/bin/env python3
"""Re-prep texture_proof_v1 assets for clean integration.

- Binary alpha (no partial transparency)
- Tight content, feet on bottom row of fixed canvas
- NEAREST scale into locked boxes
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/art/outdoor/generated_test/processed"
OUT = ROOT / "assets/art/outdoor/texture_proof_v1"


def binary_alpha(im: Image.Image, thr: int = 32) -> Image.Image:
	im = im.convert("RGBA")
	px = im.load()
	w, h = im.size
	for y in range(h):
		for x in range(w):
			r, g, b, a = px[x, y]
			if a < thr:
				px[x, y] = (0, 0, 0, 0)
			else:
				px[x, y] = (r, g, b, 255)
	return im


def trim(im: Image.Image) -> Image.Image:
	im = binary_alpha(im)
	bbox = im.getbbox()
	return im.crop(bbox) if bbox else im


def trim_dirt(im: Image.Image, max_frac: float = 0.18) -> Image.Image:
	im = im.convert("RGBA")
	w, h = im.size
	px = im.load()
	cut = 0
	limit = int(h * max_frac)
	for y in range(h - 1, max(h // 2, h - limit) - 1, -1):
		dirt = opaque = 0
		for x in range(w):
			r, g, b, a = px[x, y]
			if a < 30:
				continue
			opaque += 1
			if (r > 70 and r > b + 15 and g < r + 25) or (g > r + 10 and g > b and g > 70):
				dirt += 1
		if opaque and dirt / opaque > 0.55:
			cut += 1
		elif opaque == 0:
			cut += 1
		else:
			break
	if cut > 2:
		return im.crop((0, 0, w, h - cut + 1))
	return im


def to_canvas(im: Image.Image, tw: int, th: int, prefer_height: bool = False) -> Image.Image:
	im = trim(im)
	if im.width < 1 or im.height < 1:
		return Image.new("RGBA", (tw, th), (0, 0, 0, 0))
	if prefer_height:
		scale = th / im.height
		if im.width * scale > tw:
			scale = tw / im.width
	else:
		scale = min(tw / im.width, th / im.height)
	# never upscale > 1.0 for cleanliness
	scale = min(scale, 1.0)
	nw = max(1, int(round(im.width * scale)))
	nh = max(1, int(round(im.height * scale)))
	resized = binary_alpha(im.resize((nw, nh), Image.NEAREST))
	canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
	ox = (tw - nw) // 2
	oy = th - nh  # feet on bottom
	canvas.paste(resized, (ox, oy), resized)
	return binary_alpha(canvas)


def save(im: Image.Image, path: Path) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	binary_alpha(im).save(path)
	print(path.name, im.size, "opaque", sum(1 for p in im.getdata() if p[3] > 200))


def main() -> None:
	OUT.mkdir(parents=True, exist_ok=True)

	# Player frames — binary alpha, 24×32, feet bottom
	for i in range(20):
		src = SRC / "player" / f"frame_{i:02d}.png"
		if not src.exists():
			continue
		im = to_canvas(Image.open(src), 24, 32, prefer_height=True)
		save(im, OUT / "player" / f"frame_{i:02d}.png")

	props = [
		("vegetation/tree_oak.png", "tree_deciduous.png", 64, 80, True, True),
		("vegetation/bush_00.png", "bush.png", 32, 24, True, True),
		("obstacles/rock_03.png", "rock.png", 24, 24, False, False),
	]
	for src_rel, out_name, tw, th, dirt, pref_h in props:
		im = Image.open(SRC / src_rel).convert("RGBA")
		if dirt:
			im = trim_dirt(im)
		im = to_canvas(im, tw, th, prefer_height=pref_h)
		save(im, OUT / out_name)

	# Simple weed silhouette texture 16×16 — crisp opaque green tuft
	weed = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
	px = weed.load()
	# stem + leaves, feet on bottom
	for y, xs in [
		(4, [7, 8]),
		(5, [6, 7, 8, 9]),
		(6, [5, 7, 8, 10]),
		(7, [6, 7, 8, 9]),
		(8, [7, 8]),
		(9, [7, 8]),
		(10, [7, 8]),
		(11, [7, 8]),
		(12, [7, 8]),
		(13, [6, 7, 8, 9]),
		(14, [7, 8]),
		(15, [7, 8]),
	]:
		for x in xs:
			# brighter tip
			c = (90, 150, 55, 255) if y < 8 else (70, 120, 45, 255)
			px[x, y] = c
	save(weed, OUT / "weed.png")

	print("done")


if __name__ == "__main__":
	main()
