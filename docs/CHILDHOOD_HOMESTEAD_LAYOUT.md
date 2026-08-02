# Childhood Homestead Layout

Обновлено: 2026-08-02  
Сцена: `scenes/locations/outdoor/childhood_home/yard_vs01.tscn`  
Локация id: `childhood_home_yard` (meta / zone schema)

## Ориентация дома

- Дом стоит у **северной** границы длинного участка.
- **Север / за домом:** деревенская улица (`village_street`, пока не playable).
- **Юг / перед домом:** двор — текущий видимый вход = **дворовый вход**.
- Уличная сторона дома и главный въезд со стороны улицы — зарезервированы (север карты / portal marker).

## ASCII-схема

```
Север / улица
        ↓
[улица и главный въезд]     house_front_or_street_edge  (reserved)
[дом]
[ближний двор]              near_house_yard             (playable VS01)
[хозяйственная зона]        utility_yard                (playable light)
[старый плодовый сад]       old_orchard                 (first fragment)
[будущий огород]            future_garden               (reserved tint)
[дальняя заросшая часть]    far_overgrown_plot          (locked / blocked)
        ↓
Юг / поле или лес
```

## Размер карты

| | Значение |
|--|----------|
| Tile | 16×16 |
| Playable plate | **44 × 84** tiles (704 × 1344 px) |
| Ground + pad | +8 tiles bleed (`GROUND_PAD_TILES`) |
| Ориентир | ~25–30 соток ощущением (длинный деревенский участок, не квадрат) |

Стартовая камера **не** показывает весь участок: zoom **2.4**, offset `(0,-36)` — дом + ближний двор.

## Зоны (tile rects)

| zone_id | tiles (x, y, w, h) | Сейчас |
|---------|--------------------|--------|
| `house_front_or_street_edge` | 5, 0, 34, 7 | reserved + inactive `VillageStreetPortal` |
| `near_house_yard` | 5, 7, 34, 15 | playable (дом, колодец, дрова, расчистка) |
| `utility_yard` | 5, 22, 34, 12 | shed / path south |
| `old_orchard` | 5, 34, 34, 16 | first orchard fragment |
| `future_garden` | 5, 50, 34, 16 | ground tint + faint scars only |
| `far_overgrown_plot` | 5, 66, 34, 18 | locked behind blockage @ ~y48.5 |

Markers: `HomesteadZones/<zone_id>` в сцене (F11 debug overlay).

## State schema (совместимо)

Хранится в `WorldState.meta.locations` (без ломки `cleared_objects`):

```json
{
  "locations": {
    "childhood_home_yard": {
      "zones": {
        "near_house_yard": { "state": "neglected", "cleared_count": 0 },
        "old_orchard": { "state": "reachable", "cleared_count": 0 },
        "future_garden": { "state": "locked" },
        "far_overgrown_plot": { "state": "locked" }
      }
    }
  }
}
```

`cleared_objects` / `yard_object.gd` продолжают работать как раньше (`plot_id=yard_vs01`).

## Плодовый сад — contract

Деревья: `scripts/world/fruit_tree_stub.gd`  
Стабильные id: `orch_apple_01`, `orch_apple_02`, `orch_apple_03`, `orch_pear_01`, `orch_dead_01`  
Ягоды: `orch_berry_currant_*`, `orch_berry_goose_01`, `orch_berry_rasp_01`

Будущие состояния дерева:

`neglected → cleared → pruned → treated → flowering → fruiting`  
также: `exhausted_or_diseased`, `removed`

### Будущий игровой цикл (roadmap only)

1. Расчистить пространство вокруг дерева  
2. Удалить сухие ветви  
3. Обрезать крону  
4. Вылечить / побелить  
5. Подпорки  
6. Сезон цветения / плодоношения  
7. Урожай более высокого качества  

Ресурсы (будущее): яблоки, груши, сливы, вишня, смородина, крыжовник, малина.  
Использование (будущее): свежая продажа, еда, варенье, компот, сок, сушка.

**Сейчас не реализовано:** урожай, обрезка, лечение, сезоны.

## Кандидаты ассетов

| Runtime | Source (upload) |
|---------|-----------------|
| `props/fruit_apple_a.png` | `trees-pixel-art/.../Fruit_tree1.png` |
| `props/fruit_apple_b.png` | `Fruit_tree2.png` |
| `props/fruit_pear.png` | `Fruit_tree3.png` |
| `props/fruit_dead.png` | `Broken_tree4.png` |
| `props/berry_currant.png` | `Bush_simple1_1.png` |
| `props/berry_gooseberry.png` | `Bush_simple2_1.png` |
| `props/berry_raspberry.png` | `Bush_simple1_2.png` |

Дом: `upload/houses/main_house_v1.png` → baked `main_house_v1.png` (eave seal pass).

## Переходы

| From | To | Status |
|------|-----|--------|
| yard door | workshop stub | active |
| north portal | `village_street` | **inactive marker only** |
| orchard blockage | far plot / garden | solid blockage + hint |

## Реализовано сейчас / только reserved

**Сейчас:** eave alpha fix, map 44×84, side fences full length, no false south fence, near yard preserved, utility path, orchard fragment, blockage, zone markers, zone state schema, clearables.

**Reserved:** street scene, garden beds, harvest, seasons, animal buildings, full far-plot exploration.
