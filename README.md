# The Land That Remembers

Уютная 2D-игра о восстановлении почти покинутого дома и участка через ручной труд, ремесло и отношения с людьми.

> Здесь было пусто и заброшено. Теперь здесь снова есть жизнь.

Краткое позиционирование: [docs/POSITIONING.md](docs/POSITIONING.md).

## Стек

- **Godot 4** (Standard) + **GDScript**
- Отрисовщик: **GL Compatibility**
- Данные квестов/диалогов: JSON в `data/`

## Быстрый старт

1. Установи [Godot 4](https://godotengine.org/download/windows/) (Standard, не .NET).
2. Project Manager → **Import** → укажи эту папку (где `project.godot`).
3. Нажми **F5** (или Play).
4. По умолчанию откроется **отладочный запуск** (режим разработчика).  
   Чтобы пройти как игрок: кнопка «Открыть как игрок» или Настройки → выключить режим разработчика.
5. Читай [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) и [docs/FLOW.md](docs/FLOW.md).

Язык проекта: **русский** — см. [docs/LANGUAGE.md](docs/LANGUAGE.md).

<!-- ASSET_CATALOG_BEGIN -->
# Где смотреть ассеты

1. Все категории: [docs/assets/catalog/categories/](docs/assets/catalog/categories/)

2. Все наборы: [docs/assets/catalog/packs/](docs/assets/catalog/packs/)

3. Большие визуальные таблицы: [docs/assets/catalog/contact_sheets/](docs/assets/catalog/contact_sheets/)

4. Выбор ассетов для игровых зон: [docs/assets/AREA_ASSET_SELECTIONS.md](docs/assets/AREA_ASSET_SELECTIONS.md)

5. Каталог внутри Godot: `res://scenes/debug/asset_gallery.tscn` (F6)

6. Машинный реестр: [`data/assets/asset_catalog.json`](data/assets/asset_catalog.json)

---

**Инструкция:** откройте категорию или набор, найдите нужную картинку и сообщите Cursor её **Asset ID**.

Пример:

> Для северной границы `yard_main` используй `TREE_…`, `BUSH_…` и `ROCK_…`.
> `HOUSE_MAIN_HOUSE_V1` — основной дом. Гигантские грибы из CraftPix не использовать.

## Обновить каталог после добавления файлов в `upload/`

```bash
python tools/build_asset_catalog.py
python tools/build_asset_catalog.py --check
```

`res://upload/` — **постоянный входящий склад**. Не удалять, не очищать, не переименовывать, не переносить целиком. Оригиналы не перезаписываются каталогом.

## Stats

- Packs (unpacked): **7**
- Zip-only inbox entries: **4**
- Images: **687**
- GIFs / animated: **9**
- Sprite sheets: **30**
- Categories present: animal, bush, crystal, effect, hero, house, interior, rock, terrain, tree

## Categories

- [houses](docs/assets/catalog/categories/houses.md)
- [heroes](docs/assets/catalog/categories/heroes.md)
- [characters](docs/assets/catalog/categories/characters.md)
- [trees](docs/assets/catalog/categories/trees.md)
- [bushes](docs/assets/catalog/categories/bushes.md)
- [rocks](docs/assets/catalog/categories/rocks.md)
- [weeds](docs/assets/catalog/categories/weeds.md)
- [flowers](docs/assets/catalog/categories/flowers.md)
- [logs](docs/assets/catalog/categories/logs.md)
- [stumps](docs/assets/catalog/categories/stumps.md)
- [mushrooms](docs/assets/catalog/categories/mushrooms.md)
- [fences](docs/assets/catalog/categories/fences.md)
- [terrain](docs/assets/catalog/categories/terrain.md)
- [water](docs/assets/catalog/categories/water.md)
- [props](docs/assets/catalog/categories/props.md)
- [animations](docs/assets/catalog/categories/animations.md)
- [unknown](docs/assets/catalog/categories/unknown.md)

## Packs

- [bushes-pixel-art](docs/assets/catalog/packs/bushes-pixel-art/README.md)
- [crystals-pixel-art](docs/assets/catalog/packs/crystals-pixel-art/README.md)
- [hero](docs/assets/catalog/packs/hero/README.md)
- [houses](docs/assets/catalog/packs/houses/README.md)
- [rocks-and-stones-top-down-pixel-art](docs/assets/catalog/packs/rocks-and-stones-top-down-pixel-art/README.md)
- [trees-pixel-art](docs/assets/catalog/packs/trees-pixel-art/README.md)
- [craftpix-main-characters-home](docs/assets/catalog/packs/craftpix-main-characters-home/README.md)

## Also

- Подробный индекс каталога: [docs/assets/README.md](docs/assets/README.md)
- Overrides: `data/assets/asset_catalog_overrides.json`

<!-- ASSET_CATALOG_END -->

## Управление (прототип)

| Клавиша | Действие |
|---------|----------|
| WASD / стрелки | Ходьба |
| E | Взаимодействие |
| Esc | Закрыть диалог |

## Вертикальный слайс (сейчас)

**Снаружи** — pixel-art двор / участок (tile-based, живые объекты).  
**Внутри** — painted-диорамы дома и ключевых мест (точки `E`).

Контекст для ассистентов: [docs/VISION.md](docs/VISION.md) · [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) · [docs/GDD_VERTICAL_SLICE_01.md](docs/GDD_VERTICAL_SLICE_01.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/PROTOTYPE_FEEDBACK.md](docs/PROTOTYPE_FEEDBACK.md) · [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md).

См. [docs/ART_DIRECTION.md](docs/ART_DIRECTION.md) · [docs/POSITIONING.md](docs/POSITIONING.md).

Подробности: [docs/POSITIONING.md](docs/POSITIONING.md) · [docs/MVP.md](docs/MVP.md) · [docs/ROADMAP.md](docs/ROADMAP.md) · [docs/COURSE.md](docs/COURSE.md) · [docs/CONCEPT.md](docs/CONCEPT.md) · [docs/FLOW.md](docs/FLOW.md) · [docs/LANGUAGE.md](docs/LANGUAGE.md) · [docs/ART_DIRECTION.md](docs/ART_DIRECTION.md)

## Репозиторий

https://github.com/GarryDrezden/The-Land-That-Remembers
