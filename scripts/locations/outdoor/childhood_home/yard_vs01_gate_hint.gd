extends Area2D
## Soft south-gate hint — world continues beyond the yard (no teleport yet).


func _ready() -> void:
	monitoring = true
	collision_layer = 0
	collision_mask = 1
	if not body_entered.is_connected(_on_body_entered):
		body_entered.connect(_on_body_entered)
	if not body_exited.is_connected(_on_body_exited):
		body_exited.connect(_on_body_exited)


func get_prompt() -> String:
	return "завал · дальше участок пока закрыт"


func interact(_actor: Node) -> void:
	## Intentionally no travel yet — VS01 stays on the childhood yard.
	pass


func _on_body_entered(body: Node) -> void:
	if body.has_method("register_nearby"):
		body.register_nearby(self)


func _on_body_exited(body: Node) -> void:
	if body.has_method("unregister_nearby"):
		body.unregister_nearby(self)
