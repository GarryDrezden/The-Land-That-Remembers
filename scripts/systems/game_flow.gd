extends Node
## Центральный поток сцен: режимы игрока/разработчика и локации.

signal mode_changed(is_developer: bool)

const SCENE_BOOT := "res://scenes/boot/boot.tscn"
const SCENE_MENU := "res://scenes/ui/main_menu.tscn"
const SCENE_INTRO := "res://scenes/ui/intro.tscn"
const SCENE_CREATOR := "res://scenes/ui/character_creator.tscn"
const SCENE_ARRIVAL := "res://scenes/ui/arrival.tscn"
const SCENE_DEBUG := "res://scenes/ui/debug_launcher.tscn"
const SCENE_SETTINGS := "res://scenes/ui/settings_menu.tscn"
const SCENE_OUTDOOR := "res://scenes/world/outdoor_square.tscn"
const SCENE_BAKERY := "res://scenes/world/interiors/bakery.tscn"
const SCENE_WORKSHOP := "res://scenes/world/interiors/workshop.tscn"
## VS01 childhood-home yard (playable outdoor slice)
const SCENE_YARD_VS01 := "res://scenes/locations/outdoor/childhood_home/yard_vs01.tscn"
## Legacy monolithic slice (для сравнения)
const SCENE_LEGACY_SLICE := "res://scenes/world/valley_slice.tscn"

const LOCATION_SCENES := {
	"square": SCENE_OUTDOOR,
	"arrival": SCENE_OUTDOOR,
	"from_workshop": SCENE_OUTDOOR,
	"from_bakery": SCENE_OUTDOOR,
	"workshop": SCENE_WORKSHOP,
	"bakery": SCENE_BAKERY,
	"legacy": SCENE_LEGACY_SLICE,
	"childhood_home": SCENE_YARD_VS01,
	"yard_vs01": SCENE_YARD_VS01,
	"from_house": SCENE_YARD_VS01,
}

## Точки появления (ферма 1920×1344; yard_vs01 — локальные координаты 16px tile)
const SPAWNS := {
	"square": Vector2(860, 700),
	"arrival": Vector2(860, 800),
	"from_workshop": Vector2(420, 530),
	"from_bakery": Vector2(920, 1200),
	"workshop": Vector2(520, 500),
	"bakery": Vector2(320, 520),
	"legacy": Vector2(150, 200),
	"childhood_home": Vector2(320, 268),
	"yard_vs01": Vector2(320, 268),
	"from_house": Vector2(320, 248),
}

var spawn_point: String = "square"
var skip_menus: bool = false


func is_developer_mode() -> bool:
	_ensure_config_loaded()
	if ProjectSettings.has_setting("land/developer_mode"):
		return bool(ProjectSettings.get_setting("land/developer_mode"))
	return OS.is_debug_build()


func set_developer_mode(enabled: bool) -> void:
	ProjectSettings.set_setting("land/developer_mode", enabled)
	var cfg := ConfigFile.new()
	cfg.load("user://land_config.cfg")
	cfg.set_value("land", "developer_mode", enabled)
	cfg.save("user://land_config.cfg")
	mode_changed.emit(enabled)


func _ensure_config_loaded() -> void:
	var cfg := ConfigFile.new()
	if cfg.load("user://land_config.cfg") != OK:
		return
	if cfg.has_section_key("land", "developer_mode"):
		ProjectSettings.set_setting("land/developer_mode", bool(cfg.get_value("land", "developer_mode")))


func go(scene_path: String) -> void:
	get_tree().change_scene_to_file(scene_path)


func go_boot() -> void:
	go(SCENE_BOOT)


func go_main_menu() -> void:
	go(SCENE_MENU)


func go_debug_launcher() -> void:
	go(SCENE_DEBUG)


func go_intro() -> void:
	go(SCENE_INTRO)


func go_character_creator() -> void:
	go(SCENE_CREATOR)


func go_arrival() -> void:
	go(SCENE_ARRIVAL)


func go_settings() -> void:
	go(SCENE_SETTINGS)


func go_location(location: String, spawn: String = "") -> void:
	if spawn != "":
		spawn_point = spawn
	else:
		spawn_point = location
	WorldState.set_meta_value("spawn_point", spawn_point)
	var scene_path: String = LOCATION_SCENES.get(spawn_point, LOCATION_SCENES.get(location, SCENE_OUTDOOR))
	go(scene_path)


func start_game(spawn: String = "square") -> void:
	go_location(spawn, spawn)


func start_new_story() -> void:
	WorldState.reset_for_debug()
	Inventory.clear()
	PlayerProfile.reset()
	spawn_point = "square"
	go_intro()


func continue_story() -> void:
	if not WorldState.has_save():
		return
	WorldState.load_state()
	Inventory.load_from_world()
	PlayerProfile.load_from_world()
	spawn_point = str(WorldState.get_meta_value("spawn_point", "square"))
	var loc := str(WorldState.get_meta_value("location", "square"))
	go_location(loc, spawn_point)


func apply_chapter(chapter_id: String) -> void:
	var preset: Dictionary = ChapterPresets.get_chapter(chapter_id)
	if preset.is_empty():
		push_warning("Неизвестная глава: %s" % chapter_id)
		return
	WorldState.apply_preset(preset)
	Inventory.apply_preset(preset.get("inventory", {}))
	if preset.has("profile"):
		PlayerProfile.apply_preset(preset["profile"])
	spawn_point = str(preset.get("spawn", "square"))
	WorldState.set_meta_value("spawn_point", spawn_point)
	WorldState.set_meta_value("chapter_id", chapter_id)
	start_game(spawn_point)


func spawn_position() -> Vector2:
	return SPAWNS.get(spawn_point, SPAWNS["square"])
