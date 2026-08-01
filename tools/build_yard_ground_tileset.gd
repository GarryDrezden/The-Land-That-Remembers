extends SceneTree
## Headless: build and save yard_ground_tileset.tres
## godot --headless --script res://tools/build_yard_ground_tileset.gd

const YardTerrainTilesetFactory = preload("res://scripts/tilesets/yard_terrain_tileset_factory.gd")


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	await process_frame
	var err := YardTerrainTilesetFactory.save_ground_tileset()
	print("save yard_ground_tileset.tres -> ", err)
	quit(err)
