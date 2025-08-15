# InputComponent.gd
extends Node
class_name InputComponent

signal move_vector_changed(move_vector: Vector2)
signal jump_action_pressed
signal action_key_pressed
signal idle_state
# Add other actions as needed

# Configuration
@onready var L: String = ""
@onready var target: Node = get_parent()
@onready var current_vector: Vector2 = Vector2.ZERO
@onready var is_idle: bool = true
@export var move_left_action: String = "ui_left"
@export var move_right_action: String = "ui_right"
@export var move_up_action: String = "ui_up"
@export var move_down_action: String = "ui_down"
@export var jump_action: String = "ui_accept"
@export var action_key: String = "ui_select"

func _ready() -> void:
	var err = false
	current_vector = target.velocity
	L += '%s:%s: loaded\n'%[name, target.name] + (' still..' if err else '')

func _process(_delta: float) -> void:
	var new_vector := Input.get_vector(move_left_action, move_right_action, move_up_action, move_down_action)
	
	if new_vector != current_vector:
		current_vector = new_vector
		move_vector_changed.emit(current_vector)

	# Input and State Emissions
	if Input.is_anything_pressed():
		is_idle = false
		if Input.is_action_just_pressed(jump_action):
			jump_action_pressed.emit()
			
		if Input.is_action_just_pressed(action_key):
			action_key_pressed.emit()
	else:
		is_idle = true
		idle_state.emit()

# Method for other components to get the current input directly
func get_move_vector() -> Vector2:
	return current_vector
