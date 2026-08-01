extends Node2D
## CraftPix yard + PixelLab hero prototype test (does NOT modify craftpix_home_preview).
## F6 / ART_TEST_SHOT for verification screenshots.

const LAYOUT_PATH := "res://assets/third_party/craftpix/main_characters_home/runtime/preview/exterior_preview_layout.json"
const PLAYER_SCENE := "res://scenes/actors/player/player_pixellab_test.tscn"
const VIEW_W := 384
const VIEW_H := 240
const WINDOW_SCALE := 3
const MOVE_SPEED := 70.0

## South fence gate (path columns continue through fence line).
const GATE_CELLS := [
	Vector2i(16, 16), Vector2i(17, 16),
]
## Clear decorative clutter in/around the gate corridor for a readable exit.
## Wide enough to drop incomplete multi-tile props and open a readable path.
const GATE_CLEAR := [
	# corridor + flanks (x 10–20, y 13–17)
	Vector2i(10, 13), Vector2i(11, 13), Vector2i(12, 13), Vector2i(13, 13), Vector2i(14, 13), Vector2i(15, 13),
	Vector2i(16, 13), Vector2i(17, 13), Vector2i(18, 13), Vector2i(19, 13), Vector2i(20, 13),
	Vector2i(10, 14), Vector2i(11, 14), Vector2i(12, 14), Vector2i(13, 14), Vector2i(14, 14), Vector2i(15, 14),
	Vector2i(16, 14), Vector2i(17, 14), Vector2i(18, 14), Vector2i(19, 14), Vector2i(20, 14),
	Vector2i(10, 15), Vector2i(11, 15), Vector2i(12, 15), Vector2i(13, 15), Vector2i(14, 15), Vector2i(15, 15),
	Vector2i(16, 15), Vector2i(17, 15), Vector2i(18, 15), Vector2i(19, 15), Vector2i(20, 15),
	Vector2i(10, 16), Vector2i(11, 16), Vector2i(12, 16), Vector2i(13, 16), Vector2i(14, 16), Vector2i(15, 16),
	Vector2i(16, 16), Vector2i(17, 16), Vector2i(18, 16), Vector2i(19, 16), Vector2i(20, 16),
	Vector2i(10, 17), Vector2i(11, 17), Vector2i(12, 17), Vector2i(13, 17), Vector2i(14, 17), Vector2i(15, 17),
	Vector2i(16, 17), Vector2i(17, 17), Vector2i(18, 17), Vector2i(19, 17), Vector2i(20, 17),
	# orphan / sliced south-edge bottoms outside the corridor
	Vector2i(8, 17), Vector2i(9, 17), Vector2i(6, 17), Vector2i(7, 17),
]

var _layout: Dictionary = {}
var _tile := 16
var _map_w := 0
var _map_h := 0
var _ground_root: Node2D
var _ysort: Node2D
var _player: CharacterBody2D
var _hint: Label
var _shot_cam: Camera2D
var _gate_center := Vector2.ZERO


func _ready() -> void:
	name = "CraftpixHeroTest"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(VIEW_W * WINDOW_SCALE, VIEW_H * WINDOW_SCALE))

	if not FileAccess.file_exists(LAYOUT_PATH):
		_show_missing("Missing layout JSON.\nRun tools/organize_craftpix_home.py")
		return

	var f := FileAccess.open(LAYOUT_PATH, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if typeof(data) != TYPE_DICTIONARY:
		_show_missing("Invalid CraftPix layout JSON.")
		return
	_layout = data
	_tile = int(_layout.get("tile_size", 16))
	_map_w = int(_layout.get("width", 0))
	_map_h = int(_layout.get("height", 0))
	_apply_layout_polish()
	_gate_center = Vector2(16.5 * _tile, 16.0 * _tile)

	var roots: Dictionary = _layout.get("runtime_image_roots", {})
	var any_ok := false
	for k in roots.keys():
		if ResourceLoader.exists(str(roots[k])) or FileAccess.file_exists(ProjectSettings.globalize_path(str(roots[k]))):
			any_ok = true
			break
	if not any_ok:
		_show_missing("CraftPix Home assets are not installed locally.\nSee docs/CRAFTPIX_HOME_AUDIT.md")
		return

	_build_world()
	_build_player()
	_build_ui()

	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.35).timeout
		await _shot_sequence(shot)
		get_tree().quit()


func _apply_layout_polish() -> void:
	## Mutate loaded layout: open south gate, clear entrance clutter, drop sliced edge props.
	var layers: Array = _layout.get("layers", [])
	var gate_set := {}
	for g in GATE_CELLS:
		gate_set["%d,%d" % [g.x, g.y]] = true
	var clear_set := {}
	for g in GATE_CLEAR:
		clear_set["%d,%d" % [g.x, g.y]] = true

	for layer_info in layers:
		var lname: String = str(layer_info.get("name", ""))
		var cells: Array = layer_info.get("cells", [])
		var kept: Array = []
		for cell in cells:
			var key := "%d,%d" % [int(cell["x"]), int(cell["y"])]
			if lname == "Fence" and gate_set.has(key):
				continue
			# Props + grass/hedge overlays that choke / clip the gate corridor
			if lname in [
				"Objects1", "Objects2", "Objects3", "Objects4",
				"Grass", "Grass_top_details", "Grass_details3", "Grass_details4",
				"Grass_details5", "Grass_detail6",
			] and clear_set.has(key):
				continue
			# Extra: clear Grass hedge tiles across the south entrance band
			if lname == "Grass" and int(cell["x"]) >= 14 and int(cell["x"]) <= 19 and int(cell["y"]) >= 14 and int(cell["y"]) <= 17:
				continue
			kept.append(cell)
		layer_info["cells"] = kept


func _show_missing(msg: String) -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var lab := Label.new()
	lab.text = msg
	lab.position = Vector2(24, 24)
	lab.add_theme_font_size_override("font_size", 14)
	lab.add_theme_color_override("font_color", Color(0.95, 0.95, 0.9))
	layer.add_child(lab)
	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.2).timeout
		get_tree().quit()


func _load_tex(path: String) -> Texture2D:
	var abs_path := ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(abs_path):
		var img := Image.new()
		if img.load(abs_path) == OK:
			return ImageTexture.create_from_image(img)
	if ResourceLoader.exists(path):
		var res := load(path)
		if res is Texture2D:
			return res as Texture2D
	return null


func _build_tileset(tilesets: Array) -> TileSet:
	var ts := TileSet.new()
	ts.tile_size = Vector2i(_tile, _tile)
	var roots: Dictionary = _layout.get("runtime_image_roots", {})
	var source_id := 0
	for item in tilesets:
		var img_name: String = str(item.get("image", ""))
		var path := str(roots.get(img_name, ""))
		if path == "":
			continue
		var tex := _load_tex(path)
		if tex == null:
			push_warning("CraftPix missing texture: %s" % path)
			continue
		var src := TileSetAtlasSource.new()
		src.texture = tex
		src.texture_region_size = Vector2i(_tile, _tile)
		src.margins = Vector2i(0, 0)
		src.separation = Vector2i(0, 0)
		src.use_texture_padding = true
		var cols := int(item.get("columns", tex.get_width() / _tile))
		var rows := int(tex.get_height() / _tile)
		for y in range(rows):
			for x in range(cols):
				var coords := Vector2i(x, y)
				if not src.has_tile(coords):
					src.create_tile(coords)
		var sid := ts.add_source(src, source_id)
		item["source_id"] = sid
		source_id += 1
	return ts


func _gid_to_source_atlas(gid: int, tilesets: Array) -> Array:
	var owner = null
	for t in tilesets:
		if gid >= int(t["firstgid"]):
			owner = t
	if owner == null or not owner.has("source_id"):
		return []
	var local := gid - int(owner["firstgid"])
	var cols := int(owner["columns"])
	var count := int(owner["tilecount"])
	if cols <= 0 or local < 0 or local >= count:
		return []
	return [int(owner["source_id"]), Vector2i(local % cols, int(local / cols))]


func _tileset_name_for_gid(gid: int, tilesets: Array) -> String:
	var owner = null
	for t in tilesets:
		if gid >= int(t["firstgid"]):
			owner = t
	if owner == null:
		return ""
	if gid >= int(owner["firstgid"]) + int(owner["tilecount"]):
		return ""
	return str(owner.get("name", ""))


func _build_world() -> void:
	var bg := Polygon2D.new()
	bg.color = Color(0.22, 0.35, 0.16)
	bg.polygon = PackedVector2Array([
		Vector2(-64, -64),
		Vector2(_map_w * _tile + 64, -64),
		Vector2(_map_w * _tile + 64, _map_h * _tile + 64),
		Vector2(-64, _map_h * _tile + 64),
	])
	bg.z_index = -20
	add_child(bg)

	var tilesets: Array = _layout.get("tilesets", [])
	var ts := _build_tileset(tilesets)

	_ground_root = Node2D.new()
	_ground_root.name = "GroundLayers"
	add_child(_ground_root)

	_ysort = Node2D.new()
	_ysort.name = "YSortProps"
	_ysort.y_sort_enabled = true
	_ysort.z_index = 10
	add_child(_ysort)

	var z := 0
	for layer_info in _layout.get("layers", []):
		var lname: String = str(layer_info.get("name", "Layer"))
		var layer := TileMapLayer.new()
		layer.name = lname
		layer.tile_set = ts
		layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		layer.z_index = z
		z += 1
		if lname in ["Objects1", "Objects2", "Objects3", "Objects4", "Fence", "House_wall", "House_roof", "windows1", "windows2"]:
			layer.y_sort_enabled = true
			_ysort.add_child(layer)
		else:
			# Ground + grass overlays stay non-Y-sorted so they don't clip the player mid-body
			_ground_root.add_child(layer)

		for cell in layer_info.get("cells", []):
			var gid := int(cell["gid"])
			var mapped := _gid_to_source_atlas(gid, tilesets)
			if mapped.is_empty():
				continue
			layer.set_cell(Vector2i(int(cell["x"]), int(cell["y"])), int(mapped[0]), mapped[1] as Vector2i)

	_add_blocking_colliders(tilesets)


func _is_gate_cell(p: Vector2i) -> bool:
	for g in GATE_CELLS:
		if g == p:
			return true
	# Also treat vertical path corridor through gate as non-blocking
	if p.y >= 15 and p.y <= 17 and (p.x == 16 or p.x == 17):
		return true
	return false


func _add_blocking_colliders(tilesets: Array) -> void:
	## Fence (except gate) + house walls + tree footprints only — not every decor tile.
	var blockers := StaticBody2D.new()
	blockers.name = "Blockers"
	blockers.collision_layer = 1
	blockers.collision_mask = 0
	add_child(blockers)

	var occupied := {}

	for layer_info in _layout.get("layers", []):
		var lname: String = str(layer_info.get("name", ""))
		for cell in layer_info.get("cells", []):
			var p := Vector2i(int(cell["x"]), int(cell["y"]))
			if _is_gate_cell(p):
				continue
			var key := "%d,%d" % [p.x, p.y]
			if lname == "Fence" or lname == "House_wall":
				occupied[key] = p
				continue
			if lname in ["Objects1", "Objects2", "Objects3", "Objects4"]:
				var tname := _tileset_name_for_gid(int(cell["gid"]), tilesets)
				# Tree trunks / large exterior props only (avoid mushrooms/flowers choking paths)
				if tname == "Trees_animation":
					occupied[key] = p
				elif tname == "exterior" and lname in ["Objects1", "Objects2"]:
					# Only south-most tiles of exterior object stacks become solid footprints
					if _is_object_footprint(p, layer_info.get("cells", [])):
						occupied[key] = p

	for key in occupied.keys():
		var p: Vector2i = occupied[key]
		var cs := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(_tile * 0.8, _tile * 0.4)
		cs.shape = shape
		cs.position = Vector2(p.x * _tile + _tile * 0.5, p.y * _tile + _tile * 0.78)
		blockers.add_child(cs)


func _is_object_footprint(p: Vector2i, cells: Array) -> bool:
	## True if no object cell directly below — treat as ground contact row.
	var below := false
	for cell in cells:
		if int(cell["x"]) == p.x and int(cell["y"]) == p.y + 1:
			below = true
			break
	return not below


func _build_player() -> void:
	var packed := load(PLAYER_SCENE) as PackedScene
	if packed == null:
		push_error("Missing player scene: %s" % PLAYER_SCENE)
		return
	_player = packed.instantiate() as CharacterBody2D
	_player.name = "PlayerPixelLabTest"
	_player.position = Vector2(16.5 * _tile, 13.2 * _tile)
	_player.z_as_relative = true
	_player.z_index = 0
	# No node-level scale hacks — pixel size handled inside player (PIXEL_DIV).
	_player.scale = Vector2.ONE
	if _player.get_parent() != null:
		(_player.get_parent() as Node2D).scale = Vector2.ONE
	_ysort.scale = Vector2.ONE
	scale = Vector2.ONE
	_ysort.add_child(_player)
	var anim := _player.get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
	if anim:
		anim.scale = Vector2.ONE
		anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if _player.has_method("set_camera_zoom"):
		_player.call("set_camera_zoom", Vector2(WINDOW_SCALE, WINDOW_SCALE))
	if _player.has_method("set_camera_limits"):
		_player.call("set_camera_limits", Rect2(0, 0, _map_w * _tile, _map_h * _tile))


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hint = Label.new()
	_hint.position = Vector2(8, 6)
	_hint.add_theme_font_size_override("font_size", 11)
	_hint.add_theme_color_override("font_color", Color.WHITE)
	_hint.text = "CraftPix + PixelLab hero 8-dir · WASD · F12 · scale=1 · pixel_div=2"
	_hint.visible = false
	layer.add_child(_hint)


func _physics_process(_delta: float) -> void:
	# Movement handled by player_pixellab_test.gd
	if _player == null or not is_instance_valid(_player):
		return
	if OS.get_environment("ART_TEST_SHOT") != "" and _shot_cam != null:
		return
	_player.position.x = clampf(_player.position.x, 8.0, float(_map_w * _tile - 8))
	_player.position.y = clampf(_player.position.y, 8.0, float(_map_h * _tile - 8))


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F12:
			_hint.visible = not _hint.visible
			get_tree().debug_collisions_hint = _hint.visible
			get_viewport().set_input_as_handled()


func _shot_sequence(_mode: String) -> void:
	_hint.visible = false
	get_tree().debug_collisions_hint = false
	if _player and _player.has_method("set_camera_enabled"):
		_player.call("set_camera_enabled", false)

	_shot_cam = Camera2D.new()
	_shot_cam.enabled = true
	_shot_cam.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	add_child(_shot_cam)
	_shot_cam.make_current()

	# Provisionally accepted display: PIXEL_DIV=2, node scale 1.
	if _player.has_method("rebuild_frames_for_compare"):
		_player.call("rebuild_frames_for_compare", false)
	_player.scale = Vector2.ONE
	_player.visible = true

	var anim := _player.get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
	if anim:
		anim.flip_h = false
		anim.scale = Vector2.ONE

	var dirs := [
		"south", "south_east", "east", "north_east",
		"north", "north_west", "west", "south_west",
	]

	# 8 idle facings (open patio)
	_player.position = Vector2(16.5 * _tile, 14.2 * _tile)
	_shot_cam.position = Vector2(16.5 * _tile, 13.6 * _tile)
	for d in dirs:
		if _player.has_method("set_facing_name"):
			_player.call("set_facing_name", d)
		if anim:
			anim.play("idle_%s" % d)
		await get_tree().process_frame
		await get_tree().create_timer(0.08).timeout
		await _take("craftpix_hero_idle_%s" % d)

	# 8 walk facings (same spot)
	for d in dirs:
		if _player.has_method("set_facing_name"):
			_player.call("set_facing_name", d)
		if anim:
			anim.play("walk_%s" % d)
		await get_tree().process_frame
		await get_tree().create_timer(0.12).timeout
		await _take("craftpix_hero_walk_%s" % d)

	# Location checks
	_player.position = Vector2(17.2 * _tile, 13.15 * _tile)
	if anim:
		anim.play("idle_south")
	_shot_cam.position = Vector2(16.8 * _tile, 12.2 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("craftpix_hero_door")

	# Inside yard (patio)
	_player.position = Vector2(14.0 * _tile, 13.8 * _tile)
	_shot_cam.position = Vector2(15.0 * _tile, 13.2 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.15).timeout
	await _take("craftpix_hero_inside_yard")

	# Gate corridor
	_player.position = Vector2(16.5 * _tile, 15.5 * _tile)
	_shot_cam.position = Vector2(16.5 * _tile, 15.6 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.15).timeout
	await _take("craftpix_hero_gate")

	# Outside fence (south of gate)
	_player.position = Vector2(16.5 * _tile, 17.5 * _tile)
	_shot_cam.position = Vector2(16.5 * _tile, 16.4 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.15).timeout
	await _take("craftpix_hero_outside")

	# Beside tree
	_player.position = Vector2(5.5 * _tile, 13.5 * _tile)
	if anim:
		anim.play("idle_east")
	_shot_cam.position = Vector2(6.5 * _tile, 12.5 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.15).timeout
	await _take("craftpix_hero_tree")

	# Behind / under canopy (slightly north of tree trunk area)
	_player.position = Vector2(5.2 * _tile, 12.2 * _tile)
	if anim:
		anim.play("idle_south")
	_shot_cam.position = Vector2(6.2 * _tile, 11.8 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.15).timeout
	await _take("craftpix_hero_tree_behind")

	# Fence edge
	_player.position = Vector2(12.0 * _tile, 15.8 * _tile)
	if anim:
		anim.play("idle_east")
	_shot_cam.position = Vector2(13.0 * _tile, 14.8 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.15).timeout
	await _take("craftpix_hero_fence")

	# Rock / bushes (left boulder area)
	_player.position = Vector2(4.0 * _tile, 15.0 * _tile)
	if anim:
		anim.play("idle_south")
	_shot_cam.position = Vector2(5.0 * _tile, 14.0 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.15).timeout
	await _take("craftpix_hero_rocks")

	# Collision debug at gate
	get_tree().debug_collisions_hint = true
	var debug_draw := Node2D.new()
	debug_draw.z_as_relative = false
	debug_draw.z_index = 80
	add_child(debug_draw)
	var blockers := get_node_or_null("Blockers") as StaticBody2D
	if blockers:
		for child in blockers.get_children():
			if child is CollisionShape2D and child.shape is RectangleShape2D:
				var rs := child.shape as RectangleShape2D
				var poly := Polygon2D.new()
				var hx := rs.size.x * 0.5
				var hy := rs.size.y * 0.5
				poly.polygon = PackedVector2Array([
					Vector2(-hx, -hy), Vector2(hx, -hy), Vector2(hx, hy), Vector2(-hx, hy),
				])
				poly.color = Color(0.15, 0.85, 1.0, 0.45)
				poly.global_position = child.global_position
				debug_draw.add_child(poly)
	_player.position = Vector2(16.5 * _tile, 15.5 * _tile)
	if anim:
		anim.play("idle_south")
	for child in _player.get_children():
		if child is CollisionShape2D and child.shape is RectangleShape2D:
			var rs2 := child.shape as RectangleShape2D
			var poly2 := Polygon2D.new()
			var hx2 := rs2.size.x * 0.5
			var hy2 := rs2.size.y * 0.5
			poly2.polygon = PackedVector2Array([
				Vector2(-hx2, -hy2), Vector2(hx2, -hy2), Vector2(hx2, hy2), Vector2(-hx2, hy2),
			])
			poly2.color = Color(1.0, 0.35, 0.2, 0.55)
			poly2.global_position = _player.to_global(child.position)
			debug_draw.add_child(poly2)
	_shot_cam.position = Vector2(16.5 * _tile, 15.6 * _tile)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("craftpix_hero_collisions")
	get_tree().debug_collisions_hint = false
	debug_draw.queue_free()

	_log_hero_tex("final_pixel_div")


func _log_hero_tex(tag: String) -> void:
	if _player == null:
		return
	var anim := _player.get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
	if anim == null or anim.sprite_frames == null:
		return
	var tex := anim.sprite_frames.get_frame_texture(anim.animation, anim.frame)
	if tex:
		print("hero tex [%s] %dx%d  player.scale=%s anim.scale=%s" % [
			tag, tex.get_width(), tex.get_height(), _player.scale, anim.scale,
		])


func _take(tag: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	var path := ProjectSettings.globalize_path("res://docs/art_tests/%s.png" % tag)
	img.save_png(path)
	print("hero screenshot -> ", path)
