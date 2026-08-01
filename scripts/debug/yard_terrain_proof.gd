extends Node2D
## Seamless terrain proof — TileMapLayer + Match Corners.
## F6 this scene. ART_TEST_SHOT=sequence for screenshots.
## T: toggle alternate soil shape. F12: debug collisions only (no tile grid overlay).

const YardTerrainTilesetFactory = preload("res://scripts/tilesets/yard_terrain_tileset_factory.gd")
const SceneArt = preload("res://scripts/world/scene_art.gd")

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
var _anim: AnimatedSprite2D
var _facing: String = "down"
var _shape_b := false
var _hint: Label


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

	# Persist tileset resource for editor reuse
	var save_path := "res://resources/tilesets/yard_ground_tileset.tres"
	if not FileAccess.file_exists(ProjectSettings.globalize_path(save_path)):
		YardTerrainTilesetFactory.save_ground_tileset(save_path)

	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.4).timeout
		if shot == "sequence" or shot == "1":
			await _shot_sequence()
		else:
			await _take_screenshot(shot)
		get_tree().quit()


func _build_layers() -> void:
	# Letterbox fill behind map
	var bg := Polygon2D.new()
	bg.name = "ClearFill"
	bg.color = Color(0.29, 0.46, 0.20)
	bg.polygon = PackedVector2Array([
		Vector2(-64, -64),
		Vector2(MAP_W * TILE + 64, -64),
		Vector2(MAP_W * TILE + 64, MAP_H * TILE + 64),
		Vector2(-64, MAP_H * TILE + 64),
	])
	bg.z_index = -10
	add_child(bg)

	var ground_ts := YardTerrainTilesetFactory.build_ground_tileset()
	_ground = TileMapLayer.new()
	_ground.name = "GroundTerrain"
	_ground.tile_set = ground_ts
	_ground.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_ground)

	var decor_ts := YardTerrainTilesetFactory.build_decor_tileset()
	_decor = TileMapLayer.new()
	_decor.name = "GroundDecoration"
	_decor.tile_set = decor_ts
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
	## Solid 8×6 with soft inset (2×2) and protrusion (2×2) — no diagonal islands.
	var cells: Array[Vector2i] = []
	var ox := 8
	var oy := 4
	for y in range(6):
		for x in range(8):
			if y <= 1 and x >= 6:
				continue # inset top-right 2×2
			cells.append(Vector2i(ox + x, oy + y))
	# protrusion bottom-left 2×2
	for y in range(4, 6):
		for x in range(-2, 0):
			cells.append(Vector2i(ox + x, oy + y))
	return _unique_in_map(cells)


func _soil_shape_b() -> Array[Vector2i]:
	## Alternate solid form for auto-corner proof.
	var cells: Array[Vector2i] = []
	var ox := 7
	var oy := 5
	for y in range(6):
		for x in range(8):
			if y <= 1 and x <= 1:
				continue
			if y >= 4 and x >= 6:
				continue
			cells.append(Vector2i(ox + x, oy + y))
	for y in range(2, 4):
		for x in range(8, 10):
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


func _paint_terrain(shape_b: bool) -> void:
	_shape_b = shape_b
	_ground.clear()
	# Base grass everywhere via terrain connect
	_ground.set_cells_terrain_connect(_all_cells(), 0, YardTerrainTilesetFactory.TERRAIN_GRASS, true)
	var soil := _soil_shape_b() if shape_b else _soil_shape_a()
	_ground.set_cells_terrain_connect(soil, 0, YardTerrainTilesetFactory.TERRAIN_SOIL, true)


func _paint_decor() -> void:
	_decor.clear()
	# Rare accents — not every cell
	var blades := [Vector2i(3, 2), Vector2i(5, 10), Vector2i(18, 3), Vector2i(20, 12), Vector2i(2, 7), Vector2i(15, 13)]
	for c in blades:
		_decor.set_cell(c, 0, Vector2i(0 if (c.x + c.y) % 2 == 0 else 1, 0))
	_decor.set_cell(Vector2i(4, 12), 0, Vector2i(3, 0)) # white flowers
	_decor.set_cell(Vector2i(19, 8), 0, Vector2i(4, 0)) # yellow
	_decor.set_cell(Vector2i(10, 3), 0, Vector2i(5, 0)) # pebbles
	_decor.set_cell(Vector2i(14, 11), 0, Vector2i(5, 0))
	_decor.set_cell(Vector2i(21, 5), 0, Vector2i(6, 0)) # twig


func _build_player() -> void:
	# Unchanged hero pipeline from scene_art (same walk sheet / player.gd)
	var world := Rect2(0, 0, MAP_W * TILE, MAP_H * TILE)
	_player = SceneArt.make_player(Vector2(12 * TILE, 8 * TILE), float(WINDOW_SCALE), world)
	# Cap speed for 16px tile feel in this proof
	_player.set("speed", MOVE_SPEED)
	# Hide nametag noise on art screenshots
	var tag := _player.get_node_or_null("NameTag") as Label
	if tag:
		tag.visible = false
	add_child(_player)
	_anim = _player.get_node_or_null("Body") as AnimatedSprite2D


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hint = Label.new()
	_hint.position = Vector2(8, 6)
	_hint.add_theme_font_size_override("font_size", 11)
	_hint.add_theme_color_override("font_color", Color(1, 1, 1))
	_hint.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	_hint.add_theme_constant_override("shadow_offset_x", 1)
	_hint.add_theme_constant_override("shadow_offset_y", 1)
	_hint.text = "seamless terrain · WASD · T=alt soil shape"
	_hint.visible = false
	layer.add_child(_hint)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_T:
			_paint_terrain(not _shape_b)
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_F12:
			_hint.visible = not _hint.visible
			get_tree().debug_collisions_hint = _hint.visible
			get_viewport().set_input_as_handled()


func _shot_sequence() -> void:
	_paint_terrain(false)
	_hint.visible = false
	get_tree().debug_collisions_hint = false
	if _player:
		_player.position = Vector2(12 * TILE, 9 * TILE)
		_facing = "down"
		if _anim and _anim.sprite_frames:
			_anim.play("idle_down")
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take_screenshot("seamless")

	# Alternate soil shape (auto corners)
	_paint_terrain(true)
	if _player:
		_player.position = Vector2(11 * TILE, 9 * TILE)
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take_screenshot("seamless_alt")

	# ×4 crop of boundary region
	await _take_border_zoom()


func _take_border_zoom() -> void:
	_paint_terrain(false)
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	# Crop around soil edge (approx center of map in viewport)
	# Window is VIEW*SCALE; world camera follows player — place cam on edge
	if _player:
		_player.position = Vector2(8 * TILE, 4 * TILE) # near top of soil patch
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	img = get_viewport().get_texture().get_image()
	if img == null:
		return
	var w := img.get_width()
	var h := img.get_height()
	var cw := mini(160, w)
	var ch := mini(120, h)
	var cx := (w - cw) / 2
	var cy := (h - ch) / 2
	var crop := img.get_region(Rect2i(cx, cy, cw, ch))
	crop.resize(cw * 4, ch * 4, Image.INTERPOLATE_NEAREST)
	var path := ProjectSettings.globalize_path("res://docs/art_tests/terrain_seamless_border_x4.png")
	crop.save_png(path)
	print("seamless border x4 -> ", path)


func _take_screenshot(tag: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	var path := ProjectSettings.globalize_path("res://docs/art_tests/terrain_%s.png" % tag)
	img.save_png(path)
	print("seamless terrain screenshot -> ", path)
