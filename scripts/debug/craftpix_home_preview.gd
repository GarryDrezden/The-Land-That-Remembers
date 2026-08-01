extends Node2D
## CraftPix Main Character's Home outdoor preview (F6).
## Loads a cropped region exported from Exterior.tmx — CraftPix assets only.

const LAYOUT_PATH := "res://assets/third_party/craftpix/main_characters_home/runtime/preview/exterior_preview_layout.json"
const VIEW_W := 384
const VIEW_H := 240
const WINDOW_SCALE := 3
const MOVE_SPEED := 70.0

var _layout: Dictionary = {}
var _tile := 16
var _map_w := 0
var _map_h := 0
var _ground_root: Node2D
var _ysort: Node2D
var _player: CharacterBody2D
var _hint: Label
var _shot_cam: Camera2D


func _ready() -> void:
	name = "CraftpixHomePreview"
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

	# Verify at least one atlas exists
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
	## returns [source_id, atlas_coords] or empty
	var owner = null
	for t in tilesets:
		if gid >= int(t["firstgid"]):
			owner = t
	if owner == null:
		return []
	if not owner.has("source_id"):
		return []
	var local := gid - int(owner["firstgid"])
	var cols := int(owner["columns"])
	var count := int(owner["tilecount"])
	if cols <= 0 or local < 0 or local >= count:
		return []
	var ax := local % cols
	var ay := int(local / cols)
	return [int(owner["source_id"]), Vector2i(ax, ay)]


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

	# Layer stacking: lower first. Objects/house go into y-sort friendly TileMapLayers with z
	var z := 0
	for layer_info in _layout.get("layers", []):
		var lname: String = str(layer_info.get("name", "Layer"))
		var layer := TileMapLayer.new()
		layer.name = lname
		layer.tile_set = ts
		layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		layer.z_index = z
		z += 1
		# Y-sort higher object layers
		if lname in ["Objects1", "Objects2", "Objects3", "Objects4", "Fence", "House_wall", "House_roof", "windows1", "windows2", "Grass_top_details"]:
			layer.y_sort_enabled = true
			_ysort.add_child(layer)
		else:
			_ground_root.add_child(layer)

		for cell in layer_info.get("cells", []):
			var gid := int(cell["gid"])
			var mapped := _gid_to_source_atlas(gid, tilesets)
			if mapped.is_empty():
				continue
			var sid: int = mapped[0]
			var atlas: Vector2i = mapped[1]
			var pos := Vector2i(int(cell["x"]), int(cell["y"]))
			layer.set_cell(pos, sid, atlas)
			# Flip via alternate tiles if needed — skip transpose-heavy cases for preview
			if cell.get("fh", false) or cell.get("fv", false):
				# Godot 4 flip via transpose/flip flags on tile data is per-tile source; keep simple
				pass

	_add_blocking_colliders()


func _add_blocking_colliders() -> void:
	## Approximate blockers from dense house/fence/object cells (footprint).
	var blockers := StaticBody2D.new()
	blockers.name = "Blockers"
	blockers.collision_layer = 1
	blockers.collision_mask = 0
	add_child(blockers)

	var occupied := {}
	for layer_info in _layout.get("layers", []):
		var lname: String = str(layer_info.get("name", ""))
		if lname not in ["House_wall", "Fence", "Objects1", "Objects2", "Objects4"]:
			continue
		for cell in layer_info.get("cells", []):
			var key := "%d,%d" % [int(cell["x"]), int(cell["y"])]
			occupied[key] = Vector2i(int(cell["x"]), int(cell["y"]))

	for key in occupied.keys():
		var p: Vector2i = occupied[key]
		# Only bottom-ish tiles of multi-tile props become solid; for house walls all solid
		var cs := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(_tile * 0.85, _tile * 0.45)
		cs.shape = shape
		cs.position = Vector2(p.x * _tile + _tile * 0.5, p.y * _tile + _tile * 0.75)
		blockers.add_child(cs)


func _build_player() -> void:
	# Neutral silhouette — pack has no human character
	_player = CharacterBody2D.new()
	_player.name = "Player"
	_player.collision_layer = 1
	_player.collision_mask = 1
	_player.position = Vector2((_map_w * 0.45) * _tile, (_map_h * 0.72) * _tile)
	_player.y_sort_enabled = true
	_player.z_index = 20

	var body := Polygon2D.new()
	body.name = "Silhouette"
	body.color = Color(0.15, 0.16, 0.18, 0.95)
	body.polygon = PackedVector2Array([
		Vector2(-3, -14), Vector2(3, -14), Vector2(4, -8), Vector2(4, -2),
		Vector2(3, 0), Vector2(4, 6), Vector2(2, 6), Vector2(1, 1),
		Vector2(-1, 1), Vector2(-2, 6), Vector2(-4, 6), Vector2(-3, 0),
		Vector2(-4, -2), Vector2(-4, -8),
	])
	_player.add_child(body)

	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(6, 4)
	cs.shape = shape
	cs.position = Vector2(0, 3)
	_player.add_child(cs)

	var cam := Camera2D.new()
	cam.name = "Cam"
	cam.enabled = true
	cam.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = _map_w * _tile
	cam.limit_bottom = _map_h * _tile
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 8.0
	_player.add_child(cam)
	_ysort.add_child(_player)


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hint = Label.new()
	_hint.position = Vector2(8, 6)
	_hint.add_theme_font_size_override("font_size", 11)
	_hint.add_theme_color_override("font_color", Color.WHITE)
	_hint.text = "CraftPix home preview · WASD · F12 debug"
	_hint.visible = false
	layer.add_child(_hint)


func _physics_process(_delta: float) -> void:
	if _player == null or not is_instance_valid(_player):
		return
	if OS.get_environment("ART_TEST_SHOT") != "" and _shot_cam != null:
		return
	var dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if Input.is_key_pressed(KEY_A):
		dir.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		dir.x += 1.0
	if Input.is_key_pressed(KEY_W):
		dir.y -= 1.0
	if Input.is_key_pressed(KEY_S):
		dir.y += 1.0
	dir = dir.limit_length(1.0)
	_player.velocity = dir * MOVE_SPEED
	_player.move_and_slide()
	_player.position.x = clampf(_player.position.x, 8.0, float(_map_w * _tile - 8))
	_player.position.y = clampf(_player.position.y, 8.0, float(_map_h * _tile - 8))


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F12:
			_hint.visible = not _hint.visible
			get_tree().debug_collisions_hint = _hint.visible
			get_viewport().set_input_as_handled()


func _shot_sequence(mode: String) -> void:
	_hint.visible = false
	get_tree().debug_collisions_hint = false
	# Disable player camera so ShotCam is authoritative
	if _player:
		var pcam := _player.get_node_or_null("Cam") as Camera2D
		if pcam:
			pcam.enabled = false
		_player.visible = false
	_shot_cam = Camera2D.new()
	_shot_cam.enabled = true
	_shot_cam.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	_shot_cam.position = Vector2(_map_w * _tile * 0.52, _map_h * _tile * 0.45)
	add_child(_shot_cam)
	_shot_cam.make_current()

	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take("craftpix_home_preview")

	_shot_cam.position = Vector2(_map_w * _tile * 0.35, _map_h * _tile * 0.65)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("craftpix_home_preview_move")

	_shot_cam.position = Vector2(_map_w * _tile * 0.58, _map_h * _tile * 0.32)
	if _player:
		_player.visible = true
		_player.position = _shot_cam.position + Vector2(10, 30)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("craftpix_home_preview_ysort")

	if _player:
		_player.visible = true
	get_tree().debug_collisions_hint = true
	_shot_cam.position = Vector2(_map_w * _tile * 0.5, _map_h * _tile * 0.55)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take("craftpix_home_preview_collisions")
	get_tree().debug_collisions_hint = false
	mode = mode


func _take(tag: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	var path := ProjectSettings.globalize_path("res://docs/art_tests/%s.png" % tag)
	img.save_png(path)
	print("craftpix screenshot -> ", path)
