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

## How It Works

The application runs a listener in the background that connects to the Leap Motion service. When it detects a hand, it uses a `PoseMatcher` class to compare the current hand data against a library of saved `.json` schemas (e.g., `fist.json`, `flat.json`).

When a pose is recognized and held, the corresponding control function (e.g., `VolumeControl`, `CursorControl`) is activated, translating your hand's movements into actions using libraries like `pyautogui` and `keyboard`.

## Dependencies

-   `leap-python` (and its dependencies, included in the `leapc-python-bindings-main` directory)
-   `pyautogui`
-   `keyboard`
-   `gTTS` (implicitly used via `playsound`)
-   `random_user_agent`

To run the application, you will need to have the Leap Motion desktop software installed and a Leap Motion sensor connected.
