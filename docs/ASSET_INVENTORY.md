# ASSET INVENTORY

Обновлено: 2026-08-01 (PixelLab hero prototype)

Правила: [ART_ASSET_BRIEF.md](ART_ASSET_BRIEF.md) · third-party: [THIRD_PARTY_ASSETS.md](THIRD_PARTY_ASSETS.md) · **catalog:** [assets/README.md](assets/README.md)

## PixelLab hero v1 (under evaluation)

| Item | Path |
|------|------|
| Inbox originals | `upload/hero/*.gif` (**permanent**) |
| Importer | `tools/import_pixellab_hero.py` |
| Runtime | `assets/characters/player/pixellab_v1/` |
| Manifest | `…/source_manifest.json` |
| Player scene | `scenes/actors/player/player_pixellab_test.tscn` |
| Yard test | `scenes/locations/outdoor/childhood_home/craftpix_hero_test.tscn` |
| Audit | [HERO_PIXEL_LAB_AUDIT.md](HERO_PIXEL_LAB_AUDIT.md) |

Walk: south + east · west = flip_h · north walk **missing** (uses idle_north).

## Asset Catalog (owner selection)

| Item | Path |
|------|------|
| Inbox (permanent) | `upload/` |
| Generator | `tools/build_asset_catalog.py` |
| Registry | `data/assets/asset_catalog.json` |
| Overrides | `data/assets/asset_catalog_overrides.json` |
| Area selections | `docs/assets/AREA_ASSET_SELECTIONS.md` + `data/assets/area_asset_selections.json` |
| Previews / sheets | `docs/assets/catalog/` |
| Debug gallery | `scenes/debug/asset_gallery.tscn` |

Update: `python tools/build_asset_catalog.py` · check: `python tools/build_asset_catalog.py --check`

## Visual direction (approved)

| Поле | Значение |
|------|----------|
| Направление | original detailed Stardew-like outdoor pixel art with rural childhood-home identity |
| Status | **approved** ([DEC-005](DECISIONS.md), [DEC-006](DECISIONS.md)) |

## Scale lock

| Параметр | Значение |
|----------|----------|
| Viewport target | 384×240 (preview uses integer ×3 window) |
| CraftPix tile | **16×16** (TMX) |

---

## CraftPix Main Character’s Home (under evaluation)

| Поле | Значение |
|------|----------|
| Направление | original detailed Stardew-like outdoor pixel art with rural childhood-home identity |
| Status | **approved** ([DEC-005](DECISIONS.md), [DEC-006](DECISIONS.md)) |

## Scale lock

| Параметр | Значение |
|----------|----------|
| Viewport target | 384×240 (preview uses integer ×3 window) |
| CraftPix tile | **16×16** (TMX) |

---

## CraftPix Main Character’s Home (under evaluation)

Root: `assets/third_party/craftpix/main_characters_home/`  
Audit: [CRAFTPIX_HOME_AUDIT.md](CRAFTPIX_HOME_AUDIT.md)

### Runtime files used by preview

| File | Source | Runtime | Size | Tile | Role | Status | In preview |
|------|--------|---------|------|------|------|--------|------------|
| ground_grass_details.png | source/Tiled_files/ | runtime/terrain/ | 336×288 | 16 | grass/soil detail overlays | runtime | yes |
| exterior.png | source/Tiled_files/ | runtime/buildings/ | 272×912 | 16 | outdoor ground, paths, props, fence pieces | runtime | yes |
| house_details.png | source/Tiled_files/ | runtime/buildings/ | 160×272 | 16 | house walls/roof | runtime | yes |
| Doors_windows_animation.png | source/Tiled_files/ | runtime/buildings/ | 272×192 | 16 | doors/windows | runtime | yes |
| Smoke_animation.png | source/Tiled_files/ | runtime/buildings/ | 288×48 | 16 | chimney smoke frames | runtime | yes |
| Trees_animation.png | source/Tiled_files/ | runtime/vegetation/ | 576×1040 | 16 | trees | runtime | yes |
| bird_*.png / cat_animation.png | source/Tiled_files/ | runtime/props/ | varies | 16 | creatures (not player) | runtime | optional |
| Interior.png / walls_floor.png | source/Tiled_files/ | runtime/interiors/ | varies | 16 | interior | runtime | not in outdoor preview |
| exterior_preview_layout.json | derived from Exterior.tmx | runtime/preview/ | — | 16 | cropped layer layout | processed | yes |

### Source (originals)

| Path | Status |
|------|--------|
| `source/PNG/` | source (standalone sheets; prefer Tiled_files sizes) |
| `source/PSD/` | source (not Godot-imported) |
| `source/Tiled_files/*.tmx` | source demos (`Exterior.tmx`, `Interior1.tmx`, …) |

### Preview scene

| Item | Path |
|------|------|
| Scene | `scenes/locations/outdoor/childhood_home/craftpix_home_preview.tscn` |
| Script | `scripts/debug/craftpix_home_preview.gd` |
| Screenshots | `docs/art_tests/craftpix_home_preview*.png` |
| Tiled crop ref | `docs/art_tests/craftpix_tiled_exterior_reference.png` |

---

## Earlier experiments (kept, not used by CraftPix preview)

| Item | Notes |
|------|-------|
| Seamless procedural terrain (`terrain_proof/`) | documented experiment; not mixed into CraftPix preview |
| Puny World / AI generated outdoor tests | rejected / reference only |

Character: **not included** in CraftPix home pack — separate character pack required.
