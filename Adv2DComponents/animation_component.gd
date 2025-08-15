extends AnimationPlayer
class_name AnimationComponent

# enable logging component by `target.L += *message*`
@onready var L: String = ""
@onready var target: Node = get_parent()
@onready var current_state: String = "idle"
@onready var is_moving: bool = false
@onready var dir = 'down'
@onready var last_dir = 'down'
@export var input_controller: Node
@export var target_sprite: AnimatedSprite2D
@export var animation_map: Dictionary = {
	"move": {
		"left": "walkL",
		"right": "walkR",
		"up": "walkF",
		"down": "walkB"
	},
	"idle": {
		"left": "",
		"right": "",
		"up": "",
		"down": ""
	}
}


func _ready() -> void:
	var err = false

	if not target:
		err = true
		printerr('AnimationComponent: no target found')
		return

	if not input_controller:
		err = true
		printerr('AnimationComponent: target %s has no controller' % target.name)
		return
	
	if not target_sprite or not target_sprite.has_method("play"):
		err = true
		printerr('AnimationComponent: target %s lacks a valid target_sprite node with play() method at path "target_sprite".' % target.name)
		return # Stop processing if we can't animate

	target.L += '%s:%s: loaded\n'%[name, target.name] + (' still..' if err else '')
	set_process(!err)
	# Play initial animation state (likely stops if idle anims are "")
	play_animation()

func _process(delta: float) -> void:
	# Determine state and direction based on controller input
	var v = input_controller.get_move_vector()
	is_moving = (v != Vector2.ZERO)

	var new_dir = dir # Keep current direction if no input

	if is_moving:
		current_state = 'move'
		# Determine direction based on largest component
		if abs(v.x) > abs(v.y):
			new_dir = "left" if v.x < 0 else "right"
		elif v.y != 0: # Prioritize vertical if horizontal is zero or equal
			new_dir = "up" if v.y < 0 else "down"

		# Update direction only if it changed
		if new_dir != dir:
			last_dir = dir
			dir = new_dir

	else:
		current_state = 'idle'

	play_animation()


func play_animation():
	# Ensure target_sprite is valid before proceeding
	if not target_sprite:
		# printerr("play_animation: target_sprite is null!") # Optional debug
		return

	var state_map = animation_map.get(current_state)

	# Stop if the current_state (e.g., "idle", "move") is not found in the map
	if not state_map:
		if target_sprite.is_playing():
			target_sprite.stop()
		return

	var anim_name = state_map.get(dir)

	# Stop if the animation name for the current state/direction is missing (null) or empty ""
	# This handles the 'idle' state correctly if its animations are defined as "" in the map.
	if not anim_name or anim_name == "":
		if target_sprite.is_playing():
			target_sprite.stop()
		return

	# --- We have a valid, non-empty anim_name to play ---

	# Check if the correct animation is already playing to avoid restarting it
	if target_sprite.is_playing() and target_sprite.animation == anim_name:
		# Already playing the right one, let it continue (important for looping)
		# Optionally, you could adjust speed here if needed, but often not necessary
		# var speed = speed_scale if current_state == "move" else 1.0
		# if abs(target_sprite.get_playing_speed() - speed) > 0.01: # Check Godot version for exact speed method
		#     target_sprite.play(anim_name, -1, speed) # Adjust speed if different
		return
	else:
		# Play the new animation or restart the correct one if it was stopped/different
		var speed = speed_scale if current_state == "move" else 1.0
		# print("Playing: %s" % anim_name) # Debugging print
		# Use the appropriate method on target_sprite (assuming it's AnimatedSprite2D or similar)
		target_sprite.play(anim_name, -1, speed) # Use this if target_sprite is another AnimationPlayer
