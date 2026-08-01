# Asset Catalog

Owner-facing catalog of incoming and imported visual assets.

## How to use

1. Browse category pages or pack pages below (GitHub renders contact sheets).
2. Copy a stable **Asset ID**.
3. Tell Cursor which IDs to use in which area.

Example:

> For the north edge of `yard_main` use `TREE_TREES_PIXEL_ART_004` and `BUSH_BUSHES_PIXEL_ART_012`.

Selections are recorded in [`AREA_ASSET_SELECTIONS.md`](AREA_ASSET_SELECTIONS.md)
and `data/assets/area_asset_selections.json` (not wired to gameplay yet).

## Update catalog

```bash
python tools/build_asset_catalog.py
python tools/build_asset_catalog.py --check
```

`res://upload/` is the **permanent INBOX** — never delete it. New packs dropped there are picked up on the next catalog run.

## Stats

- Packs (unpacked): **5**
- Zip-only inbox entries (not expanded): **4**
- Image assets: **677**
- Categories present: animal, bush, crystal, effect, house, interior, rock, terrain, tree

## Categories

- [Trees](catalog/trees.md)
- [Bushes](catalog/bushes.md)
- [Rocks](catalog/rocks.md)
- [Terrain](catalog/terrain.md)
- [Houses](catalog/houses.md)
- [Props](catalog/props.md)
- [Characters](catalog/characters.md)
- [Water](catalog/water.md)
- [Unknown](catalog/unknown.md)

## Packs

- [bushes-pixel-art](catalog/packs/bushes-pixel-art/README.md)
- [crystals-pixel-art](catalog/packs/crystals-pixel-art/README.md)
- [rocks-and-stones-top-down-pixel-art](catalog/packs/rocks-and-stones-top-down-pixel-art/README.md)
- [trees-pixel-art](catalog/packs/trees-pixel-art/README.md)
- [craftpix-main-characters-home](catalog/packs/craftpix-main-characters-home/README.md)

## Machine-readable registry

- `data/assets/asset_catalog.json`
- `data/assets/asset_packs.json`
- `data/assets/asset_catalog_overrides.json`
- `data/assets/area_asset_selections.json`

## Debug gallery (Godot)

- Scene: `scenes/debug/asset_gallery.tscn`
