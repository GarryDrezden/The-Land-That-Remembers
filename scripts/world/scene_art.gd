extends RefCounted
## Подстановка иллюстраций локаций и сборка персонажей (Stardew-scale).


const WALK_SHEET := "res://assets/characters/player_walk_sheet.png"
const PETR_SHEET := "res://assets/characters/npc_petr_sheet.png"
const SOFIA_SHEET := "res://assets/characters/npc_sofia_sheet.png"

## Высота персонажа в мировых пикселях (как в Stardew ~2 тайла)
const CHAR_WORLD_H := 48.0


static func add_bg(parent: Node2D, path: String, z: int = -20) -> Sprite2D:
	var tex := load(path) as Texture2D
	if tex == null:
		push_warning("Нет текстуры: %s" % path)
		return null
	var spr := Sprite2D.new()
	spr.name = "ArtPlate"
	spr.texture = tex
	spr.centered = false
	spr.position = Vector2.ZERO
	spr.z_index = z
	_fit(spr, tex)
	parent.add_child(spr)
	return spr


static func set_bg_texture(spr: Sprite2D, path: String) -> void:
	if spr == null:
		return
	var tex := load(path) as Texture2D
	if tex == null:
		return
	spr.texture = tex
	_fit(spr, tex)


static func _fit(spr: Sprite2D, tex: Texture2D) -> void:
	var sz := tex.get_size()
	if sz.x <= 0.0 or sz.y <= 0.0:
		return
	spr.scale = Vector2(1152.0 / sz.x, 720.0 / sz.y)


static func build_walk_frames(sheet: Texture2D) -> SpriteFrames:
	var frames := SpriteFrames.new()
	var cols := 4
	var rows := 4
	var cw := float(sheet.get_width()) / float(cols)
	var ch := float(sheet.get_height()) / float(rows)
	var dirs: PackedStringArray = ["down", "left", "right", "up"]
	for row in range(rows):
		var dir_name := dirs[row]
		var walk_name := "walk_%s" % dir_name
		frames.add_animation(walk_name)
		frames.set_animation_speed(walk_name, 7.0)
		frames.set_animation_loop(walk_name, true)
		for col in range(cols):
			var at := AtlasTexture.new()
			at.atlas = sheet
			at.region = Rect2(col * cw, row * ch, cw, ch)
			frames.add_frame(walk_name, at)
		var idle_name := "idle_%s" % dir_name
		frames.add_animation(idle_name)
		frames.set_animation_speed(idle_name, 1.0)
		frames.set_animation_loop(idle_name, true)
		frames.add_frame(idle_name, frames.get_frame_texture(walk_name, 0))
	return frames


static func _char_scale(sheet: Texture2D) -> float:
	var cell_h := float(sheet.get_height()) / 4.0
	return CHAR_WORLD_H / cell_h


static func make_player(pos: Vector2, cam_zoom: float = 1.0, world_limit: Rect2 = Rect2()) -> CharacterBody2D:
	var player := CharacterBody2D.new()
	player.name = "Player"
	player.position = pos
	player.z_index = 10
	player.y_sort_enabled = true
	player.collision_layer = 1
	player.collision_mask = 1
	player.set_script(load("res://scripts/player/player.gd"))

	var body := AnimatedSprite2D.new()
	body.name = "Body"
	body.centered = true
	body.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var sheet := load(WALK_SHEET) as Texture2D
	if sheet:
		body.sprite_frames = build_walk_frames(sheet)
		var s := _char_scale(sheet)
		body.scale = Vector2(s, s)
		body.play("idle_down")
	else:
		# Never attach ColorRect as Body — player.gd requires AnimatedSprite2D.
		push_warning("scene_art: walk sheet missing, Body stays empty AnimatedSprite2D")
	player.add_child(body)

	var collision := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(16, 12)
	collision.shape = shape
	collision.position = Vector2(0, 14)
	player.add_child(collision)

	var prompt := Label.new()
	prompt.name = "Prompt"
	prompt.position = Vector2(-70, -56)
	prompt.visible = false
	prompt.add_theme_color_override("font_color", Color(1, 0.95, 0.8, 1))
	prompt.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	prompt.add_theme_constant_override("shadow_offset_x", 1)
	prompt.add_theme_constant_override("shadow_offset_y", 1)
	player.add_child(prompt)

	var tag := Label.new()
	tag.name = "NameTag"
	tag.position = Vector2(-28, 22)
	tag.text = PlayerProfile.player_name
	tag.visible = false
	tag.add_theme_color_override("font_color", Color(1, 1, 1, 0.95))
	tag.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	tag.add_theme_constant_override("shadow_offset_x", 1)
	tag.add_theme_constant_override("shadow_offset_y", 1)
	player.add_child(tag)

	var cam := Camera2D.new()
	cam.enabled = true
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 6.0
	cam.zoom = Vector2(cam_zoom, cam_zoom)
	if world_limit.size.x > 0.0:
		cam.limit_left = int(world_limit.position.x)
		cam.limit_top = int(world_limit.position.y)
		cam.limit_right = int(world_limit.position.x + world_limit.size.x)
		cam.limit_bottom = int(world_limit.position.y + world_limit.size.y)
	player.add_child(cam)
	return player


static func make_npc_sprite(sheet_path: String, facing: String = "down") -> AnimatedSprite2D:
	var body := AnimatedSprite2D.new()
	body.name = "Body"
	body.centered = true
	body.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var sheet := load(sheet_path) as Texture2D
	if sheet:
		body.sprite_frames = build_walk_frames(sheet)
		var s := _char_scale(sheet)
		body.scale = Vector2(s, s)
		var idle := "idle_%s" % facing
		if body.sprite_frames.has_animation(idle):
			body.play(idle)
		else:
			body.play("idle_down")
	return body
