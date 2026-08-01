# PROJECT STATUS

Обновлено: 2026-08-01 (full 8-direction PixelLab hero)

## Кратко

- **PixelLab hero v1**: idle + walking in **8 directions** from `upload/hero/` → `assets/characters/player/pixellab_v1/`.
- Тест: `craftpix_hero_test.tscn` (основной двор / `craftpix_home_preview` не менялись).
- Node scale `Vector2.ONE` provisionally accepted; runtime display `PIXEL_DIV=2` (PNG на диске не трогаем).
- No mirroring; dedicated west/diagonal walk frames.
- Asset Catalog остаётся интерфейсом выбора props.

## Следующее

1. Владелец смотрит 8-dir скрины / `craftpix_hero_walk8.gif` и подтверждает героя.
2. Только после подтверждения — анимации топора / кирки.
3. Не начинать house restoration states.
