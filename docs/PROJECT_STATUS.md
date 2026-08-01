# PROJECT STATUS

Обновлено: 2026-08-01 (visual asset catalog)

## Кратко

- **PixelLab hero v1** принят временно: idle+walk 8-dir, node scale `1.0`, display `PIXEL_DIV=2`.
- **Outdoor VS01:** `scenes/locations/outdoor/childhood_home/yard_vs01.tscn`.
- **Дом:** `HOUSE_MAIN_HOUSE_V1` ← `upload/houses/main_house_v1.png`.
- **Каталог ассетов:** точка входа [`docs/assets/START_HERE.md`](assets/START_HERE.md); обновление `python tools/build_asset_catalog.py`.
- Oversized fairy props не используются как якоря; старые art-test сцены не ломались.

## Следующее

1. Owner выбирает Asset ID из каталога для зон двора (`AREA_ASSET_SELECTIONS.md`).
2. Review `yard_vs01` с домом; затем interior дома детства.
3. Не генерировать axe/pickaxe, пока двор/вход не подтверждены.
