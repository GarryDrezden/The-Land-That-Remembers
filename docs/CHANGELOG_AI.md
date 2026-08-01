# CHANGELOG AI

Формат: дата → что сделано → файлы → что осталось.

## 2026-08-01 (o) — integrate approved main_house_v1 into VS01 yard

**Сделано:**
- `upload/houses/main_house_v1.png` принят как базовый exterior стартового дома;
- runtime: keyed crop + nearest ÷4 → `assets/art/outdoor/yard_vs01/main_house_v1.png` (278×146);
- сцена `yard_vs01`: отдельный узел `MainHouse` (sprite + collision + DoorHotspot);
- дверь → stub interior `workshop`; герой ~71% высоты двери; скрины обновлены.

**Не делалось:** настоящий interior дома детства, axe/pickaxe, farming/NPC.

---

## 2026-08-01 (n) — first proper VS01 yard around hero scale

**Сделано:**
- новая сцена `yard_vs01.tscn` (+ layout twin) — двор детства, путь от калитки к двери;
- ассеты `assets/art/outdoor/yard_vs01/` (ground bake, izba placeholder, fence/well/woodpile/shed, scaled props из upload);
- 4 обязательных clearable на пути + optional сорняки; Y-sort + коллизии; PixelLab hero без смены scale;
- скрины `docs/art_tests/yard_vs01_*.png`; DEC-011.

**Не делалось:** финальный house art, interior, axe/pickaxe, ломка старых test-сцен.

---

## 2026-08-01 (m) — full eight-direction PixelLab hero walk

**Сделано:**
- полный комплект GIF в `upload/hero/` (idle 8-dir + walk ×8);
- импортёр обновлён: preserve GIF transparency, shared baseline, `walk/<dir>/`, contact sheets;
- player: 16 SpriteFrames (idle+walk ×8), WASD angle facing, no flip_h;
- тест-скрины idle/walk ×8, door/gate/outside/tree/collisions + `craftpix_hero_walk8.gif`;
- docs + DEC-010; основной двор не тронут.

**Не делалось:** axe/pickaxe, house restoration, смена scale без ревью.

---

## 2026-08-01 (l) — PixelLab hero walking prototype

**Сделано:**
- аудит GIF в `upload/hero/` → `docs/HERO_PIXEL_LAB_AUDIT.md`;
- импортёр `tools/import_pixellab_hero.py` (flood-fill chroma, baseline align, contact sheets);
- runtime `assets/characters/player/pixellab_v1/`;
- `player_pixellab_test.tscn` + `craftpix_hero_test.tscn` (оригинальный CraftPix preview не тронут);
- walk south/east, west=flip, north=idle_north; скрины двери/калитки/дерева/коллизий/scale.

**Не делалось:** генерация north walk, axe/pickaxe, смена основного двора.

---

**Сделано:**
- постоянный INBOX `upload/` (убран из `.gitignore`; не удалять);
- генератор `tools/build_asset_catalog.py` (идемпотентные Asset ID, previews, contact sheets, Markdown, `--check`);
- реестр `data/assets/asset_catalog.json` + packs + overrides + area_asset_selections;
- GitHub catalog: `docs/assets/README.md`, category pages, pack pages;
- debug gallery `scenes/debug/asset_gallery.tscn`;
- DEC-009; обновлены THIRD_PARTY_ASSETS / ASSET_INVENTORY / ARCHITECTURE.

**Не делалось:** перестройка CraftPix preview, GameRoot, runtime wiring AREA selections.

---

## 2026-08-01 (j) — polish CraftPix home preview (gate / hedge / collisions)

**Сделано:**
- калитка: убраны closed gate-tiles; дорожка (Road) читается через проём x=16–17;
- вход: очищены Objects + Grass_details* + Grass_top_details в коридоре; с path сняты Grass-hedge тайлы exterior (они же давали «разрезанный»/шумный вид);
- orphan south-edge props убраны; incomplete mushroom leftovers у проёма сняты;
- коллизии: fence кроме проёма + house; CLI debug-оверлеи cyan/orange на gate_collisions shot;
- Y-sort: Grass overlays на ground (не над игроком); player z absolute;
- скрины overview / gate / outside / gate_collisions.

**Не делалось:** смена art direction, GameRoot, character pack, farming.

---

## 2026-08-01 (i) — polish CraftPix home preview

**Сделано:**
- южная калитка: убраны закрытые gate-tiles (gid 788/789) на колонках дорожки — явный проход;
- коллизии: fence кроме проёма + house walls + tree/exterior footprints (не каждый decor);
- очищен входной коридор (кусты/грибы/декор у калитки);
- убраны срезанные/orphan props на южном крае;
- скрины gate / outside / gate_collisions.

**Не делалось:** смена art direction, GameRoot, character pack.

---

## 2026-08-01 (h) — CraftPix home pack audit + outdoor preview

**Сделано:**
- аудит CraftPix Main Character’s Home (`docs/CRAFTPIX_HOME_AUDIT.md`, `THIRD_PARTY_ASSETS.md`);
- организация в `assets/third_party/craftpix/main_characters_home/` (source + runtime); `__MACOSX` / `upload/` удалены;
- экспорт кропа `Exterior.tmx` → `runtime/preview/exterior_preview_layout.json`;
- сцена `craftpix_home_preview.tscn` (CraftPix only, nearest, integer scale, Y-sort, blockers, нейтральный силуэт);
- скрины `docs/art_tests/craftpix_home_preview*.png` + tiled reference;
- DEC-008: pack under evaluation.

**Не делалось:** GameRoot, основной двор, interior gameplay, финальное утверждение pack, character pack.

---

## 2026-08-01 (g) — macro variation seamless grass/soil

**Принята техническая система.** Предыдущий detail pass отклонён как слишком слабый на game scale.

**Сделано:**
- atlas ground → 12×4: masks + grass macros (light/dark/sparse/dense) + soil macros + edge/corner visual variants (same bits, same borders);
- кластеры 2–4 клеток (не шахматка); base~65% / subtle~20% / light+dark~10% / dense~5%;
- readable decor overlays (tufts, clover, flowers, soil pebbles/clumps/root/sprout);
- простая soil shape ~9×7 (wide protrusion + soft indent);
- compare before/after: `terrain_macro_compare.png`;
- `test_terrain_atlas.py` — OK (включая border match edge variants).

**Не делалось:** персонаж, деревья, вода, дом.

---

## 2026-08-01 (f) — terrain visual detail pass

**Без изменения** tile size / masks / Terrain Set / seam contract / atlas layout (ground 8×4).

**Сделано:**
- richer grass interiors (5 close greens, low-freq density, 2–3px clusters, short blades);
- moist packed-earth soil (soft dark patches, clumps, rare pebbles/roots);
- stronger grass↔soil fringe (shared edge profiles still pixel-identical);
- decor atlas → 16 overlays (blades, dense growth, white/yellow flowers, pebbles, twig, dark/dense patches);
- sparse clustered decor placement; shots without placeholder character;
- `test_terrain_atlas.py` — OK.

**Не делалось:** character art, paths, house, water, trees.

---

## 2026-08-01 (e) — visual pass: seamless grass/soil art

**Система бесшовного terrain принята.** Только художественное улучшение атласов / shapes / decor.

**Сделано:**
- richer grass interiors (3–4 greens, clusters, short blades, soft dark patches); weights 65/20/10/5;
- warmer packed-earth soil (clumps, pebbles, root fibers) — не песок / не noise-filter;
- fringe 1–3px на grass→soil; shared edge profiles / seam contract сохранены;
- decor overlays: tufts, white+yellow flower, pebbles, twig;
- soil shapes ~9×7 (wide protrusion + shallow concave), без 1-cell tails;
- скрины без персонажа/debug: `terrain_visual*.png` + ×4 crops;
- `test_terrain_atlas.py` — OK.

**Не делалось:** персонаж, paths, дом, вода, деревья.

---

## 2026-08-01 (d) — deterministic seamless grass/soil terrain proof

**Стоп AI-sheet slicing.** Присланные листы = mood/palette reference only.

**Сделано:**
- `tools/generate_terrain_proof.py` → `terrain_ground.png` (16 corner masks + grass/soil variants) + `terrain_decor.png`;
- shared edge profiles (marching-squares seam contract); wraparound full grass/soil;
- `tools/test_terrain_atlas.py` (opaque ground, alpha decor, borders, 16 masks, seam pairs);
- `scripts/tilesets/yard_terrain_tileset_factory.gd` + `resources/tilesets/yard_ground_tileset.tres`
  (Terrain Set 0, Match Corners, Grass/Soil, probability on variants);
- сцена `yard_terrain_proof.tscn`: GroundTerrain + GroundDecoration TileMapLayer, `set_cells_terrain_connect`, player;
- скрины `terrain_seamless*.png`.

**Не делалось:** дом, вода, деревья, основной двор, production art density.

---

## 2026-08-01 (c) — tileset_v2 clustered grass + framed soil

**Источник:** новый grass/soil sheet (temporary).

**Сделано:**
- extract `tileset_v2/tiles` (11×7 → 32px);
- `tools/bake_terrain_tileset_v2.py`: grass base/var/dark/dense/flower **кластерами** (не шахматка);
- soil center + edge/corner frame; один variant на каждую сторону края;
- props: bush + rock + 1 weed;
- скрины `terrain_hero_proof_v2.png`, `…_v2_grid.png`.

**Не делалось:** production tileset, полный autotile, большой двор.

---

## 2026-08-01 (b) — soil patch as framed border

**Принцип:** центр = full soil; снаружи = full grass; периметр = edge/corner only.

**Сделано:**
- `tools/bake_soil_patch_framed.py` — ручная простая прямоугольная форма 6×4;
- role map: `ref_proto/roles/` + `terrain_plate_roles.txt`;
- недостающие bottom/side/corners — flip/rot от явных top/NW (sheet неполный);
- скрины `terrain_hero_proof_framed.png`, `…_framed_grid.png`.

**Не делалось:** полный Godot Terrain/autotile, сложные вогнутые формы.

---

## 2026-08-01 (a) — temporary terrain ref-proto tiles

**Источник:** присланный rural tileset sheet (temporary prototype only).

**Сделано:**
- `tools/prep_terrain_ref_proto.py` — вырезка grass / bare soil / transition (~3× display → 32px);
- baked `terrain_plate.png` (12×8 @32px) с неровным soil island;
- сцена: герой + bush + rock на маленьком участке; без дерева/сорняков/дома/пруда;
- скрины `terrain_hero_proof_ref_proto*.png`.

**Не делалось:** production tileset, autotile system, GameRoot, расширение двора.

---

## 2026-07-31 (n) — terrain + hero proof (narrow)

**Цель:** стабилизировать основу — не расширять объекты.

**Сделано:**
- `tools/prep_terrain_hero_proof.py` → `texture_proof_v1/terrain/` (`grass_16`, `dirt_16`, `terrain_plate` 384×240);
- ground: backdrop + текстурированная plate (трава + dirt + неровная граница), без autotile;
- герой: opaque binary alpha, idle/walk, speed 72, диагональ `limit_length(1)` + anim по dominant axis;
- объекты только: 1 дерево, 1 куст, 1 камень, 3 сорняка;
- скрины `docs/art_tests/terrain_hero_proof_{terrain,idle,walk,walk_diag,props}.png`.

**Не делалось:** дом, пруд, GameRoot, полный outdoor, новая scale-pass.

---

## 2026-07-31 (m) — texture proof v1 integration cleanup

**Причина:** v1 rejected — полупрозрачный герой, ломалась диагональная анимация, кривые baseline/offset.

**Исправлено:**
- binary alpha + hole-fill на player frames; `modulate.a=1`; pivot ног (`offset=(-12,-32)`, centered=false);
- диагональ: анимация по dominant axis (на 45° — last facing); left = prototype flip;
- сцена урезана до минимального фрагмента: grass + dirt patch + 1 tree + 1 bush + 1 rock + 3 weeds + player;
- единый feet baseline для спрайтов; убраны дом/пруд/ель/прочие силуэты;
- коллизии: ствол / основание props / ноги героя.

**Скрины:** `docs/art_tests/yard_texture_test_v1_{idle,walk,near_tree,behind_tree,debug}.png`

**Не делалось:** новые ассеты, полный terrain, GameRoot.

---

## 2026-07-31 (l) — outdoor texture proof v1 (candidate)

**Сделано:**
- greybox scale lock принят (без перестройки карты);
- `tools/prep_texture_proof_v1.py` → `assets/art/outdoor/texture_proof_v1/` (точные canvas sizes, alpha, NEAREST);
- сцена `yard_texture_test_v1.tscn` — копия greybox layout; текстуры только на player + 1 дерево + 1 ель + bush/rock/log/stump + house + pond; остальное силуэты;
- коллизии/Y-sort как в greybox; left walk = prototype flip;
- скрины `docs/art_tests/yard_texture_test_v1_*.png`;
- статус: **generated outdoor texture proof v1 — candidate**.

**Не делалось:** полный terrain/autotile, основной двор, GameRoot.

---

## 2026-07-31 (k) — DEC-007 reject generated pack v2 + yard_scale_test

**Сделано:**
- technical gate: generated outdoor pack v2 **rejected** как production; mood/направление остаются approved;
- DEC-007; `yard_art_test_v2` оставлен как failed experiment;
- isolated `yard_scale_test.tscn` — сетка 16×16, viewport 384×216, цветные заглушки точных размеров (player/weed/rock/bush/log/stump/trees/house), камера, WASD, Y-sort, коллизии, карта ≥72×48;
- GameRoot не начат.

**Файлы:** `DECISIONS.md`, `ASSET_INVENTORY.md`, `PROJECT_STATUS.md`, `CHANGELOG_AI.md`, `yard_scale_test.*`, `docs/art_tests/yard_scale_test.png`

---

## 2026-07-31 (j) — generated outdoor yard art test v2

**Цель:** изолированная сцена на AI-generated листах (не Puny); честная проверка нарезки/масштаба/композиции.

**Сделано:**
- source: `assets/art/outdoor/generated_test/source/`;
- processing: `tools/process_generated_outdoor_v2.py` → `processed/{terrain,player,vegetation,obstacles,buildings,water}/`;
- сцена `yard_art_test_v2.tscn` + `scripts/debug/yard_art_test_v2.gd` (4-dir AnimatedSprite2D, Y-sort, pond bake, 3 clearables, F12 hint);
- старая `yard_art_test.tscn` сохранена;
- скрины `docs/art_tests/yard_art_test_v2_*.png`;
- статус: **candidate generated outdoor pack — art test v2** (не финал в DECISIONS).

**Проблемы source (не маскировали):** opaque black bg; sheets не grid-safe; нет seamless grass/water → temporary ground/pond bake; left=flip; spruce ниже oak/birch; dirt-islands; fringe.

**Не делалось:** GameRoot, основной двор, WorldState/save.

---

## 2026-07-31 (i) — DEC-006 outdoor visual target + Pack 01 plan

**Сделано:**
- утверждены mood/scope референсы в `docs/art_direction/`;
- DEC-006; план `docs/OUTDOOR_ASSET_PACK_01.md` (player, terrain, water, clearables, 3 trees, house);
- Puny остаётся отклонённым; направление — detailed Stardew-like + rural childhood-home;
- GameRoot не начат; стоп до утверждения плана Pack 01.

**Файлы:** `DECISIONS.md`, `OUTDOOR_ASSET_PACK_01.md`, `PROJECT_STATUS.md`, `CHANGELOG_AI.md`, `NEXT_STEPS.md`, `art_direction/*.png`

---

**Сделано:** зафиксировано уточнение art direction — outdoor целится в detailed Stardew-like уровень + rural/Eastern European identity; Puny отклонён за недостаточную детализацию, не за «похожесть на Stardew». GameRoot не начинать; следующий шаг — выбрать production path (pack / свой tileset / pack+дорисовка).

**Файлы:** `docs/DECISIONS.md`, `ART_DIRECTION.md`, `ART_ASSET_BRIEF.md`, `ASSET_INVENTORY.md`, `NEXT_STEPS.md`, `PROJECT_STATUS.md`, `VISION.md`, `AGENTS.md`, `CHANGELOG_AI.md`

---

**Красная ошибка:** `@implicit_ready: Trying to assign value of type 'ColorRect' to a variable of type 'AnimatedSprite2D'.`  
**Строка:** `scripts/player/player.gd:8` `@onready var anim: AnimatedSprite2D = $Body`  
**Причина:** `main_slice.gd` создавал `Body` как `ColorRect` при `player.gd`.

**Сделано:**
- `main_slice._spawn_player` → `SceneArt.make_player` (Body = AnimatedSprite2D);
- убран ColorRect-fallback у персонажа в `scene_art.gd`;
- warnings: ternary bool/int в `world_state`, Vector2i/Vector2 в art test, shadowing `name` в main_slice, unused `actor` → `_actor`.

**Проверки:** yard_art_test + valley_slice CLI без ERROR/WARNING по этим темам.

---

**Цель:** убрать ошибку назначения ColorRect → AnimatedSprite2D; персонаж art test должен быть AnimatedSprite2D.

**Причина/строка-паттерн в проекте:** `scripts/player/player.gd:8` — `@onready var anim: AnimatedSprite2D = $Body` при `Body` типа ColorRect (как в legacy `main_slice`). Art test этот путь не использует; probe без спрайта заменён на явный `AnimatedSprite2D`.

**Сделано:**
- `scripts/debug/yard_art_test.gd` — `Player/Body` создаётся как `AnimatedSprite2D.new()`, walk/idle 4 направления;
- `assets/art/outdoor/puny_world/props/art_test_walker.png` — scale-probe sheet (не маскирует отсутствие персонажа в Puny Overworld для art gate);
- проверка запуска сцены без красных ошибок.

**Не менялось:** outdoor_square, GameRoot, save, interiors, player.gd / main_slice (вне scope art test).

**Проверки:** Godot 4.7.1 F6/CLI `yard_art_test.tscn` — без ERROR/ColorRect assign.

---

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
