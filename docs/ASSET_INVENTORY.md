# ASSET INVENTORY

Обновлено: 2026-08-01 (visual terrain pass)

Правила: [ART_ASSET_BRIEF.md](ART_ASSET_BRIEF.md) · ориентир: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) §20–21.

## Visual direction (approved)

| Поле | Значение |
|------|----------|
| Направление | original detailed Stardew-like outdoor pixel art with rural childhood-home identity |
| Mood refs | `docs/art_direction/outdoor_target_yard_mood.png`, `…_asset_scope.png` |
| AI sheets | **mood/palette reference only** — not tile sources |
| Status | **approved** ([DEC-005](DECISIONS.md), [DEC-006](DECISIONS.md)) |

## Scale lock (accepted greybox)

| Параметр | Значение |
|----------|----------|
| Viewport | 384×240 |
| Tile | 16×16 |
| Map | 72×45 tiles (1152×720 px) |
| Scene | `yard_scale_test.tscn` |

---

## Seamless terrain (accepted) + visual pass

| Поле | Значение |
|------|----------|
| Status | **seamless system accepted**; macro variation pass done |
| Ground | `assets/art/outdoor/terrain_proof/terrain_ground.png` (192×64, 12×4) |
| Decor | `assets/art/outdoor/terrain_proof/terrain_decor.png` (256×16, 16 overlays) |
| TileSet | `resources/tilesets/yard_ground_tileset.tres` |
| Scene | `yard_terrain_proof.tscn` |
| Tools | `generate_terrain_proof.py`, `test_terrain_atlas.py`, `build_yard_ground_tileset.gd` |
| Terrain | Match Corners · Grass / Soil · masks + macros + edge variants |
| Variant weights | base **65%**, subtle **20%**, light/dark **10%**, dense **5%** |
| Previews | `docs/art_tests/terrain_macro_compare.png`, `terrain_macro.png`, `…_decor.png`, `…_{grass,soil,edge}_x4.png` |

### Ground atlas layout

| Region | Content |
|--------|---------|
| cols 0–3, rows 0–3 | corner masks 0…15 (TL=1,TR=2,BR=4,BL=8) |
| cols 4–7, row 0 | grass variants (shared border with mask 0) |
| cols 4–7, row 1 | soil variants (shared border with mask 15) |

---

## Earlier texture_proof_v1 (superseded for terrain)

Kept under `assets/art/outdoor/texture_proof_v1/` as failed/legacy experiment material. Not used by seamless proof.
