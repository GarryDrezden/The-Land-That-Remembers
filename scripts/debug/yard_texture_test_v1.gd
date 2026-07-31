extends Node2D
## Texture proof v1 on locked greybox scale.
## Same map / camera / collisions as yard_scale_test; limited textured props.
## F12 — debug. Open yard_texture_test_v1.tscn → F6.

const TILE := 16
const MAP_W_TILES := 72
const MAP_H_TILES := 45
const VIEW_W := 384
const VIEW_H := 240
const WINDOW_SCALE := 3
const MOVE_SPEED := 78.0
const TEX_ROOT := "res://assets/art/outdoor/texture_proof_v1/"

const COL_GRASS := Color(0.28, 0.42, 0.24)
const COL_PATH := Color(0.45, 0.38, 0.26)
const COL_HOUSE := Color(0.62, 0.48, 0.38)
const COL_DOOR := Color(0.32, 0.22, 0.16)
const COL_PORCH := Color(0.55, 0.42, 0.32)
const COL_WATER := Color(0.22, 0.48, 0.58)
const COL_CROWN := Color(0.22, 0.48, 0.28)
const COL_CROWN_BIRCH := Color(0.35, 0.58, 0.32)
const COL_CROWN_SPRUCE := Color(0.16, 0.38, 0.24)
const COL_TRUNK := Color(0.42, 0.28, 0.16)
const COL_TRUNK_BIRCH := Color(0.82, 0.84, 0.78)
const COL_BUSH := Color(0.28, 0.55, 0.30)
const COL_WEED := Color(0.40, 0.62, 0.28)
const COL_ROCK := Color(0.55, 0.55, 0.58)
const COL_ROCK_LG := Color(0.48, 0.48, 0.52)
const COL_LOG := Color(0.50, 0.34, 0.20)
const COL_STUMP := Color(0.46, 0.32, 0.18)
const COL_PLAYER := Color(0.30, 0.45, 0.78)

## Which world instances use textures (rest stay silhouettes)
const TEX_HOUSE := true
const TEX_POND := true
const TEX_DECIDUOUS_AT := Vector2(140, 260)
const TEX_SPRUCE_AT := Vector2(640, 640)
const TEX_BUSH_AT := Vector2(480, 380)
const TEX_ROCK_AT := Vector2(580, 520)
const TEX_LOG_AT := Vector2(420, 470)
const TEX_STUMP_AT := Vector2(330, 360)

var _player: CharacterBody2D
var _anim: AnimatedSprite2D
var _facing: String = "down"
var _ysort: Node2D
var _ground_debug: Node2D
var _debug := false
var _debug_labels: Array[CanvasItem] = []
var _hint: Label
var _collision_shapes: Array[CollisionShape2D] = []


func _ready() -> void:
	name = "YardTextureTestV1"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(VIEW_W * WINDOW_SCALE, VIEW_H * WINDOW_SCALE))

	_build_ground()
	_ysort = Node2D.new()
	_ysort.name = "YSortWorld"
	_ysort.y_sort_enabled = true
	add_child(_ysort)

	_build_world()
	_build_player()
	_build_bounds()
	_build_ui()
	_set_debug(false)

	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.3).timeout
		if shot == "sequence" or shot == "1":
			await _shot_sequence()
		else:
			await _take_screenshot(shot)
		get_tree().quit()


func _map_px() -> Vector2i:
	return Vector2i(MAP_W_TILES * TILE, MAP_H_TILES * TILE)


func _load_tex(file_name: String) -> Texture2D:
	var path := TEX_ROOT + file_name
	if ResourceLoader.exists(path):
		var t := load(path)
		if t is Texture2D:
			return t as Texture2D
	var abs_path := ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(abs_path):
		var img := Image.new()
		if img.load(abs_path) == OK:
			return ImageTexture.create_from_image(img)
	push_warning("texture_proof: missing %s" % path)
	return null


func _sprite_feet(tex: Texture2D) -> Sprite2D:
	var spr := Sprite2D.new()
	spr.texture = tex
	spr.centered = true
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if tex:
		spr.offset = Vector2(0, -tex.get_height() * 0.5)
	return spr


func _build_ground() -> void:
	var ground := Node2D.new()
	ground.name = "Ground"
	add_child(ground)
	var map := _map_px()
	var grass := Polygon2D.new()
	grass.color = COL_GRASS
	grass.polygon = PackedVector2Array([
		Vector2(0, 0), Vector2(map.x, 0), Vector2(map.x, map.y), Vector2(0, map.y)
	])
	ground.add_child(grass)
	_add_path_blob(ground, Vector2(380, 560), Vector2(70, 40))
	_add_path_blob(ground, Vector2(430, 500), Vector2(55, 45))
	_add_path_blob(ground, Vector2(500, 430), Vector2(60, 50))
	_add_path_blob(ground, Vector2(580, 360), Vector2(70, 45))
	_add_path_blob(ground, Vector2(680, 300), Vector2(80, 50))
	_add_path_blob(ground, Vector2(780, 250), Vector2(90, 45))
	_add_path_blob(ground, Vector2(860, 220), Vector2(70, 40))
	_add_path_blob(ground, Vector2(560, 480), Vector2(120, 70), Color(0.32, 0.44, 0.26))
	_ground_debug = Node2D.new()
	_ground_debug.name = "DebugGrid"
	_ground_debug.visible = false
	_ground_debug.set_script(load("res://scripts/debug/yard_scale_grid_draw.gd"))
	ground.add_child(_ground_debug)


func _add_path_blob(parent: Node, center: Vector2, radii: Vector2, color: Color = COL_PATH) -> void:
	var poly := Polygon2D.new()
	poly.color = color
	var pts: PackedVector2Array = []
	for i in 10:
		var a := TAU * float(i) / 10.0
		var jitter := 0.85 + 0.15 * sin(i * 2.1)
		pts.append(center + Vector2(cos(a) * radii.x * jitter, sin(a) * radii.y * jitter))
	poly.polygon = pts
	parent.add_child(poly)


func _build_world() -> void:
	_make_house(Vector2(900, 210))
	_make_pond(Vector2(220, 560))

	_make_tree("deciduous", Vector2(140, 260), COL_CROWN, COL_TRUNK, Vector2(64, 80))
	_make_tree("deciduous", Vector2(1050, 480), COL_CROWN, COL_TRUNK, Vector2(64, 80))
	_make_tree("deciduous", Vector2(80, 500), COL_CROWN, COL_TRUNK, Vector2(64, 80))
	_make_tree("birch", Vector2(780, 260), COL_CROWN_BIRCH, COL_TRUNK_BIRCH, Vector2(48, 80))
	_make_tree("spruce", Vector2(640, 640), COL_CROWN_SPRUCE, COL_TRUNK, Vector2(48, 96))
	_make_tree("spruce", Vector2(320, 680), COL_CROWN_SPRUCE, COL_TRUNK, Vector2(48, 96))

	_make_bush(Vector2(480, 380))
	_make_bush(Vector2(510, 400))
	_make_bush(Vector2(700, 340))
	_make_bush(Vector2(360, 450))
	_make_bush(Vector2(820, 400))
	_make_bush(Vector2(250, 420))
	_make_bush(Vector2(560, 390))
	_make_bush(Vector2(610, 410))

	for p in [
		Vector2(400, 540), Vector2(415, 555), Vector2(390, 565),
		Vector2(460, 490), Vector2(475, 505),
		Vector2(540, 420), Vector2(555, 435), Vector2(530, 445),
		Vector2(620, 340), Vector2(635, 355),
		Vector2(720, 290), Vector2(740, 300),
		Vector2(500, 560), Vector2(520, 570), Vector2(540, 555),
		Vector2(300, 480), Vector2(315, 490),
	]:
		_make_weed(p)

	_make_rock(Vector2(350, 520), false)
	_make_rock(Vector2(370, 535), false)
	_make_rock(Vector2(580, 520), true)
	_make_rock(Vector2(200, 400), false)
	_make_rock(Vector2(860, 360), true)
	_make_rock(Vector2(450, 600), false)

	_make_log(Vector2(420, 470))
	_make_log(Vector2(760, 450))

	_make_stump(Vector2(330, 360))
	_make_stump(Vector2(600, 560))
	_make_stump(Vector2(950, 380))
	_make_stump(Vector2(180, 620))


func _label(parent: Node2D, text: String, offset: Vector2) -> void:
	var lab := Label.new()
	lab.text = text
	lab.position = offset
	lab.add_theme_font_size_override("font_size", 10)
	lab.add_theme_color_override("font_color", Color(1, 1, 0.85, 0.95))
	lab.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	lab.add_theme_constant_override("shadow_offset_x", 1)
	lab.add_theme_constant_override("shadow_offset_y", 1)
	lab.mouse_filter = Control.MOUSE_FILTER_IGNORE
	lab.visible = false
	parent.add_child(lab)
	_debug_labels.append(lab)


func _add_static(parent: Node2D, local_pos: Vector2, size: Vector2) -> void:
	var body := StaticBody2D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	body.position = local_pos
	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = size
	cs.shape = shape
	cs.debug_color = Color(1.0, 0.2, 0.2, 0.35)
	body.add_child(cs)
	parent.add_child(body)
	_collision_shapes.append(cs)


func _near(a: Vector2, b: Vector2) -> bool:
	return a.distance_to(b) < 1.5


func _make_house(feet: Vector2) -> void:
	var root := Node2D.new()
	root.name = "House"
	root.position = feet
	_ysort.add_child(root)
	if TEX_HOUSE:
		var tex := _load_tex("house.png")
		if tex:
			root.add_child(_sprite_feet(tex))
		else:
			_house_silhouette(root)
	else:
		_house_silhouette(root)
	_add_static(root, Vector2(0, -28), Vector2(120, 56))
	_add_static(root, Vector2(0, 8), Vector2(48, 16))
	_label(root, "house 144×112", Vector2(-50, -148))


func _house_silhouette(root: Node2D) -> void:
	var body := Polygon2D.new()
	body.color = COL_HOUSE
	body.polygon = PackedVector2Array([
		Vector2(-72, -112), Vector2(72, -112), Vector2(72, 0), Vector2(-72, 0)
	])
	root.add_child(body)
	var roof := Polygon2D.new()
	roof.color = Color(0.45, 0.28, 0.22)
	roof.polygon = PackedVector2Array([
		Vector2(-78, -100), Vector2(0, -130), Vector2(78, -100)
	])
	root.add_child(roof)
	var door := Polygon2D.new()
	door.color = COL_DOOR
	door.polygon = PackedVector2Array([
		Vector2(-12, -36), Vector2(12, -36), Vector2(12, 0), Vector2(-12, 0)
	])
	root.add_child(door)
	var porch := Polygon2D.new()
	porch.color = COL_PORCH
	porch.polygon = PackedVector2Array([
		Vector2(-28, 0), Vector2(28, 0), Vector2(24, 18), Vector2(-24, 18)
	])
	root.add_child(porch)


func _make_pond(center: Vector2) -> void:
	var root := Node2D.new()
	root.name = "Pond"
	root.position = center
	root.z_index = -1
	_ysort.add_child(root)
	if TEX_POND:
		var tex := _load_tex("pond.png")
		if tex:
			var spr := Sprite2D.new()
			spr.texture = tex
			spr.centered = true
			spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			root.add_child(spr)
		else:
			_pond_silhouette(root)
	else:
		_pond_silhouette(root)
	_add_static(root, Vector2(0, 0), Vector2(110, 80))
	_label(root, "pond ~128×96", Vector2(-40, -60))


func _pond_silhouette(root: Node2D) -> void:
	var water := Polygon2D.new()
	water.color = COL_WATER
	water.polygon = PackedVector2Array([
		Vector2(-50, -20), Vector2(-20, -45), Vector2(30, -48), Vector2(60, -30),
		Vector2(64, 5), Vector2(40, 40), Vector2(0, 48), Vector2(-40, 38),
		Vector2(-62, 10), Vector2(-58, -10)
	])
	root.add_child(water)


func _make_tree(kind: String, feet: Vector2, crown_c: Color, trunk_c: Color, size: Vector2) -> void:
	var root := Node2D.new()
	root.name = kind
	root.position = feet
	_ysort.add_child(root)

	var use_tex := false
	var tex_file := ""
	if kind == "deciduous" and _near(feet, TEX_DECIDUOUS_AT):
		use_tex = true
		tex_file = "tree_deciduous.png"
	elif kind == "spruce" and _near(feet, TEX_SPRUCE_AT):
		use_tex = true
		tex_file = "tree_spruce.png"

	if use_tex:
		var tex := _load_tex(tex_file)
		if tex:
			root.add_child(_sprite_feet(tex))
		else:
			_tree_silhouette(root, kind, crown_c, trunk_c, size)
	else:
		_tree_silhouette(root, kind, crown_c, trunk_c, size)

	var trunk_w := 10.0 if kind != "birch" else 8.0
	_add_static(root, Vector2(0, -6), Vector2(trunk_w + 4, 12))
	_label(root, "%s %d×%d" % [kind, int(size.x), int(size.y)], Vector2(-24, -size.y - 14))


func _tree_silhouette(root: Node2D, kind: String, crown_c: Color, trunk_c: Color, size: Vector2) -> void:
	var tw := size.x
	var th := size.y
	var trunk_h := 22.0 if kind != "spruce" else 26.0
	var trunk_w := 10.0 if kind != "birch" else 8.0
	var crown := Polygon2D.new()
	crown.color = crown_c
	if kind == "spruce":
		crown.polygon = PackedVector2Array([
			Vector2(0, -th), Vector2(tw * 0.45, -trunk_h - 8), Vector2(tw * 0.28, -trunk_h - 8),
			Vector2(tw * 0.5, -trunk_h * 0.55), Vector2(tw * 0.3, -trunk_h * 0.55),
			Vector2(tw * 0.42, -4), Vector2(-tw * 0.42, -4),
			Vector2(-tw * 0.3, -trunk_h * 0.55), Vector2(-tw * 0.5, -trunk_h * 0.55),
			Vector2(-tw * 0.28, -trunk_h - 8), Vector2(-tw * 0.45, -trunk_h - 8),
		])
	else:
		var pts: PackedVector2Array = []
		var cy := -trunk_h - (th - trunk_h) * 0.45
		var rx := tw * 0.48
		var ry := (th - trunk_h) * 0.48
		for i in 12:
			var a := TAU * float(i) / 12.0
			pts.append(Vector2(cos(a) * rx, cy + sin(a) * ry))
		crown.polygon = pts
	root.add_child(crown)
	var trunk := Polygon2D.new()
	trunk.color = trunk_c
	trunk.polygon = PackedVector2Array([
		Vector2(-trunk_w * 0.5, -trunk_h), Vector2(trunk_w * 0.5, -trunk_h),
		Vector2(trunk_w * 0.55, 0), Vector2(-trunk_w * 0.55, 0)
	])
	root.add_child(trunk)


func _make_bush(feet: Vector2) -> void:
	var root := Node2D.new()
	root.name = "Bush"
	root.position = feet
	_ysort.add_child(root)
	if _near(feet, TEX_BUSH_AT):
		var tex := _load_tex("bush.png")
		if tex:
			root.add_child(_sprite_feet(tex))
		else:
			_bush_sil(root)
	else:
		_bush_sil(root)
	_add_static(root, Vector2(0, -8), Vector2(28, 14))
	_label(root, "bush 32×24", Vector2(-16, -36))


func _bush_sil(root: Node2D) -> void:
	var poly := Polygon2D.new()
	poly.color = COL_BUSH
	poly.polygon = PackedVector2Array([
		Vector2(-16, -18), Vector2(-6, -24), Vector2(8, -24), Vector2(16, -16),
		Vector2(14, -4), Vector2(0, 0), Vector2(-14, -4)
	])
	root.add_child(poly)


func _make_weed(feet: Vector2) -> void:
	var root := Node2D.new()
	root.name = "Weed"
	root.position = feet
	_ysort.add_child(root)
	var poly := Polygon2D.new()
	poly.color = COL_WEED
	poly.polygon = PackedVector2Array([
		Vector2(-4, -14), Vector2(0, -16), Vector2(4, -12), Vector2(3, 0), Vector2(-3, 0)
	])
	root.add_child(poly)
	_label(root, "weed 16×16", Vector2(-10, -28))


func _make_rock(feet: Vector2, large: bool) -> void:
	var root := Node2D.new()
	root.name = "RockLarge" if large else "Rock"
	root.position = feet
	_ysort.add_child(root)
	if large and _near(feet, TEX_ROCK_AT):
		var tex := _load_tex("rock.png")
		if tex:
			root.add_child(_sprite_feet(tex))
		else:
			_rock_sil(root, large)
	else:
		_rock_sil(root, large)
	if large:
		_add_static(root, Vector2(0, -8), Vector2(22, 14))
		_label(root, "rock 24×24", Vector2(-14, -34))
	else:
		_add_static(root, Vector2(0, -5), Vector2(14, 10))
		_label(root, "rock 16×16", Vector2(-12, -26))


func _rock_sil(root: Node2D, large: bool) -> void:
	var poly := Polygon2D.new()
	poly.color = COL_ROCK_LG if large else COL_ROCK
	if large:
		poly.polygon = PackedVector2Array([
			Vector2(-10, -18), Vector2(4, -22), Vector2(12, -14),
			Vector2(10, -2), Vector2(-8, 0), Vector2(-12, -8)
		])
	else:
		poly.polygon = PackedVector2Array([
			Vector2(-6, -12), Vector2(4, -14), Vector2(8, -6), Vector2(4, 0), Vector2(-6, -2)
		])
	root.add_child(poly)


func _make_log(feet: Vector2) -> void:
	var root := Node2D.new()
	root.name = "Log"
	root.position = feet
	_ysort.add_child(root)
	if _near(feet, TEX_LOG_AT):
		var tex := _load_tex("log.png")
		if tex:
			root.add_child(_sprite_feet(tex))
		else:
			_log_sil(root)
	else:
		_log_sil(root)
	_add_static(root, Vector2(0, -6), Vector2(30, 10))
	_label(root, "log 32×16", Vector2(-16, -26))


func _log_sil(root: Node2D) -> void:
	var poly := Polygon2D.new()
	poly.color = COL_LOG
	poly.polygon = PackedVector2Array([
		Vector2(-16, -12), Vector2(16, -10), Vector2(16, -2), Vector2(-16, -4)
	])
	root.add_child(poly)


func _make_stump(feet: Vector2) -> void:
	var root := Node2D.new()
	root.name = "Stump"
	root.position = feet
	_ysort.add_child(root)
	if _near(feet, TEX_STUMP_AT):
		var tex := _load_tex("stump.png")
		if tex:
			root.add_child(_sprite_feet(tex))
		else:
			_stump_sil(root)
	else:
		_stump_sil(root)
	_add_static(root, Vector2(0, -6), Vector2(20, 12))
	_label(root, "stump 24×24", Vector2(-16, -32))


func _stump_sil(root: Node2D) -> void:
	var poly := Polygon2D.new()
	poly.color = COL_STUMP
	poly.polygon = PackedVector2Array([
		Vector2(-10, -18), Vector2(10, -18), Vector2(12, -4),
		Vector2(8, 0), Vector2(-8, 0), Vector2(-12, -4)
	])
	root.add_child(poly)


func _build_player() -> void:
	_player = CharacterBody2D.new()
	_player.name = "Player"
	_player.position = Vector2(390, 560)
	_player.collision_layer = 1
	_player.collision_mask = 1
	_player.y_sort_enabled = true

	_anim = AnimatedSprite2D.new()
	_anim.name = "Body"
	_anim.centered = true
	_anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_anim.offset = Vector2(0, -16) # 24×32 feet at origin
	_anim.sprite_frames = _build_player_frames()
	_anim.play("idle_down")
	_player.add_child(_anim)
	_label(_anim, "player 24×32", Vector2(-18, -46))

	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(10, 8)
	cs.shape = shape
	cs.position = Vector2(0, -4)
	cs.debug_color = Color(0.2, 0.8, 1.0, 0.4)
	_player.add_child(cs)
	_collision_shapes.append(cs)

	var cam := Camera2D.new()
	cam.enabled = true
	cam.zoom = Vector2(WINDOW_SCALE, WINDOW_SCALE)
	cam.position_smoothing_enabled = false
	var map := _map_px()
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = map.x
	cam.limit_bottom = map.y
	_player.add_child(cam)
	_ysort.add_child(_player)


func _build_player_frames() -> SpriteFrames:
	var sf := SpriteFrames.new()
	var textures: Array[Texture2D] = []
	for i in 20:
		textures.append(_load_tex("player/frame_%02d.png" % i))
	var anims := {
		"idle_down": [0],
		"walk_down": [0, 1, 0],
		"idle_up": [2],
		"walk_up": [2, 3, 4],
		"idle_right": [5],
		"walk_right": [5, 6, 7],
		"idle_left": [5],
		"walk_left": [5, 6, 7],
	}
	for anim_name in anims.keys():
		sf.add_animation(anim_name)
		sf.set_animation_loop(anim_name, true)
		sf.set_animation_speed(anim_name, 1.0 if String(anim_name).begins_with("idle_") else 7.0)
		for idx in anims[anim_name]:
			var t: Texture2D = textures[int(idx)]
			if t:
				sf.add_frame(anim_name, t)
	# Fallback silhouette frame if load failed
	if not sf.has_animation("idle_down") or sf.get_frame_count("idle_down") == 0:
		sf.add_animation("idle_down")
		sf.add_animation("walk_down")
	return sf


func _build_bounds() -> void:
	var bounds := Node2D.new()
	bounds.name = "WorldBounds"
	add_child(bounds)
	var map := _map_px()
	var t := 32.0
	_bound_rect(bounds, Vector2(map.x * 0.5, -t * 0.5), Vector2(map.x + t * 2, t))
	_bound_rect(bounds, Vector2(map.x * 0.5, map.y + t * 0.5), Vector2(map.x + t * 2, t))
	_bound_rect(bounds, Vector2(-t * 0.5, map.y * 0.5), Vector2(t, map.y + t * 2))
	_bound_rect(bounds, Vector2(map.x + t * 0.5, map.y * 0.5), Vector2(t, map.y + t * 2))


func _bound_rect(parent: Node, pos: Vector2, size: Vector2) -> void:
	var body := StaticBody2D.new()
	body.position = pos
	body.collision_layer = 1
	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = size
	cs.shape = shape
	cs.debug_color = Color(1, 0.5, 0, 0.25)
	body.add_child(cs)
	parent.add_child(body)
	_collision_shapes.append(cs)


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hint = Label.new()
	_hint.position = Vector2(8, 6)
	_hint.add_theme_font_size_override("font_size", 11)
	_hint.add_theme_color_override("font_color", Color(0.92, 0.92, 0.88))
	_hint.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	_hint.add_theme_constant_override("shadow_offset_x", 1)
	_hint.add_theme_constant_override("shadow_offset_y", 1)
	_hint.text = "TEXTURE PROOF v1 · WASD · F12 debug · left=flip"
	_hint.visible = false
	layer.add_child(_hint)


func _set_debug(on: bool) -> void:
	_debug = on
	if _ground_debug:
		_ground_debug.visible = on
		_ground_debug.queue_redraw()
	for lab in _debug_labels:
		if is_instance_valid(lab):
			lab.visible = on
	if _hint:
		_hint.visible = on
	get_tree().debug_collisions_hint = on


func _physics_process(_delta: float) -> void:
	if _player == null:
		return
	var dir := Vector2.ZERO
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		dir.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		dir.x += 1.0
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		dir.y -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		dir.y += 1.0
	dir = dir.limit_length(1.0)
	_player.velocity = dir * MOVE_SPEED
	_player.move_and_slide()
	_update_anim(dir)


func _update_anim(dir: Vector2) -> void:
	if _anim == null or _anim.sprite_frames == null:
		return
	if dir.length() < 0.12:
		_anim.flip_h = (_facing == "left")
		var idle := "idle_%s" % _facing
		if _anim.animation != idle:
			_anim.play(idle)
		return
	if absf(dir.x) > absf(dir.y):
		_facing = "right" if dir.x > 0.0 else "left"
	else:
		_facing = "down" if dir.y > 0.0 else "up"
	_anim.flip_h = (_facing == "left")
	var walk := "walk_%s" % _facing
	if _anim.animation != walk or not _anim.is_playing():
		_anim.play(walk)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F12:
		_set_debug(not _debug)
		get_viewport().set_input_as_handled()


func _shot_sequence() -> void:
	_set_debug(false)
	await _take_screenshot("start")
	_player.position = Vector2(860, 250)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take_screenshot("house")
	_player.position = Vector2(168, 248)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take_screenshot("behind_tree")
	# Scale cluster: stump + log + bush + rock nearby
	_player.position = Vector2(450, 400)
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take_screenshot("scale_cluster")
	_player.position = Vector2(540, 420)
	_set_debug(true)
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take_screenshot("debug")
	_set_debug(false)


func _take_screenshot(tag: String) -> void:
	var was := _debug
	if tag != "debug":
		_set_debug(false)
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	var path := ProjectSettings.globalize_path("res://docs/art_tests/yard_texture_test_v1_%s.png" % tag)
	img.save_png(path)
	print("texture_proof screenshot -> ", path)
	if tag != "debug":
		_set_debug(was)
