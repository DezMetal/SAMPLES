import pyaudio
import numpy as np
import sys
import argparse
import json
import hashlib
from enum import Enum

class Transceiver:
    class ReceiverState(Enum):
        LISTENING_FOR_PREAMBLE = 1
        DECODING_DATA = 2

    def __init__(self, config_path='config.json'):
        self.config = self._get_config(config_path)
        self.forward_map, self.reverse_map = self._generate_frequency_map()
        # Generate the preamble pattern based on the config
        self.preamble_pattern = [10, 5] * self.config.get('preamble_repetitions', 4)
        self.start_marker = b'\x02'
        self.end_marker = b'\x03'

    def _get_config(self, config_path):
        default_config = {
            "key": "Hmyk_QW6rV1G-c8Qp7NfPzYm-dY0d_L2q3t4_S5VfA4=",
            "waveform": "clipped_sine",
            "base_frequency_hz": 12875.0,
            "frequency_step_hz": 46.875,
            "chunk_duration_s": 0.07,
            "data_bits_per_tone": 4,
            "amplitude_threshold": 5.0,
            "preamble_repetitions": 4
        }
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                for key, value in default_config.items():
                    config.setdefault(key, value)
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"INFO: Config file not found or invalid. Using default settings.")
            return default_config

    def _generate_frequency_map(self):
        seed = int(hashlib.sha256(self.config['key'].encode('utf-8')).hexdigest()[:8], 16)
        np.random.seed(seed)
        num_values = 2**self.config['data_bits_per_tone']
        available_frequencies = [self.config['base_frequency_hz'] + i * self.config['frequency_step_hz'] for i in range(num_values)]
        np.random.shuffle(available_frequencies)
        forward_map = {i: available_frequencies[i] for i in range(num_values)}
        reverse_map = {freq: i for i, freq in forward_map.items()}
        return forward_map, reverse_map

    def _generate_tone(self, freq):
        num_samples = int(48000 * self.config['chunk_duration_s'])
        t = np.linspace(0, self.config['chunk_duration_s'], num_samples, endpoint=False)
        tone = np.sin(2 * np.pi * freq * t)
        waveform_type = self.config.get("waveform", "clipped_sine")

        if waveform_type == "clipped_sine":
            tone = np.clip(tone * 1.5, -1.0, 1.0)
        elif waveform_type == "square":
            tone = np.sign(tone)

        window = np.hanning(num_samples)
        return tone * window * 0.95

    def send(self, data_to_send):
        waveform_type = self.config.get("waveform", "clipped_sine")
        print(f"Generating transmission with '{waveform_type}' waveform...")

        waveform = np.array([], dtype=np.float32)

        for val in self.preamble_pattern:
            waveform = np.concatenate((waveform, self._generate_tone(self.forward_map[val])))

        data_with_markers = self.start_marker + data_to_send.encode('utf-8') + self.end_marker
        bits_per_tone = self.config['data_bits_per_tone']
        binary_data = ''.join(format(b, '08b') for b in data_with_markers)
        padding = (bits_per_tone - len(binary_data) % bits_per_tone) % bits_per_tone
        binary_data += '0' * padding

        for i in range(0, len(binary_data), bits_per_tone):
            value = int(binary_data[i:i + bits_per_tone], 2)
            waveform = np.concatenate((waveform, self._generate_tone(self.forward_map[value])))

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=48000, output=True)
        print("Transmitting...")
        stream.write(waveform.astype(np.float32).tobytes())
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Transmission complete.")

    def receive(self, message_callback=None):
        num_samples = int(48000 * self.config['chunk_duration_s'])
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=48000, input=True, frames_per_buffer=num_samples)

        print("Starting receiver...")
        state = self.ReceiverState.LISTENING_FOR_PREAMBLE
        value_buffer = []
        binary_buffer = ""
        message_buffer = ""

        try:
            while True:
                audio_data = stream.read(num_samples, exception_on_overflow=False)
                audio_np = np.frombuffer(audio_data, dtype=np.float32).copy() * np.hanning(num_samples)

                fft_result = np.fft.fft(audio_np)
                fft_freqs = np.fft.fftfreq(num_samples, d=1/48000)
                pos_indices = np.where(fft_freqs >= 0)
                peak_index = np.argmax(np.abs(fft_result[pos_indices]))
                peak_power = np.abs(fft_result[pos_indices])[peak_index]

                if peak_power < self.config['amplitude_threshold']:
                    if state == self.ReceiverState.DECODING_DATA:
                        print("\n[INFO] End of transmission. Resetting.")
                        state = self.ReceiverState.LISTENING_FOR_PREAMBLE
                        value_buffer.clear()
                    continue

                detected_freq = fft_freqs[pos_indices][peak_index]
                closest_freq = min(self.reverse_map.keys(), key=lambda x: abs(x - detected_freq))

                if abs(closest_freq - detected_freq) > self.config['frequency_step_hz']:
                    continue

                value = self.reverse_map[closest_freq]

                if state == self.ReceiverState.LISTENING_FOR_PREAMBLE:
                    value_buffer.append(value)
                    if len(value_buffer) > len(self.preamble_pattern):
                        value_buffer.pop(0)
                    if value_buffer == self.preamble_pattern:
                        print("\n[INFO] Preamble detected. Decoding data...")
                        sys.stdout.write("Message: ")
                        sys.stdout.flush()
                        state = self.ReceiverState.DECODING_DATA
                        value_buffer.clear()
                        binary_buffer = ""
                        message_buffer = ""

                elif state == self.ReceiverState.DECODING_DATA:
                    binary_buffer += format(value, f"0{self.config['data_bits_per_tone']}b")

                    while len(binary_buffer) >= 8:
                        byte_as_bits = binary_buffer[:8]
                        binary_buffer = binary_buffer[8:]
                        byte_value = int(byte_as_bits, 2)
                        decoded_byte = byte_value.to_bytes(1, 'big')

                        if decoded_byte == self.start_marker: continue
                        if decoded_byte == self.end_marker:
                            print("\n[INFO] End marker received. Resetting.")
                            if message_callback:
                                message_callback(message_buffer)
                            state = self.ReceiverState.LISTENING_FOR_PREAMBLE
                            break

                        try:
                            char = decoded_byte.decode('utf-8')
                            sys.stdout.write(char)
                            sys.stdout.flush()
                            message_buffer += char
                        except UnicodeDecodeError:
                            pass

        except (KeyboardInterrupt, SystemExit): print("\n\nQuitting...")
        finally:
            if 'stream' in locals() and stream.is_active():
                stream.stop_stream()
                stream.close()
            p.terminate()
            print("\nReceiver has stopped.")

def main():
    parser = argparse.ArgumentParser(
        description="A tool to transmit and receive data over audio using FSK modulation.",
        epilog="Usage examples:\n"
               "  Transmit text: python3 %(prog)s --send \"hello world\"\n"
               "  Transmit file: python3 %(prog)s --file ./message.txt\n"
               "  Receive data:  python3 %(prog)s\n"
               "All signal parameters are controlled by the 'config.json' file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--send', type=str, help='Text to transmit directly.')
    parser.add_argument('--file', type=str, help='Path to a text file to transmit.')
    parser.add_argument('--config', type=str, default='config.json', help='Path to the configuration file (default: config.json).')
    args = parser.parse_args()

    transceiver = Transceiver(args.config)

    if args.send and args.file:
        print("Error: Please use either --send or --file, not both.")
        sys.exit(1)

    data_to_process = None
    if args.file:
        try:
            with open(args.file, 'r') as f:
                data_to_process = f.read()
        except FileNotFoundError:
            print(f"Error: File not found at '{args.file}'")
            sys.exit(1)
    elif args.send:
        data_to_process = args.send

    if data_to_process:
        transceiver.send(data_to_process)
    else:
        def on_message_received(message):
            print("\n--- Callback: Message Fully Decoded ---")
            print(f"Data: \"{message}\"")
            print("---------------------------------------")

        transceiver.receive(on_message_received)

if __name__ == "__main__":
    main()
