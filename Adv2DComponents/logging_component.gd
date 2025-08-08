# LoggingComponent.gd
extends Node
class_name LoggingComponent

@export var LOG_FILE_PATH: String = "log_string.txt"
@export var DUMP_FILE_PATH: String = "dump.txt"

# --- Exported Variables ---
@export var VERBOSE: bool = true # Log to console in addition to file
@export var WRITE: bool = false   # Write logs/dumps to files
@export var enabled: bool = true  # Enable/disable logging listener

# --- Properties ---
@onready var L: String = ""
@onready var target: Node = get_parent() if get_parent() else self
@onready var target_name: String = target.name if target else "UnknownTarget"

# Dictionary to store the traversed node information { "NodeName": { "type": "NodeType", "script": "res://path/to/script.gd" } }
var group: Dictionary = {}

# String buffer for log writing (used by _write_to_log_file)
var log_string_buffer: String = ""

# --- Action Definitions ---
# Actions dictionary. Functions should ideally accept (node, depth, specific_args)
# but adapt based on how traverse_tree calls them.
# We'll keep the simpler structure (direct callables) for maintainability.
var actions: Dictionary = {
	"dump": _dump_action,
	"print_node": _print_node_action,
	"pretty": prettify
}


func _ready() -> void:
	# Ensure the target node is valid
	if not is_instance_valid(target):
		printerr("%s: Invalid target node." % name)
		enabled = false
		set_process(false) # Disable _process if target is invalid
		return

	# Initialize files (clear them if they exist)
	if WRITE:
		_initialize_file(LOG_FILE_PATH, "log")
		_initialize_file(DUMP_FILE_PATH, "dump")

	print("%s: Initialized for target '%s'. Scanning..." % [name, target_name])

	# --- Example Usage (using original array format for actions) ---
	group.clear()
	# Traverse and print node info using 'print_node' action with specific indent
	# Action format: [action_name, [arg1, arg2, ...]]
	# The args array will be passed as the third argument to the action function
	traverse_tree(target, "|-", ["print_node", ["|-"]], 0)	
	#traverse_tree(target, "|-", ['dump', [{'dump_script': true}]])
		
	print("%s: Scan complete for '%s'." % [name, target_name])


func _process(delta: float) -> void:
	if enabled and target.get('L'):
		if !target.L.is_empty():
			log_string_buffer = target.L 
			target.L = ''
			_write_to_log_file(log_string_buffer)
			log_string_buffer = ""

func traverse_tree(node: Node, base_indent: String = "  ", action: Array = [], depth: int = 0) -> void:
	if not is_instance_valid(node):
		printerr("traverse_tree: Encountered invalid node at depth %d." % depth)
		return

	var node_key: String = node.name
	var node_info: Dictionary = {
		"type": node.get_class(),
		"script": node.get_script().resource_path if node.get_script() else null
	}

	if group.has(node_key):
		printerr("Warning: Duplicate node name '%s' encountered. Overwriting in group. Consider using node paths as keys." % node_key)
	
	group[node_key] = node_info

	# Calculate current indentation string
	var indent_string = base_indent.repeat(depth)

	# --- Handle Actions---
	if not action.is_empty():
		var action_name = action[0]

		# --- Special Case: 'log' action (logs the whole group at the root) ---
		if action_name == "log":
			if depth == 0: # Only execute log action at the root level
				var group_string = prettify(group, base_indent) # Use base_indent for prettify
				log_string_buffer = "--- Group Log ---\n" + group_string + "-----------------\n"
				_write_to_log_file(log_string_buffer) # Write the formatted group
				log_string_buffer = "" # Clear buffer

		# --- Standard Action Handling ---
		elif actions.has(action_name):
			var action_func: Callable = actions[action_name]
			var specific_args: Variant = null

			# Extract arguments if provided in the action array [action_name, [args...]]
			if action.size() > 1:
				if action[1] is Array:
					specific_args = action[1] # Pass the inner array as args
				else:
					printerr("traverse_tree: Action '%s' expected arguments in an array format [action, [arg1, arg2]]. Got: %s" % [action_name, typeof(action[1])])
					specific_args = [action[1]]

			var result = action_func.call(node, depth, specific_args)

		else:
			printerr("traverse_tree: Action '%s' not found in 'actions' dictionary." % action_name)

	# --- Recurse for Children ---
	var children = node.get_children(false)
	for child in children:
		if is_instance_valid(child):
			traverse_tree(child, base_indent, action, depth + 1)
		else:
			printerr("traverse_tree: Skipping invalid child of node '%s'." % node.name)

#==============================================================================
# Action Implementations
#==============================================================================

func _print_node_action(node: Node, depth: int, args: Variant) -> void:
	var indent_char = "  "
	
	if args is Array and not args.is_empty() and args[0] is String:
		indent_char = args[0]
	elif args != null:
		printerr("_print_node_action: Invalid args format. Expected an array like ['indent_char']. Got: %s" % args)


	var indent = indent_char.repeat(depth)
	var script_path = node.get_script().resource_path if node.get_script() else "None"
	print("%s%s (%s) - Script: %s" % [indent, node.name, node.get_class(), script_path])


func _dump_action(node: Node, depth: int, args: Variant) -> void:
	if not WRITE: return # Only dump if writing is enabled

	var dump_script: bool = false
	var indent_char = "  " # Default indent

	# Extract config from args array if provided
	if args is Array and not args.is_empty() and args[0] is Dictionary:
		var config_dict = args[0]
		dump_script = config_dict.get("dump_script", false)
		indent_char = config_dict.get("indent_char", "  ")
	elif args != null:
		printerr("_dump_action: Invalid args format. Expected an array like [{'dump_script': true, 'indent_char': '--'}]. Got: %s" % args)

	var indent = indent_char.repeat(depth)
	var node_info_str = "%s%s (%s)" % [indent, node.name, node.get_class()]
	var script_content_str = ""
	var script_path = ""

	# Prepare script content if requested and available
	if dump_script and node.get_script():
		script_path = node.get_script().resource_path
		var script_file = FileAccess.open(script_path, FileAccess.READ)
		if script_file:
			script_content_str = script_file.get_as_text()
			script_file.close()
			script_content_str = "\n%s  --- Script: %s ---\n%s\n%s  --- End Script ---" % [indent, script_path.get_file(), script_content_str, indent]
		else:
			script_content_str = "\n%s  --- Failed to read script: %s (Error: %s) ---" % [indent, script_path, FileAccess.get_open_error()]
			printerr("Failed to open script file for dumping: '%s'" % script_path)

	# Append to the dump file
	var dump_file = FileAccess.open(DUMP_FILE_PATH, FileAccess.READ_WRITE) # Use READ_WRITE to append
	if dump_file:
		dump_file.seek_end() # Move cursor to the end to append
		dump_file.store_string(node_info_str + script_content_str + "\n")
		dump_file.close()
	else:
		printerr("Failed to open dump file '%s' for appending. Error: %s" % [DUMP_FILE_PATH, FileAccess.get_open_error()])
	
	print('dumped')

#==============================================================================
# File Handling & Logging
#==============================================================================

# Initializes (creates or clears) a file.
func _initialize_file(file_path: String, file_type: String) -> void:
	# Ensure the directory exists (Godot 4+) - For Godot 3, this might error if dir doesn't exist
	var dir_path = file_path.get_base_dir()
	var dir_access = DirAccess.open(dir_path.get_base_dir()) # Open parent of target dir
	if dir_access:
		if not DirAccess.dir_exists_absolute(dir_path):
			var err = DirAccess.make_dir_recursive_absolute(dir_path)
			if err != OK:
				printerr("Failed to create directory '%s'. Error code: %s" % [dir_path, err])
				# Decide if you should return here or try opening the file anyway
	else:
		printerr("Failed to access directory for path: %s" % dir_path)


	var file = FileAccess.open(file_path, FileAccess.WRITE) # WRITE mode creates or truncates
	if file:
		file.close()
		if VERBOSE:
			print("Initialized %s file: %s" % [file_type, file_path])
	else:
		printerr("Failed to initialize %s file '%s'. Error: %s" % [file_type, file_path, FileAccess.get_open_error()])


func _write_to_log_file(message: String) -> void:
	if message.is_empty():
		return

	var log_entry = "|%s: %s" % [target_name, message] # Add target name context

	if VERBOSE:
		print(log_entry) # Print to console if verbose

	if WRITE:
		# Append the single log entry to the log file
		var file = FileAccess.open(LOG_FILE_PATH, FileAccess.READ_WRITE) # Use READ_WRITE to append
		if file:
			file.seek_end() # Move to the end
			# Ensure consistent newlines, check if message already ends with one
			if not log_entry.ends_with("\n"):
				log_entry += "\n"
			file.store_string(log_entry)
			file.close()
		else:
			printerr("Failed to open log file '%s' for appending. Error: %s" % [LOG_FILE_PATH, FileAccess.get_open_error()])




func prettify(data: Variant, indent_char: String = "--", _current_indent: String = "") -> String:
	var output_string = ""
	var next_indent = _current_indent + indent_char

	if data is Dictionary:
		if data.is_empty():
			output_string += "{}\n" # Represent empty dictionary
		else:
			for key in data:
				var value = data[key]
				output_string += _current_indent + str(key) + ": "
				if value is Dictionary:
					# Recursive call for nested dictionaries
					output_string += "\n" + prettify(value, indent_char, next_indent)
				elif value is Array:
					# Format arrays nicely
					output_string += prettify(value, indent_char, _current_indent) # Recurse for array formatting
				else:
					# Simple value
					output_string += str(value) + "\n"
	elif data is Array:
		if data.is_empty():
			output_string += "[]\n" # Represent empty array
		else:
			output_string += "[\n"
			for i in range(data.size()):
				var item = data[i]
				# Indent array items slightly more than the containing structure
				output_string += next_indent + "- " # Use "- " prefix for array items
				if item is Dictionary or item is Array:
					output_string += "\n" + prettify(item, indent_char, next_indent + "  ") # Deeper indent for nested structures within array
				else:
					output_string += str(item) + "\n"
				# Removed trailing comma logic for simplicity, add back if needed
			output_string += _current_indent + "]\n"
	elif data != null:
		# Handle other data types passed directly
		output_string += _current_indent + str(data) + "\n"
	else:
		output_string += _current_indent + "null\n"


	return output_string
