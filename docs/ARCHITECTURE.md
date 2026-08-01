# ARCHITECTURE

Обновлено: 2026-08-01  
**Ориентир структуры (план):** [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)  
**Этот файл:** что **фактически** есть в репозитории сейчас (не идеальная целевая схема).

Приоритет документов: VISION → VERTICAL_SLICE → PROJECT_STRUCTURE → **этот файл** → PROJECT_STATUS.

---

## Terrain proof (факт)

| Элемент | Путь |
|---------|------|
| Ground atlas | `assets/art/outdoor/terrain_proof/terrain_ground.png` |
| Decor atlas | `assets/art/outdoor/terrain_proof/terrain_decor.png` |
| TileSet | `resources/tilesets/yard_ground_tileset.tres` |
| Factory | `scripts/tilesets/yard_terrain_tileset_factory.gd` |
| Scene | `scenes/locations/outdoor/childhood_home/yard_terrain_proof.tscn` |
| Generator | `tools/generate_terrain_proof.py` |
| Atlas tests | `tools/test_terrain_atlas.py` |

Слои proof-сцены: `GroundTerrain` (TileMapLayer, Match Corners) → `GroundDecoration` (TileMapLayer) → Player → Camera2D.  
Terrain Set 0: Grass (0) / Soil (1). Переходы не ставятся вручную — `set_cells_terrain_connect`.

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
