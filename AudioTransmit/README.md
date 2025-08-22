# AudioTransmit - Data Over Audio

**AudioTransmit** is a Python application for transmitting and receiving data wirelessly between nearby devices using sound. It encodes data into a sequence of audio tones (FSK modulation) and uses a key-based frequency mapping to ensure that only a receiver with the same key can decode the transmission.

This tool does not require any physical connection like an audio cable. One device can transmit data through its speakers, and another device running the script in receiver mode can pick it up through its microphone.

---

## How It Works

The application operates in two modes:

1.  **Sending:** The script converts a string or file into binary data. This data is then modulated into a series of audio tones at specific, high frequencies. A unique, pseudo-random frequency map is generated based on a secret `key` in the `config.json` file. This ensures the transmission is secure, as only a receiver with the identical key can interpret the frequency shifts correctly.
2.  **Receiving:** In its default mode, the script listens to the microphone input. It performs a real-time Fast Fourier Transform (FFT) on the incoming audio to detect the frequencies being played. After detecting a valid preamble signal, it decodes the subsequent tones back into binary data and reconstructs the original message.

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

The script is run from the command line. To transmit, one machine runs the script with `--send` or `--file`. To receive, another machine simply runs the script with no arguments.

### To Receive Data

Run the script without any arguments on the receiving machine. It will start listening through the default microphone.

```bash
python3 AudioTrans.py
```

### To Transmit Data

Run the script on the sending machine with the data you want to transmit.

**Transmit a string:**
```bash
python3 AudioTrans.py --send "Hello from across the room"
```

**Transmit a file:**
```bash
python3 AudioTrans.py --file ./my_secret_message.txt
```

## Configuration

For a transmission to be successful, **both the sender and receiver must have identical `config.json` files.**

*   `key`: A secret string used to seed the frequency randomization. This is the core of the security.
*   `base_frequency_hz`: The starting frequency for the transmission band. It's best to use high frequencies that are less audible to humans.
*   `chunk_duration_s`: The duration of each audio tone. A longer duration is more reliable but results in a slower data rate.
*   `data_bits_per_tone`: The number of bits encoded in each tone. More bits per tone increases the data rate but makes the transmission more susceptible to noise.
