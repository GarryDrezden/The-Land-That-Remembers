#!/usr/bin/env python3
"""
Persistent visual asset catalog for The Land That Remembers.

Scans permanent INBOX `upload/` (+ already-imported `assets/third_party/`)
and regenerates:
  - data/assets/asset_catalog.json
  - README.md section «Где смотреть ассеты» (primary owner entry)
  - docs/assets/START_HERE.md (redirect stub)
  - docs/assets/catalog/previews/<PACK>/<ASSET_ID>.png
  - docs/assets/catalog/contact_sheets/
  - docs/assets/catalog/categories/*.md
  - docs/assets/catalog/packs/<slug>/

Usage:
  python tools/build_asset_catalog.py
  python tools/build_asset_catalog.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
UPLOAD = ROOT / "upload"
THIRD_PARTY = ROOT / "assets" / "third_party"
DATA_DIR = ROOT / "data" / "assets"
CATALOG_JSON = DATA_DIR / "asset_catalog.json"
PACKS_JSON = DATA_DIR / "asset_packs.json"
OVERRIDES_JSON = DATA_DIR / "asset_catalog_overrides.json"
AREA_JSON = DATA_DIR / "area_asset_selections.json"
FINGERPRINT_JSON = DATA_DIR / "catalog_fingerprint.json"

DOCS_ASSETS = ROOT / "docs" / "assets"
CATALOG_DOCS = DOCS_ASSETS / "catalog"
CATEGORIES_DOCS = CATALOG_DOCS / "categories"
PREVIEWS = CATALOG_DOCS / "previews"
CONTACT = CATALOG_DOCS / "contact_sheets"
PACK_DOCS = CATALOG_DOCS / "packs"

IMAGE_EXTS = {".png", ".webp", ".jpg", ".jpeg", ".gif"}
META_EXTS = {".tmx", ".tsx", ".json", ".psd"}
ZIP_EXT = {".zip"}
SKIP_NAME_RE = re.compile(
    r"(^coupon$|\.url$|\.pdf$|^license$|^readme$|^thumbs\.db$|^\.ds_store$)",
    re.I,
)
SKIP_DIR_NAMES = {"__macosx", "_macosx", ".git", ".godot"}

CATEGORIES = [
    "house", "building", "terrain", "grass", "soil", "path", "water", "shore",
    "tree", "bush", "weed", "flower", "crop", "rock", "log", "stump", "mushroom",
    "fence", "gate", "well", "furniture", "interior", "prop",
    "character", "hero", "npc", "animal", "animation", "effect", "icon", "ui",
    "crystal", "sprite_sheet", "unknown",
]

CATEGORY_PREFIX = {
    "house": "HOUSE", "building": "BUILDING", "terrain": "TERRAIN",
    "grass": "GRASS", "soil": "SOIL", "path": "PATH", "water": "WATER",
    "shore": "SHORE", "tree": "TREE", "bush": "BUSH", "weed": "WEED",
    "flower": "FLOWER", "crop": "CROP", "rock": "ROCK", "log": "LOG",
    "stump": "STUMP", "mushroom": "MUSHROOM", "fence": "FENCE", "gate": "GATE",
    "well": "WELL", "furniture": "FURNITURE", "interior": "INTERIOR",
    "prop": "PROP", "character": "CHARACTER", "hero": "HERO", "npc": "NPC",
    "animal": "ANIMAL", "animation": "ANIM", "effect": "EFFECT", "icon": "ICON",
    "ui": "UI", "crystal": "CRYSTAL", "sprite_sheet": "SHEET", "unknown": "ASSET",
}

# Owner-facing Markdown category pages
MD_CATEGORY_PAGES: dict[str, list[str]] = {
    "houses": ["house", "building"],
    "heroes": ["hero"],
    "characters": ["character", "npc", "animal"],
    "trees": ["tree"],
    "bushes": ["bush"],
    "rocks": ["rock"],
    "weeds": ["weed"],
    "flowers": ["flower", "crop"],
    "logs": ["log"],
    "stumps": ["stump"],
    "mushrooms": ["mushroom"],
    "fences": ["fence", "gate"],
    "terrain": ["terrain", "grass", "soil", "path"],
    "water": ["water", "shore"],
    "props": ["prop", "furniture", "well", "crystal", "effect", "icon", "ui", "interior"],
    "animations": ["animation", "sprite_sheet"],
    "unknown": ["unknown"],
}

CONTACT_SHEET_STEM = {k: k for k in MD_CATEGORY_PAGES}

PREVIEW_MAX = 160
SHEET_CELL = 150
SHEET_COLS = 6
SHEET_ROWS = 8
LABEL_H = 40
CHECKER = (200, 200, 200, 255)
CHECKER2 = (230, 230, 230, 255)

# Pack-specific owner notes (written into pack README)
PACK_EVAL_NOTES: dict[str, dict[str, str]] = {
    "craftpix-main-characters-home": {
        "fit": "CraftPix cottage kit — useful for props/fence reference; not the VS01 primary house.",
        "style_outliers": "Cute fantasy cottage look; giant decorative mushrooms in exterior demos are fantasy_like / oversized for VS01.",
        "oversized": "Giant mushrooms and fairy-scale props — catalogued but rejected for VS01 yard anchors.",
        "vs01": "Do not use as main house. Prefer HOUSE_MAIN_HOUSE_V1. Props may be candidates after scale check.",
    },
    "trees-pixel-art": {
        "fit": "Top-down pixel trees — strong outdoor vegetation candidates for yard borders.",
        "style_outliers": "Seasonal / christmas / burned variants may look thematic; pick deliberately.",
        "oversized": "Very tall canopy sprites need Y-sort + footprint check vs hero (~23px display).",
        "vs01": "Primary tree candidates for north/left overgrown zones after owner ID selection.",
    },
    "bushes-pixel-art": {
        "fit": "Top-down bushes — good fill for overgrown yard edges.",
        "style_outliers": "Bright flower bushes may read more fantasy; prefer muted greens for VS01.",
        "oversized": "Wide bushes can block paths — keep clearances around gate/door.",
        "vs01": "Strong bush candidates for left overgrown + house perimeter.",
    },
    "rocks-and-stones-top-down-pixel-art": {
        "fit": "Top-down rocks/stones — good small decorations and path accents.",
        "style_outliers": "Crystal-looking stones belong under crystal pack instead.",
        "oversized": "Large boulders may dominate the yard; prefer small/medium for VS01.",
        "vs01": "Small rocks for front yard + perimeter; pick IDs after contact sheet review.",
    },
    "crystals-pixel-art": {
        "fit": "Decorative crystals — usually fantasy_like for childhood rural yard.",
        "style_outliers": "Glow/crystal props clash with Russian izba direction.",
        "oversized": "Tall crystal clusters read as fantasy landmarks.",
        "vs01": "Default needs_review / not for VS01 anchors unless owner selects explicitly.",
    },
    "hero": {
        "fit": "PixelLab 8-dir idle + walk GIFs — current player candidate/runtime.",
        "style_outliers": "Source GIFs are large canvas; runtime uses integer nearest PIXEL_DIV.",
        "oversized": "Do not place at native GIF canvas size in world — use prepared runtime frames.",
        "vs01": "Selected for player integration (runtime under assets/characters/player/pixellab_v1/).",
    },
    "houses": {
        "fit": "Approved childhood-home exterior source folder.",
        "style_outliers": "Source PNG may include solid black background — keyed at bake time.",
        "oversized": "Source 1536×1024; runtime uses ÷4 nearest after crop.",
        "vs01": "HOUSE_MAIN_HOUSE_V1 is the selected starting house.",
    },
}


def posix(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def rel_to_root(path: Path) -> str:
    return posix(path.relative_to(ROOT))


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "pack"


def pack_key_for_id(pack_id: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", pack_id.upper()).strip("_")


def should_skip_dir(name: str) -> bool:
    n = name.lower()
    return n in SKIP_DIR_NAMES or n.startswith(".")


def should_skip_file(path: Path) -> bool:
    if path.suffix.lower() == ".import":
        return True
    if path.name.startswith(".") or path.name.startswith("._"):
        return True
    if SKIP_NAME_RE.search(path.stem) or SKIP_NAME_RE.search(path.name):
        return True
    return False


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def content_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 256), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def path_hash4(source_path: str) -> str:
    return hashlib.sha1(source_path.encode("utf-8")).hexdigest()[:4].upper()


def infer_category(pack_id: str, rel_path: str, filename: str) -> str:
    blob = f"{pack_id}/{rel_path}/{filename}".lower()
    rules = [
        ("mushroom", ["mushroom", "mushrooms", "fungus", "toadstool"]),
        ("crystal", ["crystal"]),
        ("hero", ["/hero/", "pixellab", "idle_rotations", "idle_v3_walking"]),
        ("npc", ["npc"]),
        ("well", ["well"]),
        ("tree", ["tree", "trees"]),
        ("bush", ["bush", "bushes", "shrub"]),
        ("rock", ["rock", "stone", "boulder"]),
        ("stump", ["stump"]),
        ("log", ["log", "logs", "fallen"]),
        ("weed", ["weed", "grass_tuft", "reed"]),
        ("flower", ["flower", "flowers"]),
        ("crop", ["crop", "plant"]),
        ("fence", ["fence"]),
        ("gate", ["gate"]),
        ("house", ["house", "home", "roof", "chimney", "main_house"]),
        ("building", ["building", "shed", "barn"]),
        ("interior", ["interior", "walls_floor"]),
        ("furniture", ["furniture", "chair", "table", "bed", "cabinet"]),
        ("animal", ["animal", "cat", "bird", "dog", "cow"]),
        ("character", ["character", "player", "npc"]),
        ("animation", ["_animation", "animation"]),
        ("water", ["water", "pond", "lake", "river"]),
        ("shore", ["shore", "beach"]),
        ("path", ["path", "road", "dirt_path"]),
        ("soil", ["soil", "dirt", "earth"]),
        ("grass", ["grass"]),
        ("terrain", ["terrain", "ground", "tile"]),
        ("effect", ["smoke", "effect", "fx", "particle"]),
        ("ui", ["ui_", "/ui/", "button", "panel"]),
        ("icon", ["icon"]),
        ("prop", ["prop", "barrel", "crate", "box", "scarecrow"]),
    ]
    for cat, keys in rules:
        for k in keys:
            if k in blob:
                return cat
    if pack_id in ("hero",) or pack_id.endswith("/hero") or pack_id == "hero":
        return "hero"
    if pack_id == "houses":
        return "house"
    if "craftpix" in pack_id and "home" in pack_id:
        if "tree" in blob:
            return "tree"
        if "interior" in blob:
            return "interior"
        return "house"
    return "unknown"


def infer_tags(pack_id: str, rel_path: str, category: str, width: int | None, height: int | None) -> list[str]:
    tags = {category}
    blob = f"{pack_id}/{rel_path}".lower()
    if "shadow" in blob:
        tags.add("shadow")
    if "texture_shadow" in blob:
        tags.add("texture_shadow")
    if "no_shadow" in blob:
        tags.add("no_shadow")
    if "autumn" in blob:
        tags.add("autumn")
    if "winter" in blob or "christmas" in blob:
        tags.add("winter")
    if "burned" in blob or "broken" in blob:
        tags.add("damaged")
    if "craftpix" in pack_id or "craftpix" in blob:
        tags.add("craftpix")
    if category in ("tree", "bush", "weed", "flower", "stump", "log", "mushroom"):
        tags.add("vegetation")
    if category == "crystal" or "crystal" in blob:
        tags.add("fantasy_like")
    if category == "mushroom" or "mushroom" in blob:
        tags.update({"fantasy_like", "oversized"})
    if width and height and max(width, height) >= 512 and category in ("prop", "mushroom", "house", "tree"):
        tags.add("oversized")
    if pack_id == "hero":
        tags.update({"pixellab", "player_candidate"})
    if "main_house" in blob:
        tags.update({"vs01", "childhood_home", "old_russian_house"})
    return sorted(tags)


def detect_sprite_sheet(width: int, height: int, path: Path, frame_count: int | None = None) -> dict[str, Any]:
    name = path.name.lower()
    hints = any(k in name for k in ("sheet", "spritesheet", "atlas", "tileset", "animation"))
    large = width >= 256 or height >= 256
    is_sheet = bool(hints or (large and width % 16 == 0 and height % 16 == 0 and (width * height) >= 65536))
    meta: dict[str, Any] = {
        "is_sprite_sheet": is_sheet,
        "probable_tile_size": 16 if is_sheet and width % 16 == 0 and height % 16 == 0 else None,
        "sprite_sheet_needs_review": False,
    }
    if is_sheet and frame_count is None:
        meta["sprite_sheet_needs_review"] = True
        meta["notes_auto"] = "sprite_sheet_needs_review — no reliable TSX/JSON frame grid."
    return meta


def checkerboard(size: tuple[int, int], cell: int = 8) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = CHECKER if ((x // cell) + (y // cell)) % 2 == 0 else CHECKER2
    return img


def _compose_labeled_preview(
    rgba: Image.Image,
    asset_id: str,
    pack_id: str,
    extra_lines: list[str] | None = None,
) -> Image.Image:
    w, h = rgba.size
    scale = min(PREVIEW_MAX / max(w, 1), PREVIEW_MAX / max(h, 1), 1.0)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    scaled = rgba.resize((nw, nh), Image.NEAREST)
    lines = [asset_id, f"{pack_id}", f"{w}×{h}"]
    if extra_lines:
        lines.extend(extra_lines)
    label_h = 14 + 12 * len(lines)
    canvas_w = max(PREVIEW_MAX + 24, nw + 24, 220)
    canvas_h = nh + label_h + 16
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (32, 34, 38, 255))
    board = checkerboard((nw, nh), 8)
    board.paste(scaled, (0, 0), scaled)
    ox = (canvas_w - nw) // 2
    canvas.paste(board, (ox, 8))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, nh + 12, canvas_w, canvas_h], fill=(24, 26, 28, 255))
    draw.multiline_text((6, nh + 14), "\n".join(lines), fill=(235, 235, 230, 255), spacing=2)
    return canvas


def make_preview(src: Path, asset_id: str, pack_id: str, out: Path) -> dict[str, Any]:
    """Build static preview; for GIF also write animated preview + frame sheet when useful."""
    im = Image.open(src)
    ext = src.suffix.lower()
    is_gif = ext == ".gif"
    frame_count = getattr(im, "n_frames", 1) or 1
    durations: list[int] = []
    frames_rgba: list[Image.Image] = []

    if is_gif and frame_count > 1:
        for frame in ImageSequence.Iterator(im):
            fr = frame.convert("RGBA")
            frames_rgba.append(fr.copy())
            durations.append(int(frame.info.get("duration", 100) or 100))
        # first meaningful frame: prefer non-empty alpha content
        first = frames_rgba[0]
        for fr in frames_rgba:
            bbox = fr.split()[-1].getbbox()
            if bbox:
                first = fr
                break
        rgba = first
    else:
        rgba = im.convert("RGBA")
        frame_count = 1
        durations = []

    w, h = rgba.size
    has_alpha = any(px[3] < 255 for px in rgba.getdata())
    extra: list[str] = []
    if is_gif:
        avg_ms = (sum(durations) / len(durations)) if durations else 100
        fps = round(1000.0 / avg_ms, 2) if avg_ms > 0 else None
        extra.append(f"frames={frame_count}" + (f" ~{fps}fps" if fps else ""))

    out.parent.mkdir(parents=True, exist_ok=True)
    canvas = _compose_labeled_preview(rgba, asset_id, pack_id, extra)
    canvas.save(out)

    anim_preview_path = None
    frame_sheet_path = None
    if is_gif and frames_rgba:
        anim_path = out.with_name(out.stem + "_anim.gif")
        # Nearest scale each frame onto checker for transparency readability
        scaled_frames = []
        for fr in frames_rgba:
            scale = min(PREVIEW_MAX / max(fr.width, 1), PREVIEW_MAX / max(fr.height, 1), 1.0)
            nw, nh = max(1, int(round(fr.width * scale))), max(1, int(round(fr.height * scale)))
            s = fr.resize((nw, nh), Image.NEAREST)
            board = checkerboard((nw, nh), 8)
            board.paste(s, (0, 0), s)
            scaled_frames.append(board.convert("P", palette=Image.ADAPTIVE))
        scaled_frames[0].save(
            anim_path,
            save_all=True,
            append_images=scaled_frames[1:],
            duration=durations or 100,
            loop=0,
            optimize=False,
        )
        anim_preview_path = rel_to_root(anim_path)

        # compact contact of frames (cap 24)
        show = frames_rgba[:24]
        cols = min(8, len(show))
        rows = (len(show) + cols - 1) // cols
        cell = 48
        sheet = Image.new("RGBA", (cols * cell + 8, rows * cell + 8), (28, 30, 34, 255))
        for i, fr in enumerate(show):
            r, c = divmod(i, cols)
            scale = min((cell - 4) / fr.width, (cell - 4) / fr.height, 1.0)
            nw, nh = max(1, int(fr.width * scale)), max(1, int(fr.height * scale))
            s = fr.resize((nw, nh), Image.NEAREST)
            board = checkerboard((cell - 4, cell - 4), 6)
            board.paste(s, ((cell - 4 - nw) // 2, (cell - 4 - nh) // 2), s)
            sheet.paste(board, (4 + c * cell, 4 + r * cell))
        fs_path = out.with_name(out.stem + "_frames.png")
        sheet.save(fs_path)
        frame_sheet_path = rel_to_root(fs_path)

    sheet_meta = detect_sprite_sheet(w, h, src, frame_count if is_gif and frame_count > 1 else None)
    return {
        "width": w,
        "height": h,
        "has_alpha": has_alpha,
        "frame_count": frame_count if (is_gif or sheet_meta.get("is_sprite_sheet")) else (frame_count if is_gif else 1),
        "frame_durations": durations or None,
        "is_animated": bool(is_gif and frame_count > 1),
        "anim_preview_path": anim_preview_path,
        "frame_sheet_path": frame_sheet_path,
        "format": ext.lstrip("."),
        **sheet_meta,
    }


def discover_pack_roots() -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    if UPLOAD.exists():
        for child in sorted(UPLOAD.iterdir(), key=lambda p: p.name.lower()):
            if child.name.startswith("."):
                continue
            if child.is_dir() and not should_skip_dir(child.name):
                packs.append({
                    "pack_id": child.name,
                    "slug": slugify(child.name),
                    "root": child,
                    "source_kind": "upload",
                    "source_folder": rel_to_root(child),
                })
            elif child.is_file() and child.suffix.lower() in ZIP_EXT:
                packs.append({
                    "pack_id": child.stem,
                    "slug": slugify(child.stem),
                    "root": None,
                    "source_kind": "upload_zip",
                    "source_folder": rel_to_root(child),
                    "zip_only": True,
                })
    if THIRD_PARTY.exists():
        for vendor in sorted(THIRD_PARTY.iterdir(), key=lambda p: p.name.lower()):
            if not vendor.is_dir() or should_skip_dir(vendor.name):
                continue
            for pack in sorted(vendor.iterdir(), key=lambda p: p.name.lower()):
                if not pack.is_dir() or should_skip_dir(pack.name):
                    continue
                pack_id = f"{vendor.name}-{pack.name}"
                scan_root = pack / "source" if (pack / "source").is_dir() else pack
                packs.append({
                    "pack_id": pack_id,
                    "slug": slugify(pack_id),
                    "root": scan_root,
                    "pack_root": pack,
                    "source_kind": "third_party",
                    "source_folder": rel_to_root(pack),
                })
    return packs


def iter_pack_files(pack_root: Path):
    for path in sorted(pack_root.rglob("*")):
        if not path.is_file():
            continue
        if any(should_skip_dir(p) for p in path.parts):
            continue
        if should_skip_file(path):
            continue
        yield path


def read_pack_license(pack_root: Path | None, source_folder: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "license": "unknown",
        "license_url": None,
        "author": "unknown",
        "source_url": None,
        "license_status": "needs_review",
        "git_storage_allowed": None,
        "commercial_use": None,
        "modification_allowed": None,
        "attribution_required": None,
        "owner_confirmation": None,
    }
    search_roots = []
    if pack_root and pack_root.is_dir():
        search_roots.append(pack_root)
        parent = pack_root.parent if pack_root.name.lower() == "source" else None
        if parent:
            search_roots.append(parent)
    for base in search_roots:
        for name in ("License.txt", "LICENSE.txt", "LICENSE", "license.txt"):
            p = base / name
            if p.exists():
                text = p.read_text(encoding="utf-8", errors="replace").strip()
                info["license_file"] = rel_to_root(p)
                if text.startswith("http"):
                    info["license_url"] = text.splitlines()[0].strip()
                    info["license"] = "see_url"
                else:
                    info["license"] = text[:240]
                break
    folder = source_folder.replace("\\", "/")
    if "main_characters_home" in folder:
        info.update({
            "author": "CraftPix",
            "source_url": "https://craftpix.net/freebies/main-characters-home-free-top-down-pixel-art-asset/",
            "license": "CraftPix freebie terms",
            "license_url": "https://craftpix.net/file-licenses/",
            "license_status": "reviewed",
            "git_storage_allowed": True,
            "commercial_use": True,
            "modification_allowed": True,
            "attribution_required": False,
            "owner_confirmation": "Project owner reports explicit permission to store/publish in this Git repo.",
        })
    elif "craftpix" in folder.lower() or (info.get("license_url") or "").startswith("https://craftpix.net"):
        info.update({
            "author": "CraftPix",
            "license": "CraftPix freebie terms (verify per pack)",
            "license_url": info.get("license_url") or "https://craftpix.net/file-licenses/",
            "license_status": "needs_review",
            "commercial_use": True,
            "modification_allowed": True,
            "attribution_required": False,
        })
    elif folder.startswith("upload/hero"):
        info.update({
            "author": "PixelLab (generated)",
            "license": "project-owned generation — confirm redistribution terms",
            "license_status": "needs_review",
        })
    elif folder.startswith("upload/houses"):
        info.update({
            "author": "project / owner-provided",
            "license": "project asset",
            "license_status": "reviewed",
            "git_storage_allowed": True,
        })
    return info


def assign_asset_id(
    existing_by_path: dict[str, dict],
    used_ids: set[str],
    category: str,
    pack_id: str,
    source_path: str,
    override_id: str | None,
) -> str:
    if override_id:
        used_ids.add(override_id)
        return override_id
    if source_path in existing_by_path:
        aid = existing_by_path[source_path].get("asset_id")
        if aid:
            used_ids.add(aid)
            return aid
    prefix = CATEGORY_PREFIX.get(category, "ASSET")
    pkey = pack_key_for_id(pack_id)
    if len(pkey) > 36:
        pkey = pkey[:36].rstrip("_")
    # Prefer readable name for a few known files
    stem = Path(source_path).stem.upper()
    stem_slug = re.sub(r"[^A-Z0-9]+", "_", stem).strip("_")
    if stem_slug in {"MAIN_HOUSE_V1", "IDLE_ROTATIONS_8DIR"} or len(stem_slug) <= 24:
        nice = f"{prefix}_{pkey}_{stem_slug}" if stem_slug not in pkey else f"{prefix}_{stem_slug}"
        # For house pack keep compact approved style via override; otherwise hash suffix
        pass
    h = path_hash4(source_path)
    base = f"{prefix}_{pkey}_{h}"
    candidate = base
    n = 1
    while candidate in used_ids:
        n += 1
        candidate = f"{base}_{n}"
    used_ids.add(candidate)
    return candidate


def build_contact_sheet(items: list[dict], out_stem_path: Path, title: str) -> list[Path]:
    """Always write numbered pages: <stem>_01.png, _02.png, …"""
    if not items:
        return []
    pages: list[Path] = []
    per_page = SHEET_COLS * SHEET_ROWS
    font = ImageFont.load_default()
    stem = out_stem_path.stem
    # normalize: strip trailing _NN if present
    stem = re.sub(r"_\d{2}$", "", stem)
    suffix = out_stem_path.suffix or ".png"
    parent = out_stem_path.parent

    for page_i in range(0, len(items), per_page):
        chunk = items[page_i: page_i + per_page]
        page_n = page_i // per_page + 1
        rows = (len(chunk) + SHEET_COLS - 1) // SHEET_COLS
        header_h = 28
        W = SHEET_COLS * SHEET_CELL + 16
        H = header_h + rows * (SHEET_CELL + LABEL_H) + 16
        sheet = Image.new("RGBA", (W, H), (28, 30, 34, 255))
        draw = ImageDraw.Draw(sheet)
        page_title = f"{title} ({page_n})"
        draw.text((10, 8), page_title, fill=(240, 240, 235, 255), font=font)
        for idx, asset in enumerate(chunk):
            r, c = divmod(idx, SHEET_COLS)
            x = 8 + c * SHEET_CELL
            y = header_h + 8 + r * (SHEET_CELL + LABEL_H)
            cell = checkerboard((SHEET_CELL - 8, SHEET_CELL - 8 - 4), 8)
            prev = ROOT / asset["preview_path"] if asset.get("preview_path") else None
            if prev and prev.exists():
                pim = Image.open(prev).convert("RGBA")
                pw, ph = pim.size
                img_h = max(1, ph - LABEL_H)
                crop = pim.crop((0, 0, pw, min(img_h + 8, ph)))
                # Prefer image band above dark label
                crop = pim.crop((0, 0, pw, max(1, ph - 36)))
                cw, ch = cell.size
                scale = min(cw / max(crop.width, 1), ch / max(crop.height, 1), 1.0)
                nw, nh = max(1, int(crop.width * scale)), max(1, int(crop.height * scale))
                crop = crop.resize((nw, nh), Image.NEAREST)
                cell.paste(crop, ((cw - nw) // 2, (ch - nh) // 2), crop)
            sheet.paste(cell, (x, y))
            label = f"{asset['asset_id']}\n{asset.get('pack_id', '')}\n{asset.get('width')}×{asset.get('height')}"
            draw.multiline_text((x, y + SHEET_CELL - 10), label, fill=(220, 220, 215, 255), font=font, spacing=1)
        path = parent / f"{stem}_{page_n:02d}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(path)
        pages.append(path)
    return pages


def fingerprint_upload() -> str:
    lines: list[str] = []
    for pack in discover_pack_roots():
        root = pack.get("root")
        if root is None:
            lines.append(f"ZIP|{pack['source_folder']}")
            continue
        for f in iter_pack_files(root):
            if f.suffix.lower() not in IMAGE_EXTS | META_EXTS | ZIP_EXT:
                continue
            st = f.stat()
            lines.append(f"{rel_to_root(f)}|{st.st_size}|{int(st.st_mtime)}")
    blob = "\n".join(sorted(lines)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def md_escape(text: str) -> str:
    return str(text).replace("|", "\\|")


def write_category_md(page_key: str, cats: list[str], assets: list[dict], sheet_rel_paths: list[str]) -> None:
    out = CATEGORIES_DOCS / f"{page_key}.md"
    lines = [
        f"# {page_key.replace('_', ' ').title()}",
        "",
        f"[← Каталог ассетов](../../../../README.md#где-смотреть-ассеты)",
        "",
        f"Categories: {', '.join(f'`{c}`' for c in cats)}",
        "",
        "## Contact sheets",
        "",
    ]
    for rel in sheet_rel_paths:
        # from categories/ -> ../contact_sheets/file
        name = Path(rel).name
        lines.append(f"![contact sheet](../contact_sheets/{name})")
        lines.append("")
    ordered = sorted(
        assets,
        key=lambda a: (1 if "shadow" in a.get("tags", []) else 0, a["asset_id"]),
    )
    lines += [
        "## Assets",
        "",
        "| Asset ID | Preview | Pack | Source | Size | Alpha | Status | Tags | Notes |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for a in ordered:
        tags = ", ".join(a.get("tags") or [])
        prev = a.get("preview_path")
        if prev:
            # categories/ -> ../previews/...
            prev_rel = posix(Path(prev).as_posix().replace("docs/assets/catalog/", "../"))
            preview_cell = f"![p]({prev_rel})"
        else:
            preview_cell = "—"
        lines.append(
            "| `{id}` | {preview} | {pack} | `{src}` | {w}×{h} | {alpha} | {status} | {tags} | {notes} |".format(
                id=a["asset_id"],
                preview=preview_cell,
                pack=md_escape(a.get("pack_id", "")),
                src=md_escape(a.get("source_path", "")),
                w=a.get("width"),
                h=a.get("height"),
                alpha=a.get("has_alpha"),
                status=a.get("status"),
                tags=md_escape(tags),
                notes=md_escape(a.get("notes") or ""),
            )
        )
    lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def write_pack_md(pack: dict, assets: list[dict], license_info: dict, has_local_sheet: bool) -> None:
    slug = pack["slug"]
    out_dir = PACK_DOCS / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    cats = sorted({a["category"] for a in assets}) if assets else []
    sizes = sorted({(a.get("width"), a.get("height")) for a in assets if a.get("width")})
    sheets = [a for a in assets if a.get("is_sprite_sheet")]
    gifs = [a for a in assets if a.get("is_animated") or str(a.get("format", "")).lower() == "gif"]
    tmx = pack.get("tmx_files") or []
    tsx = pack.get("tsx_files") or []
    tile_sizes = sorted({a.get("probable_tile_size") for a in assets if a.get("probable_tile_size")})
    oversized = [a for a in assets if "oversized" in (a.get("tags") or [])]
    fantasy = [a for a in assets if "fantasy_like" in (a.get("tags") or [])]
    vs01 = [a for a in assets if a.get("status") in ("selected", "runtime", "candidate") or "vs01" in (a.get("tags") or [])]
    eval_notes = PACK_EVAL_NOTES.get(slug) or PACK_EVAL_NOTES.get(pack["pack_id"]) or {}

    lines = [
        f"# Pack: {pack['pack_id']}",
        "",
        f"[← Каталог ассетов](../../../../../README.md#где-смотреть-ассеты)",
        "",
        f"- **Slug / pack_id:** `{slug}` / `{pack['pack_id']}`",
        f"- **Source folder:** `{pack['source_folder']}`",
        f"- **Source kind:** {pack.get('source_kind')}",
        f"- **Author:** {license_info.get('author')}",
        f"- **License:** {license_info.get('license')}",
        f"- **License URL:** {license_info.get('license_url')}",
        f"- **License status:** `{license_info.get('license_status')}`",
        f"- **Files catalogued (images+meta notes):** {len(assets)}",
        f"- **Categories:** {', '.join(cats) if cats else '—'}",
        f"- **Distinct image sizes:** {', '.join(f'{w}×{h}' for w, h in sizes[:24])}{'…' if len(sizes) > 24 else ''}",
        f"- **GIF / animated:** {len(gifs)}",
        f"- **Sprite sheets:** {len(sheets)}",
        f"- **TMX:** {', '.join(f'`{Path(t).name}`' for t in tmx) if tmx else '—'}",
        f"- **TSX:** {', '.join(f'`{Path(t).name}`' for t in tsx) if tsx else '—'}",
        f"- **Tile size (probable):** {', '.join(str(t) for t in tile_sizes) if tile_sizes else '—'}",
        "",
        "## Contact sheet",
        "",
    ]
    if has_local_sheet:
        lines.append("![pack contact sheet](contact_sheet_01.png)")
    else:
        lines.append("_No images yet (zip-only or empty)._")
    lines += [
        "",
        "## Fit for this project",
        "",
        f"- {eval_notes.get('fit', 'Top-down pixel pack under review.')}",
        "",
        "## Style outliers",
        "",
        f"- {eval_notes.get('style_outliers', 'Review contact sheet for tone mismatches.')}",
        f"- Fantasy-tagged assets: **{len(fantasy)}**",
        "",
        "## Oversized / scale risks",
        "",
        f"- {eval_notes.get('oversized', 'Measure against hero display height before placing.')}",
        f"- Tagged oversized: **{len(oversized)}**",
        "",
        "## VS01 candidates",
        "",
        f"- {eval_notes.get('vs01', 'No automatic selection — pick Asset IDs explicitly.')}",
        f"- Already selected/runtime/candidate in this pack: **{len(vs01)}**",
        "",
        "## Asset IDs (sample)",
        "",
    ]
    for a in assets[:40]:
        lines.append(f"- `{a['asset_id']}` — `{a['source_path']}` [{a.get('status')}]")
    if len(assets) > 40:
        lines.append(f"- … +{len(assets) - 40} more (see category pages / `asset_catalog.json`)")
    lines.append("")
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


ASSET_CATALOG_BEGIN = "<!-- ASSET_CATALOG_BEGIN -->"
ASSET_CATALOG_END = "<!-- ASSET_CATALOG_END -->"


def _asset_catalog_section_for_root(stats: dict, pack_slugs: list[str]) -> str:
    """Markdown block for root README (links relative to repo root)."""
    lines = [
        "# Где смотреть ассеты",
        "",
        "1. Все категории: [docs/assets/catalog/categories/](docs/assets/catalog/categories/)",
        "",
        "2. Все наборы: [docs/assets/catalog/packs/](docs/assets/catalog/packs/)",
        "",
        "3. Большие визуальные таблицы: [docs/assets/catalog/contact_sheets/](docs/assets/catalog/contact_sheets/)",
        "",
        "4. Выбор ассетов для игровых зон: [docs/assets/AREA_ASSET_SELECTIONS.md](docs/assets/AREA_ASSET_SELECTIONS.md)",
        "",
        "5. Каталог внутри Godot: `res://scenes/debug/asset_gallery.tscn` (F6)",
        "",
        "6. Машинный реестр: [`data/assets/asset_catalog.json`](data/assets/asset_catalog.json)",
        "",
        "---",
        "",
        "**Инструкция:** откройте категорию или набор, найдите нужную картинку и сообщите Cursor её **Asset ID**.",
        "",
        "Пример:",
        "",
        "> Для северной границы `yard_main` используй `TREE_…`, `BUSH_…` и `ROCK_…`.",
        "> `HOUSE_MAIN_HOUSE_V1` — основной дом. Гигантские грибы из CraftPix не использовать.",
        "",
        "## Обновить каталог после добавления файлов в `upload/`",
        "",
        "```bash",
        "python tools/build_asset_catalog.py",
        "python tools/build_asset_catalog.py --check",
        "```",
        "",
        "`res://upload/` — **постоянный входящий склад**. Не удалять, не очищать, не переименовывать, не переносить целиком. Оригиналы не перезаписываются каталогом.",
        "",
        "## Stats",
        "",
        f"- Packs (unpacked): **{stats['packs']}**",
        f"- Zip-only inbox entries: **{stats.get('zip_only', 0)}**",
        f"- Images: **{stats['images']}**",
        f"- GIFs / animated: **{stats.get('gifs', 0)}**",
        f"- Sprite sheets: **{stats.get('sheets', 0)}**",
        f"- Categories present: {', '.join(stats['categories'])}",
        "",
        "## Categories",
        "",
    ]
    for key in MD_CATEGORY_PAGES:
        lines.append(f"- [{key}](docs/assets/catalog/categories/{key}.md)")
    lines += ["", "## Packs", ""]
    for slug in pack_slugs:
        lines.append(f"- [{slug}](docs/assets/catalog/packs/{slug}/README.md)")
    lines += [
        "",
        "## Also",
        "",
        "- Подробный индекс каталога: [docs/assets/README.md](docs/assets/README.md)",
        "- Overrides: `data/assets/asset_catalog_overrides.json`",
        "",
    ]
    return "\n".join(lines)


def write_start_here(stats: dict, pack_slugs: list[str]) -> None:
    """Primary owner entry lives in root README; START_HERE.md is a redirect stub."""
    section = _asset_catalog_section_for_root(stats, pack_slugs)
    readme_path = ROOT / "README.md"
    block = f"{ASSET_CATALOG_BEGIN}\n{section}\n{ASSET_CATALOG_END}"
    if readme_path.exists():
        text = readme_path.read_text(encoding="utf-8")
        if ASSET_CATALOG_BEGIN in text and ASSET_CATALOG_END in text:
            before, rest = text.split(ASSET_CATALOG_BEGIN, 1)
            _, after = rest.split(ASSET_CATALOG_END, 1)
            text = before + block + after
        else:
            text = text.rstrip() + "\n\n" + block + "\n"
        readme_path.write_text(text, encoding="utf-8")
    else:
        readme_path.write_text(block + "\n", encoding="utf-8")

    (DOCS_ASSETS / "START_HERE.md").write_text(
        "\n".join([
            "# Где смотреть ассеты",
            "",
            "Точка входа перенесена в корневой README проекта:",
            "",
            "**[README.md — Где смотреть ассеты](../../README.md#где-смотреть-ассеты)**",
            "",
            "Этот файл оставлен как короткая ссылка для старых закладок.",
            "",
        ]),
        encoding="utf-8",
    )


def write_main_readme(stats: dict, pack_slugs: list[str]) -> None:
    lines = [
        "# Asset Catalog",
        "",
        "**Primary entry:** [корневой README — Где смотреть ассеты](../../README.md#где-смотреть-ассеты)",
        "",
        "Owner-facing catalog of incoming and imported visual assets.",
        "",
        "## Update",
        "",
        "```bash",
        "python tools/build_asset_catalog.py",
        "python tools/build_asset_catalog.py --check",
        "```",
        "",
        f"- Packs: **{stats['packs']}** (+{stats.get('zip_only', 0)} zip-only)",
        f"- Images: **{stats['images']}**",
        "",
        "## Categories",
        "",
    ]
    for key in MD_CATEGORY_PAGES:
        lines.append(f"- [{key}](catalog/categories/{key}.md)")
    lines += ["", "## Packs", ""]
    for slug in pack_slugs:
        lines.append(f"- [{slug}](catalog/packs/{slug}/README.md)")
    lines.append("")
    (DOCS_ASSETS / "README.md").write_text("\n".join(lines), encoding="utf-8")


def ensure_seed_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_ASSETS.mkdir(parents=True, exist_ok=True)

    # Merge-required overrides without wiping manual entries
    overrides = load_json(OVERRIDES_JSON, {})
    if not isinstance(overrides, dict):
        overrides = {}
    overrides.setdefault(
        "_comment",
        "Manual overrides keyed by source_path (posix, relative to repo root).",
    )
    required = {
        "upload/houses/main_house_v1.png": {
            "asset_id": "HOUSE_MAIN_HOUSE_V1",
            "category": "house",
            "status": "selected",
            "tags": ["vs01", "childhood_home", "old_russian_house", "house"],
            "notes": "Утверждённый стартовый дом VS01.",
            "license_status": "reviewed",
        },
        "upload/hero/Idle_rotations_8dir.gif": {
            "asset_id": "HERO_PIXEL_LAB_IDLE_8DIR",
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "idle", "8dir", "vs01"],
            "notes": "PixelLab idle 8 directions — runtime frames under assets/characters/player/pixellab_v1/.",
        },
        "upload/hero/Idle_v3_walking_south.gif": {
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "walk", "8dir", "vs01"],
            "notes": "PixelLab walk south — part of 8-dir set.",
        },
        "upload/hero/Idle_v3_walking_north.gif": {
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "walk", "8dir", "vs01"],
        },
        "upload/hero/Idle_v3_walking_east.gif": {
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "walk", "8dir", "vs01"],
        },
        "upload/hero/Idle_v3_walking_west.gif": {
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "walk", "8dir", "vs01"],
        },
        "upload/hero/Idle_v3_walking_north-east.gif": {
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "walk", "8dir", "vs01"],
        },
        "upload/hero/Idle_v3_walking_north-west.gif": {
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "walk", "8dir", "vs01"],
        },
        "upload/hero/Idle_v3_walking_south-east.gif": {
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "walk", "8dir", "vs01"],
        },
        "upload/hero/Idle_v3_walking_south-west.gif": {
            "category": "hero",
            "status": "runtime",
            "tags": ["pixellab", "hero", "walk", "8dir", "vs01"],
        },
    }
    for path, ov in required.items():
        cur = overrides.get(path)
        if not isinstance(cur, dict):
            overrides[path] = dict(ov)
        else:
            # Ensure critical keys exist; do not wipe extra manual fields
            for k, v in ov.items():
                if k not in cur:
                    cur[k] = v
            overrides[path] = cur
    save_json(OVERRIDES_JSON, overrides)

    area = {
        "vs01_childhood_home_yard": {
            "main_house": {"selected": ["HOUSE_MAIN_HOUSE_V1"], "candidates": [], "rejected": []},
            "hero": {
                "selected": ["HERO_PIXEL_LAB_IDLE_8DIR"],
                "runtime_note": "Full 8-dir walk set from upload/hero/ is integrated as runtime candidate.",
            },
            "entrance": {"gate": [], "fence": [], "path": [], "small_decoration": []},
            "front_yard": {"grass": [], "weeds": [], "small_rocks": [], "flowers": []},
            "left_overgrown_zone": {"trees": [], "bushes": [], "logs": [], "stumps": [], "rocks": []},
            "right_utility_zone": {"well": [], "woodpile": [], "crates": [], "tools": [], "bushes": []},
            "house_perimeter": {"foundation_decoration": [], "low_weeds": [], "small_stones": []},
            "rejected_for_vs01": [
                "oversized mushrooms",
                "fantasy props",
                "objects inconsistent with hero scale",
            ],
        },
        "future_village_road": {},
        "shed_area": {},
        "pond_area": {},
    }
    # Preserve any extra keys already present
    existing_area = load_json(AREA_JSON, {})
    if isinstance(existing_area, dict):
        for k, v in existing_area.items():
            if k not in area:
                area[k] = v
    save_json(AREA_JSON, area)

    area_md = DOCS_ASSETS / "AREA_ASSET_SELECTIONS.md"
    area_md.write_text(
        """# Area Asset Selections

Owner decisions for concrete game areas. Use **Asset IDs** only.

See also: [корневой README — каталог](../../README.md#где-смотреть-ассеты) · machine: `data/assets/area_asset_selections.json`

## VS01 / childhood_home_yard

### Main house
Selected:
- HOUSE_MAIN_HOUSE_V1

### Hero
Selected / runtime:
- HERO_PIXEL_LAB_IDLE_8DIR
- (walk 8-dir set from `upload/hero/` — same PixelLab hero)

### Entrance
Gate:
Fence:
Path:
Small decoration:

### Front yard
Grass:
Weeds:
Small rocks:
Flowers:

### Left overgrown zone
Trees:
Bushes:
Logs:
Stumps:
Rocks:

### Right utility zone
Well:
Woodpile:
Crates:
Tools:
Bushes:

### House perimeter
Foundation decoration:
Low weeds:
Small stones:

### Rejected for VS01
- oversized mushrooms
- fantasy props
- objects inconsistent with hero scale

## Future village road

## Shed area

## Pond area
""",
        encoding="utf-8",
    )


def apply_craftpix_mushroom_policy(asset: dict) -> None:
    """Tag CraftPix fairy mushrooms / fantasy props when detectable; keep files."""
    blob = f"{asset.get('source_path', '')} {asset.get('pack_id', '')}".lower()
    tags = set(asset.get("tags") or [])
    if "mushroom" in blob or asset.get("category") == "mushroom":
        tags.update({"oversized", "fantasy_like", "mushroom"})
        if asset.get("status") not in ("selected", "runtime", "rejected"):
            asset["status"] = "rejected"
        if not asset.get("notes"):
            asset["notes"] = "CraftPix giant/fantasy mushroom — catalogued, not for VS01."
    # exterior sheets often contain fairy props — mark needs_review for VS01
    if "main_characters_home" in blob and asset.get("category") in ("house", "prop", "tree"):
        if "exterior" in blob or "trees_animation" in blob:
            tags.add("fantasy_like")
            if asset.get("status") == "available":
                asset["status"] = "needs_review"
                if not asset.get("notes"):
                    asset["notes"] = "CraftPix home pack — review scale/style before VS01 use."
    asset["tags"] = sorted(tags)


def run_build() -> int:
    ensure_seed_files()
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    CONTACT.mkdir(parents=True, exist_ok=True)
    PACK_DOCS.mkdir(parents=True, exist_ok=True)
    CATEGORIES_DOCS.mkdir(parents=True, exist_ok=True)

    existing = load_json(CATALOG_JSON, {"version": 1, "assets": []})
    existing_assets = existing.get("assets", [])
    by_path = {a["source_path"]: a for a in existing_assets if a.get("source_path")}
    used_ids = {a["asset_id"] for a in existing_assets if a.get("asset_id")}

    overrides_raw = load_json(OVERRIDES_JSON, {})
    overrides = {
        k: v for k, v in overrides_raw.items()
        if not str(k).startswith("_") and isinstance(v, dict)
    }

    packs_meta: list[dict] = []
    new_assets: list[dict] = []
    seen_paths: set[str] = set()

    for pack in discover_pack_roots():
        lic = read_pack_license(
            pack.get("pack_root") or pack.get("root"),
            pack["source_folder"],
        )
        pack_rec = {
            "pack_id": pack["pack_id"],
            "slug": pack["slug"],
            "source_folder": pack["source_folder"],
            "source_kind": pack["source_kind"],
            **lic,
            "tmx_files": [],
            "tsx_files": [],
            "json_files": [],
            "zip_files": [],
            "asset_count": 0,
            "categories": [],
        }
        if pack.get("zip_only") or pack.get("root") is None:
            pack_rec["zip_files"].append(pack["source_folder"])
            packs_meta.append(pack_rec)
            write_pack_md(pack, [], lic, False)
            continue

        root: Path = pack["root"]
        pack_assets: list[dict] = []
        for f in iter_pack_files(root):
            rel_src = rel_to_root(f)
            ext = f.suffix.lower()
            if ext == ".tmx":
                pack_rec["tmx_files"].append(rel_src)
                continue
            if ext == ".tsx":
                pack_rec["tsx_files"].append(rel_src)
                continue
            if ext == ".json":
                pack_rec["json_files"].append(rel_src)
                continue
            if ext == ".zip":
                pack_rec["zip_files"].append(rel_src)
                continue
            if ext == ".psd":
                source_path = rel_src
                seen_paths.add(source_path)
                ov = overrides.get(source_path, {})
                category = ov.get("category") or infer_category(pack["pack_id"], rel_src, f.name)
                asset_id = assign_asset_id(
                    by_path, used_ids, category, pack["pack_id"], source_path, ov.get("asset_id"),
                )
                prev = by_path.get(source_path, {})
                st = f.stat()
                asset = {
                    "asset_id": asset_id,
                    "pack_id": pack["pack_id"],
                    "category": category,
                    "source_path": source_path,
                    "filename": f.name,
                    "width": None,
                    "height": None,
                    "format": "psd",
                    "has_alpha": None,
                    "frame_count": None,
                    "frame_durations": None,
                    "is_animated": False,
                    "is_sprite_sheet": False,
                    "probable_tile_size": None,
                    "preview_path": None,
                    "contact_sheet_path": None,
                    "runtime_path": prev.get("runtime_path"),
                    "status": ov.get("status") or prev.get("status") or "available",
                    "tags": ov.get("tags") or infer_tags(pack["pack_id"], rel_src, category, None, None) + ["psd"],
                    "license_status": ov.get("license_status") or lic.get("license_status", "needs_review"),
                    "notes": ov.get("notes") or prev.get("notes") or "PSD source — listed, not rasterized.",
                    "content_hash": content_hash(f),
                    "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                    "missing": False,
                }
                apply_craftpix_mushroom_policy(asset)
                pack_assets.append(asset)
                new_assets.append(asset)
                continue
            if ext not in IMAGE_EXTS:
                continue

            source_path = rel_src
            seen_paths.add(source_path)
            ov = overrides.get(source_path, {})
            category = ov.get("category") or infer_category(pack["pack_id"], rel_src, f.name)
            asset_id = assign_asset_id(
                by_path, used_ids, category, pack["pack_id"], source_path, ov.get("asset_id"),
            )
            preview_rel = f"docs/assets/catalog/previews/{pack['slug']}/{asset_id}.png"
            preview_abs = ROOT / preview_rel
            try:
                meta = make_preview(f, asset_id, pack["pack_id"], preview_abs)
            except Exception as exc:  # noqa: BLE001
                print(f"WARN preview failed {source_path}: {exc}", file=sys.stderr)
                meta = {
                    "width": None, "height": None, "has_alpha": None,
                    "is_sprite_sheet": False, "frame_count": None,
                    "frame_durations": None, "is_animated": False,
                    "probable_tile_size": None, "format": ext.lstrip("."),
                }
                preview_rel = None

            prev = by_path.get(source_path, {})
            status = ov.get("status") or prev.get("status") or "available"
            notes = ov.get("notes") if "notes" in ov else (prev.get("notes") or "")
            if meta.get("notes_auto") and not notes:
                notes = meta["notes_auto"]
            tags = ov.get("tags") or infer_tags(
                pack["pack_id"], rel_src, category, meta.get("width"), meta.get("height"),
            )
            if meta.get("sprite_sheet_needs_review"):
                tags = sorted(set(tags) | {"sprite_sheet_needs_review"})
            st = f.stat()
            # runtime path for approved house / hero
            runtime_path = prev.get("runtime_path")
            if asset_id == "HOUSE_MAIN_HOUSE_V1":
                runtime_path = "assets/art/outdoor/yard_vs01/main_house_v1.png"
            if pack["pack_id"] == "hero":
                runtime_path = runtime_path or "assets/characters/player/pixellab_v1/"

            asset = {
                "asset_id": asset_id,
                "pack_id": pack["pack_id"],
                "category": category,
                "source_path": source_path,
                "filename": f.name,
                "width": meta.get("width"),
                "height": meta.get("height"),
                "format": meta.get("format") or ext.lstrip("."),
                "has_alpha": meta.get("has_alpha"),
                "frame_count": meta.get("frame_count"),
                "frame_durations": meta.get("frame_durations"),
                "is_animated": meta.get("is_animated", False),
                "is_sprite_sheet": meta.get("is_sprite_sheet", False),
                "probable_tile_size": meta.get("probable_tile_size"),
                "preview_path": preview_rel,
                "anim_preview_path": meta.get("anim_preview_path"),
                "frame_sheet_path": meta.get("frame_sheet_path"),
                "contact_sheet_path": None,
                "runtime_path": runtime_path,
                "status": status,
                "tags": tags,
                "license_status": ov.get("license_status") or lic.get("license_status", "needs_review"),
                "notes": notes,
                "content_hash": content_hash(f),
                "modified_at": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                "missing": False,
            }
            apply_craftpix_mushroom_policy(asset)
            pack_assets.append(asset)
            new_assets.append(asset)

        pack_rec["asset_count"] = len(pack_assets)
        pack_rec["categories"] = sorted({a["category"] for a in pack_assets})
        packs_meta.append(pack_rec)

        visual = [a for a in pack_assets if a.get("preview_path")]
        visual.sort(key=lambda a: (1 if "shadow" in a.get("tags", []) else 0, a["asset_id"]))
        pack_sheet = PACK_DOCS / pack["slug"] / "contact_sheet.png"
        # remove old unnumbered sheet
        for old in (PACK_DOCS / pack["slug"]).glob("contact_sheet*.png"):
            old.unlink()
        pages = build_contact_sheet(visual[: SHEET_COLS * SHEET_ROWS], pack_sheet, pack["pack_id"])
        write_pack_md(pack, pack_assets, lic, bool(pages))

    # Preserve missing assets (never silent-delete)
    for path, old in by_path.items():
        if path not in seen_paths:
            missing = dict(old)
            missing["status"] = "missing"
            missing["missing"] = True
            note = missing.get("notes") or ""
            flag = "File missing from scan roots (kept for stable Asset ID)."
            if flag not in note:
                missing["notes"] = (note + (" | " if note else "") + flag)
            # moved_candidate: same filename elsewhere?
            fname = Path(path).name
            candidates = [a["source_path"] for a in new_assets if Path(a["source_path"]).name == fname]
            if candidates:
                missing["moved_candidate"] = candidates[0]
                missing["notes"] += f" Possible move: {candidates[0]}"
            new_assets.append(missing)

    new_assets.sort(key=lambda a: a["asset_id"])
    catalog = {
        "version": 2,
        "generated": date.today().isoformat(),
        "scan_roots": ["upload/", "assets/third_party/"],
        "categories": CATEGORIES,
        "assets": new_assets,
    }
    save_json(CATALOG_JSON, catalog)
    save_json(PACKS_JSON, {"version": 1, "packs": packs_meta})

    by_cat: dict[str, list] = defaultdict(list)
    for a in new_assets:
        if a.get("status") == "missing" or a.get("missing"):
            continue
        by_cat[a["category"]].append(a)

    # Clear old category sheets then rebuild numbered
    for old in CONTACT.glob("*.png"):
        old.unlink()

    # Remove legacy category md at catalog root
    for legacy in CATALOG_DOCS.glob("*.md"):
        legacy.unlink()

    for page_key, cats in MD_CATEGORY_PAGES.items():
        items: list[dict] = []
        for c in cats:
            items.extend(by_cat.get(c, []))
        items = [a for a in items if a.get("preview_path")]
        items.sort(key=lambda a: (1 if "shadow" in a.get("tags", []) else 0, a["asset_id"]))
        sheet_base = CONTACT / f"{CONTACT_SHEET_STEM[page_key]}.png"
        pages = build_contact_sheet(items, sheet_base, page_key)
        for a in items:
            if pages:
                a["contact_sheet_path"] = rel_to_root(pages[0])
        rel_for_md = [rel_to_root(p) for p in pages]
        write_category_md(page_key, cats, items, rel_for_md)

    # rewrite catalog with contact_sheet_path updates
    save_json(CATALOG_JSON, catalog)

    unpacked = [p for p in packs_meta if p.get("source_kind") != "upload_zip"]
    zip_only = [p for p in packs_meta if p.get("source_kind") == "upload_zip"]
    live = [a for a in new_assets if not a.get("missing") and a.get("status") != "missing"]
    cats_present = sorted({a["category"] for a in live})
    stats = {
        "packs": len(unpacked),
        "zip_only": len(zip_only),
        "images": len([a for a in live if a.get("width")]),
        "gifs": len([a for a in live if a.get("is_animated") or a.get("format") == "gif"]),
        "sheets": len([a for a in live if a.get("is_sprite_sheet")]),
        "categories": cats_present,
    }
    write_start_here(stats, [p["slug"] for p in unpacked])
    write_main_readme(stats, [p["slug"] for p in unpacked])

    fp = fingerprint_upload()
    save_json(FINGERPRINT_JSON, {
        "sha256": fp,
        "generated": date.today().isoformat(),
        "image_count": stats["images"],
        "pack_count": stats["packs"],
        "zip_only_count": stats["zip_only"],
        "gif_count": stats["gifs"],
        "sprite_sheet_count": stats["sheets"],
    })

    print(
        f"Catalog OK: {stats['images']} images, {stats['gifs']} gif, "
        f"{stats['sheets']} sheets, {stats['packs']} packs (+{stats['zip_only']} zip-only), "
        f"categories={cats_present}"
    )
    return 0


def run_check() -> int:
    if not FINGERPRINT_JSON.exists() or not CATALOG_JSON.exists():
        print("Catalog missing — run: python tools/build_asset_catalog.py", file=sys.stderr)
        return 1
    recorded = load_json(FINGERPRINT_JSON, {})
    current = fingerprint_upload()
    if recorded.get("sha256") != current:
        print("Catalog out of date: upload/third_party content changed.", file=sys.stderr)
        print("Run: python tools/build_asset_catalog.py", file=sys.stderr)
        return 1
    print("Catalog fingerprint OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build persistent visual asset catalog")
    parser.add_argument("--check", action="store_true", help="Fail if catalog is stale vs upload")
    args = parser.parse_args()
    if args.check:
        return run_check()
    return run_build()


if __name__ == "__main__":
    raise SystemExit(main())
