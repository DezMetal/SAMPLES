import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv  # Import load_dotenv
import uuid  # Import the uuid module

try:
    from google import genai
    from google.genai import types
except ImportError:
    raise ImportError("The 'google-genai' library is not installed. Please run 'pip install google-genai flask'.")

# Import the ContextManager from your module
# Assuming context_manager.py is directly in a 'context_manager' directory
# and the class is exposed via __init__.py or directly in context_manager.py
from context_manager import ContextManager

# Load environment variables (e.g., GEMINI_API_KEY)
load_dotenv()

# --- Flask App Initialization ---
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Used for Flask sessions

# --- Default Configuration ---
MODEL_NAME = "gemini-1.5-flash"
RESPONSE_LENGTH = 800  # Max output tokens for Gemini's response
SETTINGS = {
    'content': {
        'low': types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        'medium': types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        'high': types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        'disable': types.HarmBlockThreshold.BLOCK_NONE
    }
}

# --- ContextManager Configuration ---
# This configuration will be passed to your ContextManager instance
CM_CONFIG = {
    "mode": "ai",  # Use AI mode for summarization
    "max_active_msgs": 10,  # Max 10 messages in active context for LLM
    "msg_count_sum_thresh": 6,  # Trigger summary when message count exceeds 6
    "keep_n": 2,  # Keep the last 2 messages verbatim after summary
    "llm_mod": MODEL_NAME,  # Use the same model for summarization
    "llm_sum_max_tok": 100  # Max tokens for the generated summary
    # "llm_key": os.environ.get("GEMINI_API_KEY") # Optional: if not set in .env
}

# Initialize the ContextManager globally
try:
    context_manager = ContextManager(CM_CONFIG)
except ValueError as e:
    print(f"Error initializing ContextManager: {e}")
    # In a real app, you might want to handle this more gracefully,
    # perhaps by exiting or disabling AI features.
    context_manager = None  # Set to None if initialization fails

# --- System and Initial Prompts ---
SYSTEM_PROMPT_TEMPLATE = """
You are an AI designed to be an immersive, interactive Japanese language learning partner, acting as a generative story driver or Dungeon Master (DM).
Your core function is to weave a continuous, creative roleplay scenario with the user while providing structured language support.

Your strict operating parameters are:

1.  **Role & Format**:
    * You control the narrator and a companion named **{character_name}**. The user's role is **{user_name}**.
    * The conversation history will be formatted with speaker labels.
    * **CRITICAL RULE: You MUST begin your *entire* response with the label `{character_name}:` on its own line. NEVER speak for `{user_name}`. Your entire output must be from the perspective of the narrator or {character_name}.**
    * After the `{character_name}:` label, provide your response using the dual-language format.
    * **RESPONSE LENGTH:** Keep your responses concise. Aim for 1-2 sentences or narrative points per turn to keep the conversation flowing quickly.

2.  **Dual-Language Output (After the `{character_name}:` label)**:
    * For every piece of dialogue or narration, provide BOTH Japanese and English text.
    * The Japanese text must be on its own line, immediately followed by the English translation on the next line. This format is critical for parsing.
    * Example of your response format:
        {character_name}:
        *優(やさ)しく微笑(ほほえ)みます。*
        *Anri smiles gently.*
        大丈夫(だいじょうぶ)ですか？
        Are you alright?

3.  **Furigana Rules (Critical)**:
    * ONLY use furigana for Kanji (漢字), like `漢字(かんじ)`.
    * NEVER use furigana for Hiragana (ひらがな) or Katakana (カタカナ).
    * **CRITICAL: Only use parentheses `（）` for Furigana. DO NOT use parentheses for translations, side comments, or any other purpose.**
"""

INITIAL_HISTORY_TEMPLATE = """{character_name}:
*柔(やわ)らかな緑(みどり)の光(ひかり)があなたの顔(かお)を照(て)らし、私(わたし)の掌(てのひら)があなたの額(ひたい)にそっと触(ふ)れている。ゆっくりと目(め)を開(あ)けると、見(み)たこともない植物(しょくぶつ)に囲(かこ)まれた静(しず)かな森(もり)のようです。*
*A soft, green light illuminates your face as my palm rests gently on your forehead. As you slowly open your eyes, you see a quiet forest, surrounded by plants you've never seen before.*
あ、気(き)がついてよかった…！大丈夫(だいじょうぶ)ですか？森(もり)の中(なか)で倒(たお)れているのを偶然(ぐうぜん)見(み)つけたんです。あなた、すごく珍(めずら)しい服(ふく)を着(き)ていますね。
Oh, I'm so glad you're awake...! Are you alright? I happened to find you collapsed in the middle of the forest. You're wearing some very unusual clothes.
申(もう)し訳(わけ)ありません、自己(じこ)紹介(しょうかい)がまだでしたね。私(わたし)は{character_name}です。治癒(ちゆ)魔法(まほう)を少(すこ)しだけ使(つか)えます。あなたの名前(なまえ)を聞(き)いてもいいですか？
I'm sorry, I haven't introduced myself. My name is {character_name}. I can use a little bit of healing magic. May I ask your name?
"""


# --- Helper Functions ---
def parse_response(text_response: str, character_name: str):
    lines = [line.strip() for line in text_response.strip().split('\n') if line.strip()]
    if lines and lines[0] == f"{character_name}:":
        lines = lines[1:]
    parsed_data = []
    i = 0
    while i < len(lines):
        japanese_line = lines[i]
        english_line = ""
        # Determine if the Japanese line contains Japanese characters
        # This regex checks for CJK Unified Ideographs (Kanji), Hiragana, and Katakana
        has_japanese_chars = any('\u4E00' <= c <= '\u9FFF' or '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' for c in japanese_line)

        if i + 1 < len(lines):
            potential_english_line = lines[i + 1]
            # Heuristic to check if the next line is likely English (doesn't contain Japanese chars)
            is_potential_english = not (any('\u4E00' <= c <= '\u9FFF' or '\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' for c in potential_english_line))

            if has_japanese_chars and is_potential_english:
                english_line = potential_english_line
                parsed_data.append({"japanese": japanese_line, "english": english_line, "has_japanese": has_japanese_chars})
                i += 2
                continue

        # Fallback for single lines or if detection fails, or if it's a non-Japanese line
        parsed_data.append({"japanese": japanese_line, "english": english_line, "has_japanese": has_japanese_chars})
        i += 1
    return parsed_data


# --- Flask Routes ---
@app.route('/')
def setup():
    return render_template('setup.html')


@app.route('/start_adventure', methods=['POST'])
def start_adventure():
    session.clear()  # Clear existing session data
    session['user_name'] = request.form.get('user_name', 'Adventurer')
    session['character_name'] = request.form.get('character_name', 'Anri')

    # Generate a unique thread ID for the ContextManager
    # Use a UUID for the session ID if it doesn't already exist
    if 'thread_id' not in session:
        session['thread_id'] = str(uuid.uuid4())
    thread_id = session['thread_id']

    if context_manager:
        # Prepare initial messages for the ContextManager
        # ONLY conversational turns (user/model) go into ContextManager's history.
        # System prompt is passed separately to the LLM.
        initial_messages_for_cm = [
            {"role": "model", "parts": [{"text": INITIAL_HISTORY_TEMPLATE.format(
                character_name=session['character_name']
            )}]}
        ]
        context_manager.set_initial_msgs(thread_id, initial_messages_for_cm)
    else:
        # Fallback if ContextManager failed to initialize
        print("ContextManager not initialized. History will not be managed.")
        session['contents_fallback'] = [
            {"role": "model", "parts": [{"text": INITIAL_HISTORY_TEMPLATE.format(
                character_name=session['character_name']
            )}]}
        ]

    return redirect(url_for('chat'))


@app.route('/chat')
def chat():
    if 'user_name' not in session or not session.get('thread_id'):
        return redirect(url_for('setup'))

    thread_id = session['thread_id']

    # Retrieve the current conversation history from the ContextManager
    if context_manager:
        conversation_history = context_manager.get_ctx(thread_id)
    else:
        # Fallback if ContextManager not initialized
        conversation_history = session.get('contents_fallback', [])

    # Prepare messages for rendering in the template
    messages_for_template = []
    for msg in conversation_history:
        # Only include 'model' and 'user' roles for display
        if msg['role'] == 'model':
            messages_for_template.append({
                "role": "model",
                "parsed_content": parse_response(msg['parts'][0]['text'], session['character_name'])
            })
        elif msg['role'] == 'user':
            messages_for_template.append({
                "role": "user",
                "parsed_content": [{"japanese": msg['parts'][0]['text'], "english": "", "has_japanese": False}]
            })
        # System messages (summaries) are not added to messages_for_template for display
        # They are internal to ContextManager and only affect the LLM context.

    return render_template('index.html',
                           messages=messages_for_template,  # Pass the structured messages
                           character_name=session['character_name'],
                           user_name=session['user_name'])


@app.route('/send_message', methods=['POST'])
def send_message():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return jsonify({'error': "GEMINI_API_KEY environment variable not set."}), 500

    if not context_manager:
        return jsonify({'error': 'AI context manager not available.'}), 500

    character_name = session.get('character_name', 'Anri')
    user_name = session.get('user_name', 'Adventurer')
    thread_id = session.get('thread_id')

    if not thread_id:
        return jsonify({'error': 'Session not initialized. Please start a new adventure.'}), 400

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        app.logger.error(f"Failed to initialize GenAI Client: {e}")
        return jsonify({'error': f"Failed to initialize GenAI Client: {e}"}), 500

    user_message_text = request.json.get('message')
    if not user_message_text: return jsonify({'error': 'Empty message received.'}), 400

    # Add user message to ContextManager
    context_manager.add_msg(thread_id, "user", user_message_text)  # Ensure role is "user"

    # Get the optimized context from ContextManager for the LLM call
    # Filter out 'system' messages from ContextManager's history before sending to LLM
    raw_contents_from_cm = context_manager.get_ctx(thread_id)
    contents_for_llm = [msg for msg in raw_contents_from_cm if msg['role'] in ['user', 'model']]

    # Re-add system_instruction as a separate parameter as per Gemini API requirements
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(character_name=character_name, user_name=user_name)

    safety_config = [types.SafetySetting(category=cat, threshold=thresh) for cat, thresh in [
        (types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, SETTINGS['content']['high']),
        (types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, SETTINGS['content']['medium']),
        (types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, SETTINGS['content']['high']), ]]
    gen_config = types.GenerateContentConfig(safety_settings=safety_config, system_instruction=system_prompt, max_output_tokens=RESPONSE_LENGTH)

    try:
        response = client.models.generate_content(model=f"models/{MODEL_NAME}", config=gen_config, contents=contents_for_llm)
        response_text = response.text
    except Exception as e:
        app.logger.error(f"An error occurred with the Gemini API: {e}")
        # Consider a more robust rollback if needed, but for now, just return error
        return jsonify({'error': 'An error occurred while generating a response from the AI.'}), 500

    # Add model's response to ContextManager
    context_manager.add_msg(thread_id, "model", response_text)  # Ensure role is "model"

    parsed_ai_response = parse_response(response_text, character_name)
    return jsonify(parsed_ai_response)


if __name__ == '__main__':
    # Ensure the ContextManager is initialized before running the app
    if context_manager:
        context_manager.verbose = True
        print("ContextManager initialized successfully.")
    else:
        print("ContextManager initialization failed. Running with limited history management.")
    app.run(debug=False)
