# ARCHITECTURE

Обновлено: 2026-08-01 (VS01 yard candidate)  
**Ориентир структуры (план):** [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)  
**Этот файл:** что **фактически** есть в репозитории сейчас (не идеальная целевая схема).

Приоритет документов: VISION → VERTICAL_SLICE → PROJECT_STRUCTURE → **этот файл** → PROJECT_STATUS.

---

## VS01 outdoor yard candidate

| Элемент | Путь |
|---------|------|
| Playable scene | `scenes/locations/outdoor/childhood_home/yard_vs01.tscn` |
| Layout twin | `…/yard_vs01_layout_test.tscn` |
| Builder script | `scripts/locations/outdoor/childhood_home/yard_vs01.gd` |
| Door hotspot | `yard_vs01_door.gd` → `GameFlow.go_location("workshop")` (stub) |
| Runtime art | `assets/art/outdoor/yard_vs01/` |
| Approved house source | `upload/houses/main_house_v1.png` (permanent; never edited) |
| House runtime | `…/yard_vs01/main_house_v1.png` — key BG, **eave gap fill**, nearest ÷4, display_scale **0.88** |
| House node | `YSortWorld/MainHouse` @ feet ~(20, 14.4) tiles |
| Start camera | player zoom **2.2**, offset `(0, -72)` — house + path + front yard |
| Map | 40×34 tiles (larger than one screen) |
| Asset bake | `tools/build_yard_vs01_assets.py` |
| Player | `player_pixellab_test.tscn` (scale unchanged) |

CraftPix `craftpix_home_preview` / `craftpix_hero_test` остаются отдельными art-test сценами.

---

## PixelLab hero v1 (8-dir)

| Элемент | Путь |
|---------|------|
| Inbox GIFs (permanent) | `upload/hero/` |
| Importer | `tools/import_pixellab_hero.py` |
| Runtime PNGs | `assets/characters/player/pixellab_v1/` (`idle/`, `walk/<dir>/`, `preview/`) |
| Manifest | `…/source_manifest.json` |
| Player test scene | `scenes/actors/player/player_pixellab_test.tscn` |
| CraftPix yard test | `scenes/locations/outdoor/childhood_home/craftpix_hero_test.tscn` |
| Audit | `docs/HERO_PIXEL_LAB_AUDIT.md` |

- Idle + walk: **8 directions**, no mirroring.
- Node scale `Vector2.ONE` (provisionally accepted); runtime nearest `PIXEL_DIV=2` without rewriting PNGs.
- `craftpix_home_preview.tscn` unchanged; hero only in `craftpix_hero_test.tscn`.

---

## Asset Catalog / inbox

| Элемент | Путь |
|---------|------|
| Permanent inbox | `upload/` (**never delete / clear / rename / move wholesale**) |
| Catalog builder | `tools/build_asset_catalog.py` (`--check` for staleness) |
| Machine registry | `data/assets/asset_catalog.json` |
| Pack registry | `data/assets/asset_packs.json` |
| Overrides | `data/assets/asset_catalog_overrides.json` |
| Area selections (data) | `data/assets/area_asset_selections.json` |
| Owner entry (GitHub) | корневой `README.md` → раздел «Где смотреть ассеты» |
| Categories / packs / sheets | `docs/assets/catalog/` |
| Debug gallery | `scenes/debug/asset_gallery.tscn` (F6) |
| Runtime selected only | after explicit Asset ID selection |

Flow: drop packs into `upload/` → run catalog → owner picks Asset IDs → record in AREA selections → only then copy/prepare into `assets/third_party/`.

Decision: [DEC-009](DECISIONS.md).

---

## CraftPix home (under evaluation)

| Элемент | Путь |
|---------|------|
| Pack root | `assets/third_party/craftpix/main_characters_home/` |
| Source | `…/source/{PNG,PSD,Tiled_files}/` |
| Runtime | `…/runtime/{terrain,buildings,vegetation,props,interiors,preview}/` |
| Preview scene | `scenes/locations/outdoor/childhood_home/craftpix_home_preview.tscn` |
| Preview script | `scripts/debug/craftpix_home_preview.gd` |
| Layout export | `…/runtime/preview/exterior_preview_layout.json` |
| Organizer | `tools/organize_craftpix_home.py` |
| Audit | `docs/CRAFTPIX_HOME_AUDIT.md` |

Tile size **16×16** from TMX. Demo map `Exterior.tmx` (no Wang/Terrain). Preview loads a cropped region into TileMapLayers; blockers approximated; player = neutral silhouette (no human character in pack).

Procedural seamless terrain proof остаётся отдельным экспериментом и **не** используется в CraftPix preview.

---

## Terrain proof (факт, experiment)

| Элемент | Путь |
|---------|------|
| Ground atlas | `assets/art/outdoor/terrain_proof/terrain_ground.png` |
| Decor atlas | `assets/art/outdoor/terrain_proof/terrain_decor.png` |
| TileSet | `resources/tilesets/yard_ground_tileset.tres` |
| Factory | `scripts/tilesets/yard_terrain_tileset_factory.gd` |
| Scene | `scenes/locations/outdoor/childhood_home/yard_terrain_proof.tscn` |
| Generator | `tools/generate_terrain_proof.py` |
| Atlas tests | `tools/test_terrain_atlas.py` |

Слои proof-сцены: `GroundTerrain` (TileMapLayer, Match Corners) → `GroundDecoration` → Camera.  
Terrain Set 0: Grass (0) / Soil (1). Переходы — `set_cells_terrain_connect`.  
Macro pass: interior grass/soil cluster overrides + edge visual variants (same peering bits, identical border pixels).

AI presentation sheets **не** являются источником тайлов (только mood/palette).

---

## Gap: сейчас vs vertical slice 01

| Область | Сейчас | Нужно для VS01 |
|---------|--------|----------------|
| Narrative | Пекарня / Пётр / Софья | Дом детства, выгоревший программист, задача через осмотр |
| Outdoor | Скрипт + ColorRect/спрайты, лоскутный вид | Tile-based pixel yard + object scenes, цельный двор |
| Interior | Workshop + bakery painted | 1 дом/мастерская diorama + overlay прогресса |
| State | `flags` + `cleared_debris` | + `tasks`, `interior_states`, `story_flags`, `cleared_objects` |
| UI | День, инв, цель, tip, теги NPC/участка | Минимум: день / инв / цель / E у игрока / прогресс |
| Камни | 1×E | ~5 ударов, уменьшение |
| Art | Placeholder character, слабый дом/вода | Единый pack (этап art) |

Legacy bakery-quest **не удаляем сразу** — уводим в debug/legacy, VS01 ведёт на дом + верстак.

---

## Предлагаемая архитектура VS01

```
Boot → (Menu | Debug) → OutdoorYard
                         ↕ portal
                      InteriorHouse (painted)
```

### Сцены (цель)

| Сцена | Путь (цель) | Содержание |
|-------|-------------|------------|
| OutdoorYard | `scenes/world/outdoor_yard.tscn` | TileMap layers + WorldObjects |
| InteriorHouse | `scenes/world/interiors/house_workshop.tscn` | painted BG + hotspots + overlays |
| Player | собирается `scene_art.make_player` | CharacterBody2D |
| HUD | CanvasLayer script | минимум UI |

Пока миграция: `outdoor_square.tscn` остаётся entry, постепенно становится thin wrapper → `outdoor_yard`.

### Autoloads

| Сейчас | VS01 | Примечание |
|--------|------|------------|
| GameFlow | оставить | добавить `yard` / `house` routes |
| WorldState | расширить | tasks / interior_states / story_flags |
| Inventory | оставить | |
| DialogueUI | оставить | + короткие monologue JSON |
| PlayerProfile | оставить | occupation programmer |
| ChapterPresets | оставить | пресет `vs01_childhood_home` |
| DevConsole | оставить | |
| QuestState | **позже**, если tasks раздуются | пока tasks в WorldState |
| SaveManager | **не отдельно** | save внутри WorldState |

### Outdoor: слои

1. **Tile layers** (цель): `ground`, `grass`, `path`, `water`, `deco`  
   Сейчас допустим один Ground ImageTexture из единого tileset, затем TileMap.
2. **Object scenes** (`scenes/world/objects/`):
   - `yard_object.tscn` — база (id, type, hits, drop, solid)
   - инстансы: weed / rock / log / stump / bush
   - `house_entrance` (portal)
   - `tree` (solid trunk, не clearable в VS01)

### Interior: diorama

- BG neglected
- Overlay `workbench_repaired` (ColorRect/Sprite или смена BG)
- Hotspots: note/inspect, workbench repair, exit
- Limited walk + collisions

### Поток VS01

1. Spawn у дома (`story_flags.arrived_at_childhood_home`)
2. Расчистка пути (`tasks.clear_path_*`, `cleared_objects`)
3. Вход в дом (`entered_house`)
4. Осмотр верстака → цель материалов
5. Сбор scrap/wood на дворе
6. Ремонт → `interior_states.workbench_repaired` + visual
7. `first_signs_of_life_restored`

### UI contract

- DayLabel, InvLabel, ObjectiveLabel
- Player Prompt only (`E — …`)
- Plot progress one line (`Заросло · N/M`)
- **Нет:** HitTag на объектах, нижний help tip в player-режиме, имя над игроком (или очень тихо)

---

## План реализации (поэтапно)

### Фаза A — фундамент состояния + UI (этот шаг)

- Расширить WorldState
- Почистить HUD / теги
- `yard_object.gd` data-driven + multi-hit rock
- Пресет / objectives под VS01
- Документация

### Фаза B — outdoor structure

- `scenes/world/objects/yard_object.tscn`
- Компактный двор (меньше «песочницы»), без выбивающейся воды или вода из того же tileset
- House entrance → interior house

### Фаза C — interior VS01

- Записка / осмотр верстака
- Ремонт верстака + overlay
- Убрать обязательность Петра/Софьи из среза

### Фаза D — art pass

- Единый 16×16 pack, дом, персонаж (отдельный этап, см. ART_ASSET_BRIEF)

Не раздувать: farming, сезоны, NPC-сеть, машина, питомцы — вне VS01.
