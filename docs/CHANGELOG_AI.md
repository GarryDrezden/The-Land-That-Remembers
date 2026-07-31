# CHANGELOG AI

Формат: дата → что сделано → файлы → что осталось.

## 2026-07-31 (e) — isolated Puny World art test

**Цель:** проверить Puny World Overworld как временную outdoor-основу без перестройки прототипа.

**Сделано:**
- сцена `yard_art_test.tscn` + `scripts/debug/yard_art_test.gd` (WASD probe без спрайта, E-расчистка + dust VFX, shimmer пруда, F12/ART_TEST_SHOT);
- нарезка только из `punyworld_overworld.png` → `assets/art/outdoor/puny_world/`;
- tool `tools/build_puny_art_test.py`;
- скрины `docs/art_tests/yard_art_test_puny_world*.png`;
- art gate: **не пройден** для атмосферы проекта (см. ASSET_INVENTORY).

**Не делалось:** GameRoot, двор, save, interiors, правки outdoor_square / pixel_yard_art.

**Проверки:** Godot 4.7.1 — сцена запускается, auto-shot ок; Python preview ×3 nearest.

**Осталось:** решение владельца по следующему кандидату pack / этапу.

---

## 2026-07-31 (d) — PROJECT_STRUCTURE

**Сделано:** добавлен обязательный ориентир структуры + VISION/DECISIONS; обновлены AGENTS и ARCHITECTURE priority.

**Файлы:**
- `docs/PROJECT_STRUCTURE.md` (новый)
- `docs/VISION.md`, `docs/DECISIONS.md` (новые)
- `docs/ARCHITECTURE.md`, `AGENTS.md`, `docs/CHANGELOG_AI.md`, `docs/PROJECT_STATUS.md`, `docs/NEXT_STEPS.md`

**Осталось:** не начинать массовую миграцию без согласования art test / этапа 0–1; ответить владельцу аудитом по §26.

---

## 2026-07-31 (c) — фаза A VS01

**Сделано:** анализ vs vision; architecture; фундамент VS01.

**Файлы:**
- `docs/ARCHITECTURE.md`, `PROJECT_STATUS.md`, `VERTICAL_SLICE_01.md`, `AGENTS.md`
- `scripts/systems/world_state.gd` — tasks / interior / story / cleared_objects
- `scripts/world/yard_object.gd` — multi-hit
- `scripts/world/outdoor_square.gd`, `workshop_interior.gd`, `workbench.gd`, `scene_art.gd`
- `scripts/ui/hud.gd`, `scripts/systems/dialogue_ui.gd`, `chapter_presets.gd`
- `data/dialogues/workbench_repair.json`

**Осталось:** TileMap + единый art pack; вода/дом/персонаж; object `.tscn`; VFX.

---

**Сделано:** зафиксированы замечания владельца по прототипу.

**Файлы:** `docs/PROTOTYPE_FEEDBACK.md`; обновлены `docs/PROJECT_STATUS.md`, `docs/NEXT_STEPS.md`.

**Суть:** двор лоскутный; вода/дом/персонаж слабые; UI-шум; interior идея сильнее outdoor; цель — маленький художественно убедительный срез, не тестовая карта.

**Осталось:** единый pack + дом + персонаж + UI-чистка → затем вертикальный срез.

---

## 2026-07-31

**Сделано:** зафиксированы 4 контекстных брифа + handoff-доки для ассистентов.

**Файлы:**

- `docs/VISION_BRIEF.md`
- `docs/GDD_VERTICAL_SLICE_01.md`
- `docs/CURSOR_IMPLEMENTATION_BRIEF.md`
- `docs/ART_ASSET_BRIEF.md`
- `docs/PROJECT_STATUS.md`
- `docs/ARCHITECTURE.md`
- `docs/VERTICAL_SLICE_01.md`
- `docs/ASSET_INVENTORY.md`
- `docs/CHANGELOG_AI.md`
- `docs/NEXT_STEPS.md`
- обновлены ссылки в `README.md`

**Осталось:** рефактор outdoor под TileMap + object scenes; вертикальный срез «дом детства»; единый pixel pack; многоударные камни.

---

## Ранее (кратко, по сессии прототипа)

- MVP: печь Софьи, верстак, сон, bakery visual diff
- Outdoor pixel yard, расчистка, коллизии, Puny World tiles
- Документы COURSE / ART_DIRECTION / POSITIONING
