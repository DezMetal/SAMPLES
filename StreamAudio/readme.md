# Dynamic TTS Voice Module

A versatile and highly configurable text-to-speech (TTS) module for Python, designed to produce more natural and "organic" sounding speech. This module uses the Piper TTS engine and enhances it with a procedural dynamics system powered by Perlin noise, allowing for continuous, smooth variations in pitch and speed.

The script can be run as a standalone, feature-rich command-line application or imported as a module into other Python projects to provide voice capabilities.

## Features

- **High-Quality TTS:** Powered by the fast and efficient Piper TTS engine.
- **Organic Procedural Dynamics:** Uses Perlin noise to generate smooth, continuous variations in pitch and speed, avoiding a robotic, monotonous delivery.
- **Highly Configurable:** All dynamic parameters (pitch range, speed variation, pause lengths) can be fine-tuned through a `settings.json` file.
- **SSML-like Tag Support:** Manually control speech dynamics using intuitive inline tags like `[pitch]`, `[scale]`, and `[pause]`.
- **Dual-Use Design:** Functions as both a standalone command-line tool and an importable Python module.
- **Multiple Output Options:**
  - Speak audio directly.
  - Save audio to a `.wav` file.
  - Return a complete in-memory `.wav` file as bytes for piping to other applications.
- **Rich CLI Experience:** Features a stylized interface with syntax highlighting and a live progress bar for synthesis.

## Requirements

- Python 3.9+
- The Python packages listed in `requirements.txt`.

## Installation

1.  **Clone the repository or download the `stream_audio.py` script.**

2.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download a Piper TTS Model:** This script requires a model file (`.onnx`) and a config file (`.onnx.json`) from Piper. You can find a variety of high-quality voices here:
    [https://huggingface.co/rhasspy/piper-voices/tree/main](https://huggingface.co/rhasspy/piper-voices/tree/main)

4.  **Update the Model Path:** Open `stream_audio.py` or your `settings.json` and update the `model_path` and `config_path` to point to your downloaded Piper model files.

## Usage

### As a Standalone CLI

Simply run the script from your terminal.

```bash
python stream_audio.py
```

You will be greeted by a welcome message and a `>>>` prompt. Type any text and press Enter to hear it spoken. You can use any of the supported tags in your input.

### As a Python Module

Import the `Voice` class into your own Python scripts to add text-to-speech functionality.

```python
import stream_audio
import pyaudio
import wave
import io

# Initialize the voice. It can be headless to suppress console output.
# You can also point to a custom settings file.
my_voice = stream_audio.Voice(settings_path="custom_settings.json", headless=True)

# 1. Simple speech
my_voice.say("Hello from my application!")

# 2. Save to a file without speaking
my_voice.say('This will be saved. [save="output.wav"]', speak_override=False)

# 3. Get audio as a complete in-memory WAV file (bytes)
audio_bytes = my_voice.say("Generate audio bytes. [bytes]")

# Example of playing the returned bytes with PyAudio
if audio_bytes:
    audio_buffer = io.BytesIO(audio_bytes)
    with wave.open(audio_buffer, 'rb') as wf:
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
            
        stream.close()
        p.terminate()
```

## Configuration (`settings.json`)

To customize the voice's behavior, create a `settings.json` file in the same directory as the script. The script will automatically load it on startup. You only need to include the settings you wish to override.

**Example `settings.json` for a calm voice:**
```json
{
    "dynamics": {
        "noise_step": 0.4,
        "pitch_deviation": 0.2,
        "scale_deviation": 0.15
    }
}
```

### Key Dynamic Settings

- **`noise_step`**: Controls how quickly the procedural dynamics change. A lower value creates slower, more gradual shifts.
- **`pitch_range`**: The maximum possible pitch variation in semitones (e.g., `[-1.5, 1.5]`).
- **`pitch_deviation`**: The volatility of the pitch within its range (0.0 to 1.0). A lower value results in a calmer, more stable pitch.
- **`scale_range`**: The maximum possible speed variation (e.g., `[0.85, 1.25]`).
- **`scale_deviation`**: The volatility of the speed within its range (0.0 to 1.0). A lower value results in a more monotonous speed.

## Supported SSML-like Tags

You can insert these tags directly into the text to control the speech output.

| Tag                          | Description                                                                                             |
| ---------------------------- | ------------------------------------------------------------------------------------------------------- |
| `[pause=500]`                | Pauses for a specified number of milliseconds.                                                          |
| `[scale=0.8]`                | Sets the speech speed. **Note:** Lower values are **faster**, higher values are **slower**. `1.0` is normal. |
| `[pitch=-2.5]`               | Sets the pitch. **Note:** Lower values are **higher** pitched, higher values are **lower** pitched. `0` is normal. |
| `[dynamics=off]`             | Temporarily disables the procedural dynamics for the text that follows.                                 |
| `[dynamics=on]`              | Re-enables the procedural dynamics.                                                                     |
| `[file="path/to/file.txt"]`  | Reads the content from the specified text file and inserts it into the speech.                          |
| `[save="output.wav"]`        | Saves the final audio to a `.wav` file. Does not speak by default.                                      |
| `[bytes]`                    | Returns the final audio as a complete, in-memory `.wav` file (in bytes). Does not speak.                  |
| `[speak=off]`                | Disables audio playback for the current text (useful when saving or getting bytes).                     |
| `[noise_scale=0.8]`          | (Piper built-in) Controls the randomness in the synthesized audio. Piper's default is `0.667`.           |
| `[noise_w=0.9]`              | (Piper built-in) Varies the length of phonemes. Piper's default is `0.8`.                               |