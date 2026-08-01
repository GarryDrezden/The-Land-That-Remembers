# PROJECT STATUS

Обновлено: 2026-08-01 (main_house_v1 in VS01 yard)

## Кратко

- **PixelLab hero v1** принят временно: idle+walk 8-dir, node scale `1.0`, display `PIXEL_DIV=2`.
- **Outdoor VS01:** `scenes/locations/outdoor/childhood_home/yard_vs01.tscn`.
- **Дом:** утвержденный `upload/houses/main_house_v1.png` → runtime `assets/art/outdoor/yard_vs01/main_house_v1.png` (integer ÷4, nearest).
- Дверь: hotspot «войти в дом» → stub interior `workshop`.
- Oversized fairy props не используются; старые art-test сцены не ломались.

## Следующее

1. Owner review `docs/art_tests/yard_vs01_*.png` с новым домом.
2. Настоящий interior дома детства (вместо workshop stub).
3. Не генерировать axe/pickaxe, пока двор/вход не подтверждены.
