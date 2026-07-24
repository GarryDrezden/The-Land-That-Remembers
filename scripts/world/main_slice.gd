extends Node2D
## Vertical slice map: workshop → square → bakery.
## Placeholders only — proves the restoration fantasy.


const COL_GRASS := Color("3D4F3F")
const COL_WOOD := Color("6B5344")
const COL_COLD := Color("8A9BB0")
const COL_WARM := Color("E8C07A")
const COL_PATH := Color("5A6A5A")
const COL_WALL := Color("2F3A32")


func _ready() -> void:
	_build_ground()
	_build_workshop()
	_build_square()
	_build_bakery()
	_spawn_player()
	_add_hud()
	_add_help()


func _rect(parent: Node, name: String, pos: Vector2, size: Vector2, color: Color, z: int = 0) -> ColorRect:
	var r := ColorRect.new()
	r.name = name
	r.position = pos
	r.size = size
	r.color = color
	r.z_index = z
	parent.add_child(r)
	return r


func _label(parent: Node, text: String, pos: Vector2, color: Color = Color.WHITE) -> Label:
	var l := Label.new()
	l.text = text
	l.position = pos
	l.add_theme_color_override("font_color", color)
	parent.add_child(l)
	return l


func _build_ground() -> void:
	_rect(self, "Grass", Vector2(-40, -40), Vector2(1280, 800), COL_GRASS, -10)
	_rect(self, "Path", Vector2(280, 280), Vector2(640, 80), COL_PATH, -9)
	_label(self, "Мастерская", Vector2(80, 40), COL_WARM)
	_label(self, "Площадь", Vector2(520, 40), COL_WARM)
	_label(self, "Пекарня", Vector2(920, 40), COL_WARM)


func _build_workshop() -> void:
	var zone := Node2D.new()
	zone.name = "Workshop"
	add_child(zone)
	_rect(zone, "Floor", Vector2(40, 80), Vector2(260, 220), Color("4A3B2F"))
	_rect(zone, "RoofLeak", Vector2(60, 90), Vector2(40, 20), COL_COLD)
	_make_static(zone, Vector2(40, 80), Vector2(260, 16))
	_make_static(zone, Vector2(40, 284), Vector2(260, 16))
	_make_static(zone, Vector2(40, 80), Vector2(16, 220))
	_make_static(zone, Vector2(284, 80), Vector2(16, 90))
	_make_static(zone, Vector2(284, 210), Vector2(16, 90))

	var bench := _make_interactable(_script_node("res://scripts/world/workbench.gd"), "Workbench", Vector2(100, 160), Vector2(70, 40), COL_WOOD, "верстак")
	zone.add_child(bench)

	var bed := _make_interactable(_script_node("res://scripts/world/bed.gd"), "Bed", Vector2(200, 200), Vector2(60, 40), Color("3A4558"), "лечь спать")
	zone.add_child(bed)

	var wood := _make_interactable(_script_node("res://scripts/world/pickup.gd"), "WoodPile", Vector2(40, 320), Vector2(50, 30), Color("7A5A3A"), "разобрать забор")
	wood.item_id = "wood"
	wood.once_flag = "got_wood"
	wood.prompt_text = "разобрать забор"
	zone.add_child(wood)


func _build_square() -> void:
	var zone := Node2D.new()
	zone.name = "Square"
	add_child(zone)
	_rect(zone, "Plaza", Vector2(360, 100), Vector2(320, 280), Color("455445"), -8)
	_rect(zone, "FountainDead", Vector2(490, 200), Vector2(60, 60), COL_COLD)

	var petr := _make_npc("Petr", Vector2(420, 180), Color("6B7B8A"), "Пётр", "res://data/dialogues/petr.json")
	zone.add_child(petr)

	var scrap := _make_interactable(_script_node("res://scripts/world/pickup.gd"), "Cart", Vector2(560, 300), Vector2(70, 40), Color("5A5A5A"), "разобрать телегу")
	scrap.item_id = "scrap_metal"
	scrap.once_flag = "got_scrap"
	scrap.prompt_text = "разобрать телегу"
	zone.add_child(scrap)


func _build_bakery() -> void:
	var zone := Node2D.new()
	zone.name = "Bakery"
	zone.set_script(load("res://scripts/world/bakery_visual.gd"))

	_rect(zone, "Floor", Vector2(760, 80), Vector2(280, 240), Color("4A4038"))
	var warm := _rect(zone, "WarmWindow", Vector2(900, 100), Vector2(50, 40), COL_WARM, 1)
	warm.visible = false
	_rect(zone, "ColdWindow", Vector2(900, 100), Vector2(50, 40), COL_COLD, 1)

	var closed := _label(zone, "ЗАКРЫТО", Vector2(820, 90), Color("C07070"))
	closed.name = "ClosedSign"
	var opened := _label(zone, "ОТКРЫТО", Vector2(820, 90), COL_WARM)
	opened.name = "OpenSign"
	opened.visible = false

	var crowd := Node2D.new()
	crowd.name = "Crowd"
	crowd.visible = false
	zone.add_child(crowd)
	_rect(crowd, "VillagerA", Vector2(800, 280), Vector2(24, 24), Color("C4A882"))
	_rect(crowd, "VillagerB", Vector2(840, 290), Vector2(24, 24), Color("A8B8C4"))
	_label(crowd, "жители ждут хлеб", Vector2(780, 320), COL_WARM)

	var oven := _make_interactable(_script_node("res://scripts/world/oven.gd"), "Oven", Vector2(820, 160), Vector2(70, 50), Color("3A3030"), "печь")
	zone.add_child(oven)

	var sofia := _make_npc("Sofia", Vector2(900, 200), Color("B07070"), "Софья", "res://data/dialogues/sofia.json")
	zone.add_child(sofia)

	add_child(zone)


func _spawn_player() -> void:
	var player := CharacterBody2D.new()
	player.name = "Player"
	player.position = Vector2(150, 200)
	player.set_script(load("res://scripts/player/player.gd"))
	var body := ColorRect.new()
	body.name = "Body"
	body.size = Vector2(28, 28)
	body.color = Color("D8C4A0")
	body.position = Vector2(-14, -14)
	player.add_child(body)
	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(24, 24)
	collision.shape = shape
	player.add_child(collision)
	var prompt := Label.new()
	prompt.name = "Prompt"
	prompt.position = Vector2(-40, -40)
	prompt.visible = false
	player.add_child(prompt)
	var tag := Label.new()
	tag.name = "NameTag"
	tag.position = Vector2(-18, 16)
	player.add_child(tag)
	var cam := Camera2D.new()
	cam.enabled = true
	cam.position_smoothing_enabled = true
	player.add_child(cam)
	add_child(player)


func _add_hud() -> void:
	var hud := CanvasLayer.new()
	hud.name = "HUD"
	hud.set_script(load("res://scripts/ui/hud.gd"))
	var root := Control.new()
	root.name = "Root"
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.add_child(root)
	var day := Label.new()
	day.name = "DayLabel"
	day.position = Vector2(16, 12)
	root.add_child(day)
	var inv := Label.new()
	inv.name = "InvLabel"
	inv.position = Vector2(16, 36)
	root.add_child(inv)
	var obj := Label.new()
	obj.name = "ObjectiveLabel"
	obj.position = Vector2(16, 60)
	obj.add_theme_color_override("font_color", COL_WARM)
	root.add_child(obj)
	add_child(hud)


func _add_help() -> void:
	var tip := Label.new()
	tip.text = "WASD / стрелки — ходить · E — взаимодействие · Esc — закрыть диалог"
	tip.position = Vector2(16, 700)
	tip.add_theme_color_override("font_color", Color(1, 1, 1, 0.7))
	add_child(tip)


func _make_static(parent: Node, pos: Vector2, size: Vector2) -> void:
	var body := StaticBody2D.new()
	body.position = pos + size * 0.5
	var shape := RectangleShape2D.new()
	shape.size = size
	var col := CollisionShape2D.new()
	col.shape = shape
	body.add_child(col)
	var vis := ColorRect.new()
	vis.size = size
	vis.position = -size * 0.5
	vis.color = COL_WALL
	body.add_child(vis)
	parent.add_child(body)


func _script_node(path: String) -> Area2D:
	return load(path).new() as Area2D


func _make_interactable(node: Area2D, name: String, pos: Vector2, size: Vector2, color: Color, prompt: String) -> Area2D:
	node.name = name
	node.position = pos
	node.prompt_text = prompt
	var vis := ColorRect.new()
	vis.name = "Vis"
	vis.size = size
	vis.color = color
	vis.position = Vector2.ZERO
	node.add_child(vis)
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = size
	col.shape = shape
	col.position = size * 0.5
	node.add_child(col)
	node.monitoring = true
	node.monitorable = true
	# collision with player character body
	node.collision_layer = 1
	node.collision_mask = 1
	var tag := Label.new()
	tag.text = prompt
	tag.position = Vector2(0, -18)
	node.add_child(tag)
	return node


func _make_npc(name: String, pos: Vector2, color: Color, title: String, dialogue: String) -> Area2D:
	var npc: Area2D = _script_node("res://scripts/world/interactable.gd")
	npc.name = name
	npc.position = pos
	npc.prompt_text = "поговорить: %s" % title
	npc.dialogue_path = dialogue
	npc.dialogue_start = "start"
	var vis := ColorRect.new()
	vis.size = Vector2(28, 28)
	vis.color = color
	npc.add_child(vis)
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(36, 36)
	col.shape = shape
	col.position = Vector2(14, 14)
	npc.add_child(col)
	var tag := Label.new()
	tag.text = title
	tag.position = Vector2(-4, 30)
	npc.add_child(tag)
	return npc
