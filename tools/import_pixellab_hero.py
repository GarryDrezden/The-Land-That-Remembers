#!/usr/bin/env python3
"""
Import PixelLab hero GIFs from upload/hero/ into transparent PNG runtime sheets.

- Does NOT delete or modify upload/hero/ originals.
- Removes chroma green via edge flood-fill (not global green delete).
- Keeps a shared canvas per clip; optional integer-pixel baseline alignment.
- Idempotent: wipes/rebuilds assets/characters/player/pixellab_v1/ outputs.
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
GIF_WALK_S = UPLOAD / "Idle_v3_walking_south.gif"
GIF_WALK_E = UPLOAD / "Idle_v3_walking_east.gif"

# After visual check of indexed contact sheet (clockwise from facing camera).
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
    "south", "south_east", "east", "north_east",
    "north", "north_west", "west", "south_west",
]


def load_gif_frames_rgb(path: Path) -> tuple[list[Image.Image], list[int], dict]:
    """Load frames as RGBA with chroma green kept opaque (ignore GIF transparency flag)."""
    im = Image.open(path)
    n = getattr(im, "n_frames", 1)
    frames: list[Image.Image] = []
    durations: list[int] = []
    meta = {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "n_frames": n,
        "loop": im.info.get("loop", None),
        "gif_mode": im.mode,
        "transparency_index": im.info.get("transparency", None),
    }
    for i in range(n):
        im.seek(i)
        durations.append(int(im.info.get("duration", 100) or 100))
        if im.mode == "P" and im.getpalette():
            pal = im.getpalette()
            data = []
            for idx in im.getdata():
                r, g, b = pal[idx * 3 : idx * 3 + 3]
                data.append((r, g, b, 255))
            fr = Image.new("RGBA", im.size)
            fr.putdata(data)
        else:
            fr = im.convert("RGBA")
            # Force full alpha so we control keying ourselves
            px = [(r, g, b, 255) for r, g, b, _a in fr.getdata()]
            fr.putdata(px)
        frames.append(fr)
    meta["durations_ms"] = durations
    meta["canvas"] = list(frames[0].size) if frames else [0, 0]
    avg = sum(durations) / max(len(durations), 1)
    meta["avg_duration_ms"] = avg
    meta["approx_fps"] = round(1000.0 / avg, 3) if avg else None
    return frames, durations, meta


def corner_bg_color(im: Image.Image) -> tuple[int, int, int]:
    w, h = im.size
    samples = [
        im.getpixel((0, 0))[:3],
        im.getpixel((w - 1, 0))[:3],
        im.getpixel((0, h - 1))[:3],
        im.getpixel((w - 1, h - 1))[:3],
    ]
    # majority / first
    return samples[0]


def color_close(c: tuple[int, int, int], ref: tuple[int, int, int], tol: int) -> bool:
    return (
        abs(c[0] - ref[0]) <= tol
        and abs(c[1] - ref[1]) <= tol
        and abs(c[2] - ref[2]) <= tol
    )


def is_chroma_like(c: tuple[int, int, int], ref: tuple[int, int, int], tol: int) -> bool:
    """Green-screen-ish: close to ref OR classic pure-green chroma."""
    if color_close(c, ref, tol):
        return True
    r, g, b = c
    # classic PixelLab green
    if g >= 200 and r <= 40 and b <= 40:
        return True
    if g > r + 80 and g > b + 80 and g >= 160:
        return True
    return False


def flood_remove_chroma(im: Image.Image, tol: int = 40, edge_tol: int = 55) -> Image.Image:
    """Remove background connected to image edges (flood fill), keep interior greens."""
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

    # Strip residual chroma halo on silhouette edge (1px ring), no blur
    out = src.copy()
    opx = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = opx[x, y]
            if a == 0:
                continue
            if not is_chroma_like((r, g, b), ref, edge_tol):
                continue
            # only if adjacent to transparent
            border = False
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nx < 0 or ny < 0 or nx >= w or ny >= h:
                    border = True
                    break
                if opx[nx, ny][3] == 0:
                    border = True
                    break
            if border:
                opx[x, y] = (0, 0, 0, 0)

    # Enclosed chroma pockets (e.g. between legs) — only near-pure key green
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


def baseline_align(frames: list[Image.Image]) -> tuple[list[Image.Image], list[dict]]:
    """Align feet to a common baseline with integer pixel shifts; keep canvas size."""
    infos = []
    bboxes = [opaque_bbox(f) for f in frames]
    foot_ys = [b[3] if b else None for b in bboxes]
    valid = [y for y in foot_ys if y is not None]
    if not valid:
        return frames, [{"dx": 0, "dy": 0} for _ in frames]
    target_foot = max(valid)  # push down to lowest foot so nothing clipped
    # horizontal: center of feet bbox mid-x to canvas center
    w, h = frames[0].size
    target_cx = w // 2
    out: list[Image.Image] = []
    for fr, bb, fy in zip(frames, bboxes, foot_ys):
        if bb is None or fy is None:
            out.append(fr)
            infos.append({"dx": 0, "dy": 0})
            continue
        cx = (bb[0] + bb[2]) // 2
        dx = target_cx - cx
        dy = target_foot - fy
        # clamp so content stays on canvas as much as possible
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.paste(fr, (dx, dy), fr)
        out.append(canvas)
        infos.append({"dx": dx, "dy": dy, "foot_y_before": fy, "foot_y_after": fy + dy})
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
    # checker under each
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, fr in enumerate(frames):
        r, c = divmod(i, cols)
        x0, y0 = c * cw, r * ch
        # checker
        for yy in range(h):
            for xx in range(w):
                col = (210, 210, 210, 255) if ((xx // 4) + (yy // 4)) % 2 == 0 else (180, 180, 180, 255)
                sheet.putpixel((x0 + cell_pad + xx, y0 + cell_pad + yy), col)
        sheet.alpha_composite(fr, (x0 + cell_pad, y0 + cell_pad))
        label = labels[i] if i < len(labels) else str(i)
        draw.text((x0 + 4, y0 + cell_pad + h + 2), label, fill=(240, 240, 235, 255), font=font)
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
    for required in (GIF_IDLE, GIF_WALK_S, GIF_WALK_E):
        if not required.exists():
            raise SystemExit(f"Missing GIF: {required}")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "idle").mkdir(parents=True)
    (OUT / "preview").mkdir(parents=True)

    manifest: dict = {
        "version": 1,
        "generated": date.today().isoformat(),
        "source_inbox": "upload/hero/",
        "runtime_root": "assets/characters/player/pixellab_v1/",
        "notes": [
            "PixelLab hero v1 under in-engine evaluation.",
            "Walk directions available: south and east.",
            "West is mirrored from east at runtime (flip_h).",
            "North walking animation is not generated yet.",
            "Original PixelLab exports remain in upload/hero/.",
        ],
        "gifs": {},
        "idle_direction_mapping": IDLE_DIRECTION_MAPPING,
        "baseline_offsets": {},
    }

    # --- Idle rotations ---
    idle_raw, idle_dur, idle_meta = load_gif_frames_rgb(GIF_IDLE)
    idle_keyed = [flood_remove_chroma(f) for f in idle_raw]
    idle_aligned, idle_off = baseline_align(idle_keyed)
    manifest["gifs"]["Idle_rotations_8dir.gif"] = idle_meta
    manifest["baseline_offsets"]["idle_rotations"] = idle_off

    # Indexed contact BEFORE mapping (all frames)
    contact_sheet(
        idle_aligned,
        [f"frame {i}" for i in range(len(idle_aligned))],
        OUT / "preview" / "idle_rotations_indexed.png",
    )

    idle_paths = {}
    for name, idx in IDLE_DIRECTION_MAPPING.items():
        p = OUT / "idle" / f"{name}.png"
        idle_aligned[idx].save(p)
        idle_paths[name] = str(p.relative_to(ROOT)).replace("\\", "/")
    manifest["idle_paths"] = idle_paths

    # --- Walk south ---
    ws_raw, ws_dur, ws_meta = load_gif_frames_rgb(GIF_WALK_S)
    ws_keyed = [flood_remove_chroma(f) for f in ws_raw]
    ws_aligned, ws_off = baseline_align(ws_keyed)
    manifest["gifs"]["Idle_v3_walking_south.gif"] = ws_meta
    manifest["baseline_offsets"]["walk_south"] = ws_off
    ws_paths = save_frames(ws_aligned, OUT / "walk_south")
    manifest["walk_south_frames"] = ws_paths
    contact_sheet(
        ws_aligned,
        [f"s{i:02d}" for i in range(len(ws_aligned))],
        OUT / "preview" / "walk_south_contact_sheet.png",
    )

    # --- Walk east ---
    we_raw, we_dur, we_meta = load_gif_frames_rgb(GIF_WALK_E)
    we_keyed = [flood_remove_chroma(f) for f in we_raw]
    we_aligned, we_off = baseline_align(we_keyed)
    manifest["gifs"]["Idle_v3_walking_east.gif"] = we_meta
    manifest["baseline_offsets"]["walk_east"] = we_off
    we_paths = save_frames(we_aligned, OUT / "walk_east")
    manifest["walk_east_frames"] = we_paths
    contact_sheet(
        we_aligned,
        [f"e{i:02d}" for i in range(len(we_aligned))],
        OUT / "preview" / "walk_east_contact_sheet.png",
    )

    # Scale comparison sheet (1.0 / 0.75 / 0.5) using idle south
    scale_sheet = Image.new("RGBA", (92 * 3 + 40, 92 + 40), (36, 38, 42, 255))
    draw = ImageDraw.Draw(scale_sheet)
    font = ImageFont.load_default()
    base = idle_aligned[IDLE_DIRECTION_MAPPING["south"]]
    for i, sc in enumerate((1.0, 0.75, 0.5)):
        nw, nh = max(1, int(round(92 * sc))), max(1, int(round(92 * sc)))
        scaled = base.resize((nw, nh), Image.NEAREST)
        x = 10 + i * (92 + 10)
        y = 20
        scale_sheet.alpha_composite(scaled, (x + (92 - nw) // 2, y + (92 - nh) // 2))
        draw.text((x, 4), f"scale {sc}", fill=(240, 240, 235, 255), font=font)
    scale_sheet.save(OUT / "preview" / "scale_compare.png")

    manifest_path = OUT / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Imported PixelLab hero ->", OUT)
    print("Idle mapping:", IDLE_DIRECTION_MAPPING)
    print("Walk south frames:", len(ws_aligned), "Walk east frames:", len(we_aligned))
    return manifest


if __name__ == "__main__":
    process()
