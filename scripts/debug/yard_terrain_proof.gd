extends Node2D
## Seamless terrain proof — macro variation pass.
## F6. ART_TEST_SHOT=sequence for screenshots. T=alt shape. F12=debug.

const YardTerrainTilesetFactory = preload("res://scripts/tilesets/yard_terrain_tileset_factory.gd")

const TILE := 16
const MAP_W := 24
const MAP_H := 15
const VIEW_W := 384
const VIEW_H := 240
const WINDOW_SCALE := 3
const MOVE_SPEED := 72.0

var _ground: TileMapLayer
var _decor: TileMapLayer
var _player: CharacterBody2D
var _shape_b := false
var _hint: Label
var _soil_cells: Array[Vector2i] = []


func _ready() -> void:
	name = "YardTerrainProof"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(VIEW_W * WINDOW_SCALE, VIEW_H * WINDOW_SCALE))

	_build_layers()
	_paint_terrain(false)
	_paint_decor()
	_build_player()
	_build_ui()

	var save_path := "res://resources/tilesets/yard_ground_tileset.tres"
	if not FileAccess.file_exists(ProjectSettings.globalize_path(save_path)):
		YardTerrainTilesetFactory.save_ground_tileset(save_path)

	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.4).timeout
		if shot == "sequence" or shot == "1":
			await _shot_sequence()
		elif shot == "before":
			await _shot_clean("before_fair")
		else:
			await _take_screenshot(shot)
		get_tree().quit()


func _build_layers() -> void:
	var bg := Polygon2D.new()
	bg.name = "ClearFill"
	bg.color = Color(0.27, 0.42, 0.18)
	bg.polygon = PackedVector2Array([
		Vector2(-64, -64),
		Vector2(MAP_W * TILE + 64, -64),
		Vector2(MAP_W * TILE + 64, MAP_H * TILE + 64),
		Vector2(-64, MAP_H * TILE + 64),
	])
	bg.z_index = -10
	add_child(bg)

	_ground = TileMapLayer.new()
	_ground.name = "GroundTerrain"
	_ground.tile_set = YardTerrainTilesetFactory.build_ground_tileset()
	_ground.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_ground)

	_decor = TileMapLayer.new()
	_decor.name = "GroundDecoration"
	_decor.tile_set = YardTerrainTilesetFactory.build_decor_tileset()
	_decor.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_decor.z_index = 1
	add_child(_decor)


func _all_cells() -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	for y in range(MAP_H):
		for x in range(MAP_W):
			cells.append(Vector2i(x, y))
	return cells


func _soil_shape_a() -> Array[Vector2i]:
	## Solid ~9×7 for material review: wide left protrusion + soft right indent.
	## No 1-cell tails / detached cells (4-connected only).
	var cells: Array[Vector2i] = []
	var ox := 7
	var oy := 4
	for y in range(7):
		for x in range(9):
			# Soft concave on right side (1 deep × 2 tall), keeps top edge clean
			if x == 8 and (y == 2 or y == 3):
				continue
			cells.append(Vector2i(ox + x, oy + y))
	# Wide protrusion left 3×2, fully attached
	for y in range(2, 4):
		for x in range(-3, 0):
			cells.append(Vector2i(ox + x, oy + y))
	return _unique_in_map(cells)


func _soil_shape_b() -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	var ox := 8
	var oy := 3
	for y in range(7):
		for x in range(9):
			if y == 6 and x >= 3 and x <= 4:
				continue
			cells.append(Vector2i(ox + x, oy + y))
	for y in range(2, 4):
		for x in range(9, 12):
			cells.append(Vector2i(ox + x, oy + y))
	return _unique_in_map(cells)


func _unique_in_map(cells: Array[Vector2i]) -> Array[Vector2i]:
	var seen := {}
	var out: Array[Vector2i] = []
	for c in cells:
		var k := "%d,%d" % [c.x, c.y]
		if seen.has(k):
			continue
		if c.x < 0 or c.y < 0 or c.x >= MAP_W or c.y >= MAP_H:
			continue
		seen[k] = true
		out.append(c)
	return out


func _is_soil(c: Vector2i) -> bool:
	for s in _soil_cells:
		if s == c:
			return true
	return false


func _ortho_near_soil(c: Vector2i) -> bool:
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		if _is_soil(c + d):
			return true
	return false


func _paint_terrain(shape_b: bool) -> void:
	_shape_b = shape_b
	_ground.clear()
	_ground.set_cells_terrain_connect(_all_cells(), 0, YardTerrainTilesetFactory.TERRAIN_GRASS, true)
	_soil_cells = _soil_shape_b() if shape_b else _soil_shape_a()
	_ground.set_cells_terrain_connect(_soil_cells, 0, YardTerrainTilesetFactory.TERRAIN_SOIL, true)
	_apply_macro_clusters()


func _apply_macro_clusters() -> void:
	if OS.get_environment("ART_TEST_NO_MACRO") != "":
		return
	var src := _ground.tile_set.get_source(0) as TileSetAtlasSource
	if src == null or not src.has_tile(Vector2i(7, 0)):
		return
	## Override interior full-grass / full-soil cells with clustered macros (not checkerboard).
	var grass_interior: Array[Vector2i] = []
	var soil_interior: Array[Vector2i] = []
	for y in range(MAP_H):
		for x in range(MAP_W):
			var c := Vector2i(x, y)
			if _is_soil(c):
				if not _has_ortho_nonsoil(c):
					soil_interior.append(c)
			elif not _ortho_near_soil(c):
				grass_interior.append(c)

	# Grass clusters: sparse(6,0) subtle, light(4,0), dark(5,0), dense(7,0)
	_stamp_clusters(grass_interior, [
		{"atlas": Vector2i(6, 0), "count": 5, "size": 3}, # sparse ~subtle
		{"atlas": Vector2i(4, 0), "count": 2, "size": 3}, # light
		{"atlas": Vector2i(5, 0), "count": 2, "size": 3}, # dark
		{"atlas": Vector2i(7, 0), "count": 2, "size": 2}, # dense accents
	], 101)

	_stamp_clusters(soil_interior, [
		{"atlas": Vector2i(4, 1), "count": 2, "size": 3}, # normal
		{"atlas": Vector2i(5, 1), "count": 2, "size": 3}, # dark
		{"atlas": Vector2i(6, 1), "count": 2, "size": 2}, # clumps
		{"atlas": Vector2i(7, 1), "count": 1, "size": 2}, # pebbles
	], 202)


func _has_ortho_nonsoil(c: Vector2i) -> bool:
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		var n: Vector2i = c + d
		if n.x < 0 or n.y < 0 or n.x >= MAP_W or n.y >= MAP_H:
			continue
		if not _is_soil(n):
			return true
	return false


func _stamp_clusters(pool: Array[Vector2i], specs: Array, seed: int) -> void:
	if pool.is_empty():
		return
	var used := {}
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	for spec in specs:
		var atlas: Vector2i = spec["atlas"]
		var count: int = int(spec["count"])
		var size: int = int(spec["size"])
		for _i in range(count):
			var tries := 0
			while tries < 40:
				tries += 1
				var start: Vector2i = pool[rng.randi_range(0, pool.size() - 1)]
				var key := "%d,%d" % [start.x, start.y]
				if used.has(key):
					continue
				var cluster: Array[Vector2i] = [start]
				used[key] = true
				# Grow 2–4 orthogonally
				var target := clampi(size + rng.randi_range(-1, 1), 2, 4)
				var guard := 0
				while cluster.size() < target and guard < 24:
					guard += 1
					var base: Vector2i = cluster[rng.randi_range(0, cluster.size() - 1)]
					var dirs: Array[Vector2i] = [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
					dirs.shuffle()
					var placed := false
					for d in dirs:
						var nxt: Vector2i = base + d
						var nk := "%d,%d" % [nxt.x, nxt.y]
						if used.has(nk):
							continue
						if not _pool_has(pool, nxt):
							continue
						cluster.append(nxt)
						used[nk] = true
						placed = true
						break
					if not placed:
						break
				for c in cluster:
					_ground.set_cell(c, 0, atlas)
				break


func _pool_has(pool: Array[Vector2i], c: Vector2i) -> bool:
	for p in pool:
		if p == c:
			return true
	return false


func _paint_decor() -> void:
	## Sparse natural groups — readable at game scale.
	_decor.clear()
	# NW tuft group
	_decor.set_cell(Vector2i(2, 2), 0, Vector2i(0, 0))
	_decor.set_cell(Vector2i(3, 2), 0, Vector2i(1, 0))
	_decor.set_cell(Vector2i(2, 3), 0, Vector2i(14, 0))
	# SW dense + clover + white flowers
	_decor.set_cell(Vector2i(3, 11), 0, Vector2i(2, 0))
	_decor.set_cell(Vector2i(4, 12), 0, Vector2i(3, 0))
	_decor.set_cell(Vector2i(5, 12), 0, Vector2i(4, 0))
	_decor.set_cell(Vector2i(6, 13), 0, Vector2i(5, 0))
	_decor.set_cell(Vector2i(4, 11), 0, Vector2i(7, 0))
	# NE blades + yellow
	_decor.set_cell(Vector2i(19, 2), 0, Vector2i(1, 0))
	_decor.set_cell(Vector2i(20, 2), 0, Vector2i(0, 0))
	_decor.set_cell(Vector2i(21, 3), 0, Vector2i(6, 0))
	_decor.set_cell(Vector2i(20, 3), 0, Vector2i(7, 0))
	# SE
	_decor.set_cell(Vector2i(20, 12), 0, Vector2i(2, 0))
	_decor.set_cell(Vector2i(21, 12), 0, Vector2i(14, 0))
	# Soil macros overlays (on / near soil)
	_decor.set_cell(Vector2i(10, 7), 0, Vector2i(8, 0))  # pebbles
	_decor.set_cell(Vector2i(12, 8), 0, Vector2i(9, 0))  # clump
	_decor.set_cell(Vector2i(14, 6), 0, Vector2i(10, 0)) # clump2
	_decor.set_cell(Vector2i(11, 9), 0, Vector2i(11, 0)) # root
	_decor.set_cell(Vector2i(13, 5), 0, Vector2i(12, 0)) # dark soil
	_decor.set_cell(Vector2i(8, 8), 0, Vector2i(13, 0))  # sprout
	# Extra grass accents
	_decor.set_cell(Vector2i(1, 7), 0, Vector2i(3, 0))
	_decor.set_cell(Vector2i(16, 13), 0, Vector2i(15, 0))


func _build_player() -> void:
	# Hidden by default on art shots; neutral cam body for interactive only.
	_player = CharacterBody2D.new()
	_player.name = "Player"
	_player.position = Vector2(12 * TILE, 9 * TILE)
	var cam := Camera2D.new()
	cam.name = "PlayerCam"
	cam.enabled = true
	cam.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = MAP_W * TILE
	cam.limit_bottom = MAP_H * TILE
	_player.add_child(cam)
	_player.visible = false
	add_child(_player)


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hint = Label.new()
	_hint.position = Vector2(8, 6)
	_hint.add_theme_font_size_override("font_size", 11)
	_hint.add_theme_color_override("font_color", Color(1, 1, 1))
	_hint.text = "macro terrain · T=alt shape"
	_hint.visible = false
	layer.add_child(_hint)


func _physics_process(_delta: float) -> void:
	if _player == null or not _player.visible:
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


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_T:
			_paint_terrain(not _shape_b)
			_paint_decor()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_F12:
			_hint.visible = not _hint.visible
			get_tree().debug_collisions_hint = _hint.visible
			get_viewport().set_input_as_handled()


func _shot_clean(tag: String) -> void:
	_hint.visible = false
	get_tree().debug_collisions_hint = false
	if _player:
		_player.visible = false
	var look := Camera2D.new()
	look.enabled = true
	look.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	look.position = Vector2(12 * TILE, 7 * TILE)
	add_child(look)
	_paint_terrain(false)
	_decor.clear()
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take_screenshot(tag)
	look.queue_free()


func _shot_sequence() -> void:
	_hint.visible = false
	get_tree().debug_collisions_hint = false
	if _player:
		_player.visible = false

	var look := Camera2D.new()
	look.name = "ShotCam"
	look.enabled = true
	look.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	look.position = Vector2(12 * TILE, 7 * TILE)
	add_child(look)

	# Clean (no decor)
	_paint_terrain(false)
	_decor.clear()
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take_screenshot("macro")

	# With decor
	_paint_decor()
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take_screenshot("macro_decor")

	look.queue_free()


func _take_screenshot(tag: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	var path := ProjectSettings.globalize_path("res://docs/art_tests/terrain_%s.png" % tag)
	img.save_png(path)
	print("terrain screenshot -> ", path)
