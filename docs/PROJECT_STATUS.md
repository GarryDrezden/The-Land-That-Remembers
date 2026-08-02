# PROJECT STATUS

Обновлено: 2026-08-02 (childhood homestead geography)

## Кратко

- **Основная outdoor-сцена VS01:** `scenes/locations/outdoor/childhood_home/yard_vs01.tscn`
- **Карта усадьбы:** **44×84** tiles (длинный участок на юг); layout: [CHILDHOOD_HOMESTEAD_LAYOUT.md](CHILDHOOD_HOMESTEAD_LAYOUT.md)
- **Дом:** `upload/houses/main_house_v1.png` → runtime bake **288×141** (eave seal pass); дворовый вход; улица на север (portal inactive)
- **Зоны:** near yard → utility → old orchard (fragment) → future garden / far plot (locked)
- **Герой / расчистка:** без изменений API (`yard_object` + `cleared_objects`); zone schema в `meta.locations`
- **Камера старта:** zoom **2.4**, offset `(0,-36)` — дом + ближний двор; участок уходит вниз за кадр

## Следующее

1. Owner playtest: двор → сад → завал; F11 зоны.
2. Interior дома детства (не workshop-stub).
3. Не делать урожай / грядки / сезоны без отдельного подтверждения.
