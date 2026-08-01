# Third-Party Assets

Registry of external art/code used by *The Land That Remembers*.

**Catalog:** [docs/assets/START_HERE.md](assets/START_HERE.md) · machine registry: `data/assets/asset_packs.json`

**Inbox:** `upload/` is the permanent incoming asset drop folder. Do **not** delete, clear, rename, or move it wholesale. Originals are never overwritten by the catalog. Unpacked packs are catalogued; runtime integration happens only after explicit Asset ID selection.

---

## CraftPix — Main Character’s Home (Free Top-Down Pixel Art Asset)

| Field | Value |
|-------|-------|
| pack_id | `craftpix-main_characters_home` |
| Package | Main Character’s Home – Free Top-Down Pixel Art Asset |
| Publisher / author | CraftPix |
| Source | https://craftpix.net/freebies/main-characters-home-free-top-down-pixel-art-asset/ |
| Local path | `assets/third_party/craftpix/main_characters_home/` |
| Tile size | 16×16 (from embedded TMX tilesets) |
| Added | 2026-08-01 |
| Git storage allowed | **Yes** — project owner reports explicit permission |
| Commercial use | Yes (CraftPix freebie terms) |
| Modification | Yes |
| Attribution required | No (typical CraftPix freebie) |
| Owner confirmation | Explicit permission to store/publish in this Git repo |
| license_status | `reviewed` |
| Review status | under evaluation as outdoor/house base |

### Project usage

- Preview scene: `craftpix_home_preview.tscn`
- Audit: [CRAFTPIX_HOME_AUDIT.md](CRAFTPIX_HOME_AUDIT.md)
- Catalog pack page: [assets/catalog/packs/craftpix-main-characters-home/README.md](assets/catalog/packs/craftpix-main-characters-home/README.md)

### Not used as AI training data

Do not use these assets to generate new images for, or to train / improve, AI models.

---

## CraftPix — Free Top-Down Trees Pixel Art

| Field | Value |
|-------|-------|
| pack_id | `trees-pixel-art` |
| Source folder | `upload/trees-pixel-art/` |
| Author | CraftPix |
| License file | `upload/trees-pixel-art/License.txt` → https://craftpix.net/file-licenses/ |
| Git storage allowed | *pending owner confirmation for this pack* |
| Commercial use | Likely yes (CraftPix freebie — verify) |
| Modification | Likely yes — verify |
| Attribution required | Typically no — verify |
| Owner confirmation | not yet recorded |
| license_status | **`needs_review`** |
| Catalog status | available in inbox catalog only (not auto-promoted to runtime) |

---

## CraftPix — Free Top-Down Bushes Pixel Art

| Field | Value |
|-------|-------|
| pack_id | `bushes-pixel-art` |
| Source folder | `upload/bushes-pixel-art/` |
| Author | CraftPix |
| License URL | https://craftpix.net/file-licenses/ |
| Git storage allowed | *pending owner confirmation for this pack* |
| Commercial use | Likely yes — verify |
| Modification | Likely yes — verify |
| Attribution required | Typically no — verify |
| Owner confirmation | not yet recorded |
| license_status | **`needs_review`** |

---

## CraftPix — Free Rocks and Stones Top-Down Pixel Art

| Field | Value |
|-------|-------|
| pack_id | `rocks-and-stones-top-down-pixel-art` |
| Source folder | `upload/rocks-and-stones-top-down-pixel-art/` |
| Author | CraftPix |
| License URL | https://craftpix.net/file-licenses/ |
| Git storage allowed | *pending owner confirmation for this pack* |
| Commercial use | Likely yes — verify |
| Modification | Likely yes — verify |
| Attribution required | Typically no — verify |
| Owner confirmation | not yet recorded |
| license_status | **`needs_review`** |

---

## CraftPix — Top-Down Crystals Pixel Art

| Field | Value |
|-------|-------|
| pack_id | `crystals-pixel-art` |
| Source folder | `upload/crystals-pixel-art/` |
| Author | CraftPix |
| License URL | https://craftpix.net/file-licenses/ |
| Git storage allowed | *pending owner confirmation for this pack* |
| Commercial use | Likely yes — verify |
| Modification | Likely yes — verify |
| Attribution required | Typically no — verify |
| Owner confirmation | not yet recorded |
| license_status | **`needs_review`** |

---

## Notes

- Do **not** treat all CraftPix freebies as identical licenses without checking the pack page + License.txt.
- `license_status=needs_review` does not block cataloguing; it blocks promoting assets to `status=runtime` until confirmed.
- Zip archives under `upload/*.zip` remain gitignored; unpacked folders are tracked.
