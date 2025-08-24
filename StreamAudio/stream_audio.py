import sys
import time
import sounddevice as sd
from contextlib import contextmanager, nullcontext
from piper import PiperVoice, SynthesisConfig
import numpy as np
import re
import wave
import io
from audiotsm import wsola
from audiotsm.io.array import ArrayReader, ArrayWriter
from scipy.signal import resample
from random import choice, uniform, randint
import json
import os
from perlin_noise import PerlinNoise
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.syntax import Syntax

# --- SETTINGS ---
DEFAULT_SETTINGS = {
    "model_path": "models/cori/en_GB-cori-high.onnx",
    "config_path": "models/cori/en_GB-cori-high.onnx.json",
    "start_phrases": ["initializing", "starting program", "hello", "ready", "initialize"],
    "stop_phrases": ["terminating", "ending program", "goodbye", "terminated", "shutting down"],
    "dynamics": {
        "pause_comma_range": [50, 80],
        "pause_period_range": [110, 350],
        "noise_step": 0.2,
        "pitch_range": [-1.5, 1.5],
        "pitch_deviation": 0.3,
        "scale_range": [0.85, 1.25],
        "scale_deviation": 0.5
    }
}

# --- HELPER FUNCTIONS ---
def _update_settings(original, update):
    for key, value in update.items():
        if isinstance(value, dict) and key in original:
            original[key] = _update_settings(original.get(key, {}), value)
        else:
            original[key] = value
    return original

@contextmanager
def _open_stream(sample_rate, channels):
    try:
        stream = sd.OutputStream(samplerate=sample_rate, channels=channels, dtype='int16')
        stream.start()
        yield stream
    except Exception as e:
        print(e)
        yield None
    finally:
        if 'stream' in locals() and stream:
            stream.stop()
            stream.close()

# --- CORE CLASSES ---
class DynamicsGenerator:
    def __init__(self, settings):
        self.settings = settings
        self.noise_pos = 0
        self.pitch_noise = PerlinNoise(octaves=4, seed=randint(1, 1000))
        self.scale_noise = PerlinNoise(octaves=4, seed=randint(1, 1000))

    def _map_noise_to_range(self, noise_val, value_range, deviation):
        center = (value_range[0] + value_range[1]) / 2
        span = (value_range[1] - value_range[0]) / 2
        return center + (noise_val * span * deviation)

    def process(self, text):
        parts = re.split(r'(\[dynamics=(?:on|off)\])', text, flags=re.IGNORECASE)
        processed_text = ""
        dynamics_on = True

        for part in parts:
            if not part: continue
            if re.match(r'\[dynamics=on\]', part, re.IGNORECASE):
                dynamics_on = True; continue
            elif re.match(r'\[dynamics=off\]', part, re.IGNORECASE):
                dynamics_on = False; continue

            if dynamics_on:
                sentences = re.split(r'(?<=[.?!])\s+', part)
                for sentence in sentences:
                    if not sentence.strip(): continue
                    self.noise_pos += self.settings['noise_step']
                    pitch_val = self._map_noise_to_range(self.pitch_noise(self.noise_pos), self.settings['pitch_range'], self.settings['pitch_deviation'])
                    scale_val = self._map_noise_to_range(self.scale_noise(self.noise_pos), self.settings['scale_range'], self.settings['scale_deviation'])
                    temp_sentence = f"[scale={scale_val:.2f}][pitch={pitch_val:.2f}]{sentence}[scale=1][pitch=0]"
                    temp_sentence = temp_sentence.replace(',', f', [pause={randint(*self.settings["pause_comma_range"])}]')
                    if temp_sentence.endswith('.'): temp_sentence = temp_sentence[:-1] + f'. [pause={randint(*self.settings["pause_period_range"])}]'
                    elif temp_sentence.endswith('?'): temp_sentence = temp_sentence[:-1] + f'? [pause={randint(*self.settings["pause_period_range"])}]'
                    elif temp_sentence.endswith('!'): temp_sentence = temp_sentence[:-1] + f'! [pause={randint(*self.settings["pause_period_range"])}]'
                    processed_text += temp_sentence + " "
            else:
                processed_text += part
        return processed_text.strip()

class Voice:
    def __init__(self, settings_path="settings.json", headless=False):
        self.console = Console()
        self.headless = headless
        self.settings = DEFAULT_SETTINGS.copy()
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    self.settings = _update_settings(self.settings, json.load(f))
                if not self.headless: self.console.print(f"[green]✔ Loaded settings from {settings_path}[/green]")
            except Exception as e:
                if not self.headless: self.console.print(f"[bold red]Error loading {settings_path}: {e}[/bold red]")
        
        self.dynamics_generator = DynamicsGenerator(self.settings['dynamics'])
        
        if not self.headless: self.console.print("[cyan]Initializing TTS model...[/cyan]")
        start_time = time.time()
        self.voice = PiperVoice.load(self.settings['model_path'], self.settings['config_path'])
        if not self.headless: self.console.print(f"[green]✔ Model loaded in {time.time() - start_time:.2f} seconds.[/green]")

    def _write_wav_to_buffer(self, audio_data, sample_rate, channels=1):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
        buffer.seek(0)
        return buffer.getvalue()

    def say(self, text, speak_override=None):
        speak_flag = True if speak_override is None else speak_override
        save_path_flag = None
        return_bytes_flag = False

        def extract_tag(pattern, text):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1), text.replace(match.group(0), '').strip()
            return None, text

        save_path_flag, text = extract_tag(r'\[save="([^"]+)"\]', text)
        if re.search(r'\[bytes\]', text, re.IGNORECASE):
            return_bytes_flag, speak_flag = True, False
            text = re.sub(r'\[bytes\]', '', text, flags=re.IGNORECASE).strip()
        if re.search(r'\[speak=(false|off)\]', text, re.IGNORECASE):
            speak_flag = False
            text = re.sub(r'\[speak=(false|off)\]', '', text, flags=re.IGNORECASE).strip()
        
        file_path, text = extract_tag(r'\[file="([^"]+)"\]', text)
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read() + " " + text
            except Exception as e:
                self.console.print(f"[bold red]Error reading file {file_path}: {e}[/bold red]")
                return

        processed_text = self.dynamics_generator.process(text)
        if not self.headless:
            self.console.print("\n---")
            self.console.print(Syntax(processed_text, "ssml", theme="monokai", line_numbers=False))
        
        tag_regex = r'(\[pause=\d+\]|\[scale=[\d.]+\]|\[pitch=[\d.-]+\]|\[noise_scale=[\d.]+\]|\[noise_w=[\d.]+\])'
        parts = [p for p in re.split(tag_regex, processed_text) if p]
        
        sample_rate, channels = self.voice.config.sample_rate, 1
        synth_config = SynthesisConfig()
        current_pitch_semitones = 0
        all_audio_data = []

        with (_open_stream(sample_rate, channels) if speak_flag else nullcontext()) as st:
            progress_context = Progress(console=self.console) if not self.headless else nullcontext()
            with progress_context as progress:
                task = progress.add_task("[cyan]Synthesizing...", total=len(parts)) if not self.headless else None
                
                for part in parts:
                    if not self.headless: progress.advance(task)
                    if part.startswith('[pause='):
                        duration_ms = int(part.strip('[]').split('=')[1])
                        silence = np.zeros(int(sample_rate * (duration_ms / 1000.0)), dtype=np.int16)
                        if speak_flag and st: st.write(silence)
                        if save_path_flag or return_bytes_flag: all_audio_data.append(silence)
                    elif part.startswith('[scale='):
                        scale_val = float(part.strip('[]').split('=')[1]); synth_config.length_scale = 1.0 / scale_val if scale_val != 0 else 1.0
                    elif part.startswith('[pitch='):
                        pitch_val = float(part.strip('[]').split('=')[1]); current_pitch_semitones = -1 * pitch_val
                    elif part.startswith('[noise_scale='):
                        synth_config.noise_scale = float(part.strip('[]').split('=')[1])
                    elif part.startswith('[noise_w='):
                        synth_config.noise_w = float(part.strip('[]').split('=')[1])
                    else:
                        if not part.strip(): continue
                        raw_chunks = [np.frombuffer(c.audio_int16_bytes, dtype=np.int16) for c in self.voice.synthesize(part, synth_config)]
                        if not raw_chunks: continue
                        audio_int16 = np.concatenate(raw_chunks)
                        final_part_audio = audio_int16

                        if current_pitch_semitones != 0:
                            speed = 2.0 ** (current_pitch_semitones / 12.0)
                            audio_float32 = (audio_int16 / 32768.0).astype(np.float32)
                            reader, writer = ArrayReader(audio_float32.reshape(channels, -1)), ArrayWriter(channels=channels)
                            wsola(channels=channels, speed=speed).run(reader, writer)
                            stretched_audio = writer.data
                            resampled_audio = resample(stretched_audio, len(audio_int16), axis=1)
                            final_part_audio = (resampled_audio.flatten() * 32768.0).astype(np.int16)

                        if speak_flag and st: st.write(final_part_audio)
                        if save_path_flag or return_bytes_flag: all_audio_data.append(final_part_audio)
        
        if not self.headless: self.console.print("---")
        final_audio = np.concatenate(all_audio_data) if all_audio_data else np.array([], dtype=np.int16)

        if save_path_flag:
             with wave.open(save_path_flag, 'wb') as wf:
                wf.setnchannels(channels); wf.setsampwidth(2); wf.setframerate(sample_rate)
                wf.writeframes(final_audio.tobytes())
             self.console.print(f"[bold green]Audio saved to {save_path_flag}[/bold green]")

        if return_bytes_flag:
            return self._write_wav_to_buffer(final_audio, sample_rate, channels)
        return None

def start_cli(tts_voice):
    console = tts_voice.console
    console.print(Panel("[bold yellow]Dynamic TTS Voice Module[/bold yellow]\nEnter text to speak. Type 'q' to quit.", title="Welcome", border_style="green"))
    
    start_phrase = choice(tts_voice.settings['start_phrases'])
    tts_voice.say(start_phrase)
    
    while True:
        try:
            t = input(">>> ")
            if t.lower().strip() in ['qqq', 'q', 'quit', 'exit']:
                stop_phrase = choice(tts_voice.settings['stop_phrases'])
                console.print(f"[bold yellow]{stop_phrase}[/bold yellow]")
                tts_voice.say(stop_phrase)
                break
            if t.strip():
                tts_voice.say(t)
        except (KeyboardInterrupt, EOFError):
            stop_phrase = choice(tts_voice.settings['stop_phrases'])
            console.print(f"\n[bold yellow]{stop_phrase}[/bold yellow]")
            tts_voice.say(stop_phrase)
            break
    
    console.print("[bold red]XXXXXXXXXXXXXXXXXXXXXXXXXXXX[/bold red]")

if __name__ == '__main__':
    tts_voice_instance = Voice(settings_path="settings.json")
    start_cli(tts_voice_instance)
    quit()