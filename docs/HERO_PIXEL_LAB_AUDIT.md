# PixelLab Hero Audit

Обновлено: 2026-08-01 (full 8-direction walk)  
Inbox (permanent): `upload/hero/` — **не удалять / не переименовывать / не очищать**.

## Source files

| File | Size | Canvas | Frames | Duration/frame | FPS | Loop |
|------|------|--------|--------|----------------|-----|------|
| `Idle_rotations_8dir.gif` | 6400 B | **92×92** | **8** | **200 ms** | **5.0** | yes (`loop=0`) |
| `Idle_v3_walking_south.gif` | 8045 B | **92×92** | **8** | **200 ms** | **5.0** | yes |
| `Idle_v3_walking_south-east.gif` | 7464 B | **92×92** | **8** | **200 ms** | **5.0** | yes |
| `Idle_v3_walking_east.gif` | 6900 B | **92×92** | **8** | **200 ms** | **5.0** | yes |
| `Idle_v3_walking_north-east.gif` | 6558 B | **92×92** | **8** | **200 ms** | **5.0** | yes |
| `Idle_v3_walking_north.gif` | 5568 B | **92×92** | **8** | **200 ms** | **5.0** | yes |
| `Idle_v3_walking_north-west.gif` | 6552 B | **92×92** | **8** | **200 ms** | **5.0** | yes |
| `Idle_v3_walking_west.gif` | 6906 B | **92×92** | **8** | **200 ms** | **5.0** | yes |
| `Idle_v3_walking_south-west.gif` | 7461 B | **92×92** | **8** | **200 ms** | **5.0** | yes |

Durations стабильны (все 200 ms). Отдельный FPS override не требуется.

## Background / alpha

- GIF mode: indexed (`P`) with `transparency` index **0**.
- Palette[0] = **RGB(0, 255, 0)** — chroma green keyed via GIF transparency.
- After `convert("RGBA")`: corners are `(0,255,0,0)`; **opaque green count = 0**.
- Partial alpha: **0** (binary transparency only).
- Importer rule: **preserve GIF transparency**; do **not** force chroma flood-fill when alpha is already present. Transparent pixels normalized to `(0,0,0,0)`. Residual pure-green pockets (if any) cleared only when opaque.

## Size / baseline

- Canvas **92×92** constant across all clips/frames.
- Figure bbox height ~**43–48** px (pose variance); visual scale consistent across directions.
- Pre-align foot Y jitter: up to **3 px** (NE/NW walk); height jitter up to **3 px**.
- Importer applies **shared integer-pixel baseline** across idle + all walk clips (center X + common foot line). Post-align opaque foot Y = **70** on all sampled frames.
- No clothing / hair / body identity swaps observed between frames of a clip (same silhouette family).

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

## Walk directions

All **8** walk GIFs imported to `assets/characters/player/pixellab_v1/walk/<dir>/`.  
**No mirroring / no direction substitution.** West uses dedicated west frames.

Contact sheets: `preview/walk_*_contact_sheet.png`  
Demo GIF: `preview/walk_8dir_demo.gif` + in-engine `docs/art_tests/craftpix_hero_walk8.gif`

## Runtime / player

| Item | Value |
|------|-------|
| Importer | `tools/import_pixellab_hero.py` |
| Runtime | `assets/characters/player/pixellab_v1/` |
| Player | `scenes/actors/player/player_pixellab_test.tscn` |
| Yard test | `scenes/locations/outdoor/childhood_home/craftpix_hero_test.tscn` |
| Node scale | `Vector2.ONE` (Player / AnimatedSprite2D / parents) |
| Filtering | Nearest |
| Display | integer nearest `PIXEL_DIV=2` at load (PNGs on disk unchanged) |
| Collision | feet box `8×4` at `(0,-1)` |
| Y-sort origin | between feet (body origin) |
| Movement | WASD, normalized; facing by 8-sector angle |

## CraftPix scale (provisionally accepted)

| Measure | Value |
|---------|-------|
| Native figure | ~46 px |
| Door opening | ~41 px |
| Display with `PIXEL_DIV=2` | ~23 px ≈ **~56%** of door |
| Node scale | **1.0** kept |

Do not silently change scale. If motion looks off, note only.

## In-engine verification shots

`docs/art_tests/`:

- idle ×8: `craftpix_hero_idle_*.png`
- walk ×8: `craftpix_hero_walk_*.png`
- locations: door, inside_yard, gate, outside, tree, tree_behind, fence, rocks, collisions
- motion GIF: `craftpix_hero_walk8.gif`

## Verdict

| Question | Answer |
|----------|--------|
| Compatible with CraftPix yard? | **Yes, provisionally** (test scene only) |
| Visual scale stable? | **Yes** (shared baseline; node scale 1; PIXEL_DIV=2 display) |
| Frames needing fix? | Minor walk foot jitter absorbed by align; no broken clips found |
| Ready for axe animation? | **Not yet** — owner review of 8-dir walk first |
| Ready for pickaxe animation? | **Not yet** — same gate |

Status: **under owner review** — show results before axe/pickaxe or house restoration.
