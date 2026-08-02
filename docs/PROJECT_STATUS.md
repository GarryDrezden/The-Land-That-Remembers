# PROJECT STATUS

Обновлено: 2026-08-02 (house scale restore + camera 2.0)

## Кратко

- **PixelLab hero v1** принят временно: idle+walk 8-dir, node scale `1.0`, display `PIXEL_DIV=2`.
- **Outdoor VS01:** `yard_vs01.tscn` — карта больше одного экрана; grass pad вокруг пластины.
- **Дом:** runtime **288×151** nearest (без ×0.88); node/sprite scale `1`; conservative alpha clean.
- **Камера:** zoom **2.0**, offset `(0,-42)`, limits по padded ground.
- **Каталог ассетов:** корневой [`README.md`](../README.md#где-смотреть-ассеты).

## Следующее

1. Owner review `docs/art_tests/yard_vs01_start.png` / door / path_down / eave_*.
2. Выбор растительности по Asset ID; затем interior дома детства.
3. Не генерировать axe/pickaxe, пока двор/вход не подтверждены.
