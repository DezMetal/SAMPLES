extends Node
class_name MovementComponent

@onready var target: Node = get_parent()
@onready var L: String = ""
@export var input_component: Node
@export var ground_speed_lerp_factor: float = 0.15
@export var move_type: String = 'topdown'

func _ready() -> void:
	var err: bool = false
	if not is_instance_valid(target):
		printerr("%s: Invalid target node." % name)
		set_process(false)
		return
	
	if not is_instance_valid(input_component) or not input_component is InputComponent:
		var found_input_component = target.get_node_or_null("InputComponent")
		if found_input_component is InputComponent:
			input_component = found_input_component
		else:
			printerr("%s: No valid InputComponent assigned or found in '%s'." % [name, target.name])
			err = true
			
	if is_instance_valid(input_component) and input_component is InputComponent:
		var ic: InputComponent = input_component as InputComponent
		ic.move_vector_changed.connect(_on_move_vector_changed)
		ic.jump_action_pressed.connect(_on_jump_action_pressed)
		ic.idle_state.connect(_on_idle_state)
	elif not err:
		printerr("%s: input_component is not a valid InputComponent on '%s'." % [name, target.name])
		err = true

	if target.has_method("get") and target.get("L") != null:
		target.L += "%s:%s: loaded" % [name, target.name if is_instance_valid(target) else "no_target"] + (" (ERRORS)" if err else "") + "\n"
	
	set_process(not err)


func _process(_delta: float) -> void:
	if not is_instance_valid(target) or not is_instance_valid(input_component):
		return

	if target.base_on_floor:
		var current_input_vector: Vector2 = (input_component as InputComponent).get_move_vector()
		var target_vx: float = current_input_vector.x * target.speed
		
		target.velocity.x = lerp(target.velocity.x, target_vx, ground_speed_lerp_factor)

		var target_vy: float = current_input_vector.y * target.speed
		target.velocity.y = lerp(target.velocity.y, target_vy, ground_speed_lerp_factor)
		
	target.move_and_slide()

	
func _on_move_vector_changed(new_vector: Vector2) -> void:
	if not is_instance_valid(target): return
	
	target.velocity.x = new_vector.x * target.speed 
	
	if target.base_on_floor:
		target.velocity.y = new_vector.y * target.speed

func _on_jump_action_pressed() -> void:
	if not is_instance_valid(target): return

	if target.base_on_floor and target.airtime == 0:
		var air_offset: float = 0.0
		var y_offset: float = target.get_process_delta_time() 
		var current_jump_velocity: Vector2 = target.jump_velocity
		
		if target.velocity.y > 0:
			air_offset = abs(current_jump_velocity.y) / 2.0
		elif target.velocity.y < 0:
			if move_type == 'topdown':
				y_offset = current_jump_velocity.y
			air_offset = abs(current_jump_velocity.y) / 2.0
	
		if target.velocity.x > 0:
			target.velocity.x += current_jump_velocity.x
		elif target.velocity.x < 0:
			target.velocity.x -= current_jump_velocity.x
		
		target.velocity.y = current_jump_velocity.y + y_offset
		target.airtime += (current_jump_velocity.y - air_offset) * 2.0


func _on_idle_state() -> void:
	if not is_instance_valid(target): return
	pass
