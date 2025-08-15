# PSMComponent.gd
extends Node
class_name PSMComponent

@export var arch_name: String = "BaseChar2DArchetype"
@export var overrides: Dictionary = {}

@onready var target: Node = get_parent()

func _ready() -> void:
	if not is_instance_valid(target):
		return

	var log_message: String = "%s:%s: PSM loaded." % [name, target.name if is_instance_valid(target) else "no_target"]
	var archetype_applied: bool = false
	var overrides_applied: bool = false
	var root_apply_node: Node = target # Initial node to apply to is the PSM's parent

	if not arch_name.is_empty():
		var scene_root: Node = get_tree().current_scene if get_tree() else null
		if is_instance_valid(scene_root):
			var archetype_node: Node = scene_root.get_node_or_null(arch_name)
			if is_instance_valid(archetype_node):
				if archetype_node.has_method("get") and archetype_node.get("data") is Dictionary:
					var archetype_data: Dictionary = archetype_node.get("data")
					if not archetype_data.is_empty():
						_apply_dictionary_hierarchically(archetype_data, root_apply_node)
						log_message += "\n|Applied parameters from archetype node '%s' data." % arch_name
						archetype_applied = true
					else:
						log_message += "\n|Archetype node '%s' 'data' dictionary is empty." % arch_name
				else:
					log_message += "\n|Archetype node '%s' found, but it does not have a 'data' Dictionary property." % arch_name
			else:
				log_message += "\n|Archetype node '%s' not found at scene root." % arch_name
		else:
			log_message += "\n|Scene root not found, cannot fetch archetype."
	else:
		log_message += "\n|No arch_name specified to fetch archetype data."

	if not overrides.is_empty():
		_apply_dictionary_hierarchically(overrides, root_apply_node) # Overrides can also target children
		log_message += "\n|Applied local overrides."
		overrides_applied = true
	elif archetype_applied : 
		log_message += "\n|No local overrides to apply."
	
	if not archetype_applied and not overrides_applied and arch_name.is_empty() and overrides.is_empty():
		log_message += "\n|No parameters to apply (no archetype specified, no overrides)."

	if target.get('L'):
		target.L += log_message + "\n"

func _apply_dictionary_hierarchically(dict_params: Dictionary, current_node: Node) -> void:
	if not is_instance_valid(current_node) or dict_params.is_empty():
		return
		
	var current_node_property_names: Dictionary = {}
	for p_info in current_node.get_property_list():
		current_node_property_names[p_info.name] = true

	for key in dict_params:
		var value = dict_params[key]
		var param_name: String = str(key)
		var setter_name: String = "set_" + param_name

		# Check if the key corresponds to a child node and the value is a dictionary for that child
		var child_node_to_configure: Node = current_node.get_node_or_null(param_name)
		if is_instance_valid(child_node_to_configure) and value is Dictionary:
			_apply_dictionary_hierarchically(value, child_node_to_configure) # Recursive call for child
		# Else, try to apply as a property to the current_node
		elif current_node.has_method(setter_name):
			current_node.call(setter_name, value)
		elif current_node_property_names.has(param_name):
			current_node.set(param_name, value)
