# ASSET INVENTORY

Обновлено: 2026-07-31 (после isolated Puny World art test)

Правила: [ART_ASSET_BRIEF.md](ART_ASSET_BRIEF.md) · ориентир: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) §20–21.

## Art test — кандидат outdoor pack

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

### Art gate (2026-07-31)

Сцена: `scenes/locations/outdoor/childhood_home/yard_art_test.tscn`  
Превью: `docs/art_tests/yard_art_test_puny_world.png` (+ `…_godot.png`)

| Критерий | Результат |
|----------|-----------|
| Визуальная цельность одного pack | да (только Puny) |
| Вода + берег из одного набора | да, читаемо, но «игрушечный» cyan |
| Персонаж не выпадает | **нет спрайта в Overworld** — walk-loop не проверялся |
| Препятствия читаются | да (камень, пень, кусты, сорняки-tufts) |
| Плотность farm/yard | слабая: больше «иконки на лужайке», чем заросший двор |
| Один размер пикселя | да (16×16, ×3 nearest) |
| Без стилистической смеси | да |
| Атмосфера «дом детства / остановившееся время» | **нет** — яркое fantasy-village |
| Можно собрать убедительный заросший двор | **сомнительно** без другого pack / кастомного арта |

**Вердикт:** Puny World **не утверждён** как временная основа прототипа «Земли, которая помнит». Технически пригоден для generic RPG meadow; для выгоревшего программиста и старого дома — слишком яркий и условный.

**Дыры pack (не маскировали):**
- нет walk-циклов персонажа (нужен отдельный Puny Characters — сознательно не подмешивали);
- нет бревна / fallen log;
- дома — крошечные fantasy-cottages, не советский сарай / старый загородный дом;
- «сорняки» — аккуратные tufts/цветы, не запустение.

---

## Прочие ассеты в репозитории

| Название / путь | Автор / источник | Лицензия | Коммерция | Модификация | Статус |
|-----------------|------------------|----------|-----------|-------------|--------|
| `assets/external/kenney_tiny_farm_sheet.png` | Kenney Tiny Farm | CC0 | да | да | reference / **не использовать в art test / дворе без gate** |
| `assets/objects/*.png` (weed, rock, log, stump, tree, farmhouse…) | project-generated | проект | да | да | временное, **не для единого outdoor** |
| `assets/characters/player_walk_sheet.png` | project-generated | проект | да | да | временное, **не подходит к Puny** |
| `assets/locations/*_interior_bg.png` | ранний painted прототип | проект | — | — | временное для interior |
| `assets/locations/outdoor_square_bg.png` | painted площадь | проект | — | — | архив |

Подробности CC0: `assets/external/ATTRIBUTION.txt`, `KENNEY_LICENSE.txt`.

## Запрещено

Прямые рипы Stardew Valley; ассеты без лицензии; запрет коммерции; AI-арт неизвестного происхождения как финал без решения владельца.
