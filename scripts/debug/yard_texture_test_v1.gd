extends Node2D
## Texture proof v1 — CLEAN integration pass.
## Minimal fragment only: grass, path, 1 tree, 1 bush, 1 rock, weeds, player.
## F12 debug. Open yard_texture_test_v1.tscn → F6.

const TILE := 16
const MAP_W_TILES := 72
const MAP_H_TILES := 45
const VIEW_W := 384
const VIEW_H := 240
const WINDOW_SCALE := 3
const MOVE_SPEED := 78.0
const TEX_ROOT := "res://assets/art/outdoor/texture_proof_v1/"

const COL_GRASS := Color(0.30, 0.46, 0.26)
const COL_PATH := Color(0.50, 0.40, 0.28)

var _player: CharacterBody2D
var _anim: AnimatedSprite2D
var _facing: String = "down"
var _ysort: Node2D
var _ground_debug: Node2D
var _debug := false
var _hint: Label
var _collision_shapes: Array[CollisionShape2D] = []


func _ready() -> void:
	name = "YardTextureTestV1"
	modulate = Color(1, 1, 1, 1)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(VIEW_W * WINDOW_SCALE, VIEW_H * WINDOW_SCALE))

	_build_ground()
	_ysort = Node2D.new()
	_ysort.name = "YSortWorld"
	_ysort.y_sort_enabled = true
	_ysort.modulate = Color(1, 1, 1, 1)
	add_child(_ysort)

	_build_props()
	_build_player()
	_build_bounds()
	_build_ui()
	_set_debug(false)

	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.35).timeout
		if shot == "sequence" or shot == "1":
			await _shot_sequence()
		else:
			await _take_screenshot(shot)
		get_tree().quit()


func _map_px() -> Vector2i:
	return Vector2i(MAP_W_TILES * TILE, MAP_H_TILES * TILE)


func _load_tex(file_name: String) -> Texture2D:
	var path := TEX_ROOT + file_name
	# Prefer raw Image load for predictable opaque alpha in this proof
	var abs_path := ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(abs_path):
		var img := Image.new()
		if img.load(abs_path) == OK:
			# Force fully opaque / fully transparent — no mid-alpha ghosts
			for y in img.get_height():
				for x in img.get_width():
					var c := img.get_pixel(x, y)
					if c.a < 0.5:
						img.set_pixel(x, y, Color(0, 0, 0, 0))
					else:
						c.a = 1.0
						img.set_pixel(x, y, c)
			var tex := ImageTexture.create_from_image(img)
			return tex
	if ResourceLoader.exists(path):
		var t := load(path)
		if t is Texture2D:
			return t as Texture2D
	push_warning("texture_proof clean: missing %s" % path)
	return null


func _sprite_feet(tex: Texture2D) -> Sprite2D:
	## Pivot at bottom-center (feet). Texture drawn upward from node origin.
	var spr := Sprite2D.new()
	spr.texture = tex
	spr.centered = false
	spr.offset = Vector2(-tex.get_width() * 0.5, -tex.get_height())
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.modulate = Color(1, 1, 1, 1)
	spr.self_modulate = Color(1, 1, 1, 1)
	return spr


func _add_static(parent: Node2D, local_pos: Vector2, size: Vector2) -> void:
	var body := StaticBody2D.new()
	body.position = local_pos
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = size
	cs.shape = shape
	cs.debug_color = Color(1.0, 0.15, 0.15, 0.4)
	body.add_child(cs)
	parent.add_child(body)
	_collision_shapes.append(cs)


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

	# One clear dirt/path patch under the fragment
	var path := Polygon2D.new()
	path.color = COL_PATH
	path.polygon = PackedVector2Array([
		Vector2(470, 430), Vector2(560, 420), Vector2(620, 450), Vector2(610, 510),
		Vector2(540, 530), Vector2(480, 510), Vector2(455, 470)
	])
	ground.add_child(path)

	_ground_debug = Node2D.new()
	_ground_debug.visible = false
	_ground_debug.set_script(load("res://scripts/debug/yard_scale_grid_draw.gd"))
	ground.add_child(_ground_debug)


func _build_props() -> void:
	# Compact readable cluster around spawn — not a full yard dump
	_make_tex_prop("Tree", "tree_deciduous.png", Vector2(520, 455), Vector2(12, 12), Vector2(0, -6))
	_make_tex_prop("Bush", "bush.png", Vector2(585, 495), Vector2(26, 12), Vector2(0, -6))
	_make_tex_prop("Rock", "rock.png", Vector2(500, 515), Vector2(18, 10), Vector2(0, -5))

	for p in [Vector2(565, 520), Vector2(545, 535), Vector2(595, 475)]:
		_make_weed(p)


func _make_tex_prop(prop_name: String, file_name: String, feet: Vector2, coll_size: Vector2, coll_pos: Vector2) -> void:
	var root := Node2D.new()
	root.name = prop_name
	root.position = feet
	root.modulate = Color(1, 1, 1, 1)
	_ysort.add_child(root)
	var tex := _load_tex(file_name)
	if tex == null:
		push_error("missing prop %s" % file_name)
		return
	root.add_child(_sprite_feet(tex))
	_add_static(root, coll_pos, coll_size)


func _make_weed(feet: Vector2) -> void:
	var root := Node2D.new()
	root.name = "Weed"
	root.position = feet
	root.modulate = Color(1, 1, 1, 1)
	_ysort.add_child(root)
	var tex := _load_tex("weed.png")
	if tex:
		root.add_child(_sprite_feet(tex))
	# weeds passable — no collision


func _build_player() -> void:
	_player = CharacterBody2D.new()
	_player.name = "Player"
	_player.position = Vector2(540, 500)
	_player.collision_layer = 1
	_player.collision_mask = 1
	_player.y_sort_enabled = true
	_player.modulate = Color(1, 1, 1, 1)

	_anim = AnimatedSprite2D.new()
	_anim.name = "Body"
	_anim.centered = false
	# 24×32 canvas, feet at bottom-center of texture → pivot at node origin
	_anim.offset = Vector2(-12, -32)
	_anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_anim.modulate = Color(1, 1, 1, 1)
	_anim.self_modulate = Color(1, 1, 1, 1)
	_anim.sprite_frames = _build_player_frames()
	_anim.play("idle_down")
	_player.add_child(_anim)

	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(10, 8)
	cs.shape = shape
	cs.position = Vector2(0, -4) # feet region
	cs.debug_color = Color(0.15, 0.85, 1.0, 0.45)
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

	# Prototype: left = flip of right frames (applied via flip_h at runtime)
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
		if sf.has_animation(anim_name):
			sf.remove_animation(anim_name)
		sf.add_animation(anim_name)
		sf.set_animation_loop(anim_name, true)
		var is_idle := String(anim_name).begins_with("idle_")
		sf.set_animation_speed(anim_name, 1.0 if is_idle else 8.0)
		for idx in anims[anim_name]:
			var t: Texture2D = textures[int(idx)]
			if t != null:
				sf.add_frame(anim_name, t)
	return sf


func _build_bounds() -> void:
	var bounds := Node2D.new()
	add_child(bounds)
	var map := _map_px()
	_bound(bounds, Vector2(map.x * 0.5, -16), Vector2(map.x + 64, 32))
	_bound(bounds, Vector2(map.x * 0.5, map.y + 16), Vector2(map.x + 64, 32))
	_bound(bounds, Vector2(-16, map.y * 0.5), Vector2(32, map.y + 64))
	_bound(bounds, Vector2(map.x + 16, map.y * 0.5), Vector2(32, map.y + 64))


func _bound(parent: Node, pos: Vector2, size: Vector2) -> void:
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
	_hint.add_theme_color_override("font_color", Color(1, 1, 1))
	_hint.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	_hint.add_theme_constant_override("shadow_offset_x", 1)
	_hint.add_theme_constant_override("shadow_offset_y", 1)
	_hint.text = "CLEAN · WASD · F12 debug · left=prototype flip"
	_hint.visible = false
	layer.add_child(_hint)


func _set_debug(on: bool) -> void:
	_debug = on
	if _ground_debug:
		_ground_debug.visible = on
		_ground_debug.queue_redraw()
	if _hint:
		_hint.visible = on
	get_tree().debug_collisions_hint = on


func _physics_process(_delta: float) -> void:
	if _player == null or _anim == null:
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
	## Diagonal OK for movement; animation uses dominant axis (or last facing on exact 45°).
	if dir.length() < 0.12:
		_anim.flip_h = (_facing == "left")
		var idle := "idle_%s" % _facing
		if _anim.animation != idle:
			_anim.play(idle)
		_anim.modulate = Color(1, 1, 1, 1)
		return

	var ax := absf(dir.x)
	var ay := absf(dir.y)
	if ax > ay:
		_facing = "right" if dir.x > 0.0 else "left"
	elif ay > ax:
		_facing = "down" if dir.y > 0.0 else "up"
	# else keep previous facing

	_anim.flip_h = (_facing == "left")
	var walk := "walk_%s" % _facing
	if _anim.animation != walk:
		_anim.play(walk)
	elif not _anim.is_playing():
		_anim.play(walk)
	_anim.modulate = Color(1, 1, 1, 1)
	_anim.self_modulate = Color(1, 1, 1, 1)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F12:
		_set_debug(not _debug)
		get_viewport().set_input_as_handled()


func _shot_sequence() -> void:
	_set_debug(false)
	_player.velocity = Vector2.ZERO
	_facing = "down"
	_anim.flip_h = false
	_anim.play("idle_down")
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take_screenshot("idle")

	# Mid walk-down pose
	_anim.play("walk_down")
	_anim.frame = 1
	await get_tree().process_frame
	await get_tree().create_timer(0.15).timeout
	await _take_screenshot("walk")

	# Beside tree + bush (south of tree so in front)
	_player.position = Vector2(555, 480)
	_facing = "up"
	_anim.flip_h = false
	_anim.play("idle_up")
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take_screenshot("near_tree")

	# Behind crown
	_player.position = Vector2(520, 430)
	_facing = "down"
	_anim.play("idle_down")
	await get_tree().process_frame
	await get_tree().create_timer(0.2).timeout
	await _take_screenshot("behind_tree")

	_player.position = Vector2(540, 500)
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
	print("texture_proof clean screenshot -> ", path)
	if tag != "debug":
		_set_debug(was)
