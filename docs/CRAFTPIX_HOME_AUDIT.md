# CraftPix Home Asset Audit

## Source

| Field | Value |
|-------|-------|
| Name | **Main Character’s Home – Free Top-Down Pixel Art Asset** |
| Publisher | CraftPix |
| Official page | https://craftpix.net/freebies/main-characters-home-free-top-down-pixel-art-asset/ |
| Also listed | https://free-game-assets.itch.io/main-characters-home-free-top-down-pixel-art-asset |
| Downloaded into | `upload/` (later moved to `assets/third_party/craftpix/main_characters_home/`) |
| Audit date | 2026-08-01 |
| License type | CraftPix freebie / royalty-free usage (see [THIRD_PARTY_ASSETS.md](THIRD_PARTY_ASSETS.md)) |

## License Summary

- Commercial use allowed (CraftPix freebie terms).
- Modification allowed.
- Use in a finished game allowed.
- Attribution not required by CraftPix freebie wording (still credit in THIRD_PARTY_ASSETS).
- Public redistribution of raw reusable asset packages is restricted by CraftPix terms in general.
- **Project owner reports that explicit permission was obtained to store and publish the asset source files in this project’s Git repository.**
- Files remain third-party licensed assets (not public domain).

## Package Structure

Original archive top-level (after removing `__MACOSX`):

```
PNG/           — standalone sheets
PSD/           — editable sources (not Godot runtime)
Tiled_files/   — TMX demos + atlas PNGs sized for Tiled
*.zip          — original download archive
```

### PNG/ (standalone)

| File | Size | Alpha |
|------|------|-------|
| `bird_fly_animation.png` | 432×1024 | yes |
| `bird_jump_animation.png` | 640×96 | yes |
| `cat_animation.png` | 96×576 | yes |
| `exterior.png` | 240×800 | yes |
| `ground_grass_details.png` | 336×288 | yes |
| `house_details.png` | 160×272 | yes |
| `Interior.png` | 192×400 | yes |
| `Smoke_animation.png` | 288×48 | yes |
| `Trees_animation.png` | 576×1040 | yes |
| `walls_floor.png` | 144×176 | yes |

### Tiled_files/ (authoritative for Godot / Tiled)

| File | Size | Role |
|------|------|------|
| `Exterior.tmx` | map demo outdoor | **primary demo map** |
| `Exterior — … .tmx` | outdoor variant / denser | demo |
| `Interior1.tmx` | interior demo | demo |
| `ground_grass_details.png` | 336×288 | terrain / grass details atlas |
| `exterior.png` | 272×912 | outdoor terrain + props + paths |
| `house_details.png` | 160×272 | house walls/roof pieces |
| `Doors_windows_animation.png` | 272×192 | doors/windows anim |
| `Smoke_animation.png` | 288×48 | chimney smoke |
| `Trees_animation.png` | 576×1040 | tree animation sheet |
| `bird_*.png`, `cat_animation.png` | — | creature anims |
| `Interior.png` | 224×432 | interior furniture/walls |
| `walls_floor.png` | 176×256 | interior floors/walls |

> Tiled atlases are often **larger** than `PNG/` counterparts (padding for 16px grid). Prefer **Tiled_files** atlases for runtime.

### PSD/

Artistic sources only (`exterior.psd`, `Interior.psd`, `ground_grass_details.psd`, animations…). **Not imported** as Godot runtime textures.

## Technical Properties

| Property | Value (from TMX) |
|----------|------------------|
| **Tile size** | **16×16** (`tilewidth`/`tileheight` on all TMX maps) |
| Orientation | orthogonal |
| Demo map size | 16×24 base, `infinite=1` with CSV chunks |
| Separate `.tsx` | **none** — tilesets are **embedded** in TMX |
| Margin / spacing | **0** (implicit; image width divisible by 16) |
| Wang / terrain sets | **not present** |
| Object collisions in TMX | **none** (tile layers only) |
| Animations | yes — smoke, doors/windows, birds, cat, trees (tile `<animation>` in embedded tilesets) |
| Ready demo maps | **yes** — `Exterior.tmx`, interior `Interior1.tmx` |

### Atlas notes (Tiled_files)

| Atlas | Columns (TMX) | Approx content |
|-------|---------------|----------------|
| `ground_grass_details` | 21 | grass tufts, flowers, soil spots, clutter overlays |
| `exterior` | 17 | ground fills, paths/plates, fences, outdoor props, vegetation pieces |
| `house_details` | 10 | house wall/roof modules |
| `Trees_animation` | 36 | multi-tile tree frames |
| `Doors_windows_animation` | 17 | animated openings |
| `walls_floor` / `Interior` | 11 / 14 | interior |

## Content Coverage

| Category | Present? | Notes |
|----------|----------|-------|
| Terrain / grass / dirt / path | **yes** | via `exterior` + `ground_grass_details` layers (Ground, Road, Plates, Grass*) |
| Water / shore | **not seen** in Exterior demo layers | may be absent from free set |
| House exterior | **yes** | House_wall / House_roof / windows |
| House interior | **yes** | `Interior1.tmx` + Interior / walls_floor |
| Furniture | **yes** | interior objects layers |
| Vegetation | **yes** | Trees_animation + exterior props |
| Rocks / fences / garden props | **yes** | Fence, Objects* layers |
| Characters (human) | **no** | only **cat** + **birds** |
| Complete demo maps | **yes** | Exterior + Interior TMX |

## Recommended Files (first outdoor art test)

Runtime copies live under:

`assets/third_party/craftpix/main_characters_home/runtime/`

| Use | Path |
|-----|------|
| Terrain / grass details | `runtime/terrain/ground_grass_details.png` |
| Outdoor ground/props/paths | `runtime/buildings/exterior.png` *(name historical; used as outdoor atlas)* |
| House | `runtime/buildings/house_details.png` |
| Doors/windows | `runtime/buildings/Doors_windows_animation.png` |
| Trees | `runtime/vegetation/Trees_animation.png` |
| Layout seed | `runtime/preview/exterior_preview_layout.json` (crop of `Exterior.tmx`) |
| Author map | `source/Tiled_files/Exterior.tmx` |

## Preview scene

- Scene: `scenes/locations/outdoor/childhood_home/craftpix_home_preview.tscn`
- Script: `scripts/debug/craftpix_home_preview.gd`
- Rebuild helper: `tools/organize_craftpix_home.py`
- Screenshots: `docs/art_tests/craftpix_home_preview*.png`
- Tiled crop reference: `docs/art_tests/craftpix_tiled_exterior_reference.png`

## Risks

- **No human player character** — need a separate compatible 16×16 top-down character pack.
- **No Wang/Terrain Set** — transitions are **hand-authored tile placements** in Tiled, not Godot Match Corners autotile.
- Some TMX tilesets reference **external** images (`../../animation.png`, etc.) **not included** in the free folder — ignored.
- `PNG/` vs `Tiled_files/` atlas sizes differ — mixing them breaks atlas coords.
- Collision must be authored in Godot (TMX has no object collisions).
- Dense Object layers can make automated blockers too aggressive — tune for GameRoot later.

## Evaluation (pending art review)

Suitable as a **candidate primary outdoor + house base** for the childhood-home yard: cohesive style, 16×16, rich props, author demo map.

Still under evaluation — see DEC entry in [DECISIONS.md](DECISIONS.md).
