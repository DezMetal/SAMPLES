# AirControl - Gesture-Based Computer Control

AirControl is a Python application that allows you to control your computer using hand gestures, powered by a Leap Motion sensor. It provides a robust, gesture-based interface for common tasks, effectively turning your hand movements into system commands.

The application uses pre-defined hand pose schemas (stored as `.json` files) to recognize gestures and trigger corresponding actions.

## Features

-   **Cursor Control**: Move the mouse cursor by moving your hand in a "neutral" pose.
-   **Clicking**: Perform left-clicks by pinching your fingers. A right-click can be triggered by folding your middle finger while pinching.
-   **Volume Control**: Adjust the system volume by raising or lowering your hand in a "flat" palm pose.
-   **Scrolling**: Scroll through pages by moving your hand up or down in a "fist" pose.
-   **Application Switching**: Switch between open windows (Alt+Tab and Alt+Shift+Tab) using a horizontal "chop" gesture.
-   **Pose-Based Activation**: Controls are activated by holding a specific hand pose for a short duration, preventing accidental inputs.
-   **Customizable Settings**: The `main.py` script contains a `CONTROL_SETTINGS` dictionary where you can fine-tune sensitivity, smoothing, and other parameters for each control function.

---
## Portfolio Highlight

### Use Cases
*   **Accessibility:** Provides an alternative input method for users with physical disabilities who may find traditional mice and keyboards challenging to use.
*   **Sterile Environments:** Enables touchless computer control in environments like labs, kitchens, or operating rooms where touching surfaces is not ideal.
*   **Presentations & Demos:** Control a presentation or application from a distance with intuitive hand gestures.
*   **Novelty & Prototyping:** Serves as a powerful base for creating unique games, interactive art installations, or VR/AR experiences.

### Proof of Concept
This project is a proof of concept for a **real-time, gesture-based human-computer interface (HCI)**. It demonstrates:
*   **Hardware Interfacing:** Capturing and interpreting complex 3D data from a specialized sensor (Leap Motion) in real-time.
*   **Event-Driven Architecture:** A listener-based model that processes a continuous stream of tracking data and triggers actions accordingly.
*   **Robust Gesture Recognition:** A `PoseMatcher` system that compares live hand data against a library of pre-defined JSON schemas, allowing for flexible and expandable gesture definitions.
*   **Signal Processing:** Implementation of smoothing (Exponential Moving Average), dead zones, and normalization to translate noisy, raw sensor data into smooth and intentional user control.

### Hireable Skills
*   **Python Development:** Advanced Python programming, including object-oriented design (OOP), modular code structure, and packaging.
*   **API & SDK Integration:** Experience with third-party hardware SDKs (`leap-cffi`) and system-level libraries (`pyautogui`, `keyboard`).
*   **Hardware Interfacing:** Proven ability to write software that interacts with and controls external hardware devices.
*   **Algorithm Design:** Developed a custom similarity scoring algorithm to match live poses against saved templates.
*   **Data Structures:** Used JSON for creating flexible and human-readable gesture definition files.
*   **Problem Solving:** Engineered a complete pipeline from raw sensor input to precise, reliable OS-level control, tackling challenges like input jitter and accidental activation.

---

## How It Works

The application runs a listener in the background that connects to the Leap Motion service. When it detects a hand, it uses a `PoseMatcher` class to compare the current hand data against a library of saved `.json` schemas (e.g., `fist.json`, `flat.json`).

When a pose is recognized and held, the corresponding control function (e.g., `VolumeControl`, `CursorControl`) is activated, translating your hand's movements into actions using libraries like `pyautogui` and `keyboard`.

## Tech Stack

-   **Core**: Python
-   **Hardware**: Leap Motion Controller
-   **Libraries**:
    -   `leap-cffi` (for Leap Motion sensor data)
    -   `pyautogui` (for mouse and keyboard control)
    -   `keyboard` (for hotkeys and system commands)

## Visuals

*Coming Soon: A video demonstrating the different hand gestures controlling the computer.*

## Getting Started

These instructions will get you a copy of the project up and running on your local machine.

### Prerequisites

*   Python 3.8+
*   Leap Motion Controller
*   Leap Motion Desktop Software (v5+)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/your-repository.git
    cd your-repository/AirControl
    ```

2.  **Install the Leap Motion Python bindings:**
    The necessary bindings are included in the `leapc-python-bindings-main` directory. Navigate into it and install the packages.
    ```sh
    cd leapc-python-bindings-main
    pip install -e leapc-cffi
    pip install -e leapc-python-api
    cd ..
    ```

3.  **Install the other dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    Ensure the Leap Motion service is running and your controller is connected.
    ```sh
    python main.py
    ```
    You should see output in your terminal as the application detects your hands and recognized poses.

5.  Press `Esc` to quit the application.
