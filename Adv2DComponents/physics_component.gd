# PhysicsComponent.gd
extends Node
class_name PhysicsComponent

@onready var target: Node = get_parent()
@onready var L: String = ""
@export var gravity: float = 5000.0
@export var modifier: float = 1.0
@export var base_type: String = "TileMapLayer"
@export var death_on_ttl: bool = false

var last_vel: Vector2
var _was_on_floor: bool = false

func _ready() -> void:
	if not is_instance_valid(target):
		printerr("%s: Target node is not valid at _ready()." % name)
		set_process(false)
		return
	
	if target.has_method("get") and target.get("base_on_floor") != null:
		_was_on_floor = target.get("base_on_floor")
		target.base_on_floor = _was_on_floor
	else:
		target.base_on_floor = false
		_was_on_floor = false

	if target.has_method("get") and target.get("L") != null:
		target.L += '%s:%s: loaded\n'%[name, target.name] # Removed unused 'err'
	
	if target.has_method("get") and target.get("velocity") != null:
		last_vel = target.velocity
	else:
		if target.has_method("set"):
			target.set("velocity", Vector2.ZERO)
		last_vel = Vector2.ZERO


func _physics_process(delta: float) -> void:
	if not is_instance_valid(target): return

	if target.has_method("get") and target.get("velocity") != null and last_vel != target.velocity:
		last_vel = target.velocity
		print('airtime: ', target.airtime, ' | velocity: ', target.velocity)

	_was_on_floor = target.base_on_floor 
	var on_sync_plat: bool = false 
	
	target.base_on_floor = false

	if is_instance_valid(target.base_cast) and target.base_cast.is_colliding():
		var collider = target.base_cast.get_collider()
		
		if is_instance_valid(collider):
			var can_sync = collider.get("sync") if collider.has_method("get") else null
			var plat_vel = collider.get("velocity") if collider.has_method("get") else null

			if can_sync == true and plat_vel is Vector2: # Simplified condition
				on_sync_plat = true
				target.base_on_floor = true 
				target.velocity.x += plat_vel.x 
				
				if target.airtime < 0: 
					target.base_on_floor = false 
				else: 
					target.velocity.y += plat_vel.y 
					target.airtime = 0 
			
			elif not on_sync_plat and collider.is_class(base_type) and target.airtime == 0:
				target.base_on_floor = true
				if not _was_on_floor: 
					target.velocity.y = 0
	
	if not target.base_on_floor:
		target.velocity.y += modifier * (gravity * delta)
		if target.airtime < 0: 
			target.airtime += modifier * (gravity * delta)
			if target.airtime >= 0:
				target.airtime = 0
				
		if death_on_ttl and target.ttl <= target.velocity.y:
			target._on_death()
