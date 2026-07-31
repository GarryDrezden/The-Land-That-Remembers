extends Node2D
## Isolated Puny World outdoor art test.
## Not wired into GameFlow. Open this scene and press F6.
## Character sprites are intentionally absent (not in Overworld pack).

const MANIFEST_PATH := "res://assets/art/outdoor/puny_world/manifest.json"
const SCALE := 3.0
const PROMPT_HIDE_DEBUG := true

var _probe: CharacterBody2D
var _prompt: Label
var _clearable: Node2D
var _cleared := false
var _shot_done := false


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	# One-screen fragment: 20×14 tiles ×16 × integer zoom 3
	DisplayServer.window_set_size(Vector2i(960, 672))

	var manifest := _load_manifest()
	if manifest.is_empty():
		push_error("yard_art_test: missing manifest")
		return

	_build_world(manifest)
	_build_probe()
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
	var data = JSON.parse_string(f.get_as_text())
	return data if typeof(data) == TYPE_DICTIONARY else {}


func _tex(path: String) -> Texture2D:
	var t: Texture2D = load(path)
	return t


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
			var sz := tex.get_size() if tex else Vector2(16, 16)
			shape.size = sz
			cs.shape = shape
			cs.position = sz * 0.5
			area.add_child(cs)
			spr.add_child(area)


func _build_probe() -> void:
	# Movement probe WITHOUT a character sprite (pack has none).
	_probe = CharacterBody2D.new()
	_probe.name = "ProbeNoSprite"
	_probe.position = Vector2(152, 108)
	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(10, 14) # ~1×2 tile footprint at 16px
	cs.shape = shape
	cs.position = Vector2(5, 7)
	_probe.add_child(cs)

	var cam := Camera2D.new()
	cam.enabled = true
	cam.zoom = Vector2(SCALE, SCALE) # integer only
	cam.position_smoothing_enabled = false
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = 320
	cam.limit_bottom = 224
	_probe.add_child(cam)

	# Tiny focus diamond from pack palette (not a character) — only if debug
	if not PROMPT_HIDE_DEBUG:
		var hint := Polygon2D.new()
		hint.polygon = PackedVector2Array([
			Vector2(5, 0), Vector2(10, 7), Vector2(5, 14), Vector2(0, 7)
		])
		hint.color = Color(0.95, 0.85, 0.4, 0.55)
		_probe.add_child(hint)

	add_child(_probe)


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
	_prompt.text = "ART TEST · Puny World · WASD · E расчистка · F12 скрин · нет спрайта героя в pack"
	layer.add_child(_prompt)


func _build_water_shimmer(manifest: Dictionary) -> void:
	var props: Dictionary = manifest.get("props", {})
	var meta: Dictionary = manifest.get("meta", {})
	var pond: Array = meta.get("pond_origin", [13, 7])
	if pond.size() < 2:
		return
	var frames: Array[Texture2D] = []
	for key in ["water_0", "water_1", "water_2"]:
		var rel := str(props.get(key, ""))
		if rel != "" and ResourceLoader.exists("res://" + rel):
			frames.append(_tex("res://" + rel))
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
	# Center cell of 3×3 pond
	anim.position = Vector2((float(pond[0]) + 1.0) * 16.0, (float(pond[1]) + 1.0) * 16.0)
	anim.modulate = Color(1, 1, 1, 0.55)
	anim.z_index = 1
	anim.play("shimmer")
	add_child(anim)


func _physics_process(_delta: float) -> void:
	if _probe == null:
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
	_probe.velocity = dir * 70.0
	_probe.move_and_slide()
	_update_prompt()


func _update_prompt() -> void:
	if _prompt == null:
		return
	if _cleared:
		_prompt.text = "сорняк убран · VFX ok · walk-loop персонажа: N/A (нет спрайта в pack)"
		return
	if _clearable and is_instance_valid(_clearable) and _near_clearable():
		_prompt.text = "E — срезать сорняк"
	else:
		_prompt.text = "ART TEST · Puny World · WASD · подойди к сорняку · F12 скрин"


func _near_clearable() -> bool:
	if _clearable == null or _probe == null:
		return false
	var cpos := _clearable.position + Vector2(8, 8)
	return _probe.position.distance_to(cpos) < 22.0


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
	# Simple dust from pack-adjacent earth tones (no external VFX sheet).
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
