extends "res://scripts/world/interactable.gd"
## Crafts oven door from scrap + wood.


func _ready() -> void:
	super._ready()
	prompt_text = "верстак"


func interact(actor: Node) -> void:
	if WorldState.has_flag("crafted_oven_door") or Inventory.has_item("oven_door"):
		DialogueUI.start("res://data/dialogues/workbench.json", "already")
		return
	if Inventory.has_item("scrap_metal") and Inventory.has_item("wood"):
		Inventory.remove_item("scrap_metal", 1)
		Inventory.remove_item("wood", 1)
		Inventory.add_item("oven_door", 1)
		WorldState.set_flag("crafted_oven_door", true)
		DialogueUI.start("res://data/dialogues/workbench.json", "crafted")
	else:
		DialogueUI.start("res://data/dialogues/workbench.json", "need_materials")
