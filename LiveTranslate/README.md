# LiveTranslate - Real-Time Voice Translator

LiveTranslate is a Python application that provides real-time, bidirectional voice translation between English and Japanese. It runs in the background, listening for speech and automatically translating it to the desired target language, which is then spoken aloud.

## Features

-   **Speech-to-Speech Translation**: The application captures audio from a microphone, sends it to a speech-recognition service, translates the resulting text, and then uses a text-to-speech engine to voice the translation.
-   **Bidirectional**: It can translate from English to Japanese and from Japanese to English.
-   **Automatic Language Detection**: The tool automatically detects the language of the input speech.
-   **Voice-Controlled**: The application can be controlled through voice commands, such as "change language mode" to switch the translation direction or "disable voice" to mute the text-to-speech output.
-   **Background Operation**: It runs continuously in the background, allowing you to use it while you work in other applications.

## Core Libraries

-   **`speech_recognition`**: For capturing microphone input and recognizing speech using the Google Web Speech API.
-   **`googletrans`**: For translating the recognized text.
-   **`gTTS` (Google Text-to-Speech)**: For converting the translated text back into speech.
-   **`playsound`**: For playing the generated audio files.
-   **`keyboard`**: For monitoring hotkeys (though the primary control is via voice).

## How to Use

1.  Ensure you have a working microphone connected.
2.  Run the `main.py` script.
3.  The application will calibrate for ambient noise and then start listening.
4.  Speak into your microphone. The application will detect the language, print the original and translated text to the console, and speak the translation aloud.
5.  Use voice commands like "switch language" to change the translation mode or "disable voice" to turn off the audio output.
