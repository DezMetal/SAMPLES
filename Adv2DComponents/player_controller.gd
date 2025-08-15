extends CharacterBody2D
class_name PlayerController

@onready var L: String = ""
@onready var base_on_floor: bool = true
@onready var airtime: int = 0
@onready var current_movement_state: String = "idle"
@export var base_cast: RayCast2D
@export var title: String = 'Player Controller'
@export var speed: float = 200.0
@export var jump_velocity: Vector2 = Vector2(800, -800)
@export var ttl: int = 5000

var last: Vector2

func _ready() -> void:
	var err = false
	if not base_cast:
		print('PlayerController has no `base_cast:RayCast2D`')
		err = true
		
	L += '%s:%s: loaded\n'%[name, title] + (' still..' if err else '')

func _on_death() -> void:
	print('AAHHHHHHHHH')
	get_tree().reload_current_scene()
