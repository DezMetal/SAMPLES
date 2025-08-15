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

---
## Portfolio Highlight

### Use Cases
*   **Live Conversations:** Enable real-time, two-way conversations between speakers of different languages (specifically English and Japanese).
*   **Travel & Tourism:** Help travelers communicate with locals for directions, ordering food, or asking questions.
*   **International Business:** Facilitate clearer communication in meetings or calls with international partners.
*   **Language Learning:** Allow learners to practice their pronunciation and get instant feedback on how their speech is understood and translated.

### Proof of Concept
This project is a proof of concept for a **real-time, bidirectional, speech-to-speech translation pipeline in Python**. It demonstrates:
*   **End-to-End Audio Pipeline:** A complete, seamless flow from capturing raw microphone audio to speaking the translated output.
*   **Concurrent Processing:** Effective use of Python's `threading` to manage multiple tasks simultaneously (listening, processing, speaking), which is essential for creating a responsive, real-time user experience.
*   **Robust API Consumption:** Implements strategies like rotating user-agents and using proxies to ensure reliable and continuous access to the Google Translate API, preventing service blocks.
*   **Voice-Controlled Interface:** The application itself is controlled by voice commands, allowing for hands-free operation to switch languages or mute the output.

### Hireable Skills
*   **Python Development:** Building multi-threaded applications and managing state in a concurrent environment.
*   **API Integration:** Proficient in using and orchestrating multiple third-party APIs and libraries (`speech_recognition`, `googletrans`, `gTTS`) to build a cohesive application.
*   **Digital Signal Processing (Audio):** Practical experience capturing, processing, and generating audio data in Python.
*   **Problem Solving:** Devised and implemented practical solutions (e.g., user-agent rotation) to overcome the limitations and usage constraints of free APIs.
*   **Software Architecture:** Designed a non-blocking, event-driven architecture suitable for real-time applications.

---

## Visuals

*Coming Soon: A video demonstrating the real-time translation of a spoken conversation.*

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

*   Python 3.8+
*   A working microphone

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/your-repository.git
    cd your-repository/LiveTranslate
    ```

2.  **Create a virtual environment and install dependencies:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```sh
    python main.py
    ```

4.  The application will calibrate for ambient noise and then start listening. Speak into your microphone to begin translation.

5.  Press `Esc` to quit the application (you may need to have the terminal window focused).
