extends RefCounted
## Builds seamless grass/soil TileSet (Match Corners) from terrain_proof atlases.
## Atlas 12×4: masks 0..15, grass/soil macros, edge/corner visual variants.

const GROUND_PATH := "res://assets/art/outdoor/terrain_proof/terrain_ground.png"
const DECOR_PATH := "res://assets/art/outdoor/terrain_proof/terrain_decor.png"
const TILE := 16
const TERRAIN_GRASS := 0
const TERRAIN_SOIL := 1
const ATLAS_COLS := 12
const ATLAS_ROWS := 4


static func build_ground_tileset() -> TileSet:
	var tex := _load_tex(GROUND_PATH)
	if tex == null:
		push_error("YardTerrainTilesetFactory: missing ground atlas")
		return TileSet.new()

	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)

	ts.add_terrain_set()
	ts.set_terrain_set_mode(0, TileSet.TERRAIN_MODE_MATCH_CORNERS)
	ts.add_terrain(0)
	ts.set_terrain_name(0, TERRAIN_GRASS, "Grass")
	ts.set_terrain_color(0, TERRAIN_GRASS, Color(0.35, 0.55, 0.25))
	ts.add_terrain(0)
	ts.set_terrain_name(0, TERRAIN_SOIL, "Soil")
	ts.set_terrain_color(0, TERRAIN_SOIL, Color(0.45, 0.30, 0.18))

	var src := TileSetAtlasSource.new()
	src.texture = tex
	src.texture_region_size = Vector2i(TILE, TILE)
	src.margins = Vector2i(0, 0)
	src.separation = Vector2i(0, 0)
	src.use_texture_padding = true

	var cols := mini(ATLAS_COLS, int(tex.get_width() / TILE))
	var rows := mini(ATLAS_ROWS, int(tex.get_height() / TILE))
	for y in range(rows):
		for x in range(cols):
			var coords := Vector2i(x, y)
			if not src.has_tile(coords):
				src.create_tile(coords)

	ts.add_source(src, 0)

	# Primary 16 masks
	for mask in range(16):
		var coords := Vector2i(mask % 4, mask / 4)
		_apply_mask_terrains(src, coords, mask)
		src.get_tile_data(coords, 0).probability = 1.0

	# Full grass macros: base 65%, sparse(subtle) 20%, light+dark 10%, dense 5%
	_apply_mask_terrains(src, Vector2i(0, 0), 0)
	src.get_tile_data(Vector2i(0, 0), 0).probability = 0.65
	var grass_probs := [0.05, 0.05, 0.20, 0.05]
	for i in range(4):
		var coords := Vector2i(4 + i, 0)
		if not src.has_tile(coords):
			continue
		_apply_mask_terrains(src, coords, 0)
		src.get_tile_data(coords, 0).probability = grass_probs[i]

	# Full soil macros
	_apply_mask_terrains(src, Vector2i(3, 3), 15)
	src.get_tile_data(Vector2i(3, 3), 0).probability = 0.55
	var soil_probs := [0.15, 0.15, 0.10, 0.05]
	for i in range(4):
		var coords := Vector2i(4 + i, 1)
		if not src.has_tile(coords):
			continue
		_apply_mask_terrains(src, coords, 15)
		src.get_tile_data(coords, 0).probability = soil_probs[i]

	if cols < 12:
		return ts

	# Straight-edge visual variants (same bits): masks 12,3,6,9 → cols 8–10
	var straights := [
		{"mask": 12, "row": 0, "primary": Vector2i(0, 3)},
		{"mask": 3, "row": 1, "primary": Vector2i(3, 0)},
		{"mask": 6, "row": 2, "primary": Vector2i(2, 1)},
		{"mask": 9, "row": 3, "primary": Vector2i(1, 2)},
	]
	for item in straights:
		var primary: Vector2i = item["primary"]
		src.get_tile_data(primary, 0).probability = 0.40
		for vi in range(3):
			var coords := Vector2i(8 + vi, item["row"])
			_apply_mask_terrains(src, coords, int(item["mask"]))
			src.get_tile_data(coords, 0).probability = 0.20

	# Corner variants
	var corner_primary := {
		1: Vector2i(1, 0),
		2: Vector2i(2, 0),
		4: Vector2i(0, 1),
		8: Vector2i(0, 2),
	}
	for mask in [1, 2, 4, 8]:
		src.get_tile_data(corner_primary[mask], 0).probability = 0.45

	var col11_masks := [1, 2, 4, 8]
	for row in range(4):
		var mask: int = col11_masks[row]
		var coords := Vector2i(11, row)
		_apply_mask_terrains(src, coords, mask)
		src.get_tile_data(coords, 0).probability = 0.25

	var corner_slots := [
		{"mask": 1, "coords": Vector2i(4, 2)},
		{"mask": 1, "coords": Vector2i(5, 2)},
		{"mask": 2, "coords": Vector2i(6, 2)},
		{"mask": 2, "coords": Vector2i(7, 2)},
		{"mask": 4, "coords": Vector2i(4, 3)},
		{"mask": 4, "coords": Vector2i(5, 3)},
		{"mask": 8, "coords": Vector2i(6, 3)},
		{"mask": 8, "coords": Vector2i(7, 3)},
	]
	for item in corner_slots:
		var coords: Vector2i = item["coords"]
		_apply_mask_terrains(src, coords, int(item["mask"]))
		src.get_tile_data(coords, 0).probability = 0.15

	return ts


static func build_decor_tileset() -> TileSet:
	var tex := _load_tex(DECOR_PATH)
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	if tex == null:
		return ts
	var src := TileSetAtlasSource.new()
	src.texture = tex
	src.texture_region_size = Vector2i(TILE, TILE)
	src.margins = Vector2i(0, 0)
	src.separation = Vector2i(0, 0)
	src.use_texture_padding = true
	var cols := int(tex.get_width() / TILE)
	for x in range(cols):
		var coords := Vector2i(x, 0)
		if not src.has_tile(coords):
			src.create_tile(coords)
	ts.add_source(src, 0)
	return ts


static func _apply_mask_terrains(src: TileSetAtlasSource, coords: Vector2i, mask: int) -> void:
	var td := src.get_tile_data(coords, 0)
	td.terrain_set = 0
	var tl := TERRAIN_SOIL if (mask & 1) != 0 else TERRAIN_GRASS
	var tr := TERRAIN_SOIL if (mask & 2) != 0 else TERRAIN_GRASS
	var br := TERRAIN_SOIL if (mask & 4) != 0 else TERRAIN_GRASS
	var bl := TERRAIN_SOIL if (mask & 8) != 0 else TERRAIN_GRASS
	td.set_terrain_peering_bit(TileSet.CELL_NEIGHBOR_TOP_LEFT_CORNER, tl)
	td.set_terrain_peering_bit(TileSet.CELL_NEIGHBOR_TOP_RIGHT_CORNER, tr)
	td.set_terrain_peering_bit(TileSet.CELL_NEIGHBOR_BOTTOM_RIGHT_CORNER, br)
	td.set_terrain_peering_bit(TileSet.CELL_NEIGHBOR_BOTTOM_LEFT_CORNER, bl)
	if mask == 15:
		td.terrain = TERRAIN_SOIL
	elif mask == 0:
		td.terrain = TERRAIN_GRASS
	else:
		td.terrain = TERRAIN_GRASS if _popcount(mask) < 2 else TERRAIN_SOIL


static func _popcount(v: int) -> int:
	var n := 0
	var x := v
	while x != 0:
		n += x & 1
		x >>= 1
	return n


static func _load_tex(path: String) -> Texture2D:
	var abs_path := ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(abs_path):
		var img := Image.new()
		if img.load(abs_path) == OK:
			return ImageTexture.create_from_image(img)
	if ResourceLoader.exists(path):
		var res := load(path)
		if res is Texture2D:
			return res as Texture2D
	push_warning("YardTerrainTilesetFactory: cannot load %s" % path)
	return null


static func save_ground_tileset(path: String = "res://resources/tilesets/yard_ground_tileset.tres") -> int:
	var ts := build_ground_tileset()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://resources/tilesets"))
	return ResourceSaver.save(ts, path)
