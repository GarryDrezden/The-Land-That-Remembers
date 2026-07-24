extends "res://scripts/world/interactable.gd"
## Sofia's oven — repair closes the vertical slice loop.


func _ready() -> void:
	super._ready()
	_refresh_prompt()
	if not WorldState.flag_changed.is_connected(_on_flag_changed):
		WorldState.flag_changed.connect(_on_flag_changed)


func _on_flag_changed(flag: String, _value: Variant) -> void:
	if flag == "oven_repaired" or flag == "*":
		_refresh_prompt()


func _refresh_prompt() -> void:
	if WorldState.has_flag("oven_repaired"):
		prompt_text = "работающая печь"
	else:
		prompt_text = "сломанная печь"


func interact(actor: Node) -> void:
	if WorldState.has_flag("oven_repaired"):
		DialogueUI.start("res://data/dialogues/oven.json", "fixed")
		return
	if Inventory.has_item("oven_door"):
		Inventory.remove_item("oven_door", 1)
		WorldState.set_flag("oven_repaired", true)
		WorldState.set_flag("bakery_open", true)
		DialogueUI.start("res://data/dialogues/oven.json", "repaired")
	else:
		DialogueUI.start("res://data/dialogues/oven.json", "broken")
