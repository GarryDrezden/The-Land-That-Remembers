extends "res://scripts/world/interactable.gd"
## Pickup piles for scrap / wood without a mine.

@export var item_id: String = "scrap_metal"
@export var amount: int = 1
@export var once_flag: String = ""
@export var dialogue_got: String = "res://data/dialogues/pickup.json"


func _ready() -> void:
	super._ready()
	_refresh()
	if not WorldState.flag_changed.is_connected(_on_flag):
		WorldState.flag_changed.connect(_on_flag)


func _on_flag(flag: String, _v: Variant) -> void:
	if flag == once_flag or flag == "*":
		_refresh()


func _refresh() -> void:
	if once_flag != "" and WorldState.has_flag(once_flag):
		visible = false
		monitoring = false
	else:
		visible = true
		monitoring = true


func interact(actor: Node) -> void:
	if once_flag != "" and WorldState.has_flag(once_flag):
		return
	Inventory.add_item(item_id, amount)
	if once_flag != "":
		WorldState.set_flag(once_flag, true)
	DialogueUI.start(dialogue_got, item_id)
	_refresh()
