extends Node
## Simple inventory for the MVP craft loop.

signal changed

var items: Dictionary = {} # id -> count


func _ready() -> void:
	# Soft start materials so the loop is reachable without grinding.
	pass


func count(item_id: String) -> int:
	return int(items.get(item_id, 0))


func has_item(item_id: String, amount: int = 1) -> bool:
	return count(item_id) >= amount


func add_item(item_id: String, amount: int = 1) -> void:
	items[item_id] = count(item_id) + amount
	changed.emit()


func remove_item(item_id: String, amount: int = 1) -> bool:
	if not has_item(item_id, amount):
		return false
	var next := count(item_id) - amount
	if next <= 0:
		items.erase(item_id)
	else:
		items[item_id] = next
	changed.emit()
	return true


func as_text() -> String:
	if items.is_empty():
		return "пусто"
	var parts: PackedStringArray = []
	for id in items.keys():
		parts.append("%s×%d" % [_label(id), items[id]])
	return ", ".join(parts)


func _label(item_id: String) -> String:
	match item_id:
		"scrap_metal":
			return "металлолом"
		"wood":
			return "дерево"
		"oven_door":
			return "дверца печи"
		_:
			return item_id
