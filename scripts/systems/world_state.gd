extends Node
## Global flags and simple save/load for the settlement slice.

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
}

var day: int = 1


func _ready() -> void:
	load_state()


func get_flag(flag: String, default: Variant = false) -> Variant:
	return flags.get(flag, default)


func set_flag(flag: String, value: Variant = true) -> void:
	flags[flag] = value
	flag_changed.emit(flag, value)
	save_state()


func has_flag(flag: String) -> bool:
	return bool(get_flag(flag, false))


func advance_day() -> void:
	day += 1
	if has_flag("oven_repaired"):
		set_flag("bakery_open", true)
	save_state()


func save_state() -> void:
	var data := {
		"flags": flags,
		"day": day,
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
	var data: Dictionary = parsed
	if data.has("flags") and typeof(data["flags"]) == TYPE_DICTIONARY:
		for key in data["flags"].keys():
			flags[key] = data["flags"][key]
	if data.has("day"):
		day = int(data["day"])


func reset_for_debug() -> void:
	for key in flags.keys():
		flags[key] = false
	day = 1
	save_state()
	flag_changed.emit("*", null)
