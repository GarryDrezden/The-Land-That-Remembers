# PROJECT STATUS

Обновлено: 2026-08-02 (VS01 house sprite + composition fix)

## Кратко

- **PixelLab hero v1** принят временно: idle+walk 8-dir, node scale `1.0`, display `PIXEL_DIV=2`.
- **Outdoor VS01:** `scenes/locations/outdoor/childhood_home/yard_vs01.tscn` — карта больше одного экрана.
- **Дом:** `HOUSE_MAIN_HOUSE_V1`; runtime bake закрывает щели под крышей; display ≈ **0.88** nearest после ÷4; стартовая камера (zoom 2.2, offset вверх) показывает весь дом + дорожку + двор.
- **Каталог ассетов:** корневой [`README.md`](../README.md#где-смотреть-ассеты).

## Следующее

1. Owner review `docs/art_tests/yard_vs01_start.png` / `yard_vs01_door.png`.
2. Выбор растительности по Asset ID; затем interior дома детства.
3. Не генерировать axe/pickaxe, пока двор/вход не подтверждены.
