# Где смотреть ассеты

1. Все категории: [docs/assets/catalog/categories/](catalog/categories/)

2. Все наборы: [docs/assets/catalog/packs/](catalog/packs/)

3. Большие визуальные таблицы: [docs/assets/catalog/contact_sheets/](catalog/contact_sheets/)

4. Выбор ассетов для игровых зон: [AREA_ASSET_SELECTIONS.md](AREA_ASSET_SELECTIONS.md)

5. Каталог внутри Godot: `res://scenes/debug/asset_gallery.tscn` (F6)

6. Машинный реестр: [`data/assets/asset_catalog.json`](../../data/assets/asset_catalog.json)

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

- [houses](catalog/categories/houses.md)
- [heroes](catalog/categories/heroes.md)
- [characters](catalog/categories/characters.md)
- [trees](catalog/categories/trees.md)
- [bushes](catalog/categories/bushes.md)
- [rocks](catalog/categories/rocks.md)
- [weeds](catalog/categories/weeds.md)
- [flowers](catalog/categories/flowers.md)
- [logs](catalog/categories/logs.md)
- [stumps](catalog/categories/stumps.md)
- [mushrooms](catalog/categories/mushrooms.md)
- [fences](catalog/categories/fences.md)
- [terrain](catalog/categories/terrain.md)
- [water](catalog/categories/water.md)
- [props](catalog/categories/props.md)
- [animations](catalog/categories/animations.md)
- [unknown](catalog/categories/unknown.md)

## Packs

- [bushes-pixel-art](catalog/packs/bushes-pixel-art/README.md)
- [crystals-pixel-art](catalog/packs/crystals-pixel-art/README.md)
- [hero](catalog/packs/hero/README.md)
- [houses](catalog/packs/houses/README.md)
- [rocks-and-stones-top-down-pixel-art](catalog/packs/rocks-and-stones-top-down-pixel-art/README.md)
- [trees-pixel-art](catalog/packs/trees-pixel-art/README.md)
- [craftpix-main-characters-home](catalog/packs/craftpix-main-characters-home/README.md)

## Also

- Legacy index: [README.md](README.md)
- Overrides: `data/assets/asset_catalog_overrides.json`
