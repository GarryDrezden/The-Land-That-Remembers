# ASSET INVENTORY

Обновлено: 2026-07-31 (texture proof v1)

Правила: [ART_ASSET_BRIEF.md](ART_ASSET_BRIEF.md) · ориентир: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) §20–21.

## Visual direction (approved)

| Поле | Значение |
|------|----------|
| Направление | original detailed Stardew-like outdoor pixel art with rural childhood-home identity |
| Mood refs | `docs/art_direction/outdoor_target_yard_mood.png`, `…_asset_scope.png` |
| Status | **approved** ([DEC-005](DECISIONS.md), [DEC-006](DECISIONS.md)) |

## Scale lock (accepted greybox)

| Параметр | Значение |
|----------|----------|
| Viewport | 384×240 |
| Tile | 16×16 |
| Map | 72×45 tiles (1152×720 px) |
| Player box | 24×32 |
| Deciduous | 64×80 |
| Birch | 48×80 |
| Spruce | 48×96 |
| Bush | 32×24 |
| Rock | 16×16 / 24×24 |
| Log | 32×16 |
| Stump | 24×24 |
| House | ~144×112 |
| Scene | `yard_scale_test.tscn` |

---

## Texture proof v1 — candidate

| Поле | Значение |
|------|----------|
| Asset ID | `generated_outdoor_texture_proof_v1` |
| Status | **generated outdoor texture proof v1 — candidate** |
| Folder | `assets/art/outdoor/texture_proof_v1/` |
| Scene | `scenes/locations/outdoor/childhood_home/yard_texture_test_v1.tscn` |
| Tool | `tools/prep_texture_proof_v1.py` |
| Manifest | `assets/art/outdoor/texture_proof_v1/manifest.json` |
| Source material | downscaled/cleaned slices from rejected generated_test refs |

### PNG used (actual sizes)

| File | Size |
|------|------|
| `player/frame_00…19.png` | 24×32 each |
| `tree_deciduous.png` | 64×80 |
| `tree_spruce.png` | 48×96 |
| `bush.png` | 32×24 |
| `rock.png` | 24×24 |
| `log.png` | 32×16 |
| `stump.png` | 24×24 |
| `house.png` | 144×112 |
| `pond.png` | 128×96 |

Notes: player left = **prototype flip** of right. Pond = temporary whole sprite. Dirt-island trim is heuristic. NEAREST downscale from larger sources → softer pixel than native 16px art.

Previews: `docs/art_tests/yard_texture_test_v1_*.png`

---

## Art test v2 — generated outdoor pack (REJECTED as production)

| Поле | Значение |
|------|----------|
| Status | **rejected as production** ([DEC-007](DECISIONS.md)) |
| Role | visual references only |
| Scene | `yard_art_test_v2.tscn` (keep as failed experiment) |

---

## Art test v1 — Puny World (отклонён)

| Status | **NOT approved** ([DEC-004](DECISIONS.md)) |

## Запрещено

Рипы Stardew; AI sheets как production без technical gate; GameRoot до утверждения арта.
