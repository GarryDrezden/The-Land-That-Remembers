extends Node2D
## Isolated generated outdoor art test v2.
## Open yard_art_test_v2.tscn and press F6. Not wired into GameRoot / WorldState.

const MANIFEST_PATH := "res://assets/art/outdoor/generated_test/processed/scene_manifest.json"
const SHOT_DIR := "res://docs/art_tests/"

@export var show_hint := true
@export var auto_shot_tag := ""

var _manifest: Dictionary = {}
var _player: CharacterBody2D
var _anim: AnimatedSprite2D
var _hint: Label
var _interact_label: Label
var _facing: String = "down"
var _clearables: Array[Dictionary] = []
var _near: Dictionary = {}
var _ysort: Node2D
var _map_w: int = 2048
var _map_h: int = 1536
var _move_speed: float = 110.0
var _fps_walk: float = 8.0


func _ready() -> void:
	name = "YardArtTestV2"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(960, 720))

	_manifest = _load_manifest()
	if _manifest.is_empty():
		push_error("yard_art_test_v2: missing manifest")
		return

	var map_size: Array = _manifest.get("map_size_px", [2048, 1536])
	_map_w = int(map_size[0])
	_map_h = int(map_size[1])
	var player_cfg: Dictionary = _manifest.get("player", {})
	_move_speed = float(player_cfg.get("move_speed", 110.0))
	_fps_walk = float(player_cfg.get("fps_walk", 8.0))

	var coll := Node2D.new()
	coll.name = "StaticCollisions"
	add_child(coll)

	_build_ground()
	_build_pond()
	_build_ysort_world()
	_build_house()
	_build_trees()
	_build_clusters()
	_build_interactive_clearables()
	_build_bounds()
	_build_player()
	_build_ui()

	var shot_env := OS.get_environment("ART_TEST_SHOT")
	if shot_env != "":
		show_hint = false
		if _hint:
			_hint.visible = false
		if _interact_label:
			_interact_label.visible = false
		await get_tree().process_frame
		await get_tree().create_timer(0.4).timeout
		if shot_env == "sequence" or shot_env == "1":
			await _take_screenshot("start")
			# Move toward oak canopy for behind-crown shot (south of oak feet)
			if _player:
				_player.position = Vector2(760, 600)
				await get_tree().process_frame
				await get_tree().create_timer(0.25).timeout
				await _take_screenshot("behind_oak")
				_player.position = Vector2(1400, 820)
				await get_tree().process_frame
				await get_tree().create_timer(0.25).timeout
				await _take_screenshot("house_path")
		else:
			await _take_screenshot(shot_env)
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


func _tex(rel: String) -> Texture2D:
	if rel.is_empty():
		return null
	var path := rel if rel.begins_with("res://") else "res://" + rel
	# Prefer imported resource when available; fall back to raw PNG load
	# so the art test works before Godot finishes importing new files.
	if ResourceLoader.exists(path):
		var loaded := load(path)
		if loaded is Texture2D:
			return loaded as Texture2D
	var abs_path := ProjectSettings.globalize_path(path)
	if not FileAccess.file_exists(abs_path):
		push_warning("yard_art_test_v2: missing texture %s" % path)
		return null
	var img := Image.new()
	var err := img.load(abs_path)
	if err != OK:
		push_warning("yard_art_test_v2: failed to load image %s (%s)" % [path, err])
		return null
	return ImageTexture.create_from_image(img)


func _sprite(tex: Texture2D, pos: Vector2, centered_bottom: bool = true) -> Sprite2D:
	var spr := Sprite2D.new()
	spr.texture = tex
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = true
	if centered_bottom and tex:
		# Origin at feet for Y-sort: offset so bottom of texture is at node origin.
		spr.offset = Vector2(0, -tex.get_height() * 0.5)
	spr.position = pos
	return spr


func _add_static_rect(parent: Node, pos: Vector2, size: Vector2) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.position = pos
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = size
	cs.shape = shape
	body.add_child(cs)
	parent.add_child(body)
	return body


func _build_ground() -> void:
	var ground_root := Node2D.new()
	ground_root.name = "Ground"
	add_child(ground_root)

	var grass := Sprite2D.new()
	grass.name = "Grass"
	grass.texture = _tex(str(_manifest.get("ground", "")))
	grass.centered = false
	grass.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	grass.position = Vector2.ZERO
	ground_root.add_child(grass)

	var details := Node2D.new()
	details.name = "GroundDetails"
	add_child(details)


func _build_pond() -> void:
	var pond_cfg: Dictionary = _manifest.get("pond", {})
	var tex := _tex(str(pond_cfg.get("texture", "")))
	if tex == null:
		return
	var pos_a: Array = pond_cfg.get("position", [420, 620])
	var pos := Vector2(float(pos_a[0]), float(pos_a[1]))

	var water_root := get_node("Ground")
	var pond := Sprite2D.new()
	pond.name = "Water"
	pond.texture = tex
	pond.centered = false
	pond.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	pond.position = pos
	water_root.add_child(pond)

	# Solid water collision (approx body — art test temporary pond bake)
	var coll_root: Node2D = get_node("StaticCollisions")
	var cx := pos.x + tex.get_width() * 0.5
	var cy := pos.y + tex.get_height() * 0.5
	_add_static_rect(coll_root, Vector2(cx, cy), Vector2(tex.get_width() * 0.72, tex.get_height() * 0.58))


func _build_ysort_world() -> void:
	_ysort = Node2D.new()
	_ysort.name = "YSortWorld"
	_ysort.y_sort_enabled = true
	add_child(_ysort)

	for n in ["House", "Trees", "Bushes", "ClearableObjects", "PlayerSlot"]:
		var folder := Node2D.new()
		folder.name = n
		folder.y_sort_enabled = true
		_ysort.add_child(folder)


func _build_house() -> void:
	var cfg: Dictionary = _manifest.get("house", {})
	var tex := _tex(str(cfg.get("texture", "")))
	if tex == null:
		return
	var pos_a: Array = cfg.get("position", [1280, 280])
	var pos := Vector2(float(pos_a[0]), float(pos_a[1]))
	var folder: Node2D = _ysort.get_node("House")
	var spr := _sprite(tex, pos, true)
	spr.name = "HouseMain"
	folder.add_child(spr)
	# Collision around stone base only (not full roof)
	var coll: Node2D = get_node("StaticCollisions")
	_add_static_rect(coll, pos + Vector2(0, -36), Vector2(tex.get_width() * 0.62, 70))

	# Building props near house (fence scraps) — irregular
	var props: Array = _manifest.get("building_props", [])
	var offsets := [Vector2(-180, 40), Vector2(200, 70), Vector2(-120, 110), Vector2(160, 130)]
	for i in mini(props.size(), offsets.size()):
		var ptex := _tex(str(props[i]))
		if ptex == null:
			continue
		var ps := _sprite(ptex, pos + offsets[i], true)
		ps.name = "HouseProp_%d" % i
		folder.add_child(ps)


func _build_trees() -> void:
	var folder: Node2D = _ysort.get_node("Trees")
	var coll: Node2D = get_node("StaticCollisions")
	var trees: Array = _manifest.get("trees", [])
	for t in trees:
		if typeof(t) != TYPE_DICTIONARY:
			continue
		var tex := _tex(str(t.get("texture", "")))
		if tex == null:
			continue
		var pos_a: Array = t.get("position", [0, 0])
		var pos := Vector2(float(pos_a[0]), float(pos_a[1]))
		var spr := _sprite(tex, pos, true)
		spr.name = str(t.get("id", "tree"))
		folder.add_child(spr)
		# Trunk-only collision near feet
		var trunk_w := clampf(tex.get_width() * 0.18, 18.0, 48.0)
		_add_static_rect(coll, pos + Vector2(0, -10), Vector2(trunk_w, 22))


func _pick_tex(kind: String, index: int) -> Texture2D:
	var key := kind
	if kind == "weed":
		key = "weeds"
	elif kind == "rock":
		key = "rocks"
	elif kind == "log":
		key = "logs"
	elif kind == "stump":
		key = "stumps"
	elif kind == "bush":
		key = "bushes"
	var arr: Array = _manifest.get(key, [])
	if arr.is_empty():
		return null
	return _tex(str(arr[index % arr.size()]))


func _build_clusters() -> void:
	var bushes_folder: Node2D = _ysort.get_node("Bushes")
	var clear_folder: Node2D = _ysort.get_node("ClearableObjects")
	var coll: Node2D = get_node("StaticCollisions")
	var clusters: Array = _manifest.get("layout_clusters", [])
	var i := 0
	for cluster in clusters:
		if typeof(cluster) != TYPE_DICTIONARY:
			continue
		var kind := str(cluster.get("kind", "weed"))
		var positions: Array = cluster.get("positions", [])
		for p in positions:
			if typeof(p) != TYPE_ARRAY or p.size() < 2:
				continue
			var tex := _pick_tex(kind, i)
			i += 1
			if tex == null:
				continue
			var pos := Vector2(float(p[0]), float(p[1]))
			var spr := _sprite(tex, pos, true)
			spr.name = "%s_%d" % [kind, i]
			if kind == "bush" or kind == "weed":
				bushes_folder.add_child(spr)
			else:
				clear_folder.add_child(spr)
			if kind in ["rock", "log", "stump"]:
				_add_static_rect(coll, pos + Vector2(0, -6), Vector2(maxf(20.0, tex.get_width() * 0.45), 18))


func _build_interactive_clearables() -> void:
	var folder: Node2D = _ysort.get_node("ClearableObjects")
	var items: Array = _manifest.get("interactive_clearables", [])
	for item in items:
		if typeof(item) != TYPE_DICTIONARY:
			continue
		var kind := str(item.get("kind", "weed"))
		var idx := int(item.get("path_index", 0))
		var tex := _pick_tex(kind, idx)
		if tex == null:
			push_warning("yard_art_test_v2: clearable missing %s" % kind)
			continue
		var pos_a: Array = item.get("position", [0, 0])
		var pos := Vector2(float(pos_a[0]), float(pos_a[1]))
		var spr := _sprite(tex, pos, true)
		spr.name = str(item.get("id", kind))
		folder.add_child(spr)

		var blocking := bool(item.get("blocking", false))
		var body: StaticBody2D = null
		if blocking:
			body = _add_static_rect(spr, Vector2(0, -6), Vector2(maxf(22.0, tex.get_width() * 0.5), 18))

		var area := Area2D.new()
		area.name = "InteractArea"
		area.monitoring = true
		area.monitorable = true
		var cs := CollisionShape2D.new()
		var shape := CircleShape2D.new()
		shape.radius = 36.0
		cs.shape = shape
		cs.position = Vector2(0, -8)
		area.add_child(cs)
		spr.add_child(area)

		_clearables.append({
			"id": str(item.get("id", kind)),
			"node": spr,
			"body": body,
			"blocking": blocking,
			"cleared": false,
			"kind": kind,
		})


func _build_bounds() -> void:
	var bounds := Node2D.new()
	bounds.name = "CameraBounds"
	add_child(bounds)
	# Invisible world edges
	var thickness := 40.0
	_add_static_rect(bounds, Vector2(_map_w * 0.5, -thickness * 0.5), Vector2(_map_w, thickness))
	_add_static_rect(bounds, Vector2(_map_w * 0.5, _map_h + thickness * 0.5), Vector2(_map_w, thickness))
	_add_static_rect(bounds, Vector2(-thickness * 0.5, _map_h * 0.5), Vector2(thickness, _map_h))
	_add_static_rect(bounds, Vector2(_map_w + thickness * 0.5, _map_h * 0.5), Vector2(thickness, _map_h))


func _build_player() -> void:
	var spawn_a: Array = _manifest.get("player_spawn", [980, 780])
	var spawn := Vector2(float(spawn_a[0]), float(spawn_a[1]))
	var zoom := float(_manifest.get("camera_zoom", 2))

	_player = CharacterBody2D.new()
	_player.name = "Player"
	_player.position = spawn
	_player.collision_layer = 1
	_player.collision_mask = 1
	_player.y_sort_enabled = true

	_anim = AnimatedSprite2D.new()
	_anim.name = "Body"
	_anim.centered = true
	_anim.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_anim.sprite_frames = _build_player_frames()
	# Feet near node origin for Y-sort
	var frame_h := 142.0
	var pcfg: Dictionary = _manifest.get("player", {})
	var fsize: Array = pcfg.get("frame_size", [79, 142])
	if fsize.size() >= 2:
		frame_h = float(fsize[1])
	_anim.offset = Vector2(0, -frame_h * 0.5)
	_anim.play("idle_down")
	_player.add_child(_anim)

	assert(_anim is AnimatedSprite2D)

	var cs := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(14, 10)
	cs.shape = shape
	cs.position = Vector2(0, -4)
	_player.add_child(cs)

	var cam := Camera2D.new()
	cam.name = "Camera2D"
	cam.enabled = true
	cam.zoom = Vector2(zoom, zoom)
	cam.position_smoothing_enabled = false
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = _map_w
	cam.limit_bottom = _map_h
	_player.add_child(cam)

	_ysort.get_node("PlayerSlot").add_child(_player)


func _build_player_frames() -> SpriteFrames:
	var frames := SpriteFrames.new()
	var pcfg: Dictionary = _manifest.get("player", {})
	var frame_paths: Array = pcfg.get("frames", [])
	var anims: Dictionary = pcfg.get("anims", {})
	var textures: Array[Texture2D] = []
	for rel in frame_paths:
		textures.append(_tex(str(rel)))

	var names := [
		"idle_down", "walk_down", "idle_up", "walk_up",
		"idle_right", "walk_right", "idle_left", "walk_left",
	]
	for anim_name in names:
		if frames.has_animation(anim_name):
			frames.remove_animation(anim_name)
		frames.add_animation(anim_name)
		frames.set_animation_loop(anim_name, true)
		var speed := 1.0 if anim_name.begins_with("idle_") else _fps_walk
		frames.set_animation_speed(anim_name, speed)
		var idxs: Array = anims.get(anim_name, [0])
		for idx_v in idxs:
			var idx := int(idx_v)
			if idx < 0 or idx >= textures.size() or textures[idx] == null:
				continue
			frames.add_frame(anim_name, textures[idx])
	return frames


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.name = "CanvasLayer"
	add_child(layer)

	_hint = Label.new()
	_hint.name = "MinimalHint"
	_hint.position = Vector2(12, 10)
	_hint.add_theme_color_override("font_color", Color(0.95, 0.93, 0.88))
	_hint.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	_hint.add_theme_constant_override("shadow_offset_x", 1)
	_hint.add_theme_constant_override("shadow_offset_y", 1)
	_hint.text = "WASD — движение · E — расчистить"
	_hint.visible = show_hint
	layer.add_child(_hint)

	_interact_label = Label.new()
	_interact_label.name = "InteractHint"
	_interact_label.position = Vector2(12, 34)
	_interact_label.add_theme_color_override("font_color", Color(1.0, 0.92, 0.55))
	_interact_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.85))
	_interact_label.add_theme_constant_override("shadow_offset_x", 1)
	_interact_label.add_theme_constant_override("shadow_offset_y", 1)
	_interact_label.visible = false
	layer.add_child(_interact_label)


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
	_player.velocity = dir * _move_speed
	_player.move_and_slide()
	_update_walk_anim(dir)
	_update_near_clearable()


func _update_walk_anim(dir: Vector2) -> void:
	if _anim.sprite_frames == null:
		return
	var flip := false
	if dir.length() < 0.12:
		var idle := "idle_%s" % _facing
		_anim.flip_h = (_facing == "left")
		if _anim.animation != idle:
			_anim.play(idle)
		return
	if absf(dir.x) > absf(dir.y):
		_facing = "right" if dir.x > 0.0 else "left"
	else:
		_facing = "down" if dir.y > 0.0 else "up"
	flip = (_facing == "left")
	_anim.flip_h = flip
	var walk := "walk_%s" % _facing
	if _anim.animation != walk or not _anim.is_playing():
		_anim.play(walk)


func _update_near_clearable() -> void:
	_near = {}
	if _player == null:
		return
	var best_d := 9999.0
	for item in _clearables:
		if bool(item.get("cleared", false)):
			continue
		var node: Node2D = item.get("node")
		if node == null or not is_instance_valid(node):
			continue
		var d := _player.position.distance_to(node.position)
		if d < 42.0 and d < best_d:
			best_d = d
			_near = item
	if _interact_label:
		if not _near.is_empty() and show_hint:
			_interact_label.visible = true
			_interact_label.text = "E — убрать"
		else:
			_interact_label.visible = false


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_E:
			_try_clear()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_F12:
			show_hint = not show_hint
			if _hint:
				_hint.visible = show_hint
			if _interact_label and not show_hint:
				_interact_label.visible = false
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_F5:
			_take_screenshot("manual")
			get_viewport().set_input_as_handled()


func _try_clear() -> void:
	if _near.is_empty():
		return
	var item := _near
	if bool(item.get("cleared", false)):
		return
	item["cleared"] = true
	var node: Node2D = item.get("node")
	if node == null:
		return
	_spawn_clear_vfx(node.position)
	var body: StaticBody2D = item.get("body")
	if body != null and is_instance_valid(body):
		body.queue_free()
	node.visible = false
	node.queue_free()
	_near = {}
	# Keep entry marked cleared
	for i in _clearables.size():
		if str(_clearables[i].get("id", "")) == str(item.get("id", "")):
			_clearables[i]["cleared"] = true
			break


func _spawn_clear_vfx(at: Vector2) -> void:
	var parts := CPUParticles2D.new()
	parts.position = at
	parts.emitting = true
	parts.one_shot = true
	parts.explosiveness = 0.92
	parts.amount = 16
	parts.lifetime = 0.4
	parts.direction = Vector2(0, -1)
	parts.spread = 70.0
	parts.gravity = Vector2(0, 55)
	parts.initial_velocity_min = 25.0
	parts.initial_velocity_max = 70.0
	parts.scale_amount_min = 1.0
	parts.scale_amount_max = 2.2
	parts.color = Color(0.75, 0.68, 0.42, 0.95)
	_ysort.add_child(parts)
	get_tree().create_timer(0.7).timeout.connect(parts.queue_free)


func _take_screenshot(tag: String = "frame") -> void:
	var was_hint := show_hint
	show_hint = false
	if _hint:
		_hint.visible = false
	if _interact_label:
		_interact_label.visible = false
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		show_hint = was_hint
		if _hint:
			_hint.visible = show_hint
		return
	var path := ProjectSettings.globalize_path("%syard_art_test_v2_%s.png" % [SHOT_DIR, tag])
	img.save_png(path)
	show_hint = was_hint
	if _hint:
		_hint.visible = show_hint
	print("yard_art_test_v2 screenshot -> ", path)
