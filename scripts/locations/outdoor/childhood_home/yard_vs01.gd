extends Node2D
## VS01 outdoor yard candidate — childhood home, overgrown, clearable path.
## Uses PixelLab hero (unchanged scale). Temporary Russian izba placeholder.
## ART_TEST_SHOT=1 for verification screenshots.

const HotspotUtil = preload("res://scripts/world/hotspot_util.gd")
const ASSET_ROOT := "res://assets/art/outdoor/yard_vs01/"
const PLAYER_SCENE := "res://scenes/actors/player/player_pixellab_test.tscn"
const TILE := 16
const MAP_W := 40
const MAP_H := 32
const VIEW_W := 384
const VIEW_H := 240
const WINDOW_SCALE := 3

var _ysort: Node2D
var _player: CharacterBody2D
var _hint: Label
var _prompt: Label
var _shot_cam: Camera2D
var _blockers: StaticBody2D


func _ready() -> void:
	name = "YardVS01"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(VIEW_W * WINDOW_SCALE, VIEW_H * WINDOW_SCALE))

	if not FileAccess.file_exists(ASSET_ROOT + "ground.png"):
		_show_missing("Missing yard_vs01 assets.\nRun: python tools/build_yard_vs01_assets.py")
		return

	_build_ground()
	_ysort = Node2D.new()
	_ysort.name = "YSortWorld"
	_ysort.y_sort_enabled = true
	_ysort.z_index = 10
	add_child(_ysort)

	_blockers = StaticBody2D.new()
	_blockers.name = "Blockers"
	_blockers.collision_layer = 1
	_blockers.collision_mask = 0
	add_child(_blockers)

	_build_fence()
	_build_house()
	_build_secondary_props()
	_build_trees()
	_build_clearables()
	_build_player()
	_build_bounds()
	_build_ui()

	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.35).timeout
		await _shot_sequence()
		get_tree().quit()


func _map_px() -> Vector2:
	return Vector2(MAP_W * TILE, MAP_H * TILE)


func _show_missing(msg: String) -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var lab := Label.new()
	lab.text = msg
	lab.position = Vector2(24, 24)
	lab.add_theme_font_size_override("font_size", 14)
	layer.add_child(lab)
	if OS.get_environment("ART_TEST_SHOT") != "":
		await get_tree().create_timer(0.2).timeout
		get_tree().quit()


func _load_tex(path: String) -> Texture2D:
	var abs_path := ProjectSettings.globalize_path(path)
	var img := Image.new()
	if FileAccess.file_exists(abs_path) and img.load(abs_path) == OK:
		return ImageTexture.create_from_image(img)
	if ResourceLoader.exists(path):
		var res := load(path)
		if res is Texture2D:
			return res
	push_warning("Missing texture: %s" % path)
	return null


func _add_sprite(parent: Node, path: String, pos: Vector2, centered := true, offset := Vector2.ZERO) -> Sprite2D:
	var spr := Sprite2D.new()
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = centered
	spr.texture = _load_tex(path)
	spr.position = pos
	spr.offset = offset
	parent.add_child(spr)
	return spr


func _add_blocker_rect(center: Vector2, size: Vector2) -> void:
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = size
	col.shape = shape
	col.position = center
	_blockers.add_child(col)


func _build_ground() -> void:
	var ground := Node2D.new()
	ground.name = "Ground"
	add_child(ground)
	var spr := _add_sprite(ground, ASSET_ROOT + "ground.png", Vector2.ZERO, false)
	spr.z_index = 0


func _build_fence() -> void:
	## Perimeter fence with south gate opening (tiles x=18..21 at y=30).
	var post := ASSET_ROOT + "fence_post.png"
	var rail := ASSET_ROOT + "fence_rail.png"
	# Top
	for x in range(8, 32):
		_fence_segment(Vector2((x + 0.5) * TILE, 7.2 * TILE), post, rail, true)
		_add_blocker_rect(Vector2((x + 0.5) * TILE, 7.5 * TILE), Vector2(14, 6))
	# Bottom (except gate)
	for x in range(8, 32):
		if x >= 18 and x <= 21:
			continue
		_fence_segment(Vector2((x + 0.5) * TILE, 30.2 * TILE), post, rail, true)
		_add_blocker_rect(Vector2((x + 0.5) * TILE, 30.4 * TILE), Vector2(14, 6))
	# Left / right
	for y in range(7, 31):
		_fence_segment(Vector2(8.2 * TILE, (y + 0.5) * TILE), post, rail, false)
		_add_blocker_rect(Vector2(8.3 * TILE, (y + 0.5) * TILE), Vector2(6, 14))
		_fence_segment(Vector2(31.8 * TILE, (y + 0.5) * TILE), post, rail, false)
		_add_blocker_rect(Vector2(31.7 * TILE, (y + 0.5) * TILE), Vector2(6, 14))
	# Gate visual (open posts)
	_add_sprite(_ysort, ASSET_ROOT + "gate.png", Vector2(20 * TILE, 30.15 * TILE), true, Vector2(0, -6))


func _fence_segment(pos: Vector2, post_path: String, rail_path: String, horizontal: bool) -> void:
	var post_spr := _add_sprite(_ysort, post_path, pos, true, Vector2(0, -8))
	post_spr.z_as_relative = true
	if horizontal:
		var rail_spr := _add_sprite(_ysort, rail_path, pos + Vector2(0, -6), true)
		rail_spr.z_as_relative = true
		# Slight crookedness
		if int(pos.x / TILE) % 5 == 0:
			post_spr.position.y += 1


func _build_house() -> void:
	var house_pos := Vector2(20 * TILE, 10.5 * TILE)
	var house := _add_sprite(
		_ysort,
		ASSET_ROOT + "house_izba_placeholder.png",
		house_pos,
		true,
		Vector2(0, -48)
	)
	house.name = "HouseIzba"
	# Solid footprint under walls / porch (not full roof)
	_add_blocker_rect(house_pos + Vector2(0, -8), Vector2(100, 36))
	# Door marker interaction zone (visual goal; interior later)
	var door_script := load("res://scripts/locations/outdoor/childhood_home/yard_vs01_door.gd")
	var door: Area2D = door_script.new()
	door.name = "DoorHotspot"
	door.monitoring = true
	door.monitorable = true
	door.collision_layer = 0
	door.collision_mask = 1
	door.position = house_pos + Vector2(0, 8)
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(22, 16)
	col.shape = shape
	door.add_child(col)
	_ysort.add_child(door)


func _build_secondary_props() -> void:
	# Well — east of path
	var well := _add_sprite(_ysort, ASSET_ROOT + "well.png", Vector2(27 * TILE, 16 * TILE), true, Vector2(0, -10))
	well.name = "Well"
	_add_blocker_rect(Vector2(27 * TILE, 16.4 * TILE), Vector2(22, 12))
	# Woodpile near house west
	var wood := _add_sprite(_ysort, ASSET_ROOT + "woodpile.png", Vector2(13 * TILE, 12.5 * TILE), true, Vector2(0, -4))
	wood.name = "Woodpile"
	_add_blocker_rect(Vector2(13 * TILE, 12.8 * TILE), Vector2(28, 10))
	# Shed corner — west edge
	var shed := _add_sprite(_ysort, ASSET_ROOT + "shed_corner.png", Vector2(10.5 * TILE, 14 * TILE), true, Vector2(0, -12))
	shed.name = "ShedCorner"
	_add_blocker_rect(Vector2(10.5 * TILE, 14.5 * TILE), Vector2(36, 16))


func _build_trees() -> void:
	var trees := [
		[ASSET_ROOT + "props/tree_a.png", Vector2(11 * TILE, 9 * TILE)],
		[ASSET_ROOT + "props/tree_b.png", Vector2(29 * TILE, 10 * TILE)],
		[ASSET_ROOT + "props/tree_c.png", Vector2(8.5 * TILE, 20 * TILE)],
		[ASSET_ROOT + "props/tree_a.png", Vector2(30.5 * TILE, 22 * TILE)],
	]
	for t in trees:
		var spr := _add_sprite(_ysort, str(t[0]), t[1], true, Vector2(0, -28))
		spr.z_as_relative = true
		_add_blocker_rect(t[1] + Vector2(0, 4), Vector2(18, 10))


func _spawn_clearable(cfg: Dictionary) -> void:
	var n: Area2D = load("res://scripts/world/yard_object.gd").new()
	n.object_id = str(cfg.id)
	n.object_type = str(cfg.kind)
	n.plot_id = "yard_vs01"
	n.prompt_text = str(cfg.get("prompt", "убрать"))
	n.item_id = str(cfg.get("item", ""))
	n.amount = 1
	n.max_hits = int(cfg.get("hits", 1))
	n.blocks_movement = bool(cfg.get("solid", false))
	n.position = cfg.pos
	n.monitoring = true
	n.collision_layer = 0
	n.collision_mask = 1

	var tex := _load_tex(str(cfg.spr))
	var spr := Sprite2D.new()
	spr.name = "Sprite"
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = true
	spr.texture = tex
	if tex:
		spr.offset = Vector2(0, -tex.get_height() * 0.35)
	n.add_child(spr)

	var hit := Vector2(20, 16)
	if tex:
		hit = Vector2(maxi(14, int(tex.get_width() * 0.8)), maxi(12, int(tex.get_height() * 0.45)))
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = hit
	col.shape = shape
	col.position = Vector2(0, -hit.y * 0.1)
	n.add_child(col)

	if bool(cfg.get("solid", false)):
		var solid_size: Vector2 = cfg.get("solid_size", Vector2(hit.x * 0.85, maxf(10.0, hit.y * 0.5)))
		HotspotUtil.add_blocker(n, Vector2(0, 2), solid_size)
	_ysort.add_child(n)


func _build_clearables() -> void:
	## Path blockers (must clear for first approach) + optional side clutter.
	var required := [
		{
			"id": "vs01_stump_path",
			"kind": "stump",
			"pos": Vector2(20.2 * TILE, 22.5 * TILE),
			"spr": ASSET_ROOT + "stump.png",
			"prompt": "убрать пень",
			"item": "wood",
			"solid": true,
			"solid_size": Vector2(16, 10),
		},
		{
			"id": "vs01_log_path",
			"kind": "log",
			"pos": Vector2(19.5 * TILE, 18.8 * TILE),
			"spr": ASSET_ROOT + "log.png",
			"prompt": "убрать бревно",
			"item": "wood",
			"solid": true,
			"solid_size": Vector2(28, 8),
		},
		{
			"id": "vs01_rock_path",
			"kind": "stone",
			"pos": Vector2(20.8 * TILE, 15.5 * TILE),
			"spr": ASSET_ROOT + "props/rock_md.png",
			"prompt": "сдвинуть камень",
			"item": "stone",
			"hits": 5,
			"solid": true,
			"solid_size": Vector2(16, 10),
		},
		{
			"id": "vs01_bush_path",
			"kind": "bush",
			"pos": Vector2(18.8 * TILE, 13.2 * TILE),
			"spr": ASSET_ROOT + "props/bush_overgrown.png",
			"prompt": "прорубить куст",
			"item": "grass",
			"solid": true,
			"solid_size": Vector2(18, 12),
		},
	]
	for cfg in required:
		_spawn_clearable(cfg)

	# Optional overgrowth (sides)
	var optional := [
		{"id": "vs01_weed_1", "kind": "weed", "pos": Vector2(16 * TILE, 24 * TILE), "spr": ASSET_ROOT + "weed_a.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_2", "kind": "weed", "pos": Vector2(23 * TILE, 23 * TILE), "spr": ASSET_ROOT + "weed_b.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_3", "kind": "weed", "pos": Vector2(15 * TILE, 17 * TILE), "spr": ASSET_ROOT + "weed_a.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_4", "kind": "weed", "pos": Vector2(24 * TILE, 19 * TILE), "spr": ASSET_ROOT + "weed_b.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_rock_side", "kind": "stone", "pos": Vector2(14 * TILE, 20 * TILE), "spr": ASSET_ROOT + "props/rock_sm.png", "prompt": "сдвинуть камень", "item": "stone", "hits": 5, "solid": true, "solid_size": Vector2(12, 8)},
		{"id": "vs01_bush_side", "kind": "bush", "pos": Vector2(25.5 * TILE, 14 * TILE), "spr": ASSET_ROOT + "props/bush_md.png", "prompt": "прорубить куст", "item": "grass", "solid": true, "solid_size": Vector2(18, 12)},
		{"id": "vs01_stump_side", "kind": "stump", "pos": Vector2(12.5 * TILE, 25 * TILE), "spr": ASSET_ROOT + "stump.png", "prompt": "убрать пень", "item": "wood", "solid": true, "solid_size": Vector2(16, 10)},
	]
	for cfg in optional:
		_spawn_clearable(cfg)

	# Decorative non-clearable rocks/bushes off path
	for p in [
		[ASSET_ROOT + "props/rock_lg.png", Vector2(12 * TILE, 17 * TILE), Vector2(20, 12)],
		[ASSET_ROOT + "props/bush_sm.png", Vector2(26 * TILE, 25 * TILE), Vector2(14, 10)],
		[ASSET_ROOT + "props/rock_sm.png", Vector2(28 * TILE, 20 * TILE), Vector2(10, 8)],
	]:
		_add_sprite(_ysort, str(p[0]), p[1], true, Vector2(0, -6))
		_add_blocker_rect(p[1] + Vector2(0, 2), p[2])


func _build_player() -> void:
	var packed := load(PLAYER_SCENE) as PackedScene
	_player = packed.instantiate() as CharacterBody2D
	_player.name = "PlayerPixelLabTest"
	# Spawn at south gate entrance
	_player.position = Vector2(20 * TILE, 29.2 * TILE)
	_player.scale = Vector2.ONE
	_ysort.add_child(_player)
	if _player.has_method("set_camera_zoom"):
		_player.call("set_camera_zoom", Vector2(WINDOW_SCALE, WINDOW_SCALE))
	if _player.has_method("set_camera_limits"):
		_player.call("set_camera_limits", Rect2(0, 0, MAP_W * TILE, MAP_H * TILE))


func _build_bounds() -> void:
	var map := _map_px()
	var thickness := 16.0
	var rects := [
		[Vector2(map.x * 0.5, -thickness * 0.5), Vector2(map.x, thickness)],
		[Vector2(map.x * 0.5, map.y + thickness * 0.5), Vector2(map.x, thickness)],
		[Vector2(-thickness * 0.5, map.y * 0.5), Vector2(thickness, map.y)],
		[Vector2(map.x + thickness * 0.5, map.y * 0.5), Vector2(thickness, map.y)],
	]
	for r in rects:
		_add_blocker_rect(r[0], r[1])


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hint = Label.new()
	_hint.position = Vector2(8, 6)
	_hint.add_theme_font_size_override("font_size", 11)
	_hint.add_theme_color_override("font_color", Color(0.95, 0.95, 0.9))
	_hint.text = "VS01 двор · WASD · E — расчистка · F12 коллизии"
	layer.add_child(_hint)
	_prompt = Label.new()
	_prompt.position = Vector2(8, VIEW_H * WINDOW_SCALE - 28)
	_prompt.add_theme_font_size_override("font_size", 12)
	_prompt.add_theme_color_override("font_color", Color(1, 0.95, 0.8))
	_prompt.visible = false
	layer.add_child(_prompt)
	if _player and _player.has_method("set_prompt_label"):
		_player.call("set_prompt_label", _prompt)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F12:
			get_tree().debug_collisions_hint = not get_tree().debug_collisions_hint
			_hint.visible = get_tree().debug_collisions_hint
			get_viewport().set_input_as_handled()


func _shot_sequence() -> void:
	_hint.visible = false
	if _player and _player.has_method("set_camera_enabled"):
		_player.call("set_camera_enabled", false)
	_shot_cam = Camera2D.new()
	_shot_cam.enabled = true
	_shot_cam.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	add_child(_shot_cam)
	_shot_cam.make_current()

	# Overview — pull back to show full yard plate
	_shot_cam.zoom = Vector2(1.45, 1.45)
	_shot_cam.position = Vector2(20 * TILE, 18.5 * TILE)
	if _player:
		_player.visible = false
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("yard_vs01_overview")

	_shot_cam.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	if _player:
		_player.visible = true
		_player.scale = Vector2.ONE
		var anim := _player.get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
		if anim:
			anim.scale = Vector2.ONE
			anim.play("idle_north")

	# Gate / entrance
	_player.position = Vector2(20 * TILE, 29.0 * TILE)
	_shot_cam.position = Vector2(20 * TILE, 26.5 * TILE)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("yard_vs01_gate")

	# Door (after path — place near door for scale shot; blockers may overlap — use cleared visual pos south of door)
	_player.position = Vector2(20 * TILE, 12.6 * TILE)
	if _player.get_node_or_null("AnimatedSprite2D"):
		(_player.get_node("AnimatedSprite2D") as AnimatedSprite2D).play("idle_north")
	_shot_cam.position = Vector2(20 * TILE, 11.5 * TILE)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("yard_vs01_door")

	# Scale check near tree + rock
	_player.position = Vector2(12.5 * TILE, 18.5 * TILE)
	if _player.get_node_or_null("AnimatedSprite2D"):
		(_player.get_node("AnimatedSprite2D") as AnimatedSprite2D).play("idle_east")
	_shot_cam.position = Vector2(14 * TILE, 16.5 * TILE)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("yard_vs01_scale")

	# Collisions debug at path
	get_tree().debug_collisions_hint = true
	_player.position = Vector2(20 * TILE, 21 * TILE)
	_shot_cam.position = Vector2(20 * TILE, 19 * TILE)
	var debug_draw := Node2D.new()
	debug_draw.z_as_relative = false
	debug_draw.z_index = 80
	add_child(debug_draw)
	for child in _blockers.get_children():
		if child is CollisionShape2D and child.shape is RectangleShape2D:
			var rs := child.shape as RectangleShape2D
			var poly := Polygon2D.new()
			var hx := rs.size.x * 0.5
			var hy := rs.size.y * 0.5
			poly.polygon = PackedVector2Array([
				Vector2(-hx, -hy), Vector2(hx, -hy), Vector2(hx, hy), Vector2(-hx, hy),
			])
			poly.color = Color(0.15, 0.85, 1.0, 0.4)
			poly.global_position = child.global_position
			debug_draw.add_child(poly)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("yard_vs01_collisions")
	get_tree().debug_collisions_hint = false
	debug_draw.queue_free()


func _take(tag: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	var path := ProjectSettings.globalize_path("res://docs/art_tests/%s.png" % tag)
	img.save_png(path)
	print("yard_vs01 screenshot -> ", path)
