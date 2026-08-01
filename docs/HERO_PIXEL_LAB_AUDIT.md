# PixelLab Hero Audit

Обновлено: 2026-08-01  
Inbox (permanent): `upload/hero/` — **не удалять / не перезаписывать**.

## Source files

| File | Size | Canvas | Frames | Duration/frame | FPS (approx) | Loop |
|------|------|--------|--------|----------------|--------------|------|
| `Idle_rotations_8dir.gif` | 6400 B | **92×92** | **8** | **200 ms** each | **5.0** | yes (`loop=0`) |
| `Idle_v3_walking_south.gif` | 8045 B | **92×92** | **8** | **200 ms** each | **5.0** | yes |
| `Idle_v3_walking_east.gif` | 6900 B | **92×92** | **8** | **200 ms** each | **5.0** | yes |

## Background / alpha

- GIF mode: indexed (`P`) with `transparency` index **0**.
- Palette color for index 0: **RGB(0, 255, 0)** — classic chroma green.
- Pillow’s default RGBA convert turns that index into alpha=0; this is **not** “true authored alpha art”, it is **green-screen keyed via GIF transparency**.
- Audit rule: **do not treat green as already-correct transparency** — importer reconstructs opaque green, then removes it via **edge flood-fill** (+ tight pure-green pocket cleanup between legs).

## Size / baseline stability

- Canvas size is **constant** across all frames of each GIF (no per-frame canvas resize).
- Character bbox width/height varies slightly by pose (expected for 8-dir / walk).
- Foot Y before align: south idle ~67–68; walk south ~67–68; walk east ~68–69 (1px jitter).
- Importer keeps shared 92×92 canvas and applies **integer-pixel** baseline offsets (see `source_manifest.json`).

## Idle direction mapping (verified)

Contact sheet: `assets/characters/player/pixellab_v1/preview/idle_rotations_indexed.png`

| Frame | Direction |
|------:|-----------|
| 0 | south |
| 1 | south_east |
| 2 | east |
| 3 | north_east |
| 4 | north |
| 5 | north_west |
| 6 | west |
| 7 | south_west |

## Prototype limitations

- Walk available: **south**, **east**.
- **West** = east frames + `flip_h` at runtime.
- **North walk** not generated — movement up uses **idle_north**.
- No axe / pickaxe / chop actions in this stage.

## Runtime output

Prepared by `tools/import_pixellab_hero.py` → `assets/characters/player/pixellab_v1/`.

Status: **under in-engine evaluation** against CraftPix home yard (`craftpix_hero_test.tscn`).
