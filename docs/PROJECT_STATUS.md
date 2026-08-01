# PROJECT STATUS

Обновлено: 2026-08-01 (Asset Catalog)

## Кратко

- **Asset Catalog** онлайн: inbox `upload/` + registry `data/assets/` + GitHub pages `docs/assets/`.  
- Команда: `python tools/build_asset_catalog.py` (`--check` для актуальности).  
- CraftPix home preview остаётся under evaluation; **не** перестраивался в этом шаге.  
- **Стоп:** не внедрять AREA selections в gameplay / GameRoot / основной двор без явного выбора владельца.

## Следующее

1. Владелец просматривает contact sheets и подтверждает лицензии packs с `needs_review`.  
2. Заполняет `docs/assets/AREA_ASSET_SELECTIONS.md` Asset ID.  
3. Только после этого — подготовка selected assets в `assets/third_party/.../runtime/`.
