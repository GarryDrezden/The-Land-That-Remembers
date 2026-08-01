extends Control
## Debug Asset Gallery — browse catalogued assets by category/pack.
## Not part of the main game flow. F6 / open this scene to inspect Asset IDs.

const CATALOG_PATH := "res://data/assets/asset_catalog.json"
const PREVIEW_ROOT := "res://docs/assets/catalog/previews/"
const VIEW_W := 960
const VIEW_H := 540

var _assets: Array = []
var _filtered: Array = []
var _category := "all"
var _pack := "all"
var _status: Label
var _grid: GridContainer
var _scroll: ScrollContainer
var _cat_option: OptionButton
var _pack_option: OptionButton
var _detail: Label


func _ready() -> void:
	name = "AssetGallery"
	set_anchors_preset(Control.PRESET_FULL_RECT)
	DisplayServer.window_set_size(Vector2i(VIEW_W, VIEW_H))
	_build_ui()
	_load_catalog()
	_rebuild_filters()
	_apply_filter()
	var shot := OS.get_environment("ART_TEST_SHOT")
	if shot != "":
		await get_tree().process_frame
		await get_tree().create_timer(0.4).timeout
		var img := get_viewport().get_texture().get_image()
		if img:
			var path := ProjectSettings.globalize_path("res://docs/art_tests/asset_gallery.png")
			img.save_png(path)
			print("asset gallery screenshot -> ", path)
		get_tree().quit()


func _build_ui() -> void:
	var root := VBoxContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override("separation", 6)
	add_child(root)

	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 8)
	root.add_child(top)

	var title := Label.new()
	title.text = "Asset Gallery (debug)"
	title.add_theme_font_size_override("font_size", 16)
	top.add_child(title)

	_cat_option = OptionButton.new()
	_cat_option.item_selected.connect(func(i: int) -> void:
		_category = str(_cat_option.get_item_text(i))
		_apply_filter()
	)
	top.add_child(_cat_option)

	_pack_option = OptionButton.new()
	_pack_option.item_selected.connect(func(i: int) -> void:
		_pack = str(_pack_option.get_item_text(i))
		_apply_filter()
	)
	top.add_child(_pack_option)

	_status = Label.new()
	_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(_status)

	_detail = Label.new()
	_detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_detail.custom_minimum_size = Vector2(0, 48)
	root.add_child(_detail)

	_scroll = ScrollContainer.new()
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root.add_child(_scroll)

	_grid = GridContainer.new()
	_grid.columns = 5
	_grid.add_theme_constant_override("h_separation", 8)
	_grid.add_theme_constant_override("v_separation", 8)
	_scroll.add_child(_grid)


func _load_catalog() -> void:
	_assets.clear()
	if not FileAccess.file_exists(CATALOG_PATH):
		_status.text = "Missing catalog JSON. Run: python tools/build_asset_catalog.py"
		return
	var f := FileAccess.open(CATALOG_PATH, FileAccess.READ)
	var data = JSON.parse_string(f.get_as_text())
	if typeof(data) != TYPE_DICTIONARY:
		_status.text = "Invalid asset_catalog.json"
		return
	var arr: Array = data.get("assets", [])
	for item in arr:
		if typeof(item) != TYPE_DICTIONARY:
			continue
		if str(item.get("status", "")) == "missing":
			continue
		if item.get("preview_path") == null:
			continue
		_assets.append(item)
	_status.text = "%d catalogued assets with previews" % _assets.size()


func _rebuild_filters() -> void:
	var cats := {"all": true}
	var packs := {"all": true}
	for a in _assets:
		cats[str(a.get("category", "unknown"))] = true
		packs[str(a.get("pack_id", "unknown"))] = true
	_cat_option.clear()
	_pack_option.clear()
	var cat_list: Array = cats.keys()
	cat_list.sort()
	var pack_list: Array = packs.keys()
	pack_list.sort()
	for c in cat_list:
		_cat_option.add_item(str(c))
	for p in pack_list:
		_pack_option.add_item(str(p))
	_category = "all"
	_pack = "all"


func _apply_filter() -> void:
	_filtered.clear()
	for a in _assets:
		if _category != "all" and str(a.get("category")) != _category:
			continue
		if _pack != "all" and str(a.get("pack_id")) != _pack:
			continue
		_filtered.append(a)
	_status.text = "Showing %d / %d" % [_filtered.size(), _assets.size()]
	_rebuild_grid()


func _rebuild_grid() -> void:
	for child in _grid.get_children():
		child.queue_free()
	var limit := mini(120, _filtered.size())
	for i in range(limit):
		var a: Dictionary = _filtered[i]
		_grid.add_child(_make_card(a))
	if _filtered.size() > limit:
		var more := Label.new()
		more.text = "… +%d more (narrow filters)" % (_filtered.size() - limit)
		_grid.add_child(more)


func _make_card(a: Dictionary) -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(160, 190)
	var vb := VBoxContainer.new()
	panel.add_child(vb)

	var tex_rect := TextureRect.new()
	tex_rect.custom_minimum_size = Vector2(140, 120)
	tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tex_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	var preview_path := str(a.get("preview_path", ""))
	var res_path := preview_path
	if res_path.begins_with("docs/"):
		res_path = "res://" + res_path
	var tex := _load_tex(res_path)
	if tex:
		tex_rect.texture = tex
	vb.add_child(tex_rect)

	var id_lab := Label.new()
	id_lab.text = str(a.get("asset_id", "?"))
	id_lab.add_theme_font_size_override("font_size", 10)
	id_lab.autowrap_mode = TextServer.AUTOWRAP_OFF
	id_lab.clip_text = true
	vb.add_child(id_lab)

	var btn := Button.new()
	btn.text = "Copy ID"
	btn.pressed.connect(func() -> void:
		DisplayServer.clipboard_set(str(a.get("asset_id", "")))
		_detail.text = "Copied %s | %s | %sx%s | %s" % [
			str(a.get("asset_id")),
			str(a.get("pack_id")),
			str(a.get("width")),
			str(a.get("height")),
			str(a.get("source_path")),
		]
	)
	vb.add_child(btn)

	panel.gui_input.connect(func(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			DisplayServer.clipboard_set(str(a.get("asset_id", "")))
			_detail.text = "Copied %s | %s | %sx%s | %s" % [
				str(a.get("asset_id")),
				str(a.get("pack_id")),
				str(a.get("width")),
				str(a.get("height")),
				str(a.get("source_path")),
			]
	)
	return panel


func _load_tex(path: String) -> Texture2D:
	var abs_path := ProjectSettings.globalize_path(path)
	if FileAccess.file_exists(abs_path):
		var img := Image.new()
		if img.load(abs_path) == OK:
			return ImageTexture.create_from_image(img)
	if ResourceLoader.exists(path):
		var res := load(path)
		if res is Texture2D:
			return res as Texture2D
	return null
