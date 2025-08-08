extends Node
class_name BaseChar2DArchetype

@export var data: Dictionary = {
	# Parameters for PlayerController (the PSMComponent's target)
	"title": "Player A",
	"scale": Vector2(3, 3),
	"speed": 400.0,
	"jump_velocity": Vector2(800, -800),
	"airtime": 0, # Initial value
	"ttl": 50,
	"current_movement_state": "idle",

	"PhysicsComponent": {
		"gravity": 5001.0,
		"modifier": 1.0
	},

	"InputComponent": {
		"move_left_action": "ui_left",
		"move_right_action": "ui_right",
		"move_up_action": "ui_up",
		"move_down_action": "ui_down",
		"jump_action": "ui_accept",
		"action_key": "ui_select"
	},

	"AnimationComponent": {
		"speed_scale": 1.0,
		"animation_map": {
			"move": {
				"left": "walkL",
				"right": "walkR",
				"up": "walkF",
				"down": "walkB"
			},
			"idle": { # Empty strings mean the animation will stop for these states/directions
				"left": "",
				"right": "",
				"up": "",
				"down": ""
			}
		}
	}
	# MovementComponent does not have direct @export vars to configure in this manner;
	# it uses properties from its target (PlayerController), which are set above.
}

func _ready() -> void:
	var scene_root: Node = get_parent()
	if not is_instance_valid(scene_root):
		return

	if scene_root.has_meta("L") or (scene_root.get_script() and "L" in scene_root.get_script().get_script_property_list()):
		var log_msg_base: String = "%s (%s): loaded\n" % [name, get_class()]
		if not data.is_empty():
			log_msg_base += "Provides %s parameters in its 'data' dictionary." % data.size()
		else:
			log_msg_base += "No parameters defined in its 'data' dictionary."
		scene_root.L += log_msg_base + "\n"
