extends HTTPRequest

class_name WebComponent

signal web_messsage

@onready var L: String = ''
# Ensure this URL is the correct /exec URL from your latest deployment
@onready var url: String = "https://posttestserver.dev/p/54s30knqjebr2lhk/2/json"
@onready var params: Dictionary = {'route': '', 'params': {}}
@onready var target: Node = get_parent() if get_parent() else self
@onready var response: JSON # Note: This variable isn't currently assigned a value after the request
@onready var code: int = 0 # Note: This variable isn't currently assigned a value after the request
@onready var method: HTTPClient.Method = HTTPClient.METHOD_GET
# Correct Content-Type casing and ensure it's the only header initially
@onready var headers: PackedStringArray = ["Content-Type: application/json"]
@onready var valid_routes: Array = [""]

@onready var verbose: bool = true


func _ready() -> void:
	var err = false
	var route = params['route']
	var request_body: String = ""
	var r = url

	# Configure HTTPRequest node properties before connecting signals or making requests
	use_threads = true # Enable threaded requests
	# request_timeout = 10 # Optional: uncomment if needed

	request_completed.connect(_handle_request)
	web_messsage.connect(_handle_message)

	if method == HTTPClient.METHOD_POST:
		L = 'post test..'
		var data_dict := {"test": "hello"}
		request_body = JSON.stringify(data_dict)
		var result = request(url, [], HTTPClient.METHOD_POST, request_body)
	else:
		L = 'get test..'
		# GET request setup (ensure this matches your Apps Script doGet if used)
		var args = {}
		var arg_string: String = '/?'
		for k in args.keys():
			arg_string += '%s=%s&'%[k, args[k]]
		arg_string = arg_string.rstrip("&")
		r = url + arg_string

	# Start the request with the populated request_body
	var result = request(r, headers, method, request_body)
	err = result != OK
	print("Request URL:", r)
	print("Headers:", headers)
	print("Method:", method)
	print("Body:", request_body)
	L = '%s:%s: loaded\n'%[name, target.name] + (' request failed to start.' if err else ' request sent.')


func _process(delta: float) -> void:
	if 'web_enabled' in target.get_property_list():
		if target.web_enabled and target.web_message:
			emit_signal('web_message', target.web_message)
			target.web_message = {}

	else:
		if verbose:
			printerr('%s: target needs "web_enabled: bool" for this to work..')
		set_process(false)

# Use more descriptive parameter names matching the signal documentation
func _handle_request(result_code, response_code, response_headers, body) -> void:
	var body_string = body.get_string_from_utf8()
	var _response_data = null

	print("Request Completion Result (HTTPRequest.Result enum):", result_code)
	print("HTTP Status Code:", response_code)
	print('------------------------------------')

	# Check the HTTPRequest.Result enum first for connection/request errors
	if result_code != HTTPRequest.RESULT_SUCCESS:
		printerr("HTTPRequest failed! Result code:", result_code)
		_response_data = {"error": "HTTPRequest Error", "result_code": result_code}
	elif response_code >= 200 and response_code < 300: # Check for successful HTTP status codes
		if method == HTTPClient.METHOD_POST:
			var json = JSON.new()
			var parse_result = json.parse(body_string)

			if parse_result == OK:
				_response_data = json.get_data()
				print("JSON Response Data:")
				print(_response_data)
			else:
				_response_data = {"error": "Failed to parse JSON", "parse_error": json.get_error_message(), "raw_body": body_string}
				print("JSON Parse Error Data:")
				print(_response_data)
		else: # Handle non-POST methods (assuming GET returning HTML/text)
			_response_data = {'body': body_string}
			print("HTML/Text Response Data:")
			print(_response_data)
	else: # Handle non-success HTTP status codes (e.g., 4xx, 5xx)
		_response_data = {"error": "HTTP Error", "code": response_code, "body": body_string}
		print("HTTP Error Data:")
		print(_response_data)

	# Assign the processed data if needed (e.g., to self.response)
	# self.response = _response_data

	print('------------------------------------')


func _handle_message(message: Dictionary) -> void:
	var title: String = message['title']
	var text: String = message.get('text', '[no text]')
	var args: Array = message.get("args", []).filter(func(n): return valid_routes.has(n))
	print('------------------------------------')
	print('Web Message from %s\nText: %s\nParams: %s'%[title, text, '/'.join(args)])
	print('------------------------------------')
