extends Node2D
## Isolated Puny World outdoor art test.
## Not wired into GameFlow. Open this scene and press F6.
## Player visual is AnimatedSprite2D (never ColorRect). Walker sheet is art-test-only scale probe.

const MANIFEST_PATH := "res://assets/art/outdoor/puny_world/manifest.json"
const WALKER_SHEET := "res://assets/art/outdoor/puny_world/props/art_test_walker.png"
const SCALE := 3.0
const TILE := 16
const MAP_W_PX := 320
const MAP_H_PX := 224

var _player: CharacterBody2D
var _anim: AnimatedSprite2D
var _prompt: Label
var _clearable: Node2D
var _cleared := false
var _shot_done := false
var _facing: String = "down"


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(960, 672))

	var manifest := _load_manifest()
	if manifest.is_empty():
		push_error("yard_art_test: missing manifest")
		return

	_build_world(manifest)
	_build_player()
	_build_ui()
	_build_water_shimmer(manifest)

	if OS.get_environment("ART_TEST_SHOT") == "1":
		if _prompt:
			_prompt.visible = false
		await get_tree().process_frame
		await get_tree().create_timer(0.4).timeout
		await _take_screenshot()
		await get_tree().process_frame
		get_tree().quit()


func _load_manifest() -> Dictionary:
	if not FileAccess.file_exists(MANIFEST_PATH):
		return {}
	var f := FileAccess.open(MANIFEST_PATH, FileAccess.READ)
	var data: Variant = JSON.parse_string(f.get_as_text())
	if typeof(data) == TYPE_DICTIONARY:
		return data
	return {}


func _tex(path: String) -> Texture2D:
	return load(path) as Texture2D


func _build_world(manifest: Dictionary) -> void:
	var ground_path: String = "res://" + str(manifest.get("ground", ""))
	var ground := Sprite2D.new()
	ground.name = "Ground"
	ground.texture = _tex(ground_path)
	ground.centered = false
	ground.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ground.position = Vector2.ZERO
	add_child(ground)

	var props_root := Node2D.new()
	props_root.name = "WorldObjects"
	props_root.y_sort_enabled = true
	add_child(props_root)

	var props: Dictionary = manifest.get("props", {})
	var layout: Array = manifest.get("layout", [])
	for item in layout:
		if typeof(item) != TYPE_DICTIONARY:
			continue
		var sprite_key := str(item.get("sprite", ""))
		var rel := str(props.get(sprite_key, ""))
		if rel == "":
			continue
		var spr := Sprite2D.new()
		spr.name = str(item.get("id", sprite_key))
		spr.texture = _tex("res://" + rel)
		spr.centered = false
		spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		spr.position = Vector2(float(item.get("x", 0)), float(item.get("y", 0)))
		props_root.add_child(spr)
		if bool(item.get("clearable", false)):
			_clearable = spr
			var area := Area2D.new()
			area.name = "ClearArea"
			area.monitoring = true
			var cs := CollisionShape2D.new()
			var shape := RectangleShape2D.new()
			var tex := spr.texture
			var sz := Vector2(16, 16)
			if tex:
				sz = Vector2(tex.get_size())
			shape.size = sz
			cs.shape = shape
			cs.position = sz * 0.5
			area.add_child(cs)
			spr.add_child(area)


func _build_player() -> void:
	## CharacterBody2D
	## └── Body: AnimatedSprite2D  ← must stay this type (not ColorRect)
	## └── CollisionShape2D
	## └── Camera2D
	_player = CharacterBody2D.new()
	_player.name = "Player"
	_player.position = Vector2(152, 108)
	_player.z_index = 10
	_player.y_sort_enabled = true
	_player.collision_layer = 1
	_player.collision_mask = 1

	_anim = AnimatedSprite2D.new()
	_anim.name = "Body"
	_anim.centered = true
	_anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_anim.sprite_frames = _build_walker_frames()
	_anim.position = Vector2(0, -8)
	_anim.play("idle_down")
	_player.add_child(_anim)

	# Sanity: never allow Body to be replaced by a Control/ColorRect
	assert(_anim is AnimatedSprite2D)
	assert(_player.get_node("Body") is AnimatedSprite2D)

	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(10, 8)
	cs.shape = shape
	cs.position = Vector2(0, 4)
	_player.add_child(cs)

	var cam := Camera2D.new()
	cam.enabled = true
	cam.zoom = Vector2(SCALE, SCALE)
	cam.position_smoothing_enabled = false
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = MAP_W_PX
	cam.limit_bottom = MAP_H_PX
	_player.add_child(cam)

	add_child(_player)


func _build_walker_frames() -> SpriteFrames:
	var sheet := _tex(WALKER_SHEET)
	var frames := SpriteFrames.new()
	if sheet == null:
		push_error("yard_art_test: missing walker sheet %s" % WALKER_SHEET)
		return frames

	const CELL_W := 16
	const CELL_H := 32
	var dirs := ["down", "left", "right", "up"]
	for ri in range(dirs.size()):
		var facing: String = dirs[ri]
		var idle_name := "idle_%s" % facing
		var walk_name := "walk_%s" % facing
		if frames.has_animation(idle_name):
			frames.remove_animation(idle_name)
		if frames.has_animation(walk_name):
			frames.remove_animation(walk_name)
		frames.add_animation(idle_name)
		frames.add_animation(walk_name)
		frames.set_animation_speed(idle_name, 1.0)
		frames.set_animation_speed(walk_name, 6.0)
		frames.set_animation_loop(idle_name, true)
		frames.set_animation_loop(walk_name, true)
		for fi in range(4):
			var at := AtlasTexture.new()
			at.atlas = sheet
			at.region = Rect2(fi * CELL_W, ri * CELL_H, CELL_W, CELL_H)
			at.filter_clip = true
			if fi == 0:
				frames.add_frame(idle_name, at)
			frames.add_frame(walk_name, at)
	return frames


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name = "ArtTestUI"
	add_child(layer)
	_prompt = Label.new()
	_prompt.name = "Prompt"
	_prompt.position = Vector2(12, 10)
	_prompt.add_theme_color_override("font_color", Color(0.95, 0.92, 0.85))
	_prompt.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	_prompt.add_theme_constant_override("shadow_offset_x", 1)
	_prompt.add_theme_constant_override("shadow_offset_y", 1)
	_prompt.text = "ART TEST · WASD · E расчистка · F12 скрин"
	layer.add_child(_prompt)


func _build_water_shimmer(manifest: Dictionary) -> void:
	var props: Dictionary = manifest.get("props", {})
	var meta: Dictionary = manifest.get("meta", {})
	var pond: Variant = meta.get("pond_origin", [13, 7])
	if typeof(pond) != TYPE_ARRAY or pond.size() < 2:
		return
	var frames: Array[Texture2D] = []
	for key in ["water_0", "water_1", "water_2"]:
		var rel := str(props.get(key, ""))
		if rel != "" and ResourceLoader.exists("res://" + rel):
			var t := _tex("res://" + rel)
			if t:
				frames.append(t)
	if frames.is_empty():
		return
	var anim := AnimatedSprite2D.new()
	anim.name = "PondShimmer"
	var sf := SpriteFrames.new()
	sf.add_animation("shimmer")
	sf.set_animation_speed("shimmer", 3.0)
	sf.set_animation_loop("shimmer", true)
	for i in frames.size():
		sf.add_frame("shimmer", frames[i])
	anim.sprite_frames = sf
	anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	anim.centered = false
	anim.position = Vector2((float(pond[0]) + 1.0) * float(TILE), (float(pond[1]) + 1.0) * float(TILE))
	anim.modulate = Color(1, 1, 1, 0.55)
	anim.z_index = 1
	anim.play("shimmer")
	add_child(anim)


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
	_player.velocity = dir * 70.0
	_player.move_and_slide()
	_update_walk_anim(dir)
	_update_prompt()


func _update_walk_anim(dir: Vector2) -> void:
	if _anim.sprite_frames == null:
		return
	if dir.length() < 0.15:
		var idle := "idle_%s" % _facing
		if _anim.animation != idle:
			_anim.play(idle)
		return
	if absf(dir.x) > absf(dir.y):
		_facing = "right" if dir.x > 0.0 else "left"
	else:
		_facing = "down" if dir.y > 0.0 else "up"
	var walk := "walk_%s" % _facing
	if _anim.animation != walk or not _anim.is_playing():
		_anim.play(walk)


func _update_prompt() -> void:
	if _prompt == null:
		return
	if _cleared:
		_prompt.text = "сорняк убран · VFX ok · walk AnimatedSprite2D"
		return
	if _clearable and is_instance_valid(_clearable) and _near_clearable():
		_prompt.text = "E — срезать сорняк"
	else:
		_prompt.text = "ART TEST · WASD · подойди к сорняку · F12 скрин"


func _near_clearable() -> bool:
	if _clearable == null or _player == null:
		return false
	var cpos := _clearable.position + Vector2(8, 8)
	return _player.position.distance_to(cpos) < 22.0


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_E:
			_try_clear()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_F12:
			_take_screenshot()
			get_viewport().set_input_as_handled()


func _try_clear() -> void:
	if _cleared or not _near_clearable():
		return
	_cleared = true
	_spawn_clear_vfx(_clearable.position + Vector2(8, 8))
	_clearable.visible = false
	_clearable.queue_free()
	_clearable = null


func _spawn_clear_vfx(at: Vector2) -> void:
	var parts := CPUParticles2D.new()
	parts.position = at
	parts.emitting = true
	parts.one_shot = true
	parts.explosiveness = 0.9
	parts.amount = 14
	parts.lifetime = 0.45
	parts.direction = Vector2(0, -1)
	parts.spread = 60.0
	parts.gravity = Vector2(0, 40)
	parts.initial_velocity_min = 20.0
	parts.initial_velocity_max = 55.0
	parts.scale_amount_min = 1.0
	parts.scale_amount_max = 2.0
	parts.color = Color(0.72, 0.62, 0.38, 0.9)
	add_child(parts)
	get_tree().create_timer(0.7).timeout.connect(parts.queue_free)


func _take_screenshot() -> void:
	if _shot_done:
		return
	if _prompt:
		_prompt.visible = false
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		if _prompt:
			_prompt.visible = true
		return
	var abs_path := ProjectSettings.globalize_path("res://docs/art_tests/yard_art_test_puny_world_godot.png")
	var err := img.save_png(abs_path)
	_shot_done = err == OK
	if _prompt:
		_prompt.visible = true
		_prompt.text = (
			"скрин: docs/art_tests/yard_art_test_puny_world_godot.png"
			if _shot_done
			else "ошибка скрина (%s)" % err
		)
