extends Area2D
## Door hotspot for VS01 yard — interior not opened yet.


func _ready() -> void:
	monitoring = true
	if not body_entered.is_connected(_on_body_entered):
		body_entered.connect(_on_body_entered)
	if not body_exited.is_connected(_on_body_exited):
		body_exited.connect(_on_body_exited)


func get_prompt() -> String:
	return "дверь — пока закрыта"


func interact(_actor: Node) -> void:
	# Vertical slice: outdoor only; house interior comes later.
	pass


func _on_body_entered(body: Node) -> void:
	if body.has_method("register_nearby"):
		body.register_nearby(self)


func _on_body_exited(body: Node) -> void:
	if body.has_method("unregister_nearby"):
		body.unregister_nearby(self)
