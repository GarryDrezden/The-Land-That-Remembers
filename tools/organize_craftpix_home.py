#!/usr/bin/env python3
"""Organize CraftPix pack + export Exterior.tmx region for Godot preview."""
from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPLOAD = ROOT / "upload"
DEST = ROOT / "assets/third_party/craftpix/main_characters_home"
SOURCE = DEST / "source"
RUNTIME = DEST / "runtime"
EXPORT = DEST / "runtime/preview"
TILE = 16


def wipe_macosx() -> None:
	for name in ("__MACOSX", "_MACOSX"):
		p = UPLOAD / name
		if p.exists():
			shutil.rmtree(p)
			print("removed", p)


def organize() -> None:
	DEST.mkdir(parents=True, exist_ok=True)
	SOURCE.mkdir(parents=True, exist_ok=True)
	# Copy original structure (no MACOSX)
	for sub in ("PNG", "PSD", "Tiled_files"):
		src = UPLOAD / sub
		dst = SOURCE / sub
		if dst.exists():
			shutil.rmtree(dst)
		if src.exists():
			shutil.copytree(src, dst)
			print("copied source", sub)

	# Runtime: use Tiled_files PNGs (atlas sizes match TMX) + keep PNG duplicates only if unique
	mapping = {
		"terrain": [
			"ground_grass_details.png",
		],
		"buildings": [
			"exterior.png",
			"house_details.png",
			"Doors_windows_animation.png",
			"Smoke_animation.png",
		],
		"vegetation": [
			"Trees_animation.png",
		],
		"props": [
			# props live inside exterior / ground atlases; keep anim helpers
			"bird_fly_animation.png",
			"bird_jump_animation.png",
			"cat_animation.png",
		],
		"interiors": [
			"Interior.png",
			"walls_floor.png",
		],
		"characters": [],  # no human character in pack
	}

	tiled = SOURCE / "Tiled_files"
	png_root = SOURCE / "PNG"
	for folder, files in mapping.items():
		out = RUNTIME / folder
		out.mkdir(parents=True, exist_ok=True)
		for name in files:
			src = tiled / name
			if not src.exists():
				src = png_root / name
			if not src.exists():
				print("MISSING", name)
				continue
			dst = out / name
			shutil.copy2(src, dst)
			print("runtime", folder, name)

	# Also copy TMX demos into source only (already in Tiled_files)
	# Zip archive into source if present
	for z in UPLOAD.glob("*.zip"):
		shutil.copy2(z, SOURCE / z.name)
		print("copied archive", z.name)

	readme = DEST / "README.md"
	readme.write_text(
		"""# CraftPix — Main Character’s Home

Local third-party pack for *The Land That Remembers*.

- `source/` — original archive contents (PNG, PSD, Tiled_files), minus `__MACOSX`
- `runtime/` — Godot-facing copies used by preview / future scenes
- Official page: https://craftpix.net/freebies/main-characters-home-free-top-down-pixel-art-asset/
- Tile size (from TMX): **16×16**
- No human player character in this pack (cat/bird animations only)

Project owner reports that explicit permission was obtained to store and publish
these asset source files in this project’s Git repository.
""",
		encoding="utf-8",
	)


def parse_gid(raw: int) -> tuple[int, bool, bool, bool]:
	FLIP_H = 0x80000000
	FLIP_V = 0x40000000
	FLIP_D = 0x20000000
	flags_h = bool(raw & FLIP_H)
	flags_v = bool(raw & FLIP_V)
	flags_d = bool(raw & FLIP_D)
	gid = raw & ~(FLIP_H | FLIP_V | FLIP_D)
	return gid, flags_h, flags_v, flags_d


def tileset_for_gid(gid: int, tilesets: list[dict]) -> dict | None:
	owner = None
	for t in tilesets:
		if gid >= t["firstgid"]:
			owner = t
	if owner is None:
		return None
	if gid >= owner["firstgid"] + owner["tilecount"]:
		return None
	return owner


def export_exterior_preview() -> None:
	tmx_path = SOURCE / "Tiled_files" / "Exterior.tmx"
	root = ET.fromstring(tmx_path.read_text(encoding="utf-8", errors="replace"))

	tilesets = []
	for ts in root.findall("tileset"):
		img = ts.find("image")
		if img is None:
			continue
		src = img.attrib.get("source", "")
		if ".." in src:
			continue
		tilesets.append(
			{
				"name": ts.attrib.get("name"),
				"firstgid": int(ts.attrib["firstgid"]),
				"tilewidth": int(ts.attrib["tilewidth"]),
				"tileheight": int(ts.attrib["tileheight"]),
				"tilecount": int(ts.attrib.get("tilecount", "0")),
				"columns": int(ts.attrib.get("columns", "0")),
				"image": src,
				"imagewidth": int(img.attrib["width"]),
				"imageheight": int(img.attrib["height"]),
			}
		)
	tilesets.sort(key=lambda t: t["firstgid"])

	wanted = [
		"Ground",
		"Spots",
		"Road",
		"Plates",
		"Grass",
		"Grass_detail6",
		"Grass_details3",
		"Grass_details4",
		"Grass_details5",
		"Objects4",
		"Objects1",
		"Objects2",
		"Fence",
		"House_wall",
		"windows1",
		"windows2",
		"House_roof",
		"Objects3",
		"Grass_top_details",
	]

	layer_cells: dict[str, list[dict]] = {}
	minx = miny = 10**9
	maxx = maxy = -10**9
	for layer in root.findall("layer"):
		name = layer.attrib.get("name", "")
		if name not in wanted:
			continue
		data = layer.find("data")
		cells: list[dict] = []
		for chunk in data.findall("chunk"):
			cx = int(chunk.attrib["x"])
			cy = int(chunk.attrib["y"])
			w = int(chunk.attrib["width"])
			nums = [int(x) for x in (chunk.text or "").replace("\n", ",").split(",") if x.strip() != ""]
			for i, raw in enumerate(nums):
				gid, fh, fv, fd = parse_gid(raw)
				if gid == 0:
					continue
				if tileset_for_gid(gid, tilesets) is None:
					continue
				x = cx + (i % w)
				y = cy + (i // w)
				minx = min(minx, x)
				miny = min(miny, y)
				maxx = max(maxx, x)
				maxy = max(maxy, y)
				cells.append({"x": x, "y": y, "gid": gid, "fh": fh, "fv": fv, "fd": fd})
		if cells:
			# Merge duplicate layer names (TMX has two Grass_details3)
			if name in layer_cells:
				layer_cells[name].extend(cells)
			else:
				layer_cells[name] = cells

	hx = hy = None
	if "House_wall" in layer_cells:
		xs = [c["x"] for c in layer_cells["House_wall"]]
		ys = [c["y"] for c in layer_cells["House_wall"]]
		hx = sum(xs) // len(xs)
		hy = sum(ys) // len(ys)
	cx = hx if hx is not None else (minx + maxx) // 2
	cy = hy if hy is not None else (miny + maxy) // 2
	win_w, win_h = 28, 18
	x0 = cx - win_w // 2
	y0 = cy - win_h // 2
	x1 = x0 + win_w - 1
	y1 = y0 + win_h - 1

	out_layers = []
	for name in wanted:
		if name not in layer_cells:
			continue
		cells = []
		for c in layer_cells[name]:
			if x0 <= c["x"] <= x1 and y0 <= c["y"] <= y1:
				cells.append(
					{
						"x": c["x"] - x0,
						"y": c["y"] - y0,
						"gid": c["gid"],
						"fh": c["fh"],
						"fv": c["fv"],
						"fd": c["fd"],
					}
				)
		if cells:
			out_layers.append({"name": name, "cells": cells})

	EXPORT.mkdir(parents=True, exist_ok=True)
	payload = {
		"tile_size": TILE,
		"width": win_w,
		"height": win_h,
		"origin_tmx": "source/Tiled_files/Exterior.tmx",
		"window": {"x0": x0, "y0": y0, "x1": x1, "y1": y1},
		"full_bounds": {"minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy, "w": maxx - minx + 1, "h": maxy - miny + 1},
		"tilesets": tilesets,
		"layers": out_layers,
		"runtime_image_roots": {
			"ground_grass_details.png": "res://assets/third_party/craftpix/main_characters_home/runtime/terrain/ground_grass_details.png",
			"exterior.png": "res://assets/third_party/craftpix/main_characters_home/runtime/buildings/exterior.png",
			"house_details.png": "res://assets/third_party/craftpix/main_characters_home/runtime/buildings/house_details.png",
			"Doors_windows_animation.png": "res://assets/third_party/craftpix/main_characters_home/runtime/buildings/Doors_windows_animation.png",
			"Smoke_animation.png": "res://assets/third_party/craftpix/main_characters_home/runtime/buildings/Smoke_animation.png",
			"Trees_animation.png": "res://assets/third_party/craftpix/main_characters_home/runtime/vegetation/Trees_animation.png",
			"bird_fly_animation.png": "res://assets/third_party/craftpix/main_characters_home/runtime/props/bird_fly_animation.png",
			"bird_jump_animation.png": "res://assets/third_party/craftpix/main_characters_home/runtime/props/bird_jump_animation.png",
			"cat_animation.png": "res://assets/third_party/craftpix/main_characters_home/runtime/props/cat_animation.png",
			"Interior.png": "res://assets/third_party/craftpix/main_characters_home/runtime/interiors/Interior.png",
			"walls_floor.png": "res://assets/third_party/craftpix/main_characters_home/runtime/interiors/walls_floor.png",
		},
	}
	out = EXPORT / "exterior_preview_layout.json"
	out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
	print("wrote", out, "layers", len(out_layers), "window", win_w, "x", win_h, "origin", x0, y0)
	print("tilesets", [t["name"] for t in tilesets])
	for L in out_layers:
		print(" ", L["name"], len(L["cells"]))


def remove_upload() -> None:
	if UPLOAD.exists():
		shutil.rmtree(UPLOAD)
		print("removed upload/")


def main() -> None:
	wipe_macosx()
	organize()
	export_exterior_preview()
	remove_upload()
	print("DONE")


if __name__ == "__main__":
	main()
