extends "res://scripts/world/interactable.gd"
## Bed advances the day — bakery "morning" after oven repair.


func _ready() -> void:
	super._ready()
	prompt_text = "лечь спать"


func interact(_actor: Node) -> void:
	WorldState.advance_day()
	if WorldState.has_flag("oven_repaired"):
		WorldState.set_flag("bakery_open", true)
		WorldState.set_flag("hint_bridge", true)
		DialogueUI.start("res://data/dialogues/bed.json", "morning_after")
	else:
		DialogueUI.start("res://data/dialogues/bed.json", "morning")
