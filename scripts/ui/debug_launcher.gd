extends Control
## Быстрый старт для разработчика: главы и состояния без интро.


func _ready() -> void:
	set_anchors_preset(PRESET_FULL_RECT)
	_build()


func _build() -> void:
	var bg := ColorRect.new()
	bg.color = Color("141A16")
	bg.set_anchors_preset(PRESET_FULL_RECT)
	add_child(bg)

	var title := Label.new()
	title.text = "Отладочный запуск"
	title.add_theme_color_override("font_color", Color("E8C07A"))
	title.add_theme_font_size_override("font_size", 28)
	title.position = Vector2(48, 32)
	add_child(title)

	var sub := Label.new()
	sub.text = "Режим разработчика · без меню, интро и анкеты"
	sub.add_theme_color_override("font_color", Color("8A9BB0"))
	sub.position = Vector2(48, 72)
	add_child(sub)

	var scroll := ScrollContainer.new()
	scroll.position = Vector2(48, 120)
	scroll.size = Vector2(520, 520)
	add_child(scroll)
	var list := VBoxContainer.new()
	list.add_theme_constant_override("separation", 8)
	scroll.add_child(list)

	for entry in ChapterPresets.titles():
		var id := str(entry["id"])
		var b := Button.new()
		b.text = str(entry["title"])
		b.custom_minimum_size = Vector2(480, 36)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.pressed.connect(func() -> void: GameFlow.apply_chapter(id))
		list.add_child(b)

	var side := VBoxContainer.new()
	side.position = Vector2(620, 120)
	side.custom_minimum_size = Vector2(460, 400)
	side.add_theme_constant_override("separation", 10)
	add_child(side)

	side.add_child(_btn("VS01 — двор дома детства", func() -> void:
		GameFlow.apply_chapter("vs01_childhood_home")
	))
	side.add_child(_btn("Открыть как игрок (главное меню)", func() -> void:
		GameFlow.set_developer_mode(false)
		GameFlow.go_main_menu()
	))
	side.add_child(_btn("Сразу в игру (мастерская)", func() -> void:
		GameFlow.apply_chapter("new_game")
	))
	side.add_child(_btn("Сбросить сохранение", func() -> void:
		WorldState.delete_save()
		Inventory.clear()
		PlayerProfile.reset()
	))

	var console_l := Label.new()
	console_l.text = "Консоль (заготовка)"
	console_l.add_theme_color_override("font_color", Color("E8C07A"))
	side.add_child(console_l)

	var console_in := LineEdit.new()
	console_in.placeholder_text = "помощь | восстановить пекарня | флаг oven_repaired да"
	console_in.custom_minimum_size = Vector2(460, 36)
	side.add_child(console_in)

	var console_out := Label.new()
	console_out.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	console_out.custom_minimum_size = Vector2(460, 120)
	console_out.add_theme_color_override("font_color", Color("A8B8A0"))
	side.add_child(console_out)

	console_in.text_submitted.connect(func(line: String) -> void:
		console_out.text = DevConsole.run_line(line)
		console_in.text = ""
	)

	var tip := Label.new()
	tip.text = "Мельница / Праздник / Дождь / Зима — появятся позже\nСейчас: главы, состояния пекарни и консоль"
	tip.add_theme_color_override("font_color", Color("8A9BB0"))
	tip.position = Vector2(48, 660)
	add_child(tip)


func _btn(text: String, action: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(460, 36)
	b.pressed.connect(action)
	return b
