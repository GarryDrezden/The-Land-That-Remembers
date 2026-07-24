extends CharacterBody2D
## Top-down player for the settlement slice.

@export var speed: float = 180.0

@onready var prompt: Label = $Prompt
@onready var label: Label = $NameTag

var _nearby: Array[Node] = []


func _ready() -> void:
	prompt.visible = false
	label.text = "Вы"


func _physics_process(_delta: float) -> void:
	if DialogueUI.is_open():
		velocity = Vector2.ZERO
		move_and_slide()
		return

	var dir := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	# WASD aliases
	if Input.is_key_pressed(KEY_A):
		dir.x -= 1
	if Input.is_key_pressed(KEY_D):
		dir.x += 1
	if Input.is_key_pressed(KEY_W):
		dir.y -= 1
	if Input.is_key_pressed(KEY_S):
		dir.y += 1
	dir = dir.limit_length(1.0)
	velocity = dir * speed
	move_and_slide()

	_update_prompt()


func _unhandled_input(event: InputEvent) -> void:
	if DialogueUI.is_open():
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_E:
			_try_interact()
			get_viewport().set_input_as_handled()


func register_nearby(node: Node) -> void:
	if node not in _nearby:
		_nearby.append(node)
		_update_prompt()


func unregister_nearby(node: Node) -> void:
	_nearby.erase(node)
	_update_prompt()


func _update_prompt() -> void:
	var target := _current_target()
	if target == null:
		prompt.visible = false
		return
	prompt.visible = true
	if target.has_method("get_prompt"):
		prompt.text = "E — %s" % target.get_prompt()
	else:
		prompt.text = "E — взаимодействие"


func _current_target() -> Node:
	while not _nearby.is_empty() and not is_instance_valid(_nearby[0]):
		_nearby.pop_front()
	if _nearby.is_empty():
		return null
	return _nearby[0]


func _try_interact() -> void:
	var target := _current_target()
	if target and target.has_method("interact"):
		target.interact(self)
