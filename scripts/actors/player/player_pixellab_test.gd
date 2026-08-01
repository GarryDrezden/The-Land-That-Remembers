extends CharacterBody2D
## PixelLab hero v1 — idle + walk in 8 directions (no mirroring).
## Node scale stays Vector2.ONE. Runtime display uses integer nearest PIXEL_DIV
## (provisionally accepted CraftPix fit). Source GIF/PNG on disk are not rewritten.

const ROOT := "res://assets/characters/player/pixellab_v1/"
const MOVE_SPEED := 70.0
## GIF duration 200 ms → 5 FPS.
const FRAME_DURATION := 0.2
const PIXEL_DIV := 2
const SRC_CANVAS := 92
const SRC_FOOT_Y := 70  ## shared baseline after import align (opaque bbox bottom)

const DIR_NAMES := [
	"east", "south_east", "south", "south_west",
	"west", "north_west", "north", "north_east",
]

var _anim: AnimatedSprite2D
var _interaction: Marker2D
var _facing_idx: int = 2  ## south
var _cam: Camera2D
## When false, load full-res frames (A/B compare only).
var use_pixel_div: bool = true
var _nearby: Array[Node] = []
var _prompt_label: Label


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	scale = Vector2.ONE
	collision_layer = 1
	collision_mask = 1
	y_sort_enabled = true
	_ensure_nodes()
	_build_sprite_frames()
	_anim.play("idle_south")
	_update_interaction()


func _ensure_nodes() -> void:
	_anim = get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
	if _anim == null:
		_anim = AnimatedSprite2D.new()
		_anim.name = "AnimatedSprite2D"
		add_child(_anim)
	_anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_anim.scale = Vector2.ONE
	_anim.centered = true
	_anim.flip_h = false
	_apply_foot_offset()

	var cs := get_node_or_null("CollisionShape2D") as CollisionShape2D
	if cs == null:
		cs = CollisionShape2D.new()
		cs.name = "CollisionShape2D"
		add_child(cs)
	if cs.shape == null:
		var shape := RectangleShape2D.new()
		shape.size = Vector2(8, 4)
		cs.shape = shape
	cs.position = Vector2(0, -1)
	cs.scale = Vector2.ONE

	_interaction = get_node_or_null("InteractionOrigin") as Marker2D
	if _interaction == null:
		_interaction = Marker2D.new()
		_interaction.name = "InteractionOrigin"
		add_child(_interaction)

	_cam = get_node_or_null("Camera2D") as Camera2D
	if _cam == null:
		_cam = Camera2D.new()
		_cam.name = "Camera2D"
		add_child(_cam)
	_cam.enabled = true
	_cam.position_smoothing_enabled = true
	_cam.position_smoothing_speed = 8.0


func _apply_foot_offset() -> void:
	var div := PIXEL_DIV if use_pixel_div else 1
	var canvas := float(SRC_CANVAS) / float(div)
	var foot := float(SRC_FOOT_Y) / float(div)
	_anim.offset = Vector2(0, canvas * 0.5 - foot)


func _load_tex(path: String) -> Texture2D:
	var abs_path := ProjectSettings.globalize_path(path)
	var img := Image.new()
	var loaded := false
	if FileAccess.file_exists(abs_path):
		if img.load(abs_path) == OK:
			loaded = true
	if not loaded and ResourceLoader.exists(path):
		var res := load(path)
		if res is Texture2D:
			img = res.get_image()
			if img != null:
				loaded = true
	if not loaded or img == null:
		push_warning("Missing hero frame: %s" % path)
		return null
	if use_pixel_div and PIXEL_DIV > 1:
		var nw := maxi(1, int(img.get_width() / PIXEL_DIV))
		var nh := maxi(1, int(img.get_height() / PIXEL_DIV))
		img.resize(nw, nh, Image.INTERPOLATE_NEAREST)
	return ImageTexture.create_from_image(img)


func _add_anim(frames: SpriteFrames, name: String, paths: Array) -> void:
	if frames.has_animation(name):
		frames.remove_animation(name)
	frames.add_animation(name)
	frames.set_animation_loop(name, true)
	frames.set_animation_speed(name, 1.0 / FRAME_DURATION)
	for p in paths:
		var tex := _load_tex(str(p))
		if tex == null:
			continue
		frames.add_frame(name, tex)


func _build_sprite_frames() -> void:
	var sf := SpriteFrames.new()
	for dir_name in DIR_NAMES:
		_add_anim(sf, "idle_%s" % dir_name, [ROOT + "idle/%s.png" % dir_name])
		var walk_paths: Array = []
		for i in range(8):
			walk_paths.append("%swalk/%s/frame_%02d.png" % [ROOT, dir_name, i])
		_add_anim(sf, "walk_%s" % dir_name, walk_paths)
	_anim.sprite_frames = sf
	_anim.flip_h = false
	_apply_foot_offset()


func rebuild_frames_for_compare(full_res: bool) -> void:
	use_pixel_div = not full_res
	scale = Vector2.ONE
	if _anim:
		_anim.scale = Vector2.ONE
		_anim.flip_h = false
	_build_sprite_frames()
	_anim.play("idle_south")


func facing_name() -> String:
	return DIR_NAMES[_facing_idx]


func set_facing_name(dir_name: String) -> void:
	var idx := DIR_NAMES.find(dir_name)
	if idx >= 0:
		_facing_idx = idx


func _facing_from_vector(dir: Vector2) -> int:
	## Godot angle(): 0=east, increases clockwise (y+). Eight 45° sectors.
	var idx := int(round(dir.angle() / (PI / 4.0)))
	return posmod(idx, 8)


func _physics_process(_delta: float) -> void:
	if OS.get_environment("ART_TEST_SHOT") != "":
		velocity = Vector2.ZERO
		return
	var dir := Vector2.ZERO
	if Input.is_key_pressed(KEY_A) or Input.is_action_pressed("ui_left"):
		dir.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_action_pressed("ui_right"):
		dir.x += 1.0
	if Input.is_key_pressed(KEY_W) or Input.is_action_pressed("ui_up"):
		dir.y -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_action_pressed("ui_down"):
		dir.y += 1.0
	## Keyboard already yields exact 8 directions; normalize so diagonals match cardinal speed.
	if dir != Vector2.ZERO:
		dir = dir.normalized()
	velocity = dir * MOVE_SPEED
	move_and_slide()
	_update_anim(dir)
	_update_interaction()


func _update_anim(dir: Vector2) -> void:
	var moving := dir.length() > 0.01
	if moving:
		_facing_idx = _facing_from_vector(dir)

	_anim.flip_h = false
	var name := facing_name()
	var anim := ("walk_%s" % name) if moving else ("idle_%s" % name)
	if _anim.animation != anim or not _anim.is_playing():
		_anim.play(anim)


func _update_interaction() -> void:
	## Unit facing vector from 8-dir index (east=0 …), then scale.
	var ang := float(_facing_idx) * (PI / 4.0)
	var forward := Vector2(cos(ang), sin(ang)) * 10.0
	_interaction.position = forward


func set_camera_limits(rect: Rect2) -> void:
	if _cam == null:
		return
	_cam.limit_left = int(rect.position.x)
	_cam.limit_top = int(rect.position.y)
	_cam.limit_right = int(rect.end.x)
	_cam.limit_bottom = int(rect.end.y)


func set_camera_zoom(z: Vector2) -> void:
	if _cam:
		_cam.zoom = z


func set_camera_enabled(on: bool) -> void:
	if _cam:
		_cam.enabled = on


func set_prompt_label(label: Label) -> void:
	_prompt_label = label
	_update_prompt()


func register_nearby(node: Node) -> void:
	if node not in _nearby:
		_nearby.append(node)
		_update_prompt()


func unregister_nearby(node: Node) -> void:
	_nearby.erase(node)
	_update_prompt()


func _update_prompt() -> void:
	if _prompt_label == null:
		return
	var target := _current_target()
	if target == null:
		_prompt_label.visible = false
		return
	_prompt_label.visible = true
	if target.has_method("get_prompt"):
		_prompt_label.text = "E — %s" % target.get_prompt()
	else:
		_prompt_label.text = "E — взаимодействие"


func _current_target() -> Node:
	while not _nearby.is_empty() and not is_instance_valid(_nearby[0]):
		_nearby.pop_front()
	if _nearby.is_empty():
		return null
	return _nearby[0]


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_E:
			var target := _current_target()
			if target and target.has_method("interact"):
				target.interact(self)
			get_viewport().set_input_as_handled()
