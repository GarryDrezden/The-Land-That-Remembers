extends Node2D
## Visual orchard tree candidate — stable object_id + future state contract.
## No harvest / prune / treat gameplay yet (roadmap only).

## Future states (documented contract — not all implemented):
## neglected | cleared | pruned | treated | flowering | fruiting |
## exhausted_or_diseased | removed

@export var object_id: String = ""
@export var species: String = "apple" ## apple | pear | plum | cherry | other
@export var tree_state: String = "neglected"
@export var zone_id: String = "old_orchard"


func _ready() -> void:
	if object_id == "":
		object_id = "fruit_%s_%d_%d" % [species, int(position.x), int(position.y)]
	set_meta("object_id", object_id)
	set_meta("species", species)
	set_meta("tree_state", tree_state)
	set_meta("zone_id", zone_id)
