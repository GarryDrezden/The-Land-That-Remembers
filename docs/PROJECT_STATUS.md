# PROJECT STATUS

Обновлено: 2026-08-02 (playable VS01 childhood yard)

## Кратко

- **Основная outdoor-сцена VS01:** `scenes/locations/outdoor/childhood_home/yard_vs01.tscn`
- **Старт главы:** Debug → «VS01 — Дом детства» (`GameFlow.apply_chapter("vs01_childhood_home")`)
- **Дом:** `upload/houses/main_house_v1.png` → runtime `assets/art/outdoor/yard_vs01/main_house_v1.png` (**288×151**, nearest, binary alpha)
- **Герой:** PixelLab v1 из `upload/hero/` → `assets/characters/player/pixellab_v1/` (`PIXEL_DIV=2`, 8-dir idle/walk)
- **Двор:** кусты/деревья/камни из CraftPix upload-паков; расчистка через `yard_object.gd` + `WorldState.cleared_objects`
- **Камера:** zoom **2.4**, offset `(0,-36)`, limits по padded grass

## Следующее

1. Owner playtest: ходьба, E-расчистка, вход в дом (stub workshop), калитка-hint.
2. Точечная правка alpha под карнизом дома (без чёрных плит), если owner подтвердит.
3. Interior дома детства (не workshop-stub).
4. Не трогать axe/pickaxe / farming, пока двор принят.
