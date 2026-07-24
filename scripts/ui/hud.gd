extends CanvasLayer
## HUD: day, inventory, short objective.


@onready var day_label: Label = $Root/DayLabel
@onready var inv_label: Label = $Root/InvLabel
@onready var obj_label: Label = $Root/ObjectiveLabel


func _ready() -> void:
	Inventory.changed.connect(_refresh)
	WorldState.flag_changed.connect(func(_f, _v): _refresh())
	_refresh()


func _refresh() -> void:
	day_label.text = "День %d" % WorldState.day
	inv_label.text = "Инвентарь: %s" % Inventory.as_text()
	obj_label.text = _objective()


func _objective() -> String:
	if WorldState.has_flag("hint_bridge"):
		return "Цель: пекарня снова жива. Дальше — мост… (конец слайса)"
	if WorldState.has_flag("oven_repaired"):
		return "Цель: лечь спать — увидеть утро у пекарни"
	if WorldState.has_flag("crafted_oven_door") or Inventory.has_item("oven_door"):
		return "Цель: установить дверцу в печь Софьи"
	if WorldState.has_flag("met_sofia"):
		return "Цель: собрать дерево и металлолом, сделать дверцу на верстаке"
	if WorldState.has_flag("met_petr"):
		return "Цель: поговорить с Софьей у пекарни"
	return "Цель: осмотреть мастерскую и поговорить с Петром"
