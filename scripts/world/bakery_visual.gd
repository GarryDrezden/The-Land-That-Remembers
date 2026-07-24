extends Node2D
## Switches bakery visuals when oven_repaired / bakery_open.

@onready var cold_window: ColorRect = $ColdWindow
@onready var warm_window: ColorRect = $WarmWindow
@onready var closed_sign: Label = $ClosedSign
@onready var open_sign: Label = $OpenSign
@onready var crowd: Node2D = $Crowd


func _ready() -> void:
	WorldState.flag_changed.connect(_on_flag)
	_apply()


func _on_flag(_flag: String, _value: Variant) -> void:
	_apply()


func _apply() -> void:
	var fixed := WorldState.has_flag("oven_repaired")
	var open := WorldState.has_flag("bakery_open")
	cold_window.visible = not fixed
	warm_window.visible = fixed
	closed_sign.visible = not open
	open_sign.visible = open
	crowd.visible = open
