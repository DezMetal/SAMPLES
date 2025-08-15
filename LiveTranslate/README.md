# LiveTranslate - Offline Voice Control & Translation

LiveTranslate is a Python application that demonstrates an offline-first, voice-controlled interface for real-time transcription and translation. It listens for spoken English commands, transcribes them locally, and can perform actions or translate the speech into Japanese. The application is designed to run on Windows and leverages local models for all its core functions, ensuring it can operate without an internet connection.

## Features

-   **Offline Speech Recognition**: Uses the Vosk engine with a local English model to transcribe audio in real time.
-   **Offline Translation**: Translates English text to Japanese using the Argos Translate library, which runs entirely offline.
-   **Offline Text-to-Speech**: Vocalizes the translated Japanese text using the built-in Windows TTS engine (`pyttsx3`).
-   **Voice-Controlled Framework**: A modular system allows you to map spoken commands to specific Python functions, making it extensible for new voice-based actions.
-   **Simple GUI**: A transparent Tkinter window displays the original English transcription and the Japanese translation.

## Core Libraries

-   **`vosk`**: For offline, real-time speech recognition.
-   **`argostranslate`**: For offline text translation.
-   **`pyttsx3`**: For using native text-to-speech engines.
-   **`pyaudio`**: For capturing microphone input.
-   **`tkinter`**: For the simple graphical user interface.
-   **`schedule`**: For time-based event scheduling.

---
## Portfolio Highlight

### Use Cases
*   **Offline Voice Assistant:** Build a custom voice assistant that can operate in environments without internet access.
*   **Accessibility Tools:** Create tools for users who rely on voice commands to interact with their computer.
*   **Custom Automation:** Automate repetitive tasks by triggering scripts with spoken phrases.
*   **Language Tools:** Assist with language learning or basic translation without needing to connect to the cloud.

### Proof of Concept
This project serves as a proof of concept for building a **modular, offline-first, voice-controlled application in Python**. It demonstrates:
*   **Local AI/ML Pipeline:** An end-to-end pipeline that uses locally-run models for speech recognition, translation, and speech synthesis, ensuring privacy and offline functionality.
*   **Extensible Command System:** A flexible architecture (`main.py`) that allows developers to easily register new voice commands and associate them with Python functions using regular expressions.
*   **System-Level Integration:** Integration with native OS features like the Windows TTS engine for low-latency audio output.
*   **Real-Time GUI Display:** Use of `tkinter` to provide immediate visual feedback for the transcribed and translated text.

### Hireable Skills
*   **Python Development:** Building applications with a modular and extensible architecture.
*   **Offline AI/ML Integration:** Experience in integrating and orchestrating multiple local libraries and models (`Vosk`, `ArgosTranslate`) to create a cohesive, offline-first application.
*   **GUI Development:** Proficient in using `tkinter` to create functional graphical interfaces in Python.
*   **Voice-Controlled Applications:** Designing and building systems that use voice as a primary input for control and interaction.
*   **Problem Solving:** Architecting a system that overcomes the need for cloud-based services, focusing on local processing and system-level integration.

---

## Visuals

*Coming Soon: A video demonstrating the real-time transcription and voice-activated commands.*

## Getting Started

These instructions will get you a copy of the project up and running on your local machine. This project is configured for **Windows**.

### Prerequisites

*   Python 3.8+
*   A working microphone
*   The project requires the `model-small-en-us` model for Vosk, which is included in this repository.

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

4.  The application will start listening immediately. The GUI window will appear, displaying the transcribed and translated text as you speak.

5.  Press `Esc` to quit the application (you may need to have the terminal window focused).

### Notes on Voices
The application uses the `pyttsx3` library, which relies on text-to-speech engines installed on your operating system. The default configuration in `functions.py` is set to use the Japanese voice (`TTS_MS_JA-JP_HARUKA_11.0`) on Windows. If you don't have this voice installed, you may need to change the `VID` variable in `functions.py` to a different voice available on your system.
