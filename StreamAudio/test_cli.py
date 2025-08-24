import pyaudio
import wave
import io

from stream_audio import Voice

# Assume 'audio_bytes' contains your WAV audio data
# For example, loading from a file:
#with open("bytes.txt", "rb") as b:
#    audio_bytes = b.read()

V = Voice(headless=True)

audio_bytes = V.say("this is another test. hello [bytes]", False)

# Wrap bytes in BytesIO
audio_buffer = io.BytesIO(audio_bytes)

# Open the WAV file from the buffer
wf = wave.open(audio_buffer, 'rb')

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open stream
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)

# Read data in chunks and play
CHUNK = 1024
data = wf.readframes(CHUNK)
while data:
    stream.write(data)
    data = wf.readframes(CHUNK)

# Stop and close the stream
stream.stop_stream()
stream.close()

# Terminate PyAudio
p.terminate()