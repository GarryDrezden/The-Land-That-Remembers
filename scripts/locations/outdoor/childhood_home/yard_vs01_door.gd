extends Area2D
## Door hotspot — enter childhood-home interior (stub: workshop indoor scene).

@export var target_location: String = "workshop"
@export var target_spawn: String = "workshop"


func _ready() -> void:
	monitoring = true
	collision_layer = 0
	collision_mask = 1
	if not body_entered.is_connected(_on_body_entered):
		body_entered.connect(_on_body_entered)
	if not body_exited.is_connected(_on_body_exited):
		body_exited.connect(_on_body_exited)


func get_prompt() -> String:
	return "войти в дом"


func interact(_actor: Node) -> void:
	WorldState.set_flag("entered_house", true)
	GameFlow.go_location(target_location, target_spawn)


func _on_body_entered(body: Node) -> void:
	if body.has_method("register_nearby"):
		body.register_nearby(self)


func _on_body_exited(body: Node) -> void:
	if body.has_method("unregister_nearby"):
		body.unregister_nearby(self)
