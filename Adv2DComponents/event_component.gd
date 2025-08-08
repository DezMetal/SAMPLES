extends CollisionObject2D

class_name EventComponent

@onready var t: int = 0
const triggers: Dictionary = {0:'hover', 1:'action', 2:'condition'}


# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	pass # Replace with function body.


# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass
	
func _do_action():
	print('action triggered!')
