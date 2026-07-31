# ASSET INVENTORY

Обновлено: 2026-07-31 (generated outdoor art test v2)

Правила: [ART_ASSET_BRIEF.md](ART_ASSET_BRIEF.md) · ориентир: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) §20–21.

## Art test v2 — candidate generated outdoor pack

| Поле | Значение |
|------|----------|
| Asset ID | `generated_outdoor_test_v2` |
| Название | AI-generated outdoor prototype sheets (terrain / player / vegetation / house) |
| Источник | пользовательские сгенерированные листы (не production pack) |
| Лицензия / происхождение | AI-generated prototype — **не финальные ассеты** |
| Файлы source | `assets/art/outdoor/generated_test/source/*` (не перезаписывать) |
| Файлы processed | `assets/art/outdoor/generated_test/processed/{terrain,player,vegetation,obstacles,buildings,water}/` |
| Сцена | `scenes/locations/outdoor/childhood_home/yard_art_test_v2.tscn` |
| Статус | **candidate generated outdoor pack — art test v2** (не production-final; в DECISIONS не фиксировать как финал) |

### Технический аудит source

| Файл | Прозрачность | Сетка | Замечания |
|------|--------------|-------|-----------|
| `terrain_water_rocks_weeds.png` | нет (opaque black) | нет регулярной | переходы/вода/сорняки кусками; нет seamless 16×16 grass/water tileset |
| `player_sheet.png` | нет (opaque black) | 4×5 content bands | нет left-facing; dark interior pixels ломаются при naive color-key |
| `vegetation_obstacles.png` | нет (opaque black) | нет | oak/birch ок; spruce на листе заметно ниже; базы с «островками» земли |
| `house_modules.png` | нет (opaque black) | нет | цельный дом + модули; CC-нарезка |
| `composition_reference.png` | n/a | n/a | **только mood-референс**, не gameplay texture |

Обработка: `tools/process_generated_outdoor_v2.py` — flood-fill bg с краёв, явные player bands, baked ground/pond как временное решение.

Превью: `docs/art_tests/yard_art_test_v2_start.png`, `…_behind_oak.png`, `…_house_path.png`  
Аудит JSON: `docs/art_tests/generated_test_v2_audit.json`

### Art gate (предварительный, v2)

| Критерий | Результат |
|----------|-----------|
| Направление / детализация ближе к target, чем Puny | **да** (стиль promising) |
| Большая карта / камера не видит край со старта | да (2048×1536, zoom 2) |
| Персонаж 4 направления idle/walk | да (left = flip right) |
| Y-sort / проход за кроной | частично да (дерево/кусты) |
| Вода + берег без ColorRect | да, но **временный pond bake** из кусков |
| Terrain как production tileset | **нет** — baked stamps, видны швы/дыры |
| Чистая нарезка без артефактов | **частично** — fringe, dirt islands, mis-classified chunks |
| Пригодность как production outdoor base | **нет без перегенерации / ручной доводки** |

**Вердикт:** направление арта **кандидат** на следующую итерацию; текущие листы **не готовы** как production tileset/sprites без новой генерации с alpha, ровным pixel grid и согласованным масштабом (особенно spruce / seamless terrain / cleaner player edges).

---

## Art test v1 — Puny World (отклонён)

| Поле | Значение |
|------|----------|
| Asset ID | `puny_world_overworld` |
| Название | 16×16 Puny World Overworld Tileset |
| Автор | Shade (merchant-shade) |
| Источник | https://opengameart.org/content/16x16-puny-world-tileset · https://merchant-shade.itch.io/16x16-puny-world |
| Лицензия | CC0 |
| Коммерческое использование | да |
| Модификация | да |
| Файлы в репозитории | `assets/external/punyworld_overworld.png`; срезы art test: `assets/art/outdoor/puny_world/**` |
| Статус | **art-tested / NOT approved for prototype yard** |

Сцена: `scenes/locations/outdoor/childhood_home/yard_art_test.tscn`  
Превью: `docs/art_tests/yard_art_test_puny_world.png` (+ `…_godot.png`)

**Вердикт:** Puny World **не утверждён** как основа прототипа (недостаточная детализация относительно DEC-005 target).

---

## Прочие ассеты в репозитории

| Название / путь | Автор / источник | Лицензия | Коммерция | Модификация | Статус |
|-----------------|------------------|----------|-----------|-------------|--------|
| `assets/external/kenney_tiny_farm_sheet.png` | Kenney Tiny Farm | CC0 | да | да | reference / **не использовать без gate** |
| `assets/objects/*.png` | project-generated | проект | да | да | временное |
| `assets/characters/player_walk_sheet.png` | project-generated | проект | да | да | временное |
| `assets/locations/*_interior_bg.png` | ранний painted прототип | проект | — | — | временное для interior |
| `assets/locations/outdoor_square_bg.png` | painted площадь | проект | — | — | архив |

Подробности CC0: `assets/external/ATTRIBUTION.txt`, `KENNEY_LICENSE.txt`.

## Запрещено

Прямые рипы Stardew Valley; ассеты без лицензии; запрет коммерции; AI-арт неизвестного происхождения как финал без решения владельца.
