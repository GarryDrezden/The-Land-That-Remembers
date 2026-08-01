# DECISIONS

Принятые архитектурные и продуктовые решения.  
Новые записи — сверху. Формат: ID, решение, причина, последствия, статус.

---

## DEC-009: Permanent asset inbox + stable Asset Catalog

**Решение:**
- `res://upload/` is the **permanent incoming asset inbox** and **must not be deleted**;
- every imported visual asset receives a **stable Asset ID**;
- GitHub Markdown contact sheets (`docs/assets/`) are the **primary owner-facing selection interface**;
- runtime scenes use **only explicitly selected** assets copied/prepared under `assets/third_party/`;
- catalog is regenerated with `python tools/build_asset_catalog.py` (idempotent IDs; `--check` for staleness).

**Последствия:**
- не авто-копировать всё из `upload/` в runtime;
- выбор зон фиксируется в `docs/assets/AREA_ASSET_SELECTIONS.md` + `data/assets/area_asset_selections.json` (пока без gameplay wiring);
- debug gallery: `scenes/debug/asset_gallery.tscn`.

**Статус:** принято · 2026-08-01

---

## DEC-008: CraftPix Main Character’s Home — under evaluation

**Решение:**
- пакет CraftPix **Main Character’s Home** рассматривается как кандидат на **primary outdoor and house visual base**;
- **не утверждён финально** до просмотра preview и подтверждения владельцем проекта;
- ассеты хранятся в `assets/third_party/craftpix/main_characters_home/` и могут коммититься в Git — **project owner reports that explicit permission was obtained** to store/publish these source files in this repository;
- procedural / AI / Puny World outdoor experiments остаются документами, не смешиваются с CraftPix preview.

**Факты аудита:**
- tile size **16×16** (TMX);
- есть demo `Exterior.tmx` / `Interior1.tmx`;
- **нет** Wang/Terrain Set;
- **нет** human character (есть cat/birds).

**Последствия:**
- сцена `craftpix_home_preview.tscn` — отдельный F6 preview;
- нужен отдельный совместимый character pack;
- GameRoot не начинать до утверждения базы.

**Статус:** under evaluation · 2026-08-01

---

## DEC-007: Generated outdoor pack v2 — technical gate failed

**Решение:**
- визуальное направление и mood (**DEC-005 / DEC-006**) — **approved**;
- generated outdoor pack v2 как production / game-ready assets — **rejected**;
- файлы в `assets/art/outdoor/generated_test/` сохраняются **только как visual references**, не как интеграционные ассеты.

**Причина отказа (технический gate, не арт-направление):**
1. внутренний масштаб изображений не соответствует сетке 16×16;
2. элементы имеют разные размеры пикселя;
3. террейн не бесшовный и не является настоящим autotile;
4. в объекты запечены земля, трава и тени → слои накладываются;
5. перспектива персонажа, дома и окружения не согласована;
6. прозрачность и края непригодны для прямой интеграции;
7. невозможно корректно настроить композицию, Y-sort и коллизии без подготовки настоящих игровых ассетов.

**Последствия:**
- сцена `yard_art_test_v2.tscn` **не удаляется** — документированный неудачный эксперимент;
- не использовать generated sheets в основном дворе / GameRoot;
- следующий шаг — утвердить **логический масштаб мира** (`yard_scale_test`) до производства новой графики;
- GameRoot не начинать.

**Статус:** принято · 2026-07-31

---

## DEC-006: Outdoor visual target images approved

**Решение:** утверждён визуальный target наружного мира.

- **Mood / quality:** `docs/art_direction/outdoor_target_yard_mood.png` — пруд, rustic house, dense vegetation, adult protagonist.  
- **Scope only:** `docs/art_direction/outdoor_target_asset_scope.png` — чеклист категорий ассетов.  
- Оба файла — **референсы**, не game-ready tileset / не прямое подключение в движок.

Параметры: 16×16; персонаж ~1×2; multi-tile trees; карта > экрана; неправильные заросли; естественный пруд; тёплая приглушённая палитра; высокая плотность; «дом детства + ручной труд + заросший участок».

Направление (подтверждение DEC-005):

> original detailed Stardew-like outdoor pixel art with rural childhood-home identity

**Puny World** остаётся отклонённым как основная outdoor-база ([DEC-004](DECISIONS.md)).

**Не делать сейчас:** GameRoot.  
**Дальше:** утвердить план [OUTDOOR_ASSET_PACK_01.md](OUTDOOR_ASSET_PACK_01.md) и выбрать production path.

**Статус:** принято · 2026-07-31

---

## DEC-005: Outdoor art direction — detailed Stardew-like + Eastern European identity

**Решение:** наружный мир ориентируется на **detailed Stardew-like** pixel art как основной структурный и художественный референс (детализация, композиция пространства, масштаб персонажа и объектов, плотность растительности, общая «приятность» кадра). Идентичность проекта — **сельский / восточноевропейский** дом детства, не generic fantasy meadow.

Формулировка направления:

> original detailed Stardew-like outdoor pixel art with project-specific rural/Eastern European identity

**Разрешено:** использовать Stardew Valley как референс по уровню и устройству картинки.  
**Запрещено:** копировать / рипать ассеты Stardew.

**Не делать:** намеренно искать стиль, далёкий от Stardew, «лишь бы не похоже».

**Следующий шаг (не GameRoot):** выбрать способ производства цельного outdoor-набора:

1. подходящий коммерческий pack нужного уровня; или  
2. собственный tileset; или  
3. единый pack + профессиональная дорисовка недостающих элементов (дом, персонаж, clutter, вода/берег).

**Статус:** принято · 2026-07-31

---

## DEC-004: Puny World Overworld — art gate не пройден для прототипа

**Решение:** не утверждать Puny World как временную основу наружного двора.

**Причина (уточнено DEC-005):** отказ **не** из‑за «близости к Stardew» и не из‑за pixel-art как такового. Puny недостаточен по **уровню**: детализация, размер деревьев, персонаж, вода, набор объектов и плотность не дотягивают до требуемого Stardew-like качества и сельской идентичности дома детства. Art test 2026-07-31 это подтвердил.

**Последствия:** основной двор на Puny не собирать; искать production path по DEC-005. GameRoot не начинать до выбора способа производства арта.

**Статус:** принято · 2026-07-31 (причина уточнена)

---

## DEC-001: В интерьерах не отображается pixel-art персонаж

**Решение:** в painted-интерьерах маленький pixel-art персонаж не ходит по сцене. Игрок — точка зрения; взаимодействие через hotspots (E / фокус).

**Причина:** конфликт визуальных языков (пиксель-фигурка поверх живописной диорамы разрушает восприятие) — см. [PROTOTYPE_FEEDBACK.md](PROTOTYPE_FEEDBACK.md), [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) §3.1 / §14.

**Последствия:**

- нужен отдельный hotspot-контроллер / InteriorController;
- PlayerOutdoor в интерьере скрыт и не двигается;
- UI: тонкая подсветка + одна строка `E — …`, без постоянных лейблов.

**Статус:** принято · 2026-07-31

---

## DEC-002: Outdoor и interior — разные режимы, не одна «карта»

**Решение:** наружный мир — tile + objects + Y-sort; интерьер — diorama + state layers.

**Причина:** единый гибрид (pixel character on painted BG) провалил art/feel тест.

**Статус:** принято · 2026-07-31

---

## DEC-003: Изменяемые объекты — не тайлы и не фон

**Решение:** clearables / repairables / plants / buildings — отдельные сцены со стабильным `object_id`; тайлы только для относительно статичной земли/воды/пола.

**Статус:** принято · 2026-07-31
