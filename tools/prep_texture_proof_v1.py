#!/usr/bin/env python3
"""Prepare texture-proof v1 PNGs at approved greybox sizes.

Sources: generated_test references (rejected as production).
Outputs: assets/art/outdoor/texture_proof_v1/
Uses NEAREST downscale into fixed canvases; feet at bottom-center.
Attempts light dirt-island trim — document remaining issues in inventory.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/art/outdoor/generated_test/processed"
OUT = ROOT / "assets/art/outdoor/texture_proof_v1"
MANIFEST = OUT / "manifest.json"


def trim_alpha(im: Image.Image) -> Image.Image:
	im = im.convert("RGBA")
	bbox = im.getbbox()
	if bbox:
		return im.crop(bbox)
	return im


def trim_dirt_island(im: Image.Image, max_frac: float = 0.22) -> Image.Image:
	"""Drop a bottom strip that looks like baked dirt/grass under the prop."""
	im = im.convert("RGBA")
	w, h = im.size
	px = im.load()
	cut = 0
	limit = int(h * max_frac)
	for y in range(h - 1, max(h // 2, h - limit) - 1, -1):
		dirt = 0
		opaque = 0
		for x in range(w):
			r, g, b, a = px[x, y]
			if a < 30:
				continue
			opaque += 1
			# brown / tan dirt or green grass patch under object
			if (r > 70 and r > b + 15 and g < r + 25) or (g > r + 10 and g > b and g > 70):
				dirt += 1
		if opaque == 0:
			cut += 1
			continue
		if dirt / opaque > 0.55:
			cut += 1
		else:
			break
	if cut > 2:
		return im.crop((0, 0, w, h - cut + 1))
	return im


def fit_canvas(im: Image.Image, tw: int, th: int) -> Image.Image:
	"""Scale with NEAREST to fit inside tw×th, feet bottom-center on transparent canvas."""
	im = trim_alpha(im)
	if im.width < 1 or im.height < 1:
		return Image.new("RGBA", (tw, th), (0, 0, 0, 0))
	scale = min(tw / im.width, th / im.height)
	nw = max(1, int(round(im.width * scale)))
	nh = max(1, int(round(im.height * scale)))
	# Prefer not upscaling tiny sources more than 1.25x
	if scale > 1.25:
		nw, nh = im.width, im.height
		scale = 1.0
	resized = im.resize((nw, nh), Image.NEAREST)
	canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
	ox = (tw - nw) // 2
	oy = th - nh
	canvas.paste(resized, (ox, oy), resized)
	return canvas


def save(im: Image.Image, path: Path) -> dict:
	path.parent.mkdir(parents=True, exist_ok=True)
	im.save(path)
	return {
		"file": path.relative_to(ROOT).as_posix(),
		"size": [im.width, im.height],
		"opaque": sum(1 for p in im.getdata() if p[3] > 20),
	}


def prep_prop(src_rel: str, out_name: str, tw: int, th: int, dirt_trim: bool = True) -> dict:
	src = SRC / src_rel
	im = Image.open(src).convert("RGBA")
	if dirt_trim:
		im = trim_dirt_island(im)
	im = fit_canvas(im, tw, th)
	meta = save(im, OUT / out_name)
	meta["source"] = ("assets/art/outdoor/generated_test/processed/" + src_rel.replace("\\", "/"))
	meta["target"] = [tw, th]
	return meta


def prep_player() -> dict:
	# Band-sliced frames already exist; fit each to 24×32
	# Mapping from process_generated_outdoor_v2 / art test v2
	anims = {
		"idle_down": [0],
		"walk_down": [0, 1, 0],
		"idle_up": [2],
		"walk_up": [2, 3, 4],
		"idle_right": [5],
		"walk_right": [5, 6, 7],
		"idle_left": [5],  # prototype flip
		"walk_left": [5, 6, 7],  # prototype flip
	}
	frames_meta = []
	out_dir = OUT / "player"
	out_dir.mkdir(parents=True, exist_ok=True)
	for i in range(20):
		src = SRC / "player" / f"frame_{i:02d}.png"
		if not src.exists():
			continue
		im = fit_canvas(Image.open(src), 24, 32)
		frames_meta.append(save(im, out_dir / f"frame_{i:02d}.png"))
	return {
		"frame_size": [24, 32],
		"frames": [m["file"] for m in frames_meta],
		"anims": anims,
		"left_is_prototype_flip": True,
		"note": "Source frames ~79×142 downscaled NEAREST to 24×32 — pixel density will look soft vs native 16px art.",
	}


def prep_pond() -> dict:
	# Prefer a water chunk over huge baked pond; build ~128×96 soft oval + stamp
	import math
	import random

	rnd = random.Random(3)
	canvas = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
	# Base irregular water from average teal
	wr, wg, wb = 40, 140, 130
	px = canvas.load()
	cx, cy = 64, 48
	for y in range(96):
		for x in range(128):
			nx = (x - cx) / 58.0
			ny = (y - cy) / 42.0
			n = nx * nx + ny * ny + 0.12 * math.sin(x * 0.11) * math.cos(y * 0.09)
			if n < 1.0:
				j = rnd.randint(-12, 12)
				px[x, y] = (
					max(0, min(255, wr + j)),
					max(0, min(255, wg + j // 2)),
					max(0, min(255, wb + j // 2)),
					255,
				)
	# Stamp water pieces if available
	for name in ["water_01.png", "water_05.png", "water_00.png"]:
		p = SRC / "water" / name
		if not p.exists():
			continue
		chunk = trim_alpha(Image.open(p))
		# scale chunk down to fit
		cw = min(70, chunk.width)
		ch = min(40, chunk.height)
		chunk = chunk.resize((cw, ch), Image.NEAREST)
		canvas.alpha_composite(chunk, (rnd.randint(10, 50), rnd.randint(10, 40)))
	meta = save(canvas, OUT / "pond.png")
	meta["note"] = "Temporary whole pond (~128×96); not production shoreline autotile."
	return meta


def main() -> None:
	OUT.mkdir(parents=True, exist_ok=True)
	manifest = {
		"status": "generated outdoor texture proof v1 — candidate",
		"scale_locked": {
			"viewport": [384, 240],
			"tile": 16,
			"map_tiles": [72, 45],
			"player": [24, 32],
			"deciduous": [64, 80],
			"birch": [48, 80],
			"spruce": [48, 96],
			"bush": [32, 24],
			"rock_s": [16, 16],
			"rock_l": [24, 24],
			"log": [32, 16],
			"stump": [24, 24],
			"house": [144, 112],
			"pond": [128, 96],
		},
		"player": prep_player(),
		"props": {
			"deciduous": prep_prop("vegetation/tree_oak.png", "tree_deciduous.png", 64, 80),
			"spruce": prep_prop("vegetation/tree_spruce.png", "tree_spruce.png", 48, 96),
			"bush": prep_prop("vegetation/bush_00.png", "bush.png", 32, 24),
			"rock": prep_prop("obstacles/rock_03.png", "rock.png", 24, 24, dirt_trim=False),
			"log": prep_prop("obstacles/log_00.png", "log.png", 32, 16),
			"stump": prep_prop("obstacles/stump_00.png", "stump.png", 24, 24),
			"house": prep_prop("buildings/house_main.png", "house.png", 144, 112),
			"pond": prep_pond(),
		},
		"limitations": [
			"Source art is larger / different pixel density than 16px grid — NEAREST downscale softens detail.",
			"Dirt-island trim is heuristic; residual base fringe may remain.",
			"Spruce source shorter than oak — vertical fit into 48×96 may look sparse.",
			"Player left = horizontal flip of right (prototype flip).",
			"Pond is temporary whole sprite, not shoreline tiles.",
		],
	}
	MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
	print("wrote", OUT)
	for k, v in manifest["props"].items():
		print(k, v.get("size"), v.get("file"))
	print("player frames", len(manifest["player"]["frames"]))


if __name__ == "__main__":
	main()
