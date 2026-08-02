extends Area2D
## Inactive future portal: childhood_home_yard ↔ village_street.
## No travel / NPC / street scene yet — marker + prompt only.

const TARGET_LOCATION := "village_street"

var _player_inside := false
var _prompt: Label


func _ready() -> void:
	monitoring = true
	collision_layer = 0
	collision_mask = 1
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)
	set_meta("portal_target", TARGET_LOCATION)
	set_meta("portal_active", false)


func bind_prompt(lab: Label) -> void:
	_prompt = lab


func _on_body_entered(body: Node) -> void:
	if body.is_in_group("player") or body.name.begins_with("Player"):
		_player_inside = true
		if _prompt:
			_prompt.visible = true
			_prompt.text = "улица деревни · позже"


func _on_body_exited(body: Node) -> void:
	if body.is_in_group("player") or body.name.begins_with("Player"):
		_player_inside = false
		if _prompt:
			_prompt.visible = false


func interact(_actor: Node) -> void:
	## Reserved — do not travel yet.
	pass
