extends Node2D
## VS01 childhood homestead — near yard + first orchard fragment on a long plot.
## PixelLab hero scale unchanged. ART_TEST_SHOT=1 for verification screenshots.

const HotspotUtil = preload("res://scripts/world/hotspot_util.gd")
const ASSET_ROOT := "res://assets/art/outdoor/yard_vs01/"
const HOUSE_TEX := ASSET_ROOT + "main_house_v1.png"
const HOUSE_META := ASSET_ROOT + "main_house_v1.json"
const PLAYER_SCENE := "res://scenes/actors/player/player_pixellab_test.tscn"
const LOCATION_ID := "childhood_home_yard"
const TILE := 16
## Long rural plot — see docs/CHILDHOOD_HOMESTEAD_LAYOUT.md
const MAP_W := 44
const MAP_H := 84
## Must match tools/build_yard_vs01_assets.py GROUND_PAD_TILES (camera bleed grass).
const GROUND_PAD_TILES := 8
const VIEW_W := 384
const VIEW_H := 240
const WINDOW_SCALE := 3
## Foundation / feet of MainHouse (upper yard, street to the north / off-screen).
const HOUSE_FEET := Vector2(20.0, 13.8)
## Front-yard spawn — yard-side door; plot continues south.
const PLAYER_SPAWN := Vector2(20.0, 16.8)
const PLAY_CAMERA_ZOOM := 2.4
const PLAY_CAMERA_OFFSET := Vector2(0, -36)
const FENCE_L := 5.5
const FENCE_R := 38.5

## Tile-space zone rectangles: Rect2(x, y, w, h) in tiles.
const ZONE_RECTS := {
	"house_front_or_street_edge": Rect2(5, 0, 34, 7),
	"near_house_yard": Rect2(5, 7, 34, 15),
	"utility_yard": Rect2(5, 22, 34, 12),
	"old_orchard": Rect2(5, 34, 34, 16),
	"future_garden": Rect2(5, 50, 34, 16),
	"far_overgrown_plot": Rect2(5, 66, 34, 18),
}

const ZONE_DEFAULTS := {
	"house_front_or_street_edge": {"state": "reserved", "cleared_count": 0},
	"near_house_yard": {"state": "neglected", "cleared_count": 0},
	"utility_yard": {"state": "neglected", "cleared_count": 0},
	"old_orchard": {"state": "reachable", "cleared_count": 0},
	"future_garden": {"state": "locked"},
	"far_overgrown_plot": {"state": "locked"},
}

var _ysort: Node2D
var _player: CharacterBody2D
var _hint: Label
var _prompt: Label
var _shot_cam: Camera2D
var _blockers: StaticBody2D
var _house: Node2D
var _door_hotspot: Area2D
var _zones_root: Node2D
var _show_zone_debug := false


func _ready() -> void:
	name = "YardVS01"
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	get_viewport().canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	DisplayServer.window_set_size(Vector2i(VIEW_W * WINDOW_SCALE, VIEW_H * WINDOW_SCALE))
	WorldState.set_meta_value("location", "childhood_home")
	WorldState.set_story("arrived_at_childhood_home", true)
	WorldState.ensure_location_zones(LOCATION_ID, ZONE_DEFAULTS)

	if not FileAccess.file_exists(ASSET_ROOT + "ground.png") or not FileAccess.file_exists(HOUSE_TEX):
		_show_missing("Missing yard_vs01 assets.\nRun: python tools/build_yard_vs01_assets.py")
		return

	_build_ground()
	_ysort = Node2D.new()
	_ysort.name = "YSortWorld"
	_ysort.y_sort_enabled = true
	_ysort.z_index = 10
	add_child(_ysort)

	_blockers = StaticBody2D.new()
	_blockers.name = "Blockers"
	_blockers.collision_layer = 1
	_blockers.collision_mask = 0
	add_child(_blockers)

	_build_zone_markers()
	_build_fence()
	_build_house()
	_build_street_portal()
	_build_secondary_props()
	_build_edge_trees()
	_build_orchard()
	_build_garden_reserve_decor()
	_build_far_blockage()
	_build_clearables()
	_build_ambient_decor()
	_build_player()
	_build_bounds()
	_build_ui()
	_build_orchard_hint()

	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.35).timeout
		await _shot_sequence()
		get_tree().quit()


func _map_px() -> Vector2:
	return Vector2(MAP_W * TILE, MAP_H * TILE)


func _show_missing(msg: String) -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var lab := Label.new()
	lab.text = msg
	lab.position = Vector2(24, 24)
	lab.add_theme_font_size_override("font_size", 14)
	layer.add_child(lab)
	if OS.get_environment("ART_TEST_SHOT") != "":
		await get_tree().create_timer(0.2).timeout
		get_tree().quit()


func _load_tex(path: String) -> Texture2D:
	var abs_path := ProjectSettings.globalize_path(path)
	var img := Image.new()
	if FileAccess.file_exists(abs_path) and img.load(abs_path) == OK:
		return ImageTexture.create_from_image(img)
	if ResourceLoader.exists(path):
		var res := load(path)
		if res is Texture2D:
			return res
	push_warning("Missing texture: %s" % path)
	return null


func _add_sprite(parent: Node, path: String, pos: Vector2, centered := true, offset := Vector2.ZERO) -> Sprite2D:
	var spr := Sprite2D.new()
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = centered
	spr.texture = _load_tex(path)
	spr.position = pos
	spr.offset = offset
	parent.add_child(spr)
	return spr


func _add_blocker_rect(center: Vector2, size: Vector2) -> void:
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = size
	col.shape = shape
	col.position = center
	_blockers.add_child(col)


func _camera_limit_rect() -> Rect2:
	var pad := float(GROUND_PAD_TILES * TILE)
	return Rect2(-pad, -pad, float((MAP_W + GROUND_PAD_TILES * 2) * TILE), float((MAP_H + GROUND_PAD_TILES * 2) * TILE))


func _apply_camera_limits(cam: Camera2D) -> void:
	var r := _camera_limit_rect()
	cam.limit_left = int(r.position.x)
	cam.limit_top = int(r.position.y)
	cam.limit_right = int(r.end.x)
	cam.limit_bottom = int(r.end.y)


func _build_ground() -> void:
	var ground := Node2D.new()
	ground.name = "Ground"
	add_child(ground)
	var spr := _add_sprite(ground, ASSET_ROOT + "ground.png", Vector2.ZERO, false)
	spr.position = Vector2(-GROUND_PAD_TILES * TILE, -GROUND_PAD_TILES * TILE)
	spr.centered = false
	spr.z_index = 0


func _build_zone_markers() -> void:
	_zones_root = Node2D.new()
	_zones_root.name = "HomesteadZones"
	_zones_root.z_index = 5
	add_child(_zones_root)
	for zid in ZONE_RECTS.keys():
		var r: Rect2 = ZONE_RECTS[zid]
		var n := Node2D.new()
		n.name = str(zid)
		n.position = Vector2(r.position.x * TILE, r.position.y * TILE)
		n.set_meta("zone_id", zid)
		n.set_meta("tile_rect", [r.position.x, r.position.y, r.size.x, r.size.y])
		n.set_meta("px_rect", [
			r.position.x * TILE, r.position.y * TILE,
			r.size.x * TILE, r.size.y * TILE
		])
		_zones_root.add_child(n)
		# Invisible area for future zone queries (not solid).
		var area := Area2D.new()
		area.name = "Bounds"
		area.monitoring = false
		area.monitorable = false
		area.collision_layer = 0
		area.collision_mask = 0
		var col := CollisionShape2D.new()
		var shape := RectangleShape2D.new()
		shape.size = Vector2(r.size.x * TILE, r.size.y * TILE)
		col.shape = shape
		col.position = Vector2(r.size.x * TILE * 0.5, r.size.y * TILE * 0.5)
		area.add_child(col)
		n.add_child(area)


func _build_fence() -> void:
	## Side fences run the length of the plot. No false south fence closing the near yard.
	## North rail marks street-edge; south of orchard is blocked by debris, not a full gate row.
	var post := ASSET_ROOT + "fence_post.png"
	var rail := ASSET_ROOT + "fence_rail.png"
	var north_y := 4.2
	var south_end := float(MAP_H - 2)
	# Top — street edge above the roof
	for x in range(int(FENCE_L) + 1, int(FENCE_R)):
		_fence_segment(Vector2((x + 0.5) * TILE, north_y * TILE), post, rail, true)
		_add_blocker_rect(Vector2((x + 0.5) * TILE, (north_y + 0.3) * TILE), Vector2(14, 6))
	# Left / right — full length, with occasional broken gaps further south
	for y in range(int(north_y), int(south_end) + 1):
		var broken := y > 55 and (y % 7 == 0 or y % 11 == 0)
		if broken:
			continue
		_fence_segment(Vector2(FENCE_L * TILE, (y + 0.5) * TILE), post, rail, false)
		_add_blocker_rect(Vector2((FENCE_L + 0.1) * TILE, (y + 0.5) * TILE), Vector2(6, 14))
		_fence_segment(Vector2(FENCE_R * TILE, (y + 0.5) * TILE), post, rail, false)
		_add_blocker_rect(Vector2((FENCE_R - 0.1) * TILE, (y + 0.5) * TILE), Vector2(6, 14))
	# Sparse ruined fence fragments in far zone (visual only, already skipped gaps)
	for x in [10, 14, 28, 33]:
		_fence_segment(Vector2((x + 0.5) * TILE, 70.5 * TILE), post, rail, true)


func _fence_segment(pos: Vector2, post_path: String, rail_path: String, horizontal: bool) -> void:
	var post_spr := _add_sprite(_ysort, post_path, pos, true, Vector2(0, -8))
	post_spr.z_as_relative = true
	if horizontal:
		var rail_spr := _add_sprite(_ysort, rail_path, pos + Vector2(0, -6), true)
		rail_spr.z_as_relative = true
		if int(pos.x / TILE) % 5 == 0:
			post_spr.position.y += 1


func _build_house() -> void:
	var tex := _load_tex(HOUSE_TEX)
	if tex == null:
		push_error("Missing approved house texture: %s" % HOUSE_TEX)
		return

	var hw := tex.get_width()
	var hh := tex.get_height()
	var door_rect := Rect2(107, 84, 12, 33)
	if FileAccess.file_exists(ProjectSettings.globalize_path(HOUSE_META)):
		var f := FileAccess.open(HOUSE_META, FileAccess.READ)
		var data = JSON.parse_string(f.get_as_text())
		if typeof(data) == TYPE_DICTIONARY and data.has("door_rect_display"):
			var d: Dictionary = data["door_rect_display"]
			door_rect = Rect2(
				float(d.x0), float(d.y0),
				float(d.x1) - float(d.x0),
				float(d.y1) - float(d.y0)
			)

	var house_pos := Vector2(HOUSE_FEET.x * TILE, HOUSE_FEET.y * TILE)
	_house = Node2D.new()
	_house.name = "MainHouse"
	_house.position = house_pos
	_house.z_as_relative = true
	_ysort.add_child(_house)

	var spr := Sprite2D.new()
	spr.name = "Sprite"
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = true
	spr.texture = tex
	spr.offset = Vector2(0, 1.0 - float(hh) * 0.5)
	spr.scale = Vector2.ONE
	_house.add_child(spr)

	var body := StaticBody2D.new()
	body.name = "HouseCollision"
	body.collision_layer = 1
	body.collision_mask = 0
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(hw * 0.72, 34)
	col.shape = shape
	col.position = Vector2(-6, -14)
	body.add_child(col)
	_house.add_child(body)

	var door_cx := door_rect.position.x + door_rect.size.x * 0.5
	var door_bottom := door_rect.position.y + door_rect.size.y
	var door_local := Vector2(
		door_cx - float(hw) * 0.5,
		spr.offset.y + (door_bottom - float(hh) * 0.5)
	)
	var door_script := load("res://scripts/locations/outdoor/childhood_home/yard_vs01_door.gd")
	_door_hotspot = door_script.new() as Area2D
	_door_hotspot.name = "DoorHotspot"
	_door_hotspot.position = Vector2(door_local.x, 8)
	var dcol := CollisionShape2D.new()
	var dshape := RectangleShape2D.new()
	dshape.size = Vector2(maxf(20.0, door_rect.size.x + 10.0), 18)
	dcol.shape = dshape
	_door_hotspot.add_child(dcol)
	_house.add_child(_door_hotspot)

	print("yard_vs01 house %dx%d map=%dx%d cam zoom=%.1f" % [
		hw, hh, MAP_W, MAP_H, PLAY_CAMERA_ZOOM
	])


func _build_street_portal() -> void:
	## North of house — future village_street transition (inactive).
	var portal_script := load("res://scripts/locations/outdoor/childhood_home/village_street_portal.gd")
	var tip: Area2D = portal_script.new()
	tip.name = "VillageStreetPortal"
	tip.position = Vector2(20 * TILE, 6.5 * TILE)
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(40, 16)
	col.shape = shape
	tip.add_child(col)
	_ysort.add_child(tip)


func _build_secondary_props() -> void:
	var well := _add_sprite(_ysort, ASSET_ROOT + "well.png", Vector2(27.5 * TILE, 16.5 * TILE), true, Vector2(0, -10))
	well.name = "Well"
	_add_blocker_rect(Vector2(27.5 * TILE, 16.9 * TILE), Vector2(22, 12))
	var wood := _add_sprite(_ysort, ASSET_ROOT + "woodpile.png", Vector2(11.8 * TILE, 13.6 * TILE), true, Vector2(0, -4))
	wood.name = "Woodpile"
	_add_blocker_rect(Vector2(11.8 * TILE, 13.9 * TILE), Vector2(28, 10))
	var shed := _add_sprite(_ysort, ASSET_ROOT + "shed_corner.png", Vector2(10.0 * TILE, 24.5 * TILE), true, Vector2(0, -12))
	shed.name = "ShedCorner"
	_add_blocker_rect(Vector2(10.0 * TILE, 25.0 * TILE), Vector2(36, 16))


func _build_edge_trees() -> void:
	## Near-house edge trees only — south bulk lives in orchard / far zones.
	var trees := [
		[ASSET_ROOT + "props/tree_a.png", Vector2(10.5 * TILE, 9.0 * TILE), Vector2(0.92, 0.92)],
		[ASSET_ROOT + "props/tree_b.png", Vector2(29.5 * TILE, 9.8 * TILE), Vector2(0.92, 0.92)],
	]
	for t in trees:
		var spr := _add_sprite(_ysort, str(t[0]), t[1], true, Vector2(0, -26))
		spr.scale = t[2]
		spr.z_as_relative = true
		_add_blocker_rect(t[1] + Vector2(0, 4), Vector2(16, 10))


func _spawn_fruit_tree(cfg: Dictionary) -> void:
	var n: Node2D = load("res://scripts/world/fruit_tree_stub.gd").new()
	n.object_id = str(cfg.id)
	n.species = str(cfg.species)
	n.tree_state = str(cfg.get("state", "neglected"))
	n.zone_id = "old_orchard"
	n.position = cfg.pos
	n.name = str(cfg.id)
	var spr := _add_sprite(n, str(cfg.spr), Vector2.ZERO, true, Vector2(0, -28))
	spr.scale = cfg.get("scale", Vector2(0.9, 0.9))
	spr.z_as_relative = true
	_ysort.add_child(n)
	_add_blocker_rect(cfg.pos + Vector2(0, 4), cfg.get("solid_size", Vector2(14, 10)))


func _build_orchard() -> void:
	## First orchard fragment — candidates with stable ids, no harvest cycle.
	var trees := [
		{"id": "orch_apple_01", "species": "apple", "pos": Vector2(14.5 * TILE, 38.0 * TILE), "spr": ASSET_ROOT + "props/fruit_apple_a.png", "scale": Vector2(1.15, 1.15)},
		{"id": "orch_apple_02", "species": "apple", "pos": Vector2(25.5 * TILE, 39.5 * TILE), "spr": ASSET_ROOT + "props/fruit_apple_b.png", "scale": Vector2(1.12, 1.12)},
		{"id": "orch_apple_03", "species": "apple", "pos": Vector2(18.0 * TILE, 43.5 * TILE), "spr": ASSET_ROOT + "props/fruit_apple_a.png", "scale": Vector2(1.05, 1.05), "state": "neglected"},
		{"id": "orch_pear_01", "species": "pear", "pos": Vector2(29.0 * TILE, 42.0 * TILE), "spr": ASSET_ROOT + "props/fruit_pear.png", "scale": Vector2(1.1, 1.1)},
		{"id": "orch_dead_01", "species": "apple", "pos": Vector2(11.5 * TILE, 44.0 * TILE), "spr": ASSET_ROOT + "props/fruit_dead.png", "scale": Vector2(0.95, 0.95), "state": "exhausted_or_diseased"},
	]
	for t in trees:
		_spawn_fruit_tree(t)

	# Berry bushes — candidates (decorative + solid), future prune/harvest.
	var berries := [
		{"id": "orch_berry_currant_01", "pos": Vector2(16.5 * TILE, 36.5 * TILE), "spr": ASSET_ROOT + "props/berry_currant.png"},
		{"id": "orch_berry_goose_01", "pos": Vector2(22.5 * TILE, 37.2 * TILE), "spr": ASSET_ROOT + "props/berry_gooseberry.png"},
		{"id": "orch_berry_rasp_01", "pos": Vector2(27.0 * TILE, 45.5 * TILE), "spr": ASSET_ROOT + "props/berry_raspberry.png"},
		{"id": "orch_berry_currant_02", "pos": Vector2(13.0 * TILE, 41.5 * TILE), "spr": ASSET_ROOT + "props/berry_currant.png"},
	]
	for b in berries:
		var n := Node2D.new()
		n.name = str(b.id)
		n.position = b.pos
		n.set_meta("object_id", b.id)
		n.set_meta("species", "berry")
		n.set_meta("tree_state", "neglected")
		n.set_meta("zone_id", "old_orchard")
		var spr := _add_sprite(n, str(b.spr), Vector2.ZERO, true, Vector2(0, -8))
		spr.scale = Vector2(0.9, 0.9)
		_ysort.add_child(n)
		_add_blocker_rect(b.pos + Vector2(0, 2), Vector2(14, 9))


func _build_garden_reserve_decor() -> void:
	## Sparse scars only — no permanent blockers that fight future bed layout.
	for p in [
		[ASSET_ROOT + "props/rock_sm.png", Vector2(12.0 * TILE, 55.0 * TILE)],
		[ASSET_ROOT + "props/rock_md.png", Vector2(30.5 * TILE, 58.5 * TILE)],
		[ASSET_ROOT + "weed_a.png", Vector2(18.0 * TILE, 57.0 * TILE)],
		[ASSET_ROOT + "weed_b.png", Vector2(24.0 * TILE, 61.0 * TILE)],
		[ASSET_ROOT + "log.png", Vector2(15.5 * TILE, 62.5 * TILE)],
	]:
		var spr := _add_sprite(_ysort, str(p[0]), p[1], true, Vector2(0, -6))
		spr.z_as_relative = true
		spr.modulate = Color(1, 1, 1, 0.92)


func _build_far_blockage() -> void:
	## Closes further plot for now — player sees the land continues.
	var y := 48.5
	for item in [
		[ASSET_ROOT + "props/tree_c.png", Vector2(17.5 * TILE, y * TILE), Vector2(0.95, 0.95), Vector2(18, 12)],
		[ASSET_ROOT + "log.png", Vector2(20.5 * TILE, (y + 0.8) * TILE), Vector2(1.1, 1.0), Vector2(36, 10)],
		[ASSET_ROOT + "log.png", Vector2(23.5 * TILE, (y + 0.3) * TILE), Vector2(1.0, 1.0), Vector2(32, 10)],
		[ASSET_ROOT + "props/bush_overgrown.png", Vector2(15.0 * TILE, (y + 0.5) * TILE), Vector2(1.0, 1.0), Vector2(18, 12)],
		[ASSET_ROOT + "props/bush_overgrown.png", Vector2(26.5 * TILE, (y + 0.6) * TILE), Vector2(1.0, 1.0), Vector2(18, 12)],
		[ASSET_ROOT + "stump.png", Vector2(19.0 * TILE, (y + 1.4) * TILE), Vector2(1.0, 1.0), Vector2(16, 10)],
	]:
		var spr := _add_sprite(_ysort, str(item[0]), item[1], true, Vector2(0, -18))
		spr.scale = item[2]
		spr.name = "FarBlockage"
		_add_blocker_rect(item[1] + Vector2(0, 4), item[3])
	# Solid wall across path so player cannot squeeze through
	_add_blocker_rect(Vector2(20 * TILE, (y + 0.6) * TILE), Vector2(140, 18))


func _spawn_clearable(cfg: Dictionary) -> void:
	var n: Area2D = load("res://scripts/world/yard_object.gd").new()
	n.object_id = str(cfg.id)
	n.object_type = str(cfg.kind)
	n.plot_id = "yard_vs01"
	n.prompt_text = str(cfg.get("prompt", "убрать"))
	n.item_id = str(cfg.get("item", ""))
	n.amount = 1
	n.max_hits = int(cfg.get("hits", 1))
	n.blocks_movement = bool(cfg.get("solid", false))
	n.position = cfg.pos
	n.monitoring = true
	n.collision_layer = 0
	n.collision_mask = 1

	var tex := _load_tex(str(cfg.spr))
	var spr := Sprite2D.new()
	spr.name = "Sprite"
	spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	spr.centered = true
	spr.texture = tex
	if tex:
		spr.offset = Vector2(0, -tex.get_height() * 0.35)
	if cfg.has("scale"):
		spr.scale = cfg.scale
	n.add_child(spr)

	var hit := Vector2(20, 16)
	if tex:
		var sc: Vector2 = cfg.get("scale", Vector2.ONE)
		hit = Vector2(
			maxi(14, int(tex.get_width() * 0.8 * sc.x)),
			maxi(12, int(tex.get_height() * 0.45 * sc.y))
		)
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = hit
	col.shape = shape
	col.position = Vector2(0, -hit.y * 0.1)
	n.add_child(col)

	if bool(cfg.get("solid", false)):
		var solid_size: Vector2 = cfg.get("solid_size", Vector2(hit.x * 0.85, maxf(10.0, hit.y * 0.5)))
		HotspotUtil.add_blocker(n, Vector2(0, 2), solid_size)
	_ysort.add_child(n)


func _build_clearables() -> void:
	## Near yard + path into orchard. Existing object_ids preserved where possible.
	var required := [
		{
			"id": "vs01_bush_door_side",
			"kind": "bush",
			"pos": Vector2(17.2 * TILE, 15.2 * TILE),
			"spr": ASSET_ROOT + "props/bush_overgrown.png",
			"prompt": "прорубить куст",
			"item": "grass",
			"solid": true,
			"solid_size": Vector2(16, 11),
			"scale": Vector2(0.85, 0.85),
		},
		{
			"id": "vs01_rock_yard",
			"kind": "stone",
			"pos": Vector2(22.4 * TILE, 17.2 * TILE),
			"spr": ASSET_ROOT + "props/rock_md.png",
			"prompt": "сдвинуть камень",
			"item": "stone",
			"hits": 5,
			"solid": true,
			"solid_size": Vector2(16, 10),
		},
		{
			"id": "vs01_log_path",
			"kind": "log",
			"pos": Vector2(19.6 * TILE, 28.5 * TILE),
			"spr": ASSET_ROOT + "log.png",
			"prompt": "убрать бревно",
			"item": "wood",
			"solid": true,
			"solid_size": Vector2(28, 8),
		},
		{
			"id": "vs01_stump_path",
			"kind": "stump",
			"pos": Vector2(20.2 * TILE, 32.5 * TILE),
			"spr": ASSET_ROOT + "stump.png",
			"prompt": "убрать пень",
			"item": "wood",
			"solid": true,
			"solid_size": Vector2(16, 10),
		},
	]
	for cfg in required:
		_spawn_clearable(cfg)

	var optional := [
		{"id": "vs01_weed_1", "kind": "weed", "pos": Vector2(16.2 * TILE, 24.5 * TILE), "spr": ASSET_ROOT + "weed_a.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_2", "kind": "weed", "pos": Vector2(23.2 * TILE, 26.8 * TILE), "spr": ASSET_ROOT + "weed_b.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_3", "kind": "weed", "pos": Vector2(15.4 * TILE, 18.2 * TILE), "spr": ASSET_ROOT + "weed_a.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_4", "kind": "weed", "pos": Vector2(24.0 * TILE, 19.0 * TILE), "spr": ASSET_ROOT + "weed_b.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_weed_5", "kind": "weed", "pos": Vector2(18.0 * TILE, 35.5 * TILE), "spr": ASSET_ROOT + "weed_a.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_orch_weed_a", "kind": "weed", "pos": Vector2(21.5 * TILE, 40.5 * TILE), "spr": ASSET_ROOT + "weed_b.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_orch_weed_b", "kind": "weed", "pos": Vector2(15.8 * TILE, 42.0 * TILE), "spr": ASSET_ROOT + "weed_a.png", "prompt": "сорвать сорняк", "item": "grass", "solid": false},
		{"id": "vs01_orch_rock", "kind": "stone", "pos": Vector2(23.8 * TILE, 41.2 * TILE), "spr": ASSET_ROOT + "props/rock_sm.png", "prompt": "сдвинуть камень", "item": "stone", "hits": 5, "solid": true, "solid_size": Vector2(12, 8)},
		{"id": "vs01_orch_branch", "kind": "log", "pos": Vector2(17.2 * TILE, 45.0 * TILE), "spr": ASSET_ROOT + "log.png", "prompt": "убрать сухие ветки", "item": "wood", "solid": true, "solid_size": Vector2(26, 8)},
		{"id": "vs01_rock_side", "kind": "stone", "pos": Vector2(14.2 * TILE, 21.5 * TILE), "spr": ASSET_ROOT + "props/rock_sm.png", "prompt": "сдвинуть камень", "item": "stone", "hits": 5, "solid": true, "solid_size": Vector2(12, 8)},
		{"id": "vs01_bush_side", "kind": "bush", "pos": Vector2(25.8 * TILE, 14.0 * TILE), "spr": ASSET_ROOT + "props/bush_md.png", "prompt": "прорубить куст", "item": "grass", "solid": true, "solid_size": Vector2(16, 11), "scale": Vector2(0.9, 0.9)},
		{"id": "vs01_stump_side", "kind": "stump", "pos": Vector2(12.8 * TILE, 30.5 * TILE), "spr": ASSET_ROOT + "stump.png", "prompt": "убрать пень", "item": "wood", "solid": true, "solid_size": Vector2(16, 10)},
	]
	for cfg in optional:
		_spawn_clearable(cfg)

	for p in [
		[ASSET_ROOT + "props/rock_lg.png", Vector2(12.2 * TILE, 15.5 * TILE), Vector2(18, 11)],
		[ASSET_ROOT + "props/bush_sm.png", Vector2(26.2 * TILE, 29.5 * TILE), Vector2(12, 9)],
		[ASSET_ROOT + "props/rock_sm.png", Vector2(28.2 * TILE, 20.5 * TILE), Vector2(10, 8)],
	]:
		_add_sprite(_ysort, str(p[0]), p[1], true, Vector2(0, -6))
		_add_blocker_rect(p[1] + Vector2(0, 2), p[2])


func _build_ambient_decor() -> void:
	var weeds := [
		Vector2(13.5 * TILE, 18.8 * TILE),
		Vector2(22.8 * TILE, 15.5 * TILE),
		Vector2(17.5 * TILE, 20.8 * TILE),
		Vector2(24.8 * TILE, 27.5 * TILE),
		Vector2(15.8 * TILE, 31.2 * TILE),
		Vector2(21.5 * TILE, 36.0 * TILE),
		Vector2(11.5 * TILE, 26.0 * TILE),
		Vector2(27.0 * TILE, 34.0 * TILE),
		Vector2(19.0 * TILE, 44.5 * TILE),
		Vector2(26.0 * TILE, 40.0 * TILE),
	]
	var i := 0
	for pos in weeds:
		var path := ASSET_ROOT + ("weed_a.png" if i % 2 == 0 else "weed_b.png")
		var spr := _add_sprite(_ysort, path, pos, true, Vector2(0, -4))
		spr.z_as_relative = true
		i += 1
	for b in [
		[ASSET_ROOT + "props/bush_sm.png", Vector2(13.8 * TILE, 12.8 * TILE)],
		[ASSET_ROOT + "props/bush_sm.png", Vector2(26.5 * TILE, 22.5 * TILE)],
	]:
		var spr2 := _add_sprite(_ysort, str(b[0]), b[1], true, Vector2(0, -6))
		spr2.z_as_relative = true


func _build_orchard_hint() -> void:
	var tip := Area2D.new()
	tip.name = "OrchardBlockHint"
	tip.monitoring = true
	tip.collision_layer = 0
	tip.collision_mask = 1
	tip.position = Vector2(20 * TILE, 47.2 * TILE)
	var col := CollisionShape2D.new()
	var shape := RectangleShape2D.new()
	shape.size = Vector2(64, 24)
	col.shape = shape
	tip.add_child(col)
	tip.set_script(load("res://scripts/locations/outdoor/childhood_home/yard_vs01_gate_hint.gd"))
	_ysort.add_child(tip)


func _resolve_player_spawn() -> Vector2:
	var sp := str(GameFlow.spawn_point)
	if sp == "from_house" or sp == "from_workshop":
		return Vector2(HOUSE_FEET.x * TILE, (HOUSE_FEET.y + 1.5) * TILE)
	if sp == "childhood_home" or sp == "yard_vs01":
		var mapped: Vector2 = GameFlow.spawn_position()
		if mapped != Vector2.ZERO:
			return mapped
	return Vector2(PLAYER_SPAWN.x * TILE, PLAYER_SPAWN.y * TILE)


func _build_player() -> void:
	var packed := load(PLAYER_SCENE) as PackedScene
	_player = packed.instantiate() as CharacterBody2D
	_player.name = "PlayerPixelLabTest"
	_player.position = _resolve_player_spawn()
	_player.scale = Vector2.ONE
	_ysort.add_child(_player)
	if _player.has_method("set_camera_zoom"):
		_player.call("set_camera_zoom", Vector2(PLAY_CAMERA_ZOOM, PLAY_CAMERA_ZOOM))
	if _player.has_method("set_camera_offset"):
		_player.call("set_camera_offset", PLAY_CAMERA_OFFSET)
	if _player.has_method("set_camera_limits"):
		_player.call("set_camera_limits", _camera_limit_rect())
	var pcam := _player.get_node_or_null("Camera2D") as Camera2D
	if pcam:
		_apply_camera_limits(pcam)


func _build_bounds() -> void:
	var map := _map_px()
	var thickness := 16.0
	var rects := [
		[Vector2(map.x * 0.5, -thickness * 0.5), Vector2(map.x, thickness)],
		[Vector2(map.x * 0.5, map.y + thickness * 0.5), Vector2(map.x, thickness)],
		[Vector2(-thickness * 0.5, map.y * 0.5), Vector2(thickness, map.y)],
		[Vector2(map.x + thickness * 0.5, map.y * 0.5), Vector2(thickness, map.y)],
	]
	for r in rects:
		_add_blocker_rect(r[0], r[1])


func _build_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	_hint = Label.new()
	_hint.position = Vector2(8, 6)
	_hint.add_theme_font_size_override("font_size", 11)
	_hint.add_theme_color_override("font_color", Color(0.95, 0.95, 0.9))
	_hint.text = "Усадьба · WASD · E — действие · F11 зоны · F12 коллизии"
	layer.add_child(_hint)
	_prompt = Label.new()
	_prompt.add_theme_font_size_override("font_size", 12)
	_prompt.add_theme_color_override("font_color", Color(1, 0.95, 0.8))
	_prompt.visible = false
	layer.add_child(_prompt)
	_prompt.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	_prompt.offset_left = 8
	_prompt.offset_bottom = -10
	_prompt.offset_top = -28
	if _player and _player.has_method("set_prompt_label"):
		_player.call("set_prompt_label", _prompt)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F12:
			get_tree().debug_collisions_hint = not get_tree().debug_collisions_hint
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_F11:
			_show_zone_debug = not _show_zone_debug
			_refresh_zone_debug()
			get_viewport().set_input_as_handled()


func _refresh_zone_debug() -> void:
	var old := get_node_or_null("ZoneDebugDraw")
	if old:
		old.queue_free()
	if not _show_zone_debug:
		return
	var root := Node2D.new()
	root.name = "ZoneDebugDraw"
	root.z_index = 90
	add_child(root)
	var colors := {
		"house_front_or_street_edge": Color(0.4, 0.5, 0.9, 0.22),
		"near_house_yard": Color(0.3, 0.8, 0.4, 0.22),
		"utility_yard": Color(0.8, 0.7, 0.2, 0.2),
		"old_orchard": Color(0.2, 0.7, 0.55, 0.25),
		"future_garden": Color(0.7, 0.5, 0.2, 0.2),
		"far_overgrown_plot": Color(0.5, 0.2, 0.5, 0.22),
	}
	for zid in ZONE_RECTS.keys():
		var r: Rect2 = ZONE_RECTS[zid]
		var poly := Polygon2D.new()
		poly.polygon = PackedVector2Array([
			Vector2(0, 0),
			Vector2(r.size.x * TILE, 0),
			Vector2(r.size.x * TILE, r.size.y * TILE),
			Vector2(0, r.size.y * TILE),
		])
		poly.color = colors.get(zid, Color(1, 1, 1, 0.15))
		poly.position = Vector2(r.position.x * TILE, r.position.y * TILE)
		root.add_child(poly)
		var lab := Label.new()
		lab.text = str(zid)
		lab.position = poly.position + Vector2(4, 4)
		lab.add_theme_font_size_override("font_size", 10)
		lab.add_theme_color_override("font_color", Color(1, 1, 1, 0.9))
		root.add_child(lab)


func _shot_sequence() -> void:
	_hint.visible = false
	if _player and _player.has_method("set_camera_enabled"):
		_player.call("set_camera_enabled", false)
	_shot_cam = Camera2D.new()
	_shot_cam.enabled = true
	_shot_cam.zoom = Vector2(PLAY_CAMERA_ZOOM, PLAY_CAMERA_ZOOM)
	_shot_cam.offset = Vector2.ZERO
	_apply_camera_limits(_shot_cam)
	add_child(_shot_cam)
	_shot_cam.make_current()

	if _player:
		_player.scale = Vector2.ONE
		var anim := _player.get_node_or_null("AnimatedSprite2D") as AnimatedSprite2D
		if anim:
			anim.scale = Vector2.ONE
			anim.play("idle_north")

	# 1) Start — house + front yard (composition preserved)
	_player.position = Vector2(PLAYER_SPAWN.x * TILE, PLAYER_SPAWN.y * TILE)
	_shot_cam.position = _player.position + PLAY_CAMERA_OFFSET
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take("yard_vs01_start")

	# 2) Transition yard → orchard
	_player.position = Vector2(20 * TILE, 33.5 * TILE)
	if _player.get_node_or_null("AnimatedSprite2D"):
		(_player.get_node("AnimatedSprite2D") as AnimatedSprite2D).play("idle_south")
	_shot_cam.position = _player.position + PLAY_CAMERA_OFFSET
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take("yard_vs01_yard_to_orchard")

	# 3) Orchard fragment
	_player.position = Vector2(20 * TILE, 40.0 * TILE)
	_shot_cam.position = _player.position + PLAY_CAMERA_OFFSET
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take("yard_vs01_orchard")

	# 4) Blockage closing far plot
	_player.position = Vector2(20 * TILE, 46.5 * TILE)
	_shot_cam.position = _player.position + Vector2(0, -20)
	await get_tree().process_frame
	await get_tree().create_timer(0.25).timeout
	await _take("yard_vs01_blockage")

	# 5) Zone debug overlay (pull back)
	_show_zone_debug = true
	_refresh_zone_debug()
	_shot_cam.zoom = Vector2(0.55, 0.55)
	_shot_cam.position = Vector2(22 * TILE, 42 * TILE)
	if _player:
		_player.visible = false
	await get_tree().process_frame
	await get_tree().create_timer(0.3).timeout
	await _take("yard_vs01_zones_debug")
	_show_zone_debug = false
	_refresh_zone_debug()
	if _player:
		_player.visible = true


func _take(tag: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	if img == null:
		return
	var path := ProjectSettings.globalize_path("res://docs/art_tests/%s.png" % tag)
	img.save_png(path)
	print("Wrote ", path)
