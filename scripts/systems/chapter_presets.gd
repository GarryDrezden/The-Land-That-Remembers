extends Node
## Пресеты глав и отладочных состояний (стабильнее сырых сохранений).

var chapters: Dictionary = {
	"vs01_childhood_home": {
		"id": "vs01_childhood_home",
		"title": "VS01 — Дом детства",
		"spawn": "childhood_home",
		"day": 1,
		"flags": {"arrived": true},
		"story_flags": {
			"vs01_active": true,
			"arrived_at_childhood_home": true,
			"entered_house": false,
			"first_signs_of_life_restored": false,
		},
		"tasks": {
			"clear_path_started": false,
			"clear_minimum_done": false,
			"first_repair_started": false,
			"first_repair_done": false,
		},
		"interior_states": {
			"workbench_repaired": false,
			"lamp_restored": false,
			"room_stage": 0,
		},
		"inventory": {},
		"profile": {
			"player_name": "Алексей",
			"occupation": "programmer",
			"arrival_reason": "tired_city",
		},
	},
	"chapter_0_arrival": {
		"id": "chapter_0_arrival",
		"title": "Глава 0 — Прибытие",
		"spawn": "arrival",
		"day": 1,
		"flags": {},
		"inventory": {},
		"profile": {"player_name": "Путник", "occupation": "master", "arrival_reason": "tired_city"},
	},
	"chapter_1_broken_oven": {
		"id": "chapter_1_broken_oven",
		"title": "Глава 1 — Сломанная печь",
		"spawn": "workshop",
		"day": 1,
		"flags": {"met_petr": true, "met_sofia": true},
		"inventory": {},
	},
	"chapter_2_bakery_restored": {
		"id": "chapter_2_bakery_restored",
		"title": "Глава 2 — Пекарня восстановлена",
		"spawn": "bakery",
		"day": 2,
		"flags": {
			"met_petr": true,
			"met_sofia": true,
			"got_scrap": true,
			"got_wood": true,
			"crafted_oven_door": true,
			"oven_repaired": true,
			"bakery_open": true,
		},
		"inventory": {},
	},
	"workshop": {
		"id": "workshop",
		"title": "Мастерская",
		"spawn": "workshop",
		"day": 1,
		"flags": {},
		"inventory": {},
	},
	"bakery_before": {
		"id": "bakery_before",
		"title": "Пекарня — до ремонта",
		"spawn": "bakery",
		"day": 1,
		"flags": {"met_sofia": true},
		"inventory": {"oven_door": 1},
	},
	"bakery_after": {
		"id": "bakery_after",
		"title": "Пекарня — после ремонта",
		"spawn": "bakery",
		"day": 2,
		"flags": {
			"met_petr": true,
			"met_sofia": true,
			"oven_repaired": true,
			"bakery_open": true,
			"hint_bridge": true,
		},
		"inventory": {},
	},
	"square": {
		"id": "square",
		"title": "Сцена 1 — Дом и участок",
		"spawn": "square",
		"day": 1,
		"flags": {"met_petr": true},
		"inventory": {},
	},
	"yard_clearing": {
		"id": "yard_clearing",
		"title": "Двор — расчистка участка",
		"spawn": "square",
		"day": 1,
		"flags": {"met_petr": true, "met_sofia": true},
		"inventory": {},
	},
	"yard_ready": {
		"id": "yard_ready",
		"title": "Двор — участок готов",
		"spawn": "square",
		"day": 2,
		"flags": {
			"met_petr": true,
			"met_sofia": true,
			"oven_repaired": true,
			"bakery_open": true,
			"hint_bridge": true,
			"yard_half_cleared": true,
			"yard_plot_ready": true,
		},
		"meta": {
			"cleared_debris": {
				"yard_weed_1": true,
				"yard_weed_2": true,
				"yard_weed_3": true,
				"yard_weed_4": true,
				"yard_weed_5": true,
				"yard_stone_1": true,
				"yard_stone_2": true,
				"yard_log_1": true,
				"yard_stump_1": true,
			},
			"yard_plots": {
				"yard_main": [
					"yard_weed_1", "yard_weed_2", "yard_weed_3", "yard_weed_4", "yard_weed_5",
					"yard_stone_1", "yard_stone_2", "yard_log_1", "yard_stump_1",
				],
			},
		},
		"inventory": {},
	},
	"new_game": {
		"id": "new_game",
		"title": "Новая игра (без интро)",
		"spawn": "square",
		"day": 1,
		"flags": {},
		"inventory": {},
	},
	"legacy_slice": {
		"id": "legacy_slice",
		"title": "Legacy: старый монолитный слайс",
		"spawn": "legacy",
		"day": 1,
		"flags": {},
		"inventory": {},
	},
}


func list_ids() -> PackedStringArray:
	var ids: PackedStringArray = []
	for key in chapters.keys():
		ids.append(str(key))
	ids.sort()
	return ids


func get_chapter(chapter_id: String) -> Dictionary:
	return chapters.get(chapter_id, {})


func titles() -> Array:
	var out: Array = []
	for key in list_ids():
		var ch: Dictionary = chapters[key]
		out.append({"id": key, "title": str(ch.get("title", key))})
	return out
