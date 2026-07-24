extends Area2D
## Base interactable: NPC, workbench, oven, scrap pile, bed.

@export var prompt_text: String = "осмотреть"
@export var dialogue_path: String = ""
@export var dialogue_start: String = "start"

signal interacted(actor: Node)


func _ready() -> void:
	if not body_entered.is_connected(_on_body_entered):
		body_entered.connect(_on_body_entered)
	if not body_exited.is_connected(_on_body_exited):
		body_exited.connect(_on_body_exited)


func get_prompt() -> String:
	return prompt_text


func interact(actor: Node) -> void:
	interacted.emit(actor)
	if dialogue_path != "":
		DialogueUI.start(dialogue_path, dialogue_start)


func _on_body_entered(body: Node) -> void:
	if body.has_method("register_nearby"):
		body.register_nearby(self)


func _on_body_exited(body: Node) -> void:
	if body.has_method("unregister_nearby"):
		body.unregister_nearby(self)
