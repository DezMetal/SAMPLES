# AudioTransmit - Data Over Audio

**AudioTransmit** is a Python tool for transmitting and receiving data encoded as audio signals using Frequency-Shift Keying (FSK) modulation. It can be used to send text or files between devices using a simple audio connection (e.g., a 3.5mm audio cable).

The script uses a secure, key-based frequency mapping to ensure that only a receiver with the same key can decode the transmission.

---

## How It Works

The script performs two main functions:

1.  **Sending:** It converts input data (text or files) into a sequence of bytes. These bytes are then modulated into a series of audio tones at specific frequencies. A preamble signal is added to the beginning of the transmission to allow the receiver to synchronize.
2.  **Receiving:** It listens to an audio input, performing real-time Fast Fourier Transform (FFT) to detect dominant frequencies. When a valid preamble is detected, it begins decoding the subsequent tones back into data bytes until an end-of-message marker is found.

All signal parameters, such as the base frequency, data rate, and security key, can be configured in the `config.json` file.

## Requirements

*   Python 3
*   `pyaudio`
*   `numpy`

You will also need `portaudio` installed on your system for `pyaudio` to function correctly.

**On Debian/Ubuntu:**
```bash
sudo apt-get install portaudio19-dev
```

**On macOS (using Homebrew):**
```bash
brew install portaudio
```

Then, install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

The script can be run from the command line in either sender or receiver mode.

### To Receive Data

Simply run the script without any arguments. It will start listening on the default audio input device.

```bash
python3 AudioTrans.py
```

### To Transmit Data

You can transmit a simple text string or the contents of a file.

**Transmit a string:**
```bash
python3 AudioTrans.py --send "Hello, this is a test transmission."
```

**Transmit a file:**
```bash
python3 AudioTrans.py --file ./path/to/your/message.txt
```

## Configuration

The `config.json` file allows you to customize the signal parameters:

*   `key`: A secret key used to seed the frequency randomization. **Both sender and receiver must use the same key.**
*   `base_frequency_hz`: The starting frequency for the transmission band.
*   `frequency_step_hz`: The difference in Hz between each data tone.
*   `chunk_duration_s`: The duration of each audio tone, which controls the data rate.
*   `data_bits_per_tone`: The number of bits encoded in each tone (e.g., 4 bits = 16 unique frequencies).
*   `amplitude_threshold`: The minimum signal power required for the receiver to detect a tone.
*   `waveform`: The shape of the audio wave ("clipped_sine" or "square").
*   `preamble_repetitions`: The number of times the preamble pattern is repeated.

A higher `chunk_duration_s` is more reliable but slower. A higher `data_bits_per_tone` increases the data rate but makes the transmission more susceptible to noise.
