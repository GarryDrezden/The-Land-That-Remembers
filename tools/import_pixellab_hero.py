#!/usr/bin/env python3
"""
Import PixelLab hero GIFs from upload/hero/ into transparent PNG runtime sheets.

- Does NOT delete, rename, or modify upload/hero/ originals.
- Preserves GIF transparency when present; flood-fill chroma only for opaque backgrounds.
- Shared canvas per clip; integer-pixel baseline alignment across the whole set.
- Idempotent: rebuilds assets/characters/player/pixellab_v1/ outputs.
"""

from __future__ import annotations

import json
import shutil
from collections import deque
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
UPLOAD = ROOT / "upload" / "hero"
OUT = ROOT / "assets" / "characters" / "player" / "pixellab_v1"

GIF_IDLE = UPLOAD / "Idle_rotations_8dir.gif"

# Filename stem → runtime direction folder name
WALK_GIFS: dict[str, Path] = {
    "south": UPLOAD / "Idle_v3_walking_south.gif",
    "south_east": UPLOAD / "Idle_v3_walking_south-east.gif",
    "east": UPLOAD / "Idle_v3_walking_east.gif",
    "north_east": UPLOAD / "Idle_v3_walking_north-east.gif",
    "north": UPLOAD / "Idle_v3_walking_north.gif",
    "north_west": UPLOAD / "Idle_v3_walking_north-west.gif",
    "west": UPLOAD / "Idle_v3_walking_west.gif",
    "south_west": UPLOAD / "Idle_v3_walking_south-west.gif",
}

# Verified from indexed contact sheet (clockwise from facing camera / south).
IDLE_DIRECTION_MAPPING = {
    "south": 0,
    "south_east": 1,
    "east": 2,
    "north_east": 3,
    "north": 4,
    "north_west": 5,
    "west": 6,
    "south_west": 7,
}

DIR_ORDER = [
    "south",
    "south_east",
    "east",
    "north_east",
    "north",
    "north_west",
    "west",
    "south_west",
]


def load_gif_frames(path: Path) -> tuple[list[Image.Image], list[int], dict]:
    """Load frames as RGBA. Preserve GIF transparency when present."""
    im = Image.open(path)
    n = getattr(im, "n_frames", 1)
    frames: list[Image.Image] = []
    durations: list[int] = []
    transparency_index = im.info.get("transparency", None)
    meta: dict = {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "source_name": path.name,
        "n_frames": n,
        "loop": im.info.get("loop", None),
        "gif_mode": im.mode,
        "transparency_index": transparency_index,
    }

    zero_alpha_total = 0
    opaque_green_total = 0
    for i in range(n):
        im.seek(i)
        durations.append(int(im.info.get("duration", 100) or 100))
        fr = im.convert("RGBA")
        # Normalize fully-transparent pixels to (0,0,0,0) to avoid green under alpha.
        px = []
        for r, g, b, a in fr.getdata():
            if a == 0:
                zero_alpha_total += 1
                px.append((0, 0, 0, 0))
            else:
                if g >= 200 and r <= 40 and b <= 40:
                    opaque_green_total += 1
                px.append((r, g, b, a))
        fr.putdata(px)
        frames.append(fr)

    meta["durations_ms"] = durations
    meta["canvas"] = list(frames[0].size) if frames else [0, 0]
    avg = sum(durations) / max(len(durations), 1)
    meta["avg_duration_ms"] = avg
    meta["approx_fps"] = round(1000.0 / avg, 3) if avg else None
    meta["zero_alpha_pixels"] = zero_alpha_total
    meta["opaque_green_pixels"] = opaque_green_total
    # Treat as authored/GIF transparency if most background is already alpha=0.
    pixels = max(1, sum(f.size[0] * f.size[1] for f in frames))
    meta["has_gif_transparency"] = (transparency_index is not None) or (
        zero_alpha_total / pixels > 0.2
    )
    meta["needs_chroma_flood"] = opaque_green_total > 0 and not meta["has_gif_transparency"]
    return frames, durations, meta


def corner_bg_color(im: Image.Image) -> tuple[int, int, int]:
    w, h = im.size
    return im.getpixel((0, 0))[:3]


def color_close(c: tuple[int, int, int], ref: tuple[int, int, int], tol: int) -> bool:
    return (
        abs(c[0] - ref[0]) <= tol
        and abs(c[1] - ref[1]) <= tol
        and abs(c[2] - ref[2]) <= tol
    )


def is_chroma_like(c: tuple[int, int, int], ref: tuple[int, int, int], tol: int) -> bool:
    if color_close(c, ref, tol):
        return True
    r, g, b = c
    if g >= 200 and r <= 40 and b <= 40:
        return True
    if g > r + 80 and g > b + 80 and g >= 160:
        return True
    return False


def flood_remove_chroma(im: Image.Image, tol: int = 40, edge_tol: int = 55) -> Image.Image:
    """Remove background connected to image edges only (no interior green wipe)."""
    src = im.convert("RGBA")
    w, h = src.size
    px = src.load()
    ref = corner_bg_color(src)
    visited = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def try_enqueue(x: int, y: int, use_tol: int) -> None:
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            return
        r, g, b, a = px[x, y]
        if a == 0:
            visited[y][x] = True
            return
        if is_chroma_like((r, g, b), ref, use_tol):
            visited[y][x] = True
            q.append((x, y))

    for x in range(w):
        try_enqueue(x, 0, tol)
        try_enqueue(x, h - 1, tol)
    for y in range(h):
        try_enqueue(0, y, tol)
        try_enqueue(w - 1, y, tol)

    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            try_enqueue(nx, ny, tol)

    out = src.copy()
    opx = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = opx[x, y]
            if a == 0:
                continue
            if not is_chroma_like((r, g, b), ref, edge_tol):
                continue
            border = False
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nx < 0 or ny < 0 or nx >= w or ny >= h or opx[nx, ny][3] == 0:
                    border = True
                    break
            if border:
                opx[x, y] = (0, 0, 0, 0)

    # Enclosed pure-key pockets (e.g. between legs)
    for y in range(h):
        for x in range(w):
            r, g, b, a = opx[x, y]
            if a == 0:
                continue
            if g >= 250 and r <= 8 and b <= 8:
                opx[x, y] = (0, 0, 0, 0)
            elif color_close((r, g, b), ref, 12) and g >= 220 and r <= 30 and b <= 30:
                opx[x, y] = (0, 0, 0, 0)
    return out


def prepare_frames(frames: list[Image.Image], meta: dict) -> list[Image.Image]:
    if meta.get("needs_chroma_flood"):
        return [flood_remove_chroma(f) for f in frames]
    # Transparency already present — keep it; strip residual opaque pure-green pockets only.
    out: list[Image.Image] = []
    for fr in frames:
        img = fr.copy()
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    px[x, y] = (0, 0, 0, 0)
                elif g >= 250 and r <= 8 and b <= 8:
                    px[x, y] = (0, 0, 0, 0)
        out.append(img)
    return out


def opaque_bbox(im: Image.Image) -> tuple[int, int, int, int] | None:
    px = im.load()
    w, h = im.size
    minx, miny, maxx, maxy = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 10:
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if maxx < 0:
        return None
    return minx, miny, maxx, maxy


def align_frames_to_target(
    frames: list[Image.Image], target_foot: int, target_cx: int
) -> tuple[list[Image.Image], list[dict]]:
    """Integer-pixel shift to shared foot baseline + horizontal center. Keep canvas."""
    out: list[Image.Image] = []
    infos: list[dict] = []
    w, h = frames[0].size
    for fr in frames:
        bb = opaque_bbox(fr)
        if bb is None:
            out.append(fr)
            infos.append({"dx": 0, "dy": 0})
            continue
        cx = (bb[0] + bb[2]) // 2
        fy = bb[3]
        dx = target_cx - cx
        dy = target_foot - fy
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.paste(fr, (dx, dy), fr)
        out.append(canvas)
        infos.append(
            {
                "dx": dx,
                "dy": dy,
                "foot_y_before": fy,
                "foot_y_after": fy + dy,
                "bbox_before": list(bb),
            }
        )
    return out, infos


def contact_sheet(frames: list[Image.Image], labels: list[str], path: Path, cell_pad: int = 8) -> None:
    if not frames:
        return
    w, h = frames[0].size
    n = len(frames)
    cols = min(8, n)
    rows = (n + cols - 1) // cols
    label_h = 18
    cw, ch = w + cell_pad * 2, h + cell_pad * 2 + label_h
    sheet = Image.new("RGBA", (cols * cw, rows * ch), (40, 42, 46, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, fr in enumerate(frames):
        r, c = divmod(i, cols)
        x0, y0 = c * cw, r * ch
        for yy in range(h):
            for xx in range(w):
                col = (
                    (210, 210, 210, 255)
                    if ((xx // 4) + (yy // 4)) % 2 == 0
                    else (180, 180, 180, 255)
                )
                sheet.putpixel((x0 + cell_pad + xx, y0 + cell_pad + yy), col)
        sheet.alpha_composite(fr, (x0 + cell_pad, y0 + cell_pad))
        label = labels[i] if i < len(labels) else str(i)
        draw.text(
            (x0 + 4, y0 + cell_pad + h + 2),
            label,
            fill=(240, 240, 235, 255),
            font=font,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def save_frames(frames: list[Image.Image], folder: Path, prefix: str = "frame_") -> list[str]:
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, fr in enumerate(frames):
        p = folder / f"{prefix}{i:02d}.png"
        fr.save(p)
        paths.append(str(p.relative_to(ROOT)).replace("\\", "/"))
    return paths


def process() -> dict:
    if not UPLOAD.is_dir():
        raise SystemExit(f"Missing inbox: {UPLOAD}")
    required = [GIF_IDLE, *WALK_GIFS.values()]
    for path in required:
        if not path.exists():
            raise SystemExit(f"Missing GIF: {path}")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "idle").mkdir(parents=True)
    (OUT / "walk").mkdir(parents=True)
    (OUT / "preview").mkdir(parents=True)

    manifest: dict = {
        "version": 2,
        "generated": date.today().isoformat(),
        "source_inbox": "upload/hero/",
        "runtime_root": "assets/characters/player/pixellab_v1/",
        "notes": [
            "PixelLab hero v1: idle + walking in 8 directions.",
            "No mirroring or direction substitution.",
            "Current in-engine node scale is Vector2.ONE (provisionally accepted).",
            "Runtime display may apply integer nearest PIXEL_DIV=2 (does not rewrite PNGs).",
            "Original PixelLab exports remain permanently in upload/hero/.",
        ],
        "gifs": {},
        "idle_direction_mapping": IDLE_DIRECTION_MAPPING,
        "baseline": {},
        "baseline_offsets": {},
        "walk_paths": {},
        "idle_paths": {},
    }

    # Load + key all clips first (shared baseline pass).
    idle_raw, _idle_dur, idle_meta = load_gif_frames(GIF_IDLE)
    idle_keyed = prepare_frames(idle_raw, idle_meta)
    manifest["gifs"][GIF_IDLE.name] = idle_meta

    walk_keyed: dict[str, list[Image.Image]] = {}
    for direction, gif_path in WALK_GIFS.items():
        raw, _dur, meta = load_gif_frames(gif_path)
        keyed = prepare_frames(raw, meta)
        walk_keyed[direction] = keyed
        manifest["gifs"][gif_path.name] = meta

    # Shared foot baseline + center across every frame in the set.
    all_frames: list[Image.Image] = list(idle_keyed)
    for d in DIR_ORDER:
        all_frames.extend(walk_keyed[d])
    foot_ys: list[int] = []
    for fr in all_frames:
        bb = opaque_bbox(fr)
        if bb:
            foot_ys.append(bb[3])
    if not foot_ys:
        raise SystemExit("No opaque pixels found in hero frames.")
    target_foot = max(foot_ys)
    target_cx = idle_keyed[0].size[0] // 2
    manifest["baseline"] = {
        "target_foot_y": target_foot,
        "target_center_x": target_cx,
        "canvas": list(idle_keyed[0].size),
        "method": "integer_pixel_shift_shared_across_idle_and_walk",
    }

    idle_aligned, idle_off = align_frames_to_target(idle_keyed, target_foot, target_cx)
    manifest["baseline_offsets"]["idle_rotations"] = idle_off

    contact_sheet(
        idle_aligned,
        [f"{i}:{next(k for k,v in IDLE_DIRECTION_MAPPING.items() if v==i)}" for i in range(len(idle_aligned))],
        OUT / "preview" / "idle_rotations_indexed.png",
    )

    idle_paths = {}
    for name, idx in IDLE_DIRECTION_MAPPING.items():
        p = OUT / "idle" / f"{name}.png"
        idle_aligned[idx].save(p)
        idle_paths[name] = str(p.relative_to(ROOT)).replace("\\", "/")
    manifest["idle_paths"] = idle_paths

    for direction in DIR_ORDER:
        keyed = walk_keyed[direction]
        aligned, offs = align_frames_to_target(keyed, target_foot, target_cx)
        manifest["baseline_offsets"][f"walk_{direction}"] = offs
        folder = OUT / "walk" / direction
        paths = save_frames(aligned, folder)
        manifest["walk_paths"][direction] = paths
        contact_sheet(
            aligned,
            [f"{direction[0:2]}{i:02d}" for i in range(len(aligned))],
            OUT / "preview" / f"walk_{direction}_contact_sheet.png",
        )

    # Compact 8-dir walk demo GIF (frame 0 of each direction, then a short cycle of south).
    demo_frames: list[Image.Image] = []
    for direction in DIR_ORDER:
        demo_frames.append(Image.open(OUT / "walk" / direction / "frame_00.png").convert("RGBA"))
    south_cycle = [
        Image.open(OUT / "walk" / "south" / f"frame_{i:02d}.png").convert("RGBA")
        for i in range(8)
    ]
    demo_path = OUT / "preview" / "walk_8dir_demo.gif"
    demo_frames[0].save(
        demo_path,
        save_all=True,
        append_images=demo_frames[1:] + south_cycle,
        duration=220,
        loop=0,
        disposal=2,
    )
    manifest["preview_demo_gif"] = str(demo_path.relative_to(ROOT)).replace("\\", "/")

    manifest_path = OUT / "source_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Imported PixelLab hero ->", OUT)
    print("Idle mapping:", IDLE_DIRECTION_MAPPING)
    print("Walk directions:", ", ".join(DIR_ORDER))
    print("Shared foot_y:", target_foot, "canvas:", idle_keyed[0].size)
    return manifest


if __name__ == "__main__":
    process()
