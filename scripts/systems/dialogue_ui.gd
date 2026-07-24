extends CanvasLayer
## Minimal dialogue UI driven by JSON + WorldState flags.

signal closed

@onready var panel: PanelContainer = $Panel
@onready var name_label: Label = $Panel/Margin/VBox/NameLabel
@onready var body_label: RichTextLabel = $Panel/Margin/VBox/BodyLabel
@onready var choices_box: VBoxContainer = $Panel/Margin/VBox/Choices

var _nodes: Dictionary = {}
var _current_id: String = ""
var _active: bool = false


func _ready() -> void:
	visible = false
	process_mode = Node.PROCESS_MODE_ALWAYS


func is_open() -> bool:
	return _active


func start(dialogue_path: String, start_node: String = "start") -> void:
	var file := FileAccess.open(dialogue_path, FileAccess.READ)
	if file == null:
		push_error("Dialogue not found: %s" % dialogue_path)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("Bad dialogue JSON: %s" % dialogue_path)
		return
	_nodes = parsed.get("nodes", {})
	_active = true
	visible = true
	get_tree().paused = true
	_show_node(start_node)


func _show_node(node_id: String) -> void:
	_current_id = node_id
	if not _nodes.has(node_id):
		end_dialogue()
		return
	var node: Dictionary = _nodes[node_id]
	# Conditional jump by WorldState flags
	if node.has("if_flag"):
		var flag: String = str(node["if_flag"])
		var expect: bool = bool(node.get("equals", true))
		if WorldState.has_flag(flag) == expect:
			_show_node(str(node.get("then", "end")))
			return
		_show_node(str(node.get("else", "end")))
		return

	name_label.text = str(node.get("speaker", ""))
	body_label.text = str(node.get("text", ""))

	for child in choices_box.get_children():
		child.queue_free()

	var choices: Array = node.get("choices", [])
	if choices.is_empty():
		var btn := Button.new()
		btn.text = "…"
		btn.pressed.connect(func() -> void: _advance(node))
		choices_box.add_child(btn)
	else:
		for choice in choices:
			var c: Dictionary = choice
			var btn := Button.new()
			btn.text = str(c.get("text", "…"))
			var next_id := str(c.get("next", "end"))
			var set_flag := str(c.get("set_flag", ""))
			var give_item := str(c.get("give_item", ""))
			btn.pressed.connect(func() -> void:
				if set_flag != "":
					WorldState.set_flag(set_flag, true)
				if give_item != "":
					Inventory.add_item(give_item, int(c.get("give_amount", 1)))
				if next_id == "end" or next_id == "":
					_apply_effects(node)
					end_dialogue()
				else:
					_show_node(next_id)
			)
			choices_box.add_child(btn)


func _advance(node: Dictionary) -> void:
	_apply_effects(node)
	var next_id := str(node.get("next", "end"))
	if next_id == "end" or next_id == "":
		end_dialogue()
	else:
		_show_node(next_id)


func _apply_effects(node: Dictionary) -> void:
	if node.has("set_flag"):
		WorldState.set_flag(str(node["set_flag"]), true)
	if node.has("give_item"):
		Inventory.add_item(str(node["give_item"]), int(node.get("give_amount", 1)))
	if node.has("advance_day"):
		WorldState.advance_day()


func end_dialogue() -> void:
	_active = false
	visible = false
	get_tree().paused = false
	closed.emit()


func _unhandled_input(event: InputEvent) -> void:
	if not _active:
		return
	if event.is_action_pressed("ui_cancel"):
		end_dialogue()
		get_viewport().set_input_as_handled()
