extends Node2D
## Дом / мастерская: painted diorama + hotspot ремонта верстака (VS01).

const SceneArt = preload("res://scripts/world/scene_art.gd")
const HotspotUtil = preload("res://scripts/world/hotspot_util.gd")

const COL_WARM := Color("E8C07A")

var _repair_overlay: CanvasItem


func _ready() -> void:
	SceneArt.add_bg(self, "res://assets/locations/workshop_interior_bg.png")
	_build_collisions()
	_build_hotspots()
	_build_repair_overlay()
	_spawn_player()
	_add_hud()
	WorldState.set_meta_value("location", "workshop")
	WorldState.set_meta_value("spawn_point", GameFlow.spawn_point)
	if WorldState.is_vs01():
		WorldState.set_story("entered_house", true)
	WorldState.save_state()
	WorldState.flag_changed.connect(func(_f, _v): refresh_interior_visual())
	refresh_interior_visual()


func refresh_interior_visual() -> void:
	if _repair_overlay == null:
		return
	var repaired := bool(WorldState.get_interior("workbench_repaired", false))
	_repair_overlay.visible = repaired


func _build_repair_overlay() -> void:
	# Тёплый слой «оживания» над верстаком после ремонта
	var glow := ColorRect.new()
	glow.name = "RepairGlow"
	glow.position = Vector2(180, 260)
	glow.size = Vector2(200, 140)
	glow.color = Color(1.0, 0.85, 0.45, 0.18)
	glow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	glow.visible = false
	glow.z_index = 2
	add_child(glow)
	_repair_overlay = glow
	var tag := Label.new()
	tag.text = "верстак приведён в порядок"
	tag.position = Vector2(190, 250)
	tag.add_theme_color_override("font_color", Color(0.95, 0.9, 0.7, 1))
	tag.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	tag.add_theme_constant_override("shadow_offset_x", 1)
	tag.add_theme_constant_override("shadow_offset_y", 1)
	tag.visible = false
	tag.z_index = 3
	tag.name = "RepairTag"
	add_child(tag)
	# связка видимости через refresh
	WorldState.flag_changed.connect(func(flag: String, _v: Variant) -> void:
		if flag == "*" or flag.begins_with("interior:"):
			tag.visible = bool(WorldState.get_interior("workbench_repaired", false))
	)


func _build_collisions() -> void:
	HotspotUtil.wall(self, Vector2(80, 200), Vector2(360, 140))
	HotspotUtil.wall(self, Vector2(720, 280), Vector2(320, 160))
	HotspotUtil.wall(self, Vector2(0, 0), Vector2(1152, 50))
	HotspotUtil.wall(self, Vector2(480, 120), Vector2(120, 40))


func _build_hotspots() -> void:
	var bench: Area2D = load("res://scripts/world/workbench.gd").new()
	HotspotUtil.setup_hitbox(bench, Vector2(200, 300), Vector2(140, 80), Color(0.42, 0.33, 0.27, 0.2), "верстак", false, false)
	add_child(bench)

	if not WorldState.is_vs01():
		var bed: Area2D = load("res://scripts/world/bed.gd").new()
		HotspotUtil.setup_hitbox(bed, Vector2(800, 400), Vector2(140, 80), Color(0.23, 0.27, 0.35, 0.2), "лечь спать", false, false)
		add_child(bed)

	var exit_p: Area2D = load("res://scripts/world/location_portal.gd").new()
	if WorldState.is_vs01():
		exit_p.target_location = "childhood_home"
		exit_p.target_spawn = "from_house"
	else:
		exit_p.target_location = "square"
		exit_p.target_spawn = "from_workshop"
	exit_p.prompt_text = "выйти во двор"
	HotspotUtil.setup_hitbox(exit_p, Vector2(500, 200), Vector2(120, 70), Color(0.91, 0.75, 0.48, 0.18), "выход", false, false)
	add_child(exit_p)


func _spawn_player() -> void:
	add_child(SceneArt.make_player(GameFlow.spawn_position()))


func _add_hud() -> void:
	var hud := CanvasLayer.new()
	hud.set_script(load("res://scripts/ui/hud.gd"))
	var root := Control.new()
	root.name = "Root"
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.add_child(root)
	for n in ["DayLabel", "InvLabel", "ObjectiveLabel"]:
		var l := Label.new()
		l.name = n
		root.add_child(l)
	root.get_node("DayLabel").position = Vector2(16, 16)
	root.get_node("InvLabel").position = Vector2(16, 40)
	var obj: Label = root.get_node("ObjectiveLabel")
	obj.position = Vector2(16, 64)
	obj.add_theme_color_override("font_color", COL_WARM)
	add_child(hud)
