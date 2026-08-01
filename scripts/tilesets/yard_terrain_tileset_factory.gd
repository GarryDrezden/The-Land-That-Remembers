extends RefCounted
## Builds seamless grass/soil TileSet (Match Corners) from terrain_proof atlases.

const GROUND_PATH := "res://assets/art/outdoor/terrain_proof/terrain_ground.png"
const DECOR_PATH := "res://assets/art/outdoor/terrain_proof/terrain_decor.png"
const TILE := 16
const TERRAIN_GRASS := 0
const TERRAIN_SOIL := 1

## Atlas layout: masks 0..15 at (mask%4, mask/4); grass vars (4..7, 0); soil vars (4..7, 1)
const GRASS_PROBS := [0.60, 0.20, 0.12, 0.06]  # base + 3 extras; 4th var gets 0.02 via remaining


static func build_ground_tileset() -> TileSet:
	var tex := _load_tex(GROUND_PATH)
	if tex == null:
		push_error("YardTerrainTilesetFactory: missing ground atlas")
		return TileSet.new()

	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)

	ts.add_terrain_set()
	ts.set_terrain_set_mode(0, TileSet.TERRAIN_MODE_MATCH_CORNERS)
	ts.add_terrain(0) # Grass -> index 0
	ts.set_terrain_name(0, TERRAIN_GRASS, "Grass")
	ts.set_terrain_color(0, TERRAIN_GRASS, Color(0.35, 0.55, 0.25))
	ts.add_terrain(0) # Soil -> index 1
	ts.set_terrain_name(0, TERRAIN_SOIL, "Soil")
	ts.set_terrain_color(0, TERRAIN_SOIL, Color(0.45, 0.30, 0.18))

	var src := TileSetAtlasSource.new()
	src.texture = tex
	src.texture_region_size = Vector2i(TILE, TILE)
	src.margins = Vector2i(0, 0)
	src.separation = Vector2i(0, 0)
	src.use_texture_padding = true

	# Create all atlas tiles in 8×4
	for y in range(4):
		for x in range(8):
			var coords := Vector2i(x, y)
			if not src.has_tile(coords):
				src.create_tile(coords)

	var src_id := ts.add_source(src, 0)

	# 16 corner masks
	for mask in range(16):
		var coords := Vector2i(mask % 4, mask / 4)
		_apply_mask_terrains(src, coords, mask)
		# probability 1.0 for unique transition masks; full grass/soil overridden below
		var td := src.get_tile_data(coords, 0)
		td.probability = 1.0

	# Full grass = mask 0 + variants at (4..7, 0) with probabilities
	_apply_mask_terrains(src, Vector2i(0, 0), 0)
	src.get_tile_data(Vector2i(0, 0), 0).probability = 0.60
	var grass_probs := [0.20, 0.12, 0.06, 0.02]
	for i in range(4):
		var coords := Vector2i(4 + i, 0)
		_apply_mask_terrains(src, coords, 0)
		src.get_tile_data(coords, 0).probability = grass_probs[i]

	# Full soil = mask 15 + variants
	_apply_mask_terrains(src, Vector2i(3, 3), 15)
	src.get_tile_data(Vector2i(3, 3), 0).probability = 0.60
	var soil_probs := [0.20, 0.12, 0.06, 0.02]
	for i in range(4):
		var coords := Vector2i(4 + i, 1)
		_apply_mask_terrains(src, coords, 15)
		src.get_tile_data(coords, 0).probability = soil_probs[i]

	# Silence unused
	src_id = src_id
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
	for x in range(8):
		src.create_tile(Vector2i(x, 0))
	ts.add_source(src, 0)
	return ts


static func _apply_mask_terrains(src: TileSetAtlasSource, coords: Vector2i, mask: int) -> void:
	## TL=1 TR=2 BR=4 BL=8 ; bit set => Soil, else Grass
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
	# Center terrain: majority / soil if any soil for connect API
	if mask == 15:
		td.terrain = TERRAIN_SOIL
	elif mask == 0:
		td.terrain = TERRAIN_GRASS
	else:
		# mixed: leave as grass center; peering bits drive edges
		td.terrain = TERRAIN_GRASS if _popcount(mask) < 2 else TERRAIN_SOIL


static func _popcount(v: int) -> int:
	var n := 0
	var x := v
	while x != 0:
		n += x & 1
		x >>= 1
	return n


static func _load_tex(path: String) -> Texture2D:
	if ResourceLoader.exists(path):
		var res := load(path)
		if res is Texture2D:
			return res as Texture2D
	var abs_path := ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(abs_path):
		var img := Image.new()
		if img.load(abs_path) == OK:
			return ImageTexture.create_from_image(img)
	push_warning("YardTerrainTilesetFactory: cannot load %s" % path)
	return null


static func save_ground_tileset(path: String = "res://resources/tilesets/yard_ground_tileset.tres") -> int:
	var ts := build_ground_tileset()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://resources/tilesets"))
	return ResourceSaver.save(ts, path)
