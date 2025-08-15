# Adv2DComponents - Advanced 2D Godot Components

## Problem Statement

This project provides a collection of reusable, modular components for the Godot Engine, designed to accelerate the development of 2D games by simplifying the creation of complex character controllers.

## Features

-   **Component-Based Architecture**: Build complex characters by combining small, focused components.
-   **Data-Driven Design**: Character properties (speed, jump height, animation names) are defined in a central `archetype` script, allowing for easy creation of character variations.
-   **Player State Machine (PSM)**: A robust state machine (`player_controller.gd`) manages character states like idle, moving, and jumping.
-   **Modular Components**: Includes individual components for:
    -   `MovementComponent`: Handles walking, running, and jumping.
    -   `InputComponent`: Maps Godot Input Actions to character behavior.
    -   `AnimationComponent`: Drives the `AnimationPlayer` based on state.
    -   `PhysicsComponent`: Manages gravity and other physics properties.
    -   And more for events, logging, and web requests.

---
## Portfolio Highlight

### Use Cases
*   **Rapid Prototyping:** Quickly create and test different character controllers for 2D platformers, RPGs, and action games without rewriting code.
*   **Team Collaboration:** Designers can create and tweak character archetypes in the Godot editor using the data-driven approach, while programmers focus on component logic.
*   **Scalable Game Design:** Easily manage hundreds of unique enemies or character classes by creating new archetypes, rather than new scenes or scripts for each one.

### Proof of Concept
This project serves as a proof of concept for a **decoupled, data-driven architecture** in Godot. It demonstrates that complex game entities can be assembled from modular components whose properties are configured remotely from a central "archetype" data source. This is a powerful pattern that separates character *data* from character *logic*, leading to a more flexible, maintainable, and scalable codebase.

### Hireable Skills
*   **Game Architecture:** Proficient in designing and implementing component-based and data-driven design patterns.
*   **Godot & GDScript:** Strong practical skills in Godot Engine 4.x and GDScript, including scene management, custom nodes, and signals.
*   **Problem Solving:** Identified the common challenge of monolithic character controllers and engineered a modular, reusable solution.
*   **Tool Development:** Created a set of tools that improve the development workflow for game designers and programmers.

---

## Tech Stack

-   **Engine**: Godot 4.x
-   **Language**: GDScript

## Visuals

*Coming Soon: A GIF showing a character built with these components running and jumping in a simple test environment.*

## Getting Started

To use these components in your own Godot project:

1.  **Copy the `Adv2DComponents` directory** into your Godot project's folder.

2.  **Create your character scene.** A typical setup would be a `CharacterBody2D` as the root.

3.  **Instance the Player Controller:**
    -   Instance the `Adv2DComponents/player_controller.tscn` scene as a child of your character. This scene comes pre-packaged with all the necessary components.

4.  **Create and Configure the Archetype:**
    -   Add a new `Node` to your character scene and attach the `Adv2DComponents/base_char_2d_archetype.gd` script to it.
    -   In the Inspector for this node, you will see a `Data` property. This is where you define your character's behavior. For example:
        ```gdscript
        # In your archetype node's script or directly in the inspector
        var data = {
            "WALK_SPEED": 100.0,
            "JUMP_VELOCITY": -300.0,
            "ANIMATIONS": {
                "idle": "idle_animation_name",
                "move": "run_animation_name"
            },
            "INPUT_ACTIONS": {
                "jump": "ui_accept"
            }
        }
        ```

5.  **Connect the Archetype:**
    -   In the `player_controller.gd` script (or from the Inspector), assign your newly created archetype node to the `archetype` property.

6.  **Set up Input Map:**
    -   Go to `Project > Project Settings > Input Map` and make sure the actions you defined in your archetype (e.g., `ui_accept`) are configured.

Now, when you run your character scene, the `player_controller` will use the data from your archetype to manage movement, animations, and input.
