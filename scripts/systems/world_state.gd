extends Node
## Состояние мира: флаги, задачи, интерьеры, расчистка, save/load.
## Схема VS01: cleared_objects / tasks / interior_states / story_flags.

signal flag_changed(flag: String, value: Variant)

const SAVE_PATH := "user://world_state.json"

var flags: Dictionary = {
	"met_petr": false,
	"met_sofia": false,
	"got_scrap": false,
	"got_wood": false,
	"crafted_oven_door": false,
	"oven_repaired": false,
	"bakery_open": false,
	"hint_bridge": false,
	"arrived": false,
	"got_workshop_key": false,
	"yard_half_cleared": false,
	"yard_plot_ready": false,
}

var meta: Dictionary = {}
var day: int = 1
var _suppress_save: bool = false

## id объекта → true (alias: cleared_debris в сейвах)
var cleared_objects: Dictionary = {}
var tasks: Dictionary = {
	"clear_path_started": false,
	"clear_minimum_done": false,
	"first_repair_started": false,
	"first_repair_done": false,
}
var interior_states: Dictionary = {
	"workbench_repaired": false,
	"lamp_restored": false,
	"room_stage": 0,
}
var story_flags: Dictionary = {
	"arrived_at_childhood_home": false,
	"entered_house": false,
	"first_signs_of_life_restored": false,
	"vs01_active": false,
}

## Обратная совместимость
var cleared_debris: Dictionary:
	get:
		return cleared_objects
	set(value):
		cleared_objects = value


func _ready() -> void:
	pass


func get_flag(flag: String, default: Variant = false) -> Variant:
	return flags.get(flag, default)


func set_flag(flag: String, value: Variant = true) -> void:
	flags[flag] = value
	flag_changed.emit(flag, value)
	if not _suppress_save:
		save_state()


func has_flag(flag: String) -> bool:
	return bool(get_flag(flag, false))


func get_meta_value(key: String, default: Variant = null) -> Variant:
	return meta.get(key, default)


func set_meta_value(key: String, value: Variant) -> void:
	meta[key] = value


func get_task(task_id: String, default: Variant = false) -> Variant:
	return tasks.get(task_id, default)


func set_task(task_id: String, value: Variant = true) -> void:
	tasks[task_id] = value
	flag_changed.emit("task:%s" % task_id, value)
	if not _suppress_save:
		save_state()


func has_task(task_id: String) -> bool:
	return bool(get_task(task_id, false))


func get_interior(key: String, default: Variant = false) -> Variant:
	return interior_states.get(key, default)


func set_interior(key: String, value: Variant = true) -> void:
	interior_states[key] = value
	flag_changed.emit("interior:%s" % key, value)
	if not _suppress_save:
		save_state()


func get_story(key: String, default: Variant = false) -> Variant:
	return story_flags.get(key, default)


func set_story(key: String, value: Variant = true) -> void:
	story_flags[key] = value
	flag_changed.emit("story:%s" % key, value)
	if not _suppress_save:
		save_state()


func is_vs01() -> bool:
	return bool(get_story("vs01_active", false)) or str(get_meta_value("chapter_id", "")) == "vs01_childhood_home"


func is_debris_cleared(debris_id: String) -> bool:
	return bool(cleared_objects.get(debris_id, false))


func ensure_location_zones(location_id: String, defaults: Dictionary) -> void:
	## Compatible nested schema under meta.locations — no save migration break.
	if not meta.has("locations") or typeof(meta["locations"]) != TYPE_DICTIONARY:
		meta["locations"] = {}
	var locs: Dictionary = meta["locations"]
	if not locs.has(location_id) or typeof(locs[location_id]) != TYPE_DICTIONARY:
		locs[location_id] = {"zones": {}}
	var loc: Dictionary = locs[location_id]
	if not loc.has("zones") or typeof(loc["zones"]) != TYPE_DICTIONARY:
		loc["zones"] = {}
	var zones: Dictionary = loc["zones"]
	for zid in defaults.keys():
		if not zones.has(zid):
			zones[zid] = (defaults[zid] as Dictionary).duplicate(true)
	loc["zones"] = zones
	locs[location_id] = loc
	meta["locations"] = locs


func get_location_zone(location_id: String, zone_id: String) -> Dictionary:
	var locs: Dictionary = meta.get("locations", {})
	if not locs.has(location_id):
		return {}
	var loc: Dictionary = locs[location_id]
	var zones: Dictionary = loc.get("zones", {})
	return zones.get(zone_id, {})


func set_location_zone_state(location_id: String, zone_id: String, state: String) -> void:
	ensure_location_zones(location_id, {zone_id: {"state": state, "cleared_count": 0}})
	var locs: Dictionary = meta["locations"]
	var zones: Dictionary = locs[location_id]["zones"]
	var z: Dictionary = zones.get(zone_id, {"cleared_count": 0})
	z["state"] = state
	zones[zone_id] = z
	locs[location_id]["zones"] = zones
	meta["locations"] = locs
	flag_changed.emit("zone:%s/%s" % [location_id, zone_id], state)
	if not _suppress_save:
		save_state()


func mark_debris_cleared(debris_id: String, plot_id: String = "yard_main") -> void:
	cleared_objects[debris_id] = true
	var plots: Dictionary = meta.get("yard_plots", {})
	if not plots.has(plot_id):
		plots[plot_id] = []
	var ids: Array = plots[plot_id]
	if debris_id not in ids:
		ids.append(debris_id)
	plots[plot_id] = ids
	meta["yard_plots"] = plots
	if not has_task("clear_path_started"):
		set_task("clear_path_started", true)
	var count := plot_cleared_count(plot_id)
	if count >= 4 and not has_task("clear_minimum_done"):
		set_task("clear_minimum_done", true)
	flag_changed.emit("debris", debris_id)
	if not _suppress_save:
		save_state()


func plot_cleared_count(plot_id: String) -> int:
	var plots: Dictionary = meta.get("yard_plots", {})
	if not plots.has(plot_id):
		return 0
	return (plots[plot_id] as Array).size()


func advance_day() -> void:
	day += 1
	if has_flag("oven_repaired"):
		set_flag("bakery_open", true)
	if not _suppress_save:
		save_state()


func has_save() -> bool:
	if not FileAccess.file_exists(SAVE_PATH):
		return false
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		return false
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		return false
	var data: Dictionary = parsed
	var m: Dictionary = data.get("meta", {})
	var f: Dictionary = data.get("flags", {})
	var sf: Dictionary = data.get("story_flags", m.get("story_flags", {}))
	return bool(m.get("playthrough", false)) or bool(f.get("arrived", false)) or bool(f.get("met_petr", false)) or bool(f.get("oven_repaired", false)) or bool(sf.get("arrived_at_childhood_home", false))


func save_state() -> void:
	meta["spawn_point"] = GameFlow.spawn_point
	meta["profile"] = PlayerProfile.to_dict()
	meta["inventory"] = Inventory.items.duplicate()
	meta["playthrough"] = true
	meta["cleared_debris"] = cleared_objects.duplicate()
	meta["cleared_objects"] = cleared_objects.duplicate()
	meta["tasks"] = tasks.duplicate()
	meta["interior_states"] = interior_states.duplicate()
	meta["story_flags"] = story_flags.duplicate()
	var data := {
		"flags": flags,
		"day": day,
		"meta": meta,
		"tasks": tasks,
		"interior_states": interior_states,
		"story_flags": story_flags,
		"cleared_objects": cleared_objects,
	}
	var file := FileAccess.open(SAVE_PATH, FileAccess.WRITE)
	if file == null:
		push_warning("WorldState: cannot write save file")
		return
	file.store_string(JSON.stringify(data))


func load_state() -> void:
	if not FileAccess.file_exists(SAVE_PATH):
		return
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	_apply_data(parsed)


func _reset_structured() -> void:
	cleared_objects.clear()
	for k in tasks.keys():
		if typeof(tasks[k]) == TYPE_BOOL:
			tasks[k] = false
		else:
			tasks[k] = 0
	interior_states = {
		"workbench_repaired": false,
		"lamp_restored": false,
		"room_stage": 0,
	}
	story_flags = {
		"arrived_at_childhood_home": false,
		"entered_house": false,
		"first_signs_of_life_restored": false,
		"vs01_active": false,
	}


func _merge_dict(target: Dictionary, source: Dictionary) -> void:
	for key in source.keys():
		target[key] = source[key]


func _apply_data(data: Dictionary) -> void:
	_suppress_save = true
	for key in flags.keys():
		flags[key] = false
	_reset_structured()
	if data.has("flags") and typeof(data["flags"]) == TYPE_DICTIONARY:
		for key in data["flags"].keys():
			flags[key] = data["flags"][key]
	if data.has("day"):
		day = int(data["day"])
	if data.has("meta") and typeof(data["meta"]) == TYPE_DICTIONARY:
		meta = data["meta"]
	if data.has("cleared_objects") and typeof(data["cleared_objects"]) == TYPE_DICTIONARY:
		cleared_objects = data["cleared_objects"].duplicate()
	elif meta.has("cleared_objects") and typeof(meta["cleared_objects"]) == TYPE_DICTIONARY:
		cleared_objects = meta["cleared_objects"].duplicate()
	elif meta.has("cleared_debris") and typeof(meta["cleared_debris"]) == TYPE_DICTIONARY:
		cleared_objects = meta["cleared_debris"].duplicate()
	if data.has("tasks") and typeof(data["tasks"]) == TYPE_DICTIONARY:
		_merge_dict(tasks, data["tasks"])
	elif meta.has("tasks") and typeof(meta["tasks"]) == TYPE_DICTIONARY:
		_merge_dict(tasks, meta["tasks"])
	if data.has("interior_states") and typeof(data["interior_states"]) == TYPE_DICTIONARY:
		_merge_dict(interior_states, data["interior_states"])
	elif meta.has("interior_states") and typeof(meta["interior_states"]) == TYPE_DICTIONARY:
		_merge_dict(interior_states, meta["interior_states"])
	if data.has("story_flags") and typeof(data["story_flags"]) == TYPE_DICTIONARY:
		_merge_dict(story_flags, data["story_flags"])
	elif meta.has("story_flags") and typeof(meta["story_flags"]) == TYPE_DICTIONARY:
		_merge_dict(story_flags, meta["story_flags"])
	_suppress_save = false
	flag_changed.emit("*", null)


func apply_preset(preset: Dictionary) -> void:
	_suppress_save = true
	for key in flags.keys():
		flags[key] = false
	_reset_structured()
	day = int(preset.get("day", 1))
	meta = {}
	var preset_flags: Dictionary = preset.get("flags", {})
	for key in preset_flags.keys():
		flags[key] = preset_flags[key]
	if preset.has("meta") and typeof(preset["meta"]) == TYPE_DICTIONARY:
		meta = preset["meta"].duplicate()
	if preset.has("tasks") and typeof(preset["tasks"]) == TYPE_DICTIONARY:
		_merge_dict(tasks, preset["tasks"])
	elif meta.has("tasks"):
		_merge_dict(tasks, meta["tasks"])
	if preset.has("interior_states") and typeof(preset["interior_states"]) == TYPE_DICTIONARY:
		_merge_dict(interior_states, preset["interior_states"])
	elif meta.has("interior_states"):
		_merge_dict(interior_states, meta["interior_states"])
	if preset.has("story_flags") and typeof(preset["story_flags"]) == TYPE_DICTIONARY:
		_merge_dict(story_flags, preset["story_flags"])
	elif meta.has("story_flags"):
		_merge_dict(story_flags, meta["story_flags"])
	if preset.has("cleared_objects") and typeof(preset["cleared_objects"]) == TYPE_DICTIONARY:
		cleared_objects = preset["cleared_objects"].duplicate()
	elif meta.has("cleared_debris") and typeof(meta["cleared_debris"]) == TYPE_DICTIONARY:
		cleared_objects = meta["cleared_debris"].duplicate()
	_suppress_save = false
	save_state()
	flag_changed.emit("*", null)


func reset_for_debug() -> void:
	_suppress_save = true
	for key in flags.keys():
		flags[key] = false
	_reset_structured()
	day = 1
	meta = {}
	_suppress_save = false
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(SAVE_PATH)
	flag_changed.emit("*", null)


func delete_save() -> void:
	if FileAccess.file_exists(SAVE_PATH):
		DirAccess.remove_absolute(SAVE_PATH)
	_suppress_save = true
	for key in flags.keys():
		flags[key] = false
	_reset_structured()
	day = 1
	meta = {}
	_suppress_save = false
	flag_changed.emit("*", null)
