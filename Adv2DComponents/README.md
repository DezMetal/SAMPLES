# Adv2DComponents - Advanced 2D Components for Godot

This project is a collection of reusable components for the Godot Engine, designed to simplify the creation of 2D characters with common functionalities like movement, animation, and input handling.

The system is built around a component-based architecture, where different nodes provide specific behaviors to a central character scene.

## Key Components

*   **`base_char_2d_archetype.gd`**: A data-driven node that holds the configuration for a character. This allows you to define parameters like speed, jump velocity, animation names, and input actions in a single dictionary, making it easy to create different character types from the same base scene.

*   **`player_controller.gd`**: The core Player State Machine (PSM) that manages the character's state (e.g., idle, moving, jumping) and orchestrates the other components.

*   **`movement_component.gd`**: Handles the physical movement of the character, including walking, running, and jumping, based on parameters from the archetype.

*   **`input_component.gd`**: Manages player input, mapping actions defined in the archetype (e.g., "ui_left", "ui_right") to character behaviors.

*   **`animation_component.gd`**: Controls the character's animations, playing the correct animation based on the current state and direction.

*   **`physics_component.gd`**: Manages physics-related properties like gravity.

*   **`event_component.gd`**: A general-purpose component for handling events.

*   **`logging_component.gd`**: Provides a simple logging mechanism for debugging.

*   **`web_component.gd`**: A component for handling web requests.

## How to Use

1.  Attach the `player_controller.tscn` scene as the root of your character.
2.  Add a `base_char_2d_archetype.gd` script to a child node and configure the `data` dictionary with your character's specific parameters.
3.  Ensure the necessary components (Movement, Animation, etc.) are attached to the Player Controller scene.
4.  Map your input actions in Godot's Input Map to the actions defined in the archetype.
