# Childhood Homestead Layout

Обновлено: 2026-08-02 (approved structures layout-pass)  
Сцена: `scenes/locations/outdoor/childhood_home/yard_vs01.tscn`  
Локация id: `childhood_home_yard`  
**Approved reference:** [art_direction/childhood_homestead_layout_target.png](art_direction/childhood_homestead_layout_target.png)

## Ориентация дома

- Дом у **северной** границы длинного участка.
- **Север / за домом:** деревенская улица (`village_street` — отдельная будущая сцена).
- **Юг / перед домом:** двор — текущий вход = **дворовый вход**.
- Северная калитка = inactive portal (не travel).

## ASCII-схема

```
Север / улица
        ↓
[N-Gate → village_street]   house_front_or_street_edge
[Дом] [Garage↗]
[ближний двор: Well, Doghouse]
[UtilityShed ←]             utility_yard
[старый сад + Outhouse→]    old_orchard
[Pond←] [RuinedBath→]       future_garden (partial / reserved)
[Greenhouse] [Compost]      future_garden reserved
[SouthBlockage]             far_overgrown_plot locked
        ↓
Юг
```

## Размер карты

| | Значение |
|--|----------|
| Tile | 16×16 |
| Playable plate | **44 × 84** tiles |
| Start camera | zoom **2.4**, offset `(0,-36)` — только ближний двор |

## Зоны

| zone_id | tiles (x,y,w,h) |
|---------|----------------|
| `house_front_or_street_edge` | 5, 0, 34, 7 |
| `near_house_yard` | 5, 7, 34, 15 |
| `utility_yard` | 5, 22, 34, 12 |
| `old_orchard` | 5, 34, 34, 16 |
| `future_garden` | 5, 50, 34, 16 |
| `far_overgrown_plot` | 5, 66, 34, 18 |

## Утверждённые объекты (layout table)

| Объект (node) | zone_id | Статус | Координаты feet (tiles) | Asset ID / placeholder | Будущая функция |
|---------------|---------|--------|-------------------------|------------------------|-----------------|
| `MainHouse` | near / street edge | available | 20.0, 13.8 | `HOUSE_MAIN_HOUSE_V1` | жилой дом, дворовый вход |
| `Garage` | near_house_yard | partial | 33.0, 12.2 | `BLOCKOUT_GARAGE_V1` | гараж / дровник, хранение |
| `UtilityShed` | utility_yard | available | 9.5, 26.0 | `BLOCKOUT_UTILITY_SHED_V1` | хозсарай (единственный) |
| `Well` | near_house_yard | available | 14.0, 17.4 | `YARD_WELL_DRAWN_V1` | вода (один колодец) |
| `Doghouse` | near_house_yard | available | 16.2, 14.0 | `BLOCKOUT_DOGHOUSE_V1` | будка |
| `Outhouse` | old_orchard | partial | 33.0, 41.0 | `BLOCKOUT_OUTHOUSE_V1` | уличный туалет |
| `Pond` | future_garden | partial | 11.5, 52.5 | `BLOCKOUT_POND_V1` | пруд / рыбалка позже |
| `RuinedBathhouse` | future_garden | reserved | 30.5, 53.5 | `BLOCKOUT_RUINED_BATH_V1` | ремонт бани |
| `GreenhouseReserved` | future_garden | reserved | 18.0, 58.5 | `BLOCKOUT_GREENHOUSE_V1` | теплица |
| `CompostReserved` | future_garden | reserved | 26.5, 60.5 | `BLOCKOUT_COMPOST_V1` | компост |
| `SouthBlockage` | far_overgrown_plot | locked | 20.0, 68.0 | `COMPOSITE_SOUTH_BLOCKAGE` | открытие дальнего участка |
| `VillageStreetPortal` / `NorthGateVisual` | street edge | reserved | 20.0, ~5.5 | `GATE_DRAWN_V1` | переход в `village_street` |

**Подтверждения layout-pass:**
- один колодец (`Well` only);
- верхний левый сарай **отсутствует** (нет ShedCorner / NW shed);
- `village_street` остаётся **отдельной** будущей сценой (inactive portal).

## Забор

Не идеальный периметр: секции `intact` / `leaning` / `broken` / `missing` / `overgrown`.  
Север: разрыв под калитку. Юг ближнего двора **не** замкнут сплошным забором.

## Плодовый сад — contract (без изменений цикла)

Stub-деревья / ягоды с stable ids; урожай / обрезка — roadmap only. См. предыдущий раздел contract в истории коммитов / `fruit_tree_stub.gd`.

## Переходы

| From | To | Status |
|------|-----|--------|
| yard door | workshop stub | active |
| north gate | `village_street` | **inactive** |
| SouthBlockage | far plot | locked |

## Реализовано / не делать

**Сейчас:** spatial layout объектов, коллизии, маршруты двор→сад→огород (до завала), broken fence, docs + reference PNG.

**Не делать в этом этапе:** ремонт, хранение, рыбалка, баня, теплица gameplay, компост gameplay, урожай, грядки, сезоны, сцена улицы.
