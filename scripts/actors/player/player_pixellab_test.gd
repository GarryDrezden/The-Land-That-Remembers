extends CharacterBody2D
## PixelLab hero prototype (south/east walk; west=flip; north=idle until generated).

const ROOT := "res://assets/characters/player/pixellab_v1/"
const MOVE_SPEED := 70.0
const FRAME_DURATION := 0.2  ## from GIF 200ms

enum Facing { SOUTH, NORTH, EAST, WEST }

var _anim: AnimatedSprite2D
var _interaction: Marker2D
var _facing: Facing = Facing.SOUTH
var _cam: Camera2D


func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
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
	_anim.centered = true
	# Canvas 92×92, feet near y≈69 → place feet on CharacterBody2D origin
	_anim.offset = Vector2(0, -23)

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


func _load_tex(path: String) -> Texture2D:
	var abs_path := ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(abs_path):
		var img := Image.new()
		if img.load(abs_path) == OK:
			var tex := ImageTexture.create_from_image(img)
			return tex
	if ResourceLoader.exists(path):
		var res := load(path)
		if res is Texture2D:
			return res as Texture2D
	push_warning("Missing hero frame: %s" % path)
	return null


func _add_anim(frames: SpriteFrames, name: String, paths: Array, flip_h: bool = false) -> void:
	if frames.has_animation(name):
		frames.remove_animation(name)
	frames.add_animation(name)
	frames.set_animation_loop(name, true)
	frames.set_animation_speed(name, 1.0 / FRAME_DURATION)
	for p in paths:
		var tex := _load_tex(str(p))
		if tex == null:
			continue
		var at := AtlasTexture.new()
		at.atlas = tex
		at.region = Rect2(Vector2.ZERO, tex.get_size())
		# flip handled on node, not per-frame atlas
		frames.add_frame(name, at)


func _build_sprite_frames() -> void:
	var sf := SpriteFrames.new()
	var idle_dirs := {
		"idle_south": "idle/south.png",
		"idle_north": "idle/north.png",
		"idle_east": "idle/east.png",
		"idle_west": "idle/west.png",
	}
	for anim_name in idle_dirs.keys():
		_add_anim(sf, anim_name, [ROOT + idle_dirs[anim_name]])

	var walk_s: Array = []
	var walk_e: Array = []
	for i in range(8):
		walk_s.append("%swalk_south/frame_%02d.png" % [ROOT, i])
		walk_e.append("%swalk_east/frame_%02d.png" % [ROOT, i])
	_add_anim(sf, "walk_south", walk_s)
	_add_anim(sf, "walk_east", walk_e)
	_add_anim(sf, "walk_west", walk_e)  ## same frames; flip_h at runtime
	_anim.sprite_frames = sf


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
	dir = dir.limit_length(1.0)
	velocity = dir * MOVE_SPEED
	move_and_slide()
	_update_anim(dir)
	_update_interaction()


func _update_anim(dir: Vector2) -> void:
	var moving := dir.length() > 0.01
	if moving:
		if absf(dir.x) > absf(dir.y):
			_facing = Facing.EAST if dir.x > 0.0 else Facing.WEST
		else:
			_facing = Facing.SOUTH if dir.y > 0.0 else Facing.NORTH

	_anim.flip_h = false
	var anim := "idle_south"
	if not moving:
		match _facing:
			Facing.SOUTH:
				anim = "idle_south"
			Facing.NORTH:
				anim = "idle_north"
			Facing.EAST:
				anim = "idle_east"
			Facing.WEST:
				anim = "idle_west"
				_anim.flip_h = true
				anim = "idle_east"
	else:
		match _facing:
			Facing.SOUTH:
				anim = "walk_south"
			Facing.EAST:
				anim = "walk_east"
			Facing.WEST:
				anim = "walk_west"
				_anim.flip_h = true
			Facing.NORTH:
				# Prototype limitation: no walk_north yet
				anim = "idle_north"

	if _anim.animation != anim or not _anim.is_playing():
		_anim.play(anim)


func _update_interaction() -> void:
	var forward := Vector2(0, 10)
	match _facing:
		Facing.SOUTH:
			forward = Vector2(0, 10)
		Facing.NORTH:
			forward = Vector2(0, -10)
		Facing.EAST:
			forward = Vector2(10, 0)
		Facing.WEST:
			forward = Vector2(-10, 0)
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
