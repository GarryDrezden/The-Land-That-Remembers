#!/usr/bin/env python3
"""
Incremental visual asset catalog for The Land That Remembers.

Scans permanent INBOX `upload/` (+ already-imported `assets/third_party/`)
and regenerates:
  - data/assets/asset_catalog.json
  - docs/assets/catalog/previews/
  - docs/assets/catalog/contact_sheets/
  - docs/assets/catalog/*.md
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
from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

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
PREVIEWS = CATALOG_DOCS / "previews"
CONTACT = CATALOG_DOCS / "contact_sheets"
PACK_DOCS = CATALOG_DOCS / "packs"

IMAGE_EXTS = {".png", ".webp", ".jpg", ".jpeg", ".gif"}
META_EXTS = {".tmx", ".tsx", ".json", ".psd"}
SKIP_NAME_RE = re.compile(
    r"(^coupon$|\.url$|\.pdf$|^license$|^readme$|^thumbs\.db$|^\.ds_store$)",
    re.I,
)
SKIP_DIR_NAMES = {"__macosx", "_macosx", ".git", ".godot"}

CATEGORIES = [
    "terrain", "grass", "soil", "path", "water", "shore",
    "tree", "bush", "weed", "flower", "crop",
    "rock", "log", "stump", "fence", "gate",
    "house", "building", "interior", "furniture", "prop",
    "character", "animal", "effect", "icon", "ui", "crystal", "unknown",
]

CATEGORY_PREFIX = {
    "terrain": "TERRAIN", "grass": "GRASS", "soil": "SOIL", "path": "PATH",
    "water": "WATER", "shore": "SHORE", "tree": "TREE", "bush": "BUSH",
    "weed": "WEED", "flower": "FLOWER", "crop": "CROP", "rock": "ROCK",
    "log": "LOG", "stump": "STUMP", "fence": "FENCE", "gate": "GATE",
    "house": "HOUSE", "building": "BUILDING", "interior": "INTERIOR",
    "furniture": "FURNITURE", "prop": "PROP", "character": "CHARACTER",
    "animal": "ANIMAL", "effect": "EFFECT", "icon": "ICON", "ui": "UI",
    "crystal": "CRYSTAL", "unknown": "ASSET",
}

# Markdown category pages (group some categories together for owner UX)
MD_CATEGORY_PAGES = {
    "trees": ["tree", "stump", "log"],
    "bushes": ["bush", "weed", "flower"],
    "rocks": ["rock"],
    "terrain": ["terrain", "grass", "soil", "path"],
    "houses": ["house", "building", "fence", "gate"],
    "props": ["prop", "furniture", "crystal", "crop", "effect", "icon", "ui"],
    "characters": ["character", "animal"],
    "water": ["water", "shore"],
    "unknown": ["unknown", "interior"],
}

CONTACT_SHEET_NAME = {
    "trees": "trees",
    "bushes": "bushes",
    "rocks": "rocks",
    "terrain": "terrain",
    "houses": "houses",
    "props": "props",
    "characters": "characters",
    "water": "water",
    "unknown": "unknown",
}

PREVIEW_MAX = 128
SHEET_CELL = 150
SHEET_COLS = 6
SHEET_ROWS = 8
LABEL_H = 36
CHECKER = (200, 200, 200, 255)
CHECKER2 = (230, 230, 230, 255)


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
    return name.lower() in SKIP_DIR_NAMES


def should_skip_file(path: Path) -> bool:
    stem = path.stem
    if SKIP_NAME_RE.search(stem) or SKIP_NAME_RE.search(path.name):
        return True
    if path.name.startswith("._"):
        return True
    return False


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def infer_category(pack_id: str, rel_path: str, filename: str) -> str:
    blob = f"{pack_id}/{rel_path}/{filename}".lower()
    rules = [
        ("crystal", ["crystal"]),
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
        ("house", ["house", "home", "roof", "chimney"]),
        ("building", ["building", "shed", "barn", "well"]),
        ("interior", ["interior", "walls_floor"]),
        ("furniture", ["furniture", "chair", "table", "bed", "cabinet"]),
        ("character", ["character", "player", "hero", "npc"]),
        ("animal", ["animal", "cat", "bird", "dog", "cow"]),
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
    if "craftpix" in pack_id and "home" in pack_id:
        if "tree" in blob:
            return "tree"
        if "interior" in blob:
            return "interior"
        return "house"
    return "unknown"


def infer_tags(pack_id: str, rel_path: str, category: str) -> list[str]:
    tags = {"outdoor", category}
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
    if pack_id.startswith("craftpix") or "craftpix" in pack_id:
        tags.add("craftpix")
    if category in ("tree", "bush", "weed", "flower", "stump", "log"):
        tags.add("vegetation")
    return sorted(tags)


def detect_sprite_sheet(width: int, height: int, path: Path) -> dict[str, Any]:
    """Heuristic only when filename suggests a sheet; do not invent frame grids."""
    name = path.name.lower()
    hints = any(k in name for k in ("sheet", "spritesheet", "atlas", "tileset", "animation"))
    large = width >= 256 or height >= 256
    is_sheet = hints or (large and width % 16 == 0 and height % 16 == 0 and (width * height) >= 65536)
    meta: dict[str, Any] = {
        "is_sprite_sheet": bool(is_sheet),
        "frame_count": None,
        "tile_size": 16 if is_sheet and width % 16 == 0 and height % 16 == 0 else None,
    }
    # Reliable grid only if exact 16 and looks like tileset atlas (not guessing frames).
    if meta["tile_size"] == 16 and is_sheet:
        meta["notes_auto"] = "Possible 16px atlas; frame groups not inferred without TSX/JSON."
    return meta


def checkerboard(size: tuple[int, int], cell: int = 8) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[x, y] = CHECKER if ((x // cell) + (y // cell)) % 2 == 0 else CHECKER2
    return img


def make_preview(src: Path, asset_id: str, out: Path) -> dict[str, Any]:
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    has_alpha = im.mode == "RGBA" and any(px[3] < 255 for px in im.getdata())
    scale = min(PREVIEW_MAX / max(w, 1), PREVIEW_MAX / max(h, 1), 1.0)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    scaled = im.resize((nw, nh), Image.NEAREST)
    canvas_w = max(PREVIEW_MAX + 16, nw + 16)
    canvas_h = nh + LABEL_H + 16
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (32, 34, 38, 255))
    board = checkerboard((nw, nh), 8)
    board.paste(scaled, (0, 0), scaled)
    ox = (canvas_w - nw) // 2
    canvas.paste(board, (ox, 8))
    draw = ImageDraw.Draw(canvas)
    label = f"{asset_id}\n{w}×{h}"
    draw.rectangle([0, nh + 12, canvas_w, canvas_h], fill=(24, 26, 28, 255))
    draw.multiline_text((6, nh + 14), label, fill=(235, 235, 230, 255), spacing=2)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    sheet_meta = detect_sprite_sheet(w, h, src)
    return {
        "width": w,
        "height": h,
        "has_alpha": has_alpha,
        **sheet_meta,
    }


def discover_pack_roots() -> list[dict[str, Any]]:
    packs: list[dict[str, Any]] = []
    if UPLOAD.exists():
        for child in sorted(UPLOAD.iterdir()):
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
            elif child.is_file() and child.suffix.lower() == ".zip":
                packs.append({
                    "pack_id": child.stem,
                    "slug": slugify(child.stem),
                    "root": None,
                    "source_kind": "upload_zip",
                    "source_folder": rel_to_root(child),
                    "zip_only": True,
                })
    # Already-imported third_party packs (e.g. CraftPix home)
    if THIRD_PARTY.exists():
        for vendor in sorted(THIRD_PARTY.iterdir()):
            if not vendor.is_dir() or should_skip_dir(vendor.name):
                continue
            for pack in sorted(vendor.iterdir()):
                if not pack.is_dir() or should_skip_dir(pack.name):
                    continue
                pack_id = f"{vendor.name}-{pack.name}"
                # Prefer source/ if present for cataloging originals
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
    info = {
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
    if pack_root and pack_root.is_dir():
        for name in ("License.txt", "LICENSE.txt", "LICENSE", "license.txt"):
            p = pack_root / name
            if p.exists():
                text = p.read_text(encoding="utf-8", errors="replace").strip()
                info["license_file"] = rel_to_root(p)
                if text.startswith("http"):
                    info["license_url"] = text.splitlines()[0].strip()
                    info["license"] = "see_url"
                else:
                    info["license"] = text[:240]
                break
    # Known CraftPix home (owner confirmed git storage)
    if "main_characters_home" in source_folder.replace("\\", "/"):
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
    elif "craftpix" in source_folder.lower() or (info.get("license_url") or "").startswith("https://craftpix.net"):
        info.update({
            "author": "CraftPix",
            "license": "CraftPix freebie terms (verify per pack)",
            "license_url": info.get("license_url") or "https://craftpix.net/file-licenses/",
            "license_status": "needs_review",
            "commercial_use": True,
            "modification_allowed": True,
            "attribution_required": False,
            "git_storage_allowed": None,
            "owner_confirmation": None,
            "notes": "CraftPix freebies typically allow game use; confirm git redistribution / this specific pack before runtime.",
        })
    return info


def assign_asset_id(
    existing_by_path: dict[str, dict],
    used_ids: set[str],
    counters: dict[str, int],
    category: str,
    pack_id: str,
    source_path: str,
) -> str:
    if source_path in existing_by_path:
        aid = existing_by_path[source_path].get("asset_id")
        if aid:
            return aid
    prefix = CATEGORY_PREFIX.get(category, "ASSET")
    pkey = pack_key_for_id(pack_id)
    # Keep pack key readable but bounded
    if len(pkey) > 40:
        pkey = pkey[:40].rstrip("_")
    base = f"{prefix}_{pkey}_"
    key = f"{prefix}|{pkey}"
    n = counters.get(key, 0)
    while True:
        n += 1
        candidate = f"{base}{n:03d}"
        if candidate not in used_ids:
            counters[key] = n
            used_ids.add(candidate)
            return candidate


def build_contact_sheet(items: list[dict], out_path: Path, title: str) -> list[Path]:
    """Return list of written page paths."""
    if not items:
        return []
    pages: list[Path] = []
    per_page = SHEET_COLS * SHEET_ROWS
    font = ImageFont.load_default()
    for page_i in range(0, len(items), per_page):
        chunk = items[page_i: page_i + per_page]
        page_n = page_i // per_page + 1
        rows = (len(chunk) + SHEET_COLS - 1) // SHEET_COLS
        header_h = 28
        W = SHEET_COLS * SHEET_CELL + 16
        H = header_h + rows * (SHEET_CELL + LABEL_H) + 16
        sheet = Image.new("RGBA", (W, H), (28, 30, 34, 255))
        draw = ImageDraw.Draw(sheet)
        page_title = title if page_n == 1 and len(items) <= per_page else f"{title} ({page_n})"
        draw.text((10, 8), page_title, fill=(240, 240, 235, 255), font=font)
        for idx, asset in enumerate(chunk):
            r, c = divmod(idx, SHEET_COLS)
            x = 8 + c * SHEET_CELL
            y = header_h + 8 + r * (SHEET_CELL + LABEL_H)
            cell = checkerboard((SHEET_CELL - 8, SHEET_CELL - 8 - 4), 8)
            prev = ROOT / asset["preview_path"] if asset.get("preview_path") else None
            if prev and prev.exists():
                pim = Image.open(prev).convert("RGBA")
                # Use only the image portion of preview (above label)
                pw, ph = pim.size
                img_h = max(1, ph - LABEL_H)
                crop = pim.crop((0, 0, pw, img_h))
                cw, ch = cell.size
                scale = min(cw / crop.width, ch / crop.height, 1.0)
                nw, nh = max(1, int(crop.width * scale)), max(1, int(crop.height * scale))
                crop = crop.resize((nw, nh), Image.NEAREST)
                cell.paste(crop, ((cw - nw) // 2, (ch - nh) // 2), crop)
            sheet.paste(cell, (x, y))
            label = f"{asset['asset_id']}\n{asset.get('pack_id','')}\n{asset.get('width')}×{asset.get('height')}"
            draw.multiline_text((x, y + SHEET_CELL - 10), label, fill=(220, 220, 215, 255), font=font, spacing=1)
        if len(items) <= per_page:
            path = out_path
        else:
            path = out_path.with_name(f"{out_path.stem}_{page_n:02d}{out_path.suffix}")
        path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(path)
        pages.append(path)
    return pages


def fingerprint_upload() -> str:
    """Stable fingerprint of scanned content for --check."""
    lines: list[str] = []
    for pack in discover_pack_roots():
        root = pack.get("root")
        if root is None:
            lines.append(f"ZIP|{pack['source_folder']}")
            continue
        for f in iter_pack_files(root):
            if f.suffix.lower() not in IMAGE_EXTS | META_EXTS:
                continue
            st = f.stat()
            lines.append(f"{rel_to_root(f)}|{st.st_size}|{int(st.st_mtime)}")
    blob = "\n".join(sorted(lines)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def write_category_md(page_key: str, cats: list[str], assets: list[dict], sheet_rel_paths: list[str]) -> None:
    out = CATALOG_DOCS / f"{page_key}.md"
    lines = [
        f"# {page_key.replace('_', ' ').title()}",
        "",
        f"Categories: {', '.join(cats)}",
        "",
        "## Contact sheets",
        "",
    ]
    for rel in sheet_rel_paths:
        lines.append(f"![contact sheet]({posix(Path(rel).as_posix().replace('docs/assets/catalog/', ''))})")
        lines.append("")
    # Prefer primary (non-shadow) first in table
    ordered = sorted(
        assets,
        key=lambda a: (1 if "shadow" in a.get("tags", []) else 0, a["asset_id"]),
    )
    lines += [
        "## Assets",
        "",
        "| Asset ID | Pack | Source | Size | Alpha | Status | Tags | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for a in ordered:
        tags = ", ".join(a.get("tags") or [])
        lines.append(
            "| `{id}` | {pack} | `{src}` | {w}×{h} | {alpha} | {status} | {tags} | {notes} |".format(
                id=a["asset_id"],
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
    out.write_text("\n".join(lines), encoding="utf-8")


def write_pack_md(pack: dict, assets: list[dict], license_info: dict, sheet_rel: str | None) -> None:
    slug = pack["slug"]
    out_dir = PACK_DOCS / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    cats = sorted({a["category"] for a in assets}) if assets else []
    sizes = sorted({(a.get("width"), a.get("height")) for a in assets if a.get("width")})
    sheets = [a for a in assets if a.get("is_sprite_sheet")]
    tmx = pack.get("tmx_files") or []
    lines = [
        f"# Pack: {pack['pack_id']}",
        "",
        f"- **Slug:** `{slug}`",
        f"- **Source folder:** `{pack['source_folder']}`",
        f"- **Source kind:** {pack.get('source_kind')}",
        f"- **Author:** {license_info.get('author')}",
        f"- **License:** {license_info.get('license')}",
        f"- **License URL:** {license_info.get('license_url')}",
        f"- **License status:** `{license_info.get('license_status')}`",
        f"- **Added (catalog):** {date.today().isoformat()}",
        f"- **Image assets:** {len([a for a in assets if a.get('width')])}",
        f"- **Categories:** {', '.join(cats) if cats else '—'}",
        f"- **Distinct sizes:** {', '.join(f'{w}×{h}' for w,h in sizes[:20])}{'…' if len(sizes)>20 else ''}",
        f"- **Sprite sheets:** {len(sheets)}",
        f"- **Tiled files:** {', '.join(f'`{t}`' for t in tmx) if tmx else '—'}",
        "",
        "## Contact sheet",
        "",
    ]
    if sheet_rel:
        # relative from pack readme: packs/<slug>/README.md -> ../contact or local
        local = out_dir / "contact_sheet.png"
        if local.exists():
            lines.append("![pack contact sheet](contact_sheet.png)")
        else:
            lines.append(f"![pack contact sheet](../../{posix(Path(sheet_rel).name)})")
    else:
        lines.append("_No images yet (zip-only or empty)._")
    lines += [
        "",
        "## Fit for this project",
        "",
        "- Top-down CraftPix-style packs generally match the outdoor direction under evaluation.",
        "- Prefer separate object PNGs over huge sheets when placing yard props.",
        "- Shadow / texture_shadow variants are tagged; use deliberately.",
        "",
        "## Style / prep notes",
        "",
        "- Confirm license + Git storage before promoting to `status=runtime`.",
        "- Do not auto-copy into `assets/third_party/` until explicitly selected.",
        "- Scale lock remains 16×16 world grid; measure each asset before wiring collisions/Y-sort.",
        "",
        "## Asset IDs (sample)",
        "",
    ]
    for a in assets[:25]:
        lines.append(f"- `{a['asset_id']}` — `{a['source_path']}`")
    if len(assets) > 25:
        lines.append(f"- … +{len(assets)-25} more (see category pages / `asset_catalog.json`)")
    lines.append("")
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_main_readme(stats: dict, pack_slugs: list[str]) -> None:
    lines = [
        "# Asset Catalog",
        "",
        "Owner-facing catalog of incoming and imported visual assets.",
        "",
        "## How to use",
        "",
        "1. Browse category pages or pack pages below (GitHub renders contact sheets).",
        "2. Copy a stable **Asset ID**.",
        "3. Tell Cursor which IDs to use in which area.",
        "",
        "Example:",
        "",
        "> For the north edge of `yard_main` use `TREE_TREES_PIXEL_ART_004` and `BUSH_BUSHES_PIXEL_ART_012`.",
        "",
        "Selections are recorded in [`AREA_ASSET_SELECTIONS.md`](AREA_ASSET_SELECTIONS.md)",
        "and `data/assets/area_asset_selections.json` (not wired to gameplay yet).",
        "",
        "## Update catalog",
        "",
        "```bash",
        "python tools/build_asset_catalog.py",
        "python tools/build_asset_catalog.py --check",
        "```",
        "",
        "`res://upload/` is the **permanent INBOX** — never delete it. New packs dropped there are picked up on the next catalog run.",
        "",
        "## Stats",
        "",
        f"- Packs (unpacked): **{stats['packs']}**",
        f"- Zip-only inbox entries (not expanded): **{stats.get('zip_only', 0)}**",
        f"- Image assets: **{stats['images']}**",
        f"- Categories present: {', '.join(stats['categories'])}",
        "",
        "## Categories",
        "",
    ]
    for key in MD_CATEGORY_PAGES:
        lines.append(f"- [{key.title()}](catalog/{key}.md)")
    lines += [
        "",
        "## Packs",
        "",
    ]
    for slug in pack_slugs:
        lines.append(f"- [{slug}](catalog/packs/{slug}/README.md)")
    lines += [
        "",
        "## Machine-readable registry",
        "",
        "- `data/assets/asset_catalog.json`",
        "- `data/assets/asset_packs.json`",
        "- `data/assets/asset_catalog_overrides.json`",
        "- `data/assets/area_asset_selections.json`",
        "",
        "## Debug gallery (Godot)",
        "",
        "- Scene: `scenes/debug/asset_gallery.tscn`",
        "",
    ]
    (DOCS_ASSETS / "README.md").write_text("\n".join(lines), encoding="utf-8")


def ensure_seed_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not OVERRIDES_JSON.exists():
        save_json(OVERRIDES_JSON, {
            "_comment": "Manual overrides keyed by source_path (posix, relative to repo root).",
        })
    if not AREA_JSON.exists():
        save_json(AREA_JSON, {
            "yard_main": {
                "house": {"selected": [], "candidates": [], "rejected": []},
                "north_border": {"trees": [], "bushes": [], "rocks": []},
                "entrance": {"fence": [], "gate": [], "path": [], "decoration": []},
                "pond_zone": {"water": [], "shore": [], "reeds": [], "rocks": []},
                "overgrown_zone": {"weeds": [], "bushes": [], "logs": [], "stumps": [], "trees": []},
            },
            "house_exterior": {},
            "shed_zone": {},
            "future_village_road": {},
        })
    area_md = DOCS_ASSETS / "AREA_ASSET_SELECTIONS.md"
    if not area_md.exists():
        area_md.write_text(
            """# Area Asset Selections

Owner decisions for concrete game areas. Use **Asset IDs** only.

Update this file when choosing assets from the [Asset Catalog](README.md).
Mirror important choices into `data/assets/area_asset_selections.json`.

## yard_main

### House
- selected:
- candidates:
- rejected:

### North border
- trees:
- bushes:
- rocks:

### Entrance
- fence:
- gate:
- path:
- decoration:

### Pond zone
- water:
- shore:
- reeds:
- rocks:

### Overgrown zone
- weeds:
- bushes:
- logs:
- stumps:
- trees:

## house_exterior

## shed_zone

## future_village_road
""",
            encoding="utf-8",
        )


def run_build() -> int:
    ensure_seed_files()
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    CONTACT.mkdir(parents=True, exist_ok=True)
    PACK_DOCS.mkdir(parents=True, exist_ok=True)

    existing = load_json(CATALOG_JSON, {"version": 1, "assets": []})
    existing_assets = existing.get("assets", [])
    by_path = {a["source_path"]: a for a in existing_assets if a.get("source_path")}
    used_ids = {a["asset_id"] for a in existing_assets if a.get("asset_id")}
    counters: dict[str, int] = {}
    # Seed counters from existing IDs
    for aid in used_ids:
        m = re.match(r"^([A-Z]+)_([A-Z0-9_]+)_(\d+)$", aid)
        if m:
            key = f"{m.group(1)}|{m.group(2)}"
            counters[key] = max(counters.get(key, 0), int(m.group(3)))

    overrides = load_json(OVERRIDES_JSON, {})
    overrides = {k: v for k, v in overrides.items() if not str(k).startswith("_") and isinstance(v, dict)}

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
            "asset_count": 0,
            "categories": [],
        }
        if pack.get("zip_only") or pack.get("root") is None:
            packs_meta.append(pack_rec)
            continue

        root: Path = pack["root"]
        pack_assets: list[dict] = []
        for f in iter_pack_files(root):
            rel_src = rel_to_root(f)
            ext = f.suffix.lower()
            if ext in {".tmx"}:
                pack_rec["tmx_files"].append(rel_src)
                continue
            if ext in {".tsx"}:
                pack_rec["tsx_files"].append(rel_src)
                continue
            if ext == ".json" and "preview" not in rel_src:
                # keep registry note only for map-like json later if needed
                continue
            if ext == ".psd":
                source_path = rel_src
                seen_paths.add(source_path)
                ov = overrides.get(source_path, {})
                category = ov.get("category") or infer_category(pack["pack_id"], rel_src, f.name)
                asset_id = assign_asset_id(by_path, used_ids, counters, category, pack["pack_id"], source_path)
                prev = by_path.get(source_path, {})
                asset = {
                    "asset_id": asset_id,
                    "pack_id": pack["pack_id"],
                    "category": category,
                    "source_path": source_path,
                    "runtime_path": prev.get("runtime_path"),
                    "preview_path": None,
                    "width": None,
                    "height": None,
                    "has_alpha": None,
                    "tile_size": None,
                    "is_sprite_sheet": False,
                    "frame_count": None,
                    "tags": ov.get("tags") or infer_tags(pack["pack_id"], rel_src, category) + ["psd"],
                    "license_status": lic.get("license_status", "needs_review"),
                    "status": ov.get("status") or prev.get("status") or "available",
                    "notes": ov.get("notes") or prev.get("notes") or "PSD source — not rasterized in catalog.",
                }
                pack_assets.append(asset)
                new_assets.append(asset)
                continue
            if ext not in IMAGE_EXTS:
                continue

            source_path = rel_src
            seen_paths.add(source_path)
            ov = overrides.get(source_path, {})
            category = ov.get("category") or infer_category(pack["pack_id"], rel_src, f.name)
            asset_id = assign_asset_id(by_path, used_ids, counters, category, pack["pack_id"], source_path)
            preview_rel = f"docs/assets/catalog/previews/{asset_id}.png"
            preview_abs = ROOT / preview_rel
            try:
                meta = make_preview(f, asset_id, preview_abs)
            except Exception as exc:  # noqa: BLE001
                print(f"WARN preview failed {source_path}: {exc}", file=sys.stderr)
                meta = {
                    "width": None, "height": None, "has_alpha": None,
                    "is_sprite_sheet": False, "frame_count": None, "tile_size": None,
                }
                preview_rel = None

            prev = by_path.get(source_path, {})
            # Preserve user notes / status unless override sets them
            status = ov.get("status") or prev.get("status") or "available"
            if lic.get("license_status") == "needs_review" and status == "runtime":
                status = "needs_review"
            notes = ov.get("notes") if "notes" in ov else (prev.get("notes") or "")
            if meta.get("notes_auto") and not notes:
                notes = meta["notes_auto"]
            tags = ov.get("tags") or infer_tags(pack["pack_id"], rel_src, category)

            asset = {
                "asset_id": asset_id,
                "pack_id": pack["pack_id"],
                "category": category,
                "source_path": source_path,
                "runtime_path": prev.get("runtime_path"),
                "preview_path": preview_rel,
                "width": meta.get("width"),
                "height": meta.get("height"),
                "has_alpha": meta.get("has_alpha"),
                "tile_size": meta.get("tile_size"),
                "is_sprite_sheet": meta.get("is_sprite_sheet", False),
                "frame_count": meta.get("frame_count"),
                "tags": tags,
                "license_status": lic.get("license_status", "needs_review"),
                "status": status,
                "notes": notes,
            }
            pack_assets.append(asset)
            new_assets.append(asset)

        # Mark missing from this pack that disappeared
        pack_rec["asset_count"] = len(pack_assets)
        pack_rec["categories"] = sorted({a["category"] for a in pack_assets})
        packs_meta.append(pack_rec)

        # Pack contact sheet (prefer non-shadow first)
        visual = [a for a in pack_assets if a.get("preview_path")]
        visual.sort(key=lambda a: (1 if "shadow" in a.get("tags", []) else 0, a["asset_id"]))
        pack_sheet = PACK_DOCS / pack["slug"] / "contact_sheet.png"
        pages = build_contact_sheet(visual[:SHEET_COLS * SHEET_ROWS], pack_sheet, pack["pack_id"])
        sheet_rel = rel_to_root(pages[0]) if pages else None
        write_pack_md(pack, pack_assets, lic, sheet_rel)

    # Preserve missing assets
    for path, old in by_path.items():
        if path not in seen_paths:
            missing = dict(old)
            missing["status"] = "missing"
            missing["notes"] = (missing.get("notes") or "") + (" | " if missing.get("notes") else "") + "File missing from scan roots."
            new_assets.append(missing)

    new_assets.sort(key=lambda a: a["asset_id"])
    catalog = {
        "version": 1,
        "generated": date.today().isoformat(),
        "scan_roots": ["upload/", "assets/third_party/"],
        "assets": new_assets,
    }
    save_json(CATALOG_JSON, catalog)
    save_json(PACKS_JSON, {"version": 1, "packs": packs_meta})

    # Category contact sheets + markdown
    by_cat: dict[str, list] = defaultdict(list)
    for a in new_assets:
        if a.get("status") == "missing":
            continue
        by_cat[a["category"]].append(a)

    for page_key, cats in MD_CATEGORY_PAGES.items():
        items: list[dict] = []
        for c in cats:
            items.extend(by_cat.get(c, []))
        items = [a for a in items if a.get("preview_path")]
        items.sort(key=lambda a: (1 if "shadow" in a.get("tags", []) else 0, a["asset_id"]))
        sheet_base = CONTACT / f"{CONTACT_SHEET_NAME[page_key]}.png"
        # Clear old paged sheets for this stem
        for old in CONTACT.glob(f"{CONTACT_SHEET_NAME[page_key]}*.png"):
            old.unlink()
        pages = build_contact_sheet(items, sheet_base, page_key)
        sheet_rels = [rel_to_root(p) for p in pages]
        # Paths inside catalog md should be relative to docs/assets/catalog/
        rel_for_md = []
        for p in pages:
            rel_for_md.append(posix(p.relative_to(CATALOG_DOCS)))
        write_category_md(page_key, cats, items, rel_for_md)

    unpacked = [p for p in packs_meta if not p.get("source_kind") == "upload_zip"]
    zip_only = [p for p in packs_meta if p.get("source_kind") == "upload_zip"]
    cats_present = sorted({a["category"] for a in new_assets if a.get("status") != "missing"})
    stats = {
        "packs": len(unpacked),
        "zip_only": len(zip_only),
        "images": len([a for a in new_assets if a.get("width") and a.get("status") != "missing"]),
        "categories": cats_present,
    }
    write_main_readme(stats, [p["slug"] for p in unpacked])

    fp = fingerprint_upload()
    save_json(FINGERPRINT_JSON, {
        "sha256": fp,
        "generated": date.today().isoformat(),
        "image_count": stats["images"],
        "pack_count": stats["packs"],
        "zip_only_count": stats["zip_only"],
    })

    print(
        f"Catalog OK: {stats['images']} images, {stats['packs']} packs"
        f" (+{stats['zip_only']} zip-only), categories={cats_present}"
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
    parser = argparse.ArgumentParser(description="Build incremental visual asset catalog")
    parser.add_argument("--check", action="store_true", help="Fail if catalog is stale vs upload")
    args = parser.parse_args()
    if args.check:
        return run_check()
    return run_build()


if __name__ == "__main__":
    raise SystemExit(main())
