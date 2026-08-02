extends Node2D
## VS01 outdoor yard — childhood home with approved main_house_v1 + overgrown yard.
## PixelLab hero scale unchanged. ART_TEST_SHOT=1 for verification screenshots.

const HotspotUtil = preload("res://scripts/world/hotspot_util.gd")
const ASSET_ROOT := "res://assets/art/outdoor/yard_vs01/"
const HOUSE_TEX := ASSET_ROOT + "main_house_v1.png"
const HOUSE_META := ASSET_ROOT + "main_house_v1.json"
const PLAYER_SCENE := "res://scenes/actors/player/player_pixellab_test.tscn"
const TILE := 16
const MAP_W := 40
const MAP_H := 34
## Must match tools/build_yard_vs01_assets.py GROUND_PAD_TILES (camera bleed grass).
const GROUND_PAD_TILES := 8
const VIEW_W := 384
const VIEW_H := 240
const WINDOW_SCALE := 3
## Runtime house size is baked into PNG (~288×151); node/sprite scale stays 1.
## Foundation / feet of MainHouse in tile space.
const HOUSE_FEET := Vector2(20.0, 14.4)
## Front-yard spawn: house + hero + path; gate is further south.
const PLAYER_SPAWN := Vector2(20.0, 18.6)
## Integer pixel-perfect zoom — whole yard must NOT fit on one screen.
const PLAY_CAMERA_ZOOM := 2.0
## Nudge up so roof has a little air; player sits slightly below center.
const PLAY_CAMERA_OFFSET := Vector2(0, -42)

var _ysort: Node2D
var _player: CharacterBody2D
var _hint: Label
var _prompt: Label
var _shot_cam: Camera2D
var _blockers: StaticBody2D
var _house: Node2D
var _door_hotspot: Area2D


func _ready() -> void:
	name = "YardVS01"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(VIEW_W * WINDOW_SCALE, VIEW_H * WINDOW_SCALE))

	if not FileAccess.file_exists(ASSET_ROOT + "ground.png") or not FileAccess.file_exists(HOUSE_TEX):
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


func _camera_limit_rect() -> Rect2:
	## Padded grass plate — playable fence stays on MAP_*; void never shows.
	var pad := float(GROUND_PAD_TILES * TILE)
	return Rect2(-pad, -pad, float((MAP_W + GROUND_PAD_TILES * 2) * TILE), float((MAP_H + GROUND_PAD_TILES * 2) * TILE))


func _apply_camera_limits(cam: Camera2D) -> void:
	var r := _camera_limit_rect()
	cam.limit_left = int(r.position.x)
	cam.limit_top = int(r.position.y)
	cam.limit_right = int(r.end.x)
	cam.limit_bottom = int(r.end.y)


func _build_ground() -> void:
	var ground := Node2D.new()
	ground.name = "Ground"
	add_child(ground)
	var spr := _add_sprite(ground, ASSET_ROOT + "ground.png", Vector2.ZERO, false)
	## Ground bake includes GROUND_PAD_TILES of grass around the playable plate.
	spr.position = Vector2(-GROUND_PAD_TILES * TILE, -GROUND_PAD_TILES * TILE)
	spr.centered = false
	spr.z_index = 0


func _build_fence() -> void:
	## Perimeter fence with south gate. North fence sits above the house roof for air.
	var post := ASSET_ROOT + "fence_post.png"
	var rail := ASSET_ROOT + "fence_rail.png"
	var north_y := 4.2
	var south_y := 32.2
	# Top — leave breathing room above the roof
	for x in range(8, 32):
		_fence_segment(Vector2((x + 0.5) * TILE, north_y * TILE), post, rail, true)
		_add_blocker_rect(Vector2((x + 0.5) * TILE, (north_y + 0.3) * TILE), Vector2(14, 6))
	# Bottom (except gate)
	for x in range(8, 32):
		if x >= 18 and x <= 21:
			continue
		_fence_segment(Vector2((x + 0.5) * TILE, south_y * TILE), post, rail, true)
		_add_blocker_rect(Vector2((x + 0.5) * TILE, (south_y + 0.2) * TILE), Vector2(14, 6))
	# Left / right
	for y in range(int(north_y), int(south_y) + 1):
		_fence_segment(Vector2(8.2 * TILE, (y + 0.5) * TILE), post, rail, false)
		_add_blocker_rect(Vector2(8.3 * TILE, (y + 0.5) * TILE), Vector2(6, 14))
		_fence_segment(Vector2(31.8 * TILE, (y + 0.5) * TILE), post, rail, false)
		_add_blocker_rect(Vector2(31.7 * TILE, (y + 0.5) * TILE), Vector2(6, 14))
	# Gate visual (open posts)
	_add_sprite(_ysort, ASSET_ROOT + "gate.png", Vector2(20 * TILE, south_y * TILE), true, Vector2(0, -6))


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
	## Separate house object: sprite + footprint collision + door hotspot.
	## Feet/Y-sort origin at foundation bottom; door offset from main_house_v1.json.
	var tex := _load_tex(HOUSE_TEX)
	if tex == null:
		push_error("Missing approved house texture: %s" % HOUSE_TEX)
		return

	var hw := tex.get_width()
	var hh := tex.get_height()
	var door_rect := Rect2(107, 84, 12, 33)  # fallback display-space door
	if FileAccess.file_exists(ProjectSettings.globalize_path(HOUSE_META)):
		var f := FileAccess.open(HOUSE_META, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		if typeof(data) == TYPE_DICTIONARY and data.has("door_rect_display"):
			var d: Dictionary = data["door_rect_display"]
			door_rect = Rect2(
				float(d.x0), float(d.y0),
				float(d.x1) - float(d.x0),
				float(d.y1) - float(d.y0)
			)

	# Foundation higher in the yard plate → more playable space south of the house.
	var house_pos := Vector2(HOUSE_FEET.x * TILE, HOUSE_FEET.y * TILE)

	_house = Node2D.new()
	_house.name = "MainHouse"
	_house.position = house_pos
	_house.z_as_relative = true
	_ysort.add_child(_house)

	var spr := Sprite2D.new()
	spr.name = "Sprite"
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = true
	spr.texture = tex
	# Bottom of texture sits on node origin (Y-sort / feet line).
	spr.offset = Vector2(0, 1.0 - float(hh) * 0.5)
	# Scale baked into runtime PNG; keep node scale 1 for nearest pixels.
	spr.scale = Vector2.ONE
	_house.add_child(spr)

	# Solid footprint: stone foundation / walls — not full roof canopy.
	var body := StaticBody2D.new()
	body.name = "HouseCollision"
	body.collision_layer = 1
	body.collision_mask = 0
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(hw * 0.72, 34)
	col.shape = shape
	col.position = Vector2(-6, -14)
	body.add_child(col)
	_house.add_child(body)

	# Door local: texture point → node space with centered + offset.
	var door_cx := door_rect.position.x + door_rect.size.x * 0.5
	var door_bottom := door_rect.position.y + door_rect.size.y
	var door_local := Vector2(
		door_cx - float(hw) * 0.5,
		spr.offset.y + (door_bottom - float(hh) * 0.5)
	)
	# Interaction south of steps — in front of the house sprite, not under it.
	var door_script := load("res://scripts/locations/outdoor/childhood_home/yard_vs01_door.gd")
	_door_hotspot = door_script.new() as Area2D
	_door_hotspot.name = "DoorHotspot"
	_door_hotspot.position = Vector2(door_local.x, 8)
	var dcol := CollisionShape2D.new()
	var dshape := RectangleShape2D.new()
	dshape.size = Vector2(maxf(20.0, door_rect.size.x + 10.0), 18)
	dcol.shape = dshape
	_door_hotspot.add_child(dcol)
	_house.add_child(_door_hotspot)

	print("yard_vs01 house display %dx%d door_local=%s cam zoom=%.1f offset=%s" % [
		hw, hh, door_local, PLAY_CAMERA_ZOOM, PLAY_CAMERA_OFFSET
	])


func _build_secondary_props() -> void:
	# Well — east of path / house
	var well := _add_sprite(_ysort, ASSET_ROOT + "well.png", Vector2(28 * TILE, 17 * TILE), true, Vector2(0, -10))
	well.name = "Well"
	_add_blocker_rect(Vector2(28 * TILE, 17.4 * TILE), Vector2(22, 12))
	# Woodpile west of house
	var wood := _add_sprite(_ysort, ASSET_ROOT + "woodpile.png", Vector2(11.5 * TILE, 14.2 * TILE), true, Vector2(0, -4))
	wood.name = "Woodpile"
	_add_blocker_rect(Vector2(11.5 * TILE, 14.5 * TILE), Vector2(28, 10))
	# Shed corner — west edge
	var shed := _add_sprite(_ysort, ASSET_ROOT + "shed_corner.png", Vector2(10.2 * TILE, 21 * TILE), true, Vector2(0, -12))
	shed.name = "ShedCorner"
	_add_blocker_rect(Vector2(10.2 * TILE, 21.5 * TILE), Vector2(36, 16))


func _build_trees() -> void:
	## Keep trees at yard edges — not oversized fairy props, not covering the house.
	var trees := [
		[ASSET_ROOT + "props/tree_a.png", Vector2(10 * TILE, 9.5 * TILE)],
		[ASSET_ROOT + "props/tree_b.png", Vector2(30 * TILE, 10.5 * TILE)],
		[ASSET_ROOT + "props/tree_c.png", Vector2(8.5 * TILE, 24 * TILE)],
		[ASSET_ROOT + "props/tree_a.png", Vector2(30.5 * TILE, 26 * TILE)],
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
	# Path toward door (slightly left of map center because of ¾ house facing).
	var required := [
		{
			"id": "vs01_stump_path",
			"kind": "stump",
			"pos": Vector2(19.8 * TILE, 26.5 * TILE),
			"spr": ASSET_ROOT + "stump.png",
			"prompt": "убрать пень",
			"item": "wood",
			"solid": true,
			"solid_size": Vector2(16, 10),
		},
		{
			"id": "vs01_log_path",
			"kind": "log",
			"pos": Vector2(19.2 * TILE, 23.5 * TILE),
			"spr": ASSET_ROOT + "log.png",
			"prompt": "убрать бревно",
			"item": "wood",
			"solid": true,
			"solid_size": Vector2(28, 8),
		},
		{
			"id": "vs01_rock_path",
			"kind": "stone",
			"pos": Vector2(19.0 * TILE, 18.8 * TILE),
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
			"pos": Vector2(18.4 * TILE, 16.0 * TILE),
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
		{"id": "vs01_weed_1", "kind": "weed", "pos": Vector2(16 * TILE, 25 * TILE), "spr": ASSET_ROOT + "weed_a.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_2", "kind": "weed", "pos": Vector2(23 * TILE, 24 * TILE), "spr": ASSET_ROOT + "weed_b.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_3", "kind": "weed", "pos": Vector2(15 * TILE, 16 * TILE), "spr": ASSET_ROOT + "weed_a.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_4", "kind": "weed", "pos": Vector2(24 * TILE, 18 * TILE), "spr": ASSET_ROOT + "weed_b.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_rock_side", "kind": "stone", "pos": Vector2(14 * TILE, 21 * TILE), "spr": ASSET_ROOT + "props/rock_sm.png", "prompt": "сдвинуть камень", "item": "stone", "hits": 5, "solid": true, "solid_size": Vector2(12, 8)},
		{"id": "vs01_bush_side", "kind": "bush", "pos": Vector2(25.5 * TILE, 13.2 * TILE), "spr": ASSET_ROOT + "props/bush_md.png", "prompt": "прорубить куст", "item": "grass", "solid": true, "solid_size": Vector2(18, 12)},
		{"id": "vs01_stump_side", "kind": "stump", "pos": Vector2(12.5 * TILE, 27 * TILE), "spr": ASSET_ROOT + "stump.png", "prompt": "убрать пень", "item": "wood", "solid": true, "solid_size": Vector2(16, 10)},
	]
	for cfg in optional:
		_spawn_clearable(cfg)

	# Decorative non-clearable rocks/bushes off path
	for p in [
		[ASSET_ROOT + "props/rock_lg.png", Vector2(12 * TILE, 16 * TILE), Vector2(20, 12)],
		[ASSET_ROOT + "props/bush_sm.png", Vector2(26 * TILE, 27 * TILE), Vector2(14, 10)],
		[ASSET_ROOT + "props/rock_sm.png", Vector2(28 * TILE, 21 * TILE), Vector2(10, 8)],
	]:
		_add_sprite(_ysort, str(p[0]), p[1], true, Vector2(0, -6))
		_add_blocker_rect(p[1] + Vector2(0, 2), p[2])


func _build_player() -> void:
	var packed := load(PLAYER_SCENE) as PackedScene
	_player = packed.instantiate() as CharacterBody2D
	_player.name = "PlayerPixelLabTest"
	# Mid-path spawn: follow-cam frames whole house + entrance path + front yard.
	_player.position = Vector2(PLAYER_SPAWN.x * TILE, PLAYER_SPAWN.y * TILE)
	_player.scale = Vector2.ONE
	_ysort.add_child(_player)
	if _player.has_method("set_camera_zoom"):
		_player.call("set_camera_zoom", Vector2(PLAY_CAMERA_ZOOM, PLAY_CAMERA_ZOOM))
	if _player.has_method("set_camera_offset"):
		_player.call("set_camera_offset", PLAY_CAMERA_OFFSET)
	if _player.has_method("set_camera_limits"):
		_player.call("set_camera_limits", _camera_limit_rect())
	# Also stamp limits on the live Camera2D in case the helper missed limit_enabled.
	var pcam := _player.get_node_or_null("Camera2D") as Camera2D
	if pcam:
		_apply_camera_limits(pcam)


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
	_shot_cam.zoom = Vector2(PLAY_CAMERA_ZOOM, PLAY_CAMERA_ZOOM)
	_shot_cam.offset = Vector2.ZERO
	_apply_camera_limits(_shot_cam)
	add_child(_shot_cam)
	_shot_cam.make_current()

	# Overview — pull back to show full yard plate
	_shot_cam.zoom = Vector2(1.35, 1.35)
	_shot_cam.position = Vector2(20 * TILE, 18.0 * TILE)
	if _player:
		_player.visible = false
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("yard_vs01_overview")

	_shot_cam.zoom = Vector2(PLAY_CAMERA_ZOOM, PLAY_CAMERA_ZOOM)
	if _player:
		_player.visible = true
		_player.scale = Vector2.ONE
		var anim := _player.get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
		if anim:
			anim.scale = Vector2.ONE
			anim.play("idle_north")

	# Start composition — house + hero + path (not the whole yard)
	_player.position = Vector2(PLAYER_SPAWN.x * TILE, PLAYER_SPAWN.y * TILE)
	_shot_cam.position = _player.position + PLAY_CAMERA_OFFSET
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take("yard_vs01_start")

	# Door — hero at steps
	if _door_hotspot:
		_player.position = _door_hotspot.global_position + Vector2(0, 12)
	else:
		_player.position = Vector2(HOUSE_FEET.x * TILE, (HOUSE_FEET.y + 1.2) * TILE)
	if _player.get_node_or_null("AnimatedSprite2D"):
		(_player.get_node("AnimatedSprite2D") as AnimatedSprite2D).play("idle_north")
	_shot_cam.position = _player.position + PLAY_CAMERA_OFFSET
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take("yard_vs01_door")

	# Path down — camera follows; yard continues off-screen
	_player.position = Vector2(PLAYER_SPAWN.x * TILE, (PLAYER_SPAWN.y + 4.5) * TILE)
	if _player.get_node_or_null("AnimatedSprite2D"):
		(_player.get_node("AnimatedSprite2D") as AnimatedSprite2D).play("idle_south")
	_shot_cam.position = _player.position + PLAY_CAMERA_OFFSET
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take("yard_vs01_path_down")

	# Gate / entrance (south)
	_player.position = Vector2(20 * TILE, 31.5 * TILE)
	_shot_cam.position = Vector2(20 * TILE, 28.5 * TILE)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("yard_vs01_gate")

	# Scale check near tree + rock
	_player.position = Vector2(12.5 * TILE, 17.0 * TILE)
	if _player.get_node_or_null("AnimatedSprite2D"):
		(_player.get_node("AnimatedSprite2D") as AnimatedSprite2D).play("idle_east")
	_shot_cam.position = Vector2(14 * TILE, 15.0 * TILE)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("yard_vs01_scale")

	# Collisions debug at path
	get_tree().debug_collisions_hint = true
	_player.position = Vector2(PLAYER_SPAWN.x * TILE, PLAYER_SPAWN.y * TILE)
	_shot_cam.position = _player.position + PLAY_CAMERA_OFFSET
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
