import sys
import time
import json
import os
import math
import keyboard as kb  # Import for keyboard control (e.g., volume)
import pyautogui  # Import for mouse and scroll control
import leap

# --- Configuration ---
SCHEMA_DIR = "hand_schemas"  # Directory to save JSON schemas

# --- Global Control Settings ---
# This dictionary centralizes all tunable parameters for the control system.
# Adjust these values to customize sensitivity, responsiveness, and behavior.
CONTROL_SETTINGS = {
    # Default smoothing factor for controls that don't specify their own.
    # Value is the 'alpha' in an Exponential Moving Average (EMA).
    # Higher alpha (e.g., 0.7) = less smoothing, more responsive, more jitter.
    # Lower alpha (e.g., 0.1) = more smoothing, less responsive, less jitter.
    "default_smoothing_factor": 0.4,

    # Duration a pose must be held before its control activates (in seconds).
    # Prevents accidental activation from transient poses.
    "pose_hold_duration": 0.5,

    "volume_control": {
        # The vertical distance (in mm) your hand needs to travel up or down
        # from the activation point to cover the full volume range (0-100%).
        "relative_control_range_y": 150.0,
        "output_min_volume": 0.0,
        "output_max_volume": 100.0,
        # Uses default_smoothing_factor unless overridden here.
    },
    "cursor_control": {
        # --- ENHANCEMENT: Cursor-specific smoothing for better responsiveness ---
        "smoothing_factor": 0.6,

        # The physical area (in mm) your hand moves in to control the cursor.
        # This defines a "virtual box" around your hand's activation point.
        # Moving to the edge of this box moves the cursor across the screen.
        # SMALLER values = HIGHER sensitivity (less physical movement for more screen distance).
        # LARGER values = LOWER sensitivity (more physical movement for less screen distance).
        "virtual_space_range_x": 200.0,  # X-axis range in mm that maps to full screen width
        "virtual_space_range_y": 170.0,  # Y-axis (height) range in mm that maps to full screen height

        # Dead zone for cursor movement (based on normalized wrist movement).
        # Helps prevent cursor drift from tiny, unintentional hand movements.
        "dead_zone_threshold": 0.06,

        # Pinch strength required to initiate a click (0.0 to 1.0).
        # Higher value requires a more deliberate pinch.
        "pinch_threshold": 0.90,

        # --- ENHANCEMENT: Right-click modifier ---
        # If true, folding the middle finger while pinching will trigger a right-click.
        # If false, all pinches are left-clicks.
        "enable_right_click_modifier": True,
    },
    # --- NEW: Scroll Control Settings ---
    "scroll_control": {
        "smoothing_factor": 0.5,
        # Multiplier for scroll speed. Higher value = faster scrolling.
        # Represents scroll units per millimeter of vertical hand movement.
        "y_sensitivity": 12.0,  # Increased significantly for more noticeable scrolling
        # The distance (in mm) the hand must move before scrolling begins.
        "dead_zone_mm": 1.0,
    },
    # --- NEW: Chop Control Settings for Alt+Tab / Alt+Shift+Tab ---
    "chop_control": {
        "smoothing_factor": 0.4,  # Smoothing for horizontal hand movement
        # The normalized threshold (0.0 to 1.0) for smoothed_delta_x to trigger an Alt+Tab or Alt+Shift+Tab action.
        # A value of 0.5 means the hand must move halfway to the edge of its defined virtual space (related to chop_trigger_threshold_x in normalization).
        "chop_trigger_normalized_threshold": 0.5,
        # The normalized threshold (0.0 to 1.0) for smoothed_delta_x to return to,
        # to allow another Alt+Tab / Alt+Shift+Tab action to be triggered.
        "chop_reset_normalized_threshold": 0.2,
    },
    # --- NEW: Cursor Mode Toggle Settings (Mouse vs. Arrow Keys) ---
    "cursor_mode_toggle": {
        "toggle_key": "shift+space",  # Hotkey to switch between mouse and arrow modes
        "initial_mode": "mouse",  # Starting mode: "mouse" or "arrows"
        "arrow_control": {
            # Normalized value (0.0 to 1.0) for wrist movement to trigger an arrow key press.
            # Higher value means larger movement needed.
            "arrow_trigger_normalized_threshold": 0.8,
            # Normalized value (0.0 to 1.0) for wrist movement to reset the key press state.
            # Hand must return closer to the center than this to allow a new press.
            "arrow_reset_normalized_threshold": 0.3,
            # Time in seconds between repeated key presses for continuous movement.
            # Smaller value = faster continuous movement.
            "arrow_press_interval": 0.9,
        }
    }
}


class ControlNormalizer:
    """
    Processes raw tracking data into smoothed, normalized control values.
    Manages separate smoothing states for different controls.
    """

    def __init__(self, default_smoothing_factor=CONTROL_SETTINGS["default_smoothing_factor"]):
        self.default_smoothing_factor = default_smoothing_factor
        self.smoothed_values = {}

    def normalize_value(self, value, input_min, input_max, output_min, output_max,
                        control_id="default", smoothing_override=None):
        """
        Normalizes an input value from one range to another, with smoothing.

        :param smoothing_override: If provided, this smoothing factor is used instead of the default.
        :return: Smoothed and normalized output value.
        """
        clamped_value = max(input_min, min(input_max, value))

        if (input_max - input_min) == 0:
            normalized_output = output_min
        else:
            normalized_output = ((clamped_value - input_min) / (input_max - input_min)) * \
                                (output_max - output_min) + output_min

        # Determine which smoothing factor to use
        smoothing_factor = smoothing_override if smoothing_override is not None else self.default_smoothing_factor

        if control_id not in self.smoothed_values or self.smoothed_values[control_id] is None:
            self.smoothed_values[control_id] = normalized_output
        else:
            self.smoothed_values[control_id] = (smoothing_factor * normalized_output) + \
                                               ((1 - smoothing_factor) * self.smoothed_values[control_id])

        return self.smoothed_values[control_id]

    def reset_smoothing(self, control_id=None):
        """Resets the smoothing state for a specific control, or all controls."""
        if control_id:
            if control_id in self.smoothed_values:
                self.smoothed_values[control_id] = None
        else:
            self.smoothed_values = {}


class BaseControlFunction:
    """Abstract base class for all control functions."""

    def __init__(self, control_id, normalizer: ControlNormalizer):
        self.control_id = control_id
        self.normalizer = normalizer
        self.is_active = False

    def activate(self, hand_data=None):
        if not self.is_active:
            self.is_active = True
            self.normalizer.reset_smoothing(self.control_id)
            print(f"\nControl '{self.control_id}' activated.")

    def deactivate(self):
        if self.is_active:
            self.is_active = False
            self.normalizer.reset_smoothing(self.control_id)
            print(f"\nControl '{self.control_id}' deactivated.")

    def update(self, hand_data) -> str:
        raise NotImplementedError("Subclasses must implement 'update' method.")


class VolumeControl(BaseControlFunction):
    """Controls system volume by raising/lowering the hand."""

    def __init__(self, normalizer: ControlNormalizer):
        super().__init__("volume_control", normalizer)
        self._initial_wrist_y = None
        self.settings = CONTROL_SETTINGS["volume_control"]
        self._last_sent_volume = -1

    def activate(self, hand_data):
        super().activate(hand_data)
        if hand_data:
            self._initial_wrist_y = hand_data['arm']['next_joint'][1]
            self._last_sent_volume = -1
        else:
            print("\nVolume control activated without initial hand data.")

    def deactivate(self):
        super().deactivate()
        self._initial_wrist_y = None
        self._last_sent_volume = -1

    def update(self, hand_data) -> str:
        if not self.is_active or self._initial_wrist_y is None:
            return ""

        wrist_y = hand_data['arm']['next_joint'][1]
        input_min_y = self._initial_wrist_y - (self.settings["relative_control_range_y"] / 2)
        input_max_y = self._initial_wrist_y + (self.settings["relative_control_range_y"] / 2)

        # Note: Output range is reversed so that raising the hand (higher Y) increases volume.
        normalized_volume = self.normalizer.normalize_value(
            wrist_y, input_min_y, input_max_y,
            self.settings["output_min_volume"], self.settings["output_max_volume"],
            self.control_id
        )

        current_volume_int = int(normalized_volume)
        if self._last_sent_volume != -1:
            if current_volume_int > self._last_sent_volume:
                kb.send('volume up', do_press=True, do_release=True)
            elif current_volume_int < self._last_sent_volume:
                kb.send('volume down', do_press=True, do_release=True)
        self._last_sent_volume = current_volume_int

        return f" Volume: {current_volume_int}%"


class CursorControl(BaseControlFunction):
    """
    --- ENHANCED CURSOR CONTROL ---
    Controls the mouse cursor via wrist position and handles clicks via pinching.
    - Sensitivity is now properly tuned.
    - Uses its own smoothing factor for high responsiveness.
    - Features a right-click modifier gesture (fold middle finger while pinching).
    """

    def __init__(self, normalizer: ControlNormalizer):
        super().__init__("cursor_control", normalizer)
        self._initial_wrist_pos = None
        self._initial_screen_pos = None
        self.settings = CONTROL_SETTINGS["cursor_control"]
        self._is_left_clicking = False
        self._is_right_clicking = False  # State for right-click

        # New: Cursor mode and arrow key states
        self._cursor_mode = CONTROL_SETTINGS["cursor_mode_toggle"]["initial_mode"]
        self._last_arrow_press_time = {
            'up': 0.0, 'down': 0.0, 'left': 0.0, 'right': 0.0
        }
        self._arrow_key_states = {  # To track if a key is currently "held" by gesture
            'up': False, 'down': False, 'left': False, 'right': False
        }
        self.arrow_settings = CONTROL_SETTINGS["cursor_mode_toggle"]["arrow_control"]

    def set_mode(self, mode):
        """Sets the operating mode for cursor control (mouse or arrows)."""
        if mode in ["mouse", "arrows"]:
            self._cursor_mode = mode
            print(f"Cursor control mode set to: {self._cursor_mode}")
            # Reset all key states when changing mode
            for key in self._arrow_key_states:
                if self._arrow_key_states[key]:
                    kb.release(key)
                self._arrow_key_states[key] = False
            # Reset smoothing to prevent jumpiness when switching modes
            self.normalizer.reset_smoothing(f"{self.control_id}_x")
            self.normalizer.reset_smoothing(f"{self.control_id}_y")
        else:
            print(f"Invalid cursor mode: {mode}")

    def activate(self, hand_data):
        super().activate(hand_data)
        if hand_data:
            self._initial_wrist_pos = hand_data['arm']['next_joint']
            self._initial_screen_pos = pyautogui.position()
            self._is_left_clicking = False
            self._is_right_clicking = False
            # Ensure arrow keys are released if they were pressed before activation
            for key in self._arrow_key_states:
                if self._arrow_key_states[key]:
                    kb.release(key)
                self._arrow_key_states[key] = False
        else:
            print("\nCursor control activated without valid hand data.")
            self.deactivate()

    def deactivate(self):
        super().deactivate()
        self._initial_wrist_pos = None
        self._initial_screen_pos = None
        self._is_left_clicking = False
        self._is_right_clicking = False
        # Release all arrow keys when deactivating
        for key in self._arrow_key_states:
            if self._arrow_key_states[key]:
                kb.release(key)
            self._arrow_key_states[key] = False

    def update(self, hand_data) -> str:
        if not self.is_active or self._initial_wrist_pos is None or self._initial_screen_pos is None:
            return ""

        current_wrist_pos = hand_data['arm']['next_joint']
        screen_width, screen_height = pyautogui.size()

        # --- Common Calculations for both modes ---
        delta_wrist_x = current_wrist_pos[0] - self._initial_wrist_pos[0]
        delta_wrist_y_screen = current_wrist_pos[1] - self._initial_wrist_pos[1]

        # Normalize wrist movement deltas to -1.0 to 1.0 range based on virtual_space_range
        norm_wrist_x = max(-1.0, min(1.0, delta_wrist_x / (self.settings["virtual_space_range_x"] / 2)))
        norm_wrist_y_screen = max(-1.0, min(1.0, delta_wrist_y_screen / (self.settings["virtual_space_range_y"] / 2)))

        smoothed_norm_wrist_x = self.normalizer.normalize_value(
            norm_wrist_x, -1.0, 1.0, -1.0, 1.0, f"{self.control_id}_x",
            smoothing_override=self.settings["smoothing_factor"]
        )
        smoothed_norm_wrist_y_screen = self.normalizer.normalize_value(
            norm_wrist_y_screen, -1.0, 1.0, -1.0, 1.0, f"{self.control_id}_y",
            smoothing_override=self.settings["smoothing_factor"]
        )

        movement_magnitude = math.sqrt(smoothed_norm_wrist_x ** 2 + smoothed_norm_wrist_y_screen ** 2)
        if movement_magnitude < self.settings["dead_zone_threshold"]:
            smoothed_norm_wrist_x = 0.0
            smoothed_norm_wrist_y_screen = 0.0

        feedback = ""  # Initialize feedback string

        if self._cursor_mode == "mouse":
            # Release any arrow keys that might be stuck if mode changed
            for key in self._arrow_key_states:
                if self._arrow_key_states[key]:
                    kb.release(key)
                self._arrow_key_states[key] = False

            # --- Mouse Cursor Movement ---
            # User wants: move left -> cursor left. So, negative delta_wrist_x -> negative target_x_offset.
            # This means we should NOT negate smoothed_norm_wrist_x.
            target_x_offset = smoothed_norm_wrist_x * (screen_width / 2)

            # User wants: move up -> cursor up. So, positive delta_wrist_y_screen -> negative target_y_offset.
            # This means we should negate smoothed_norm_wrist_y_screen.
            target_y_offset = -smoothed_norm_wrist_y_screen * (screen_height / 2)

            target_screen_x = max(0, min(screen_width - 1, self._initial_screen_pos[0] + target_x_offset))
            target_screen_y = max(0, min(screen_height - 1, self._initial_screen_pos[1] + target_y_offset))

            pyautogui.moveTo(target_screen_x, target_screen_y, _pause=False)

            # --- Handle Clicking (Mouse Mode) ---
            pinch_detected = hand_data['pinch_strength'] > self.settings["pinch_threshold"]
            middle_finger_is_folded = not hand_data['digits'][2]['is_extended']
            is_right_click_intent = self.settings["enable_right_click_modifier"] and middle_finger_is_folded

            if pinch_detected:
                if is_right_click_intent:
                    if not self._is_right_clicking:
                        pyautogui.rightClick()
                        self._is_right_clicking = True
                        self._is_left_clicking = False
                        feedback = " RIGHT CLICK!"
                else:
                    if not self._is_left_clicking:
                        pyautogui.click()
                        self._is_left_clicking = True
                        self._is_right_clicking = False
                        feedback = " CLICK!"
            else:
                self._is_left_clicking = False
                self._is_right_clicking = False

            feedback = (f" Mode: Mouse | Cursor: ({target_screen_x:.0f}, {target_screen_y:.0f})"
                        f" Pinch: {hand_data['pinch_strength']:.2f}{feedback}")

        elif self._cursor_mode == "arrows":
            # Release any mouse clicks that might be stuck if mode changed
            if self._is_left_clicking:
                pyautogui.mouseUp(button='left')
                self._is_left_clicking = False
            if self._is_right_clicking:
                pyautogui.mouseUp(button='right')
                self._is_right_clicking = False

            current_time = time.time()
            arrow_trigger = self.arrow_settings["arrow_trigger_normalized_threshold"]
            arrow_reset = self.arrow_settings["arrow_reset_normalized_threshold"]
            press_interval = self.arrow_settings["arrow_press_interval"]

            # --- Arrow Key Logic ---
            # Up Arrow (move hand up)
            if smoothed_norm_wrist_y_screen > arrow_trigger:
                if not self._arrow_key_states['up']:
                    kb.press('up')
                    self._arrow_key_states['up'] = True
                    self._last_arrow_press_time['up'] = current_time
                elif current_time - self._last_arrow_press_time['up'] >= press_interval:
                    kb.press('up')  # Simulate continuous press
                    self._last_arrow_press_time['up'] = current_time
                feedback += " UP"
            elif self._arrow_key_states['up'] and smoothed_norm_wrist_y_screen < arrow_reset:
                kb.release('up')
                self._arrow_key_states['up'] = False

            # Down Arrow (move hand down)
            if smoothed_norm_wrist_y_screen < -arrow_trigger:
                if not self._arrow_key_states['down']:
                    kb.press('down')
                    self._arrow_key_states['down'] = True
                    self._last_arrow_press_time['down'] = current_time
                elif current_time - self._last_arrow_press_time['down'] >= press_interval:
                    kb.press('down')
                    self._last_arrow_press_time['down'] = current_time
                feedback += " DOWN"
            elif self._arrow_key_states['down'] and smoothed_norm_wrist_y_screen > -arrow_reset:
                kb.release('down')
                self._arrow_key_states['down'] = False

            # Left Arrow (move hand left)
            if smoothed_norm_wrist_x < -arrow_trigger:
                if not self._arrow_key_states['left']:
                    kb.press('left')
                    self._arrow_key_states['left'] = True
                    self._last_arrow_press_time['left'] = current_time
                elif current_time - self._last_arrow_press_time['left'] >= press_interval:
                    kb.press('left')
                    self._last_arrow_press_time['left'] = current_time
                feedback += " LEFT"
            elif self._arrow_key_states['left'] and smoothed_norm_wrist_x > -arrow_reset:
                kb.release('left')
                self._arrow_key_states['left'] = False

            # Right Arrow (move hand right)
            if smoothed_norm_wrist_x > arrow_trigger:
                if not self._arrow_key_states['right']:
                    kb.press('right')
                    self._arrow_key_states['right'] = True
                    self._last_arrow_press_time['right'] = current_time
                elif current_time - self._last_arrow_press_time['right'] >= press_interval:
                    kb.press('right')
                    self._last_arrow_press_time['right'] = current_time
                feedback += " RIGHT"
            elif self._arrow_key_states['right'] and smoothed_norm_wrist_x < arrow_reset:
                kb.release('right')
                self._arrow_key_states['right'] = False

            # Handle pinch for "Enter" or "Space" in arrow mode
            pinch_detected = hand_data['pinch_strength'] > self.settings["pinch_threshold"]
            if pinch_detected:
                if not self._is_left_clicking:  # Re-using _is_left_clicking for pinch state in arrow mode
                    kb.send('enter')  # Simulates Enter key press
                    self._is_left_clicking = True
                    feedback += " ENTER!"
            else:
                self._is_left_clicking = False  # Reset pinch state

            feedback = f" Mode: Arrows | Smoothed Norm: ({smoothed_norm_wrist_x:.2f}, {smoothed_norm_wrist_y_screen:.2f}){feedback}"

        return feedback


class ScrollControl(BaseControlFunction):
    """
    --- NEW CONTROL FUNCTION ---
    Scrolls vertically based on the up/down movement of a hand in a 'fist' pose.
    This is a relative control; continuous movement results in continuous scrolling.
    """

    def __init__(self, normalizer: ControlNormalizer):
        super().__init__("scroll_control", normalizer)
        self._last_wrist_y = None
        self.settings = CONTROL_SETTINGS["scroll_control"]

    def activate(self, hand_data):
        super().activate(hand_data)
        if hand_data:
            # On activation, we store the initial position but don't use it for scrolling yet.
            # The first 'update' call will establish the baseline.
            self._last_wrist_y = hand_data['arm']['next_joint'][1]
        else:
            print("\nScroll control activated without initial hand data.")

    def deactivate(self):
        super().deactivate()
        self._last_wrist_y = None

    def update(self, hand_data) -> str:
        if not self.is_active:
            return ""

        current_wrist_y = hand_data['arm']['next_joint'][1]

        # On the very first update after activation, just set the last position.
        if self._last_wrist_y is None:
            self._last_wrist_y = current_wrist_y
            return "Scroll Active"

        # Calculate the change in Y position since the last frame.
        delta_y = current_wrist_y - self._last_wrist_y

        # Apply dead zone to prevent jittery scrolling from minor movements.
        if abs(delta_y) < self.settings["dead_zone_mm"]:
            scroll_amount = 0
        else:
            # Apply sensitivity. Note that pyautogui.scroll uses inverted direction
            # (positive scrolls up, negative scrolls down), so we negate our delta.
            scroll_amount = -delta_y * self.settings["y_sensitivity"]

        # Apply smoothing to the scroll amount for a less jerky experience.
        smoothed_scroll = self.normalizer.normalize_value(
            scroll_amount, -100, 100, -100, 100,  # Input/output ranges are arbitrary here
            f"{self.control_id}_y",
            smoothing_override=self.settings["smoothing_factor"]
        )

        if abs(smoothed_scroll) > 0.1:  # Only scroll if there's meaningful movement
            pyautogui.scroll(int(smoothed_scroll))

        # Update the last known position for the next frame's calculation.
        self._last_wrist_y = current_wrist_y

        return f" Scrolling: {smoothed_scroll:+.1f}"


class ChopControl(BaseControlFunction):
    """
    Controls Alt+Tab / Alt+Shift+Tab based on horizontal wrist movement.
    """

    def __init__(self, normalizer: ControlNormalizer):
        super().__init__("chop_control", normalizer)
        self._initial_wrist_x = None
        self._last_action_direction = None  # 'left', 'right', or None
        self.settings = CONTROL_SETTINGS["chop_control"]

    def activate(self, hand_data):
        super().activate(hand_data)
        if hand_data:
            self._initial_wrist_x = hand_data['arm']['next_joint'][0]  # Get initial X position
            self._last_action_direction = None  # Reset action state on activation
            print(f"\nChop control activated! Initial X: {self._initial_wrist_x:.1f}")
        else:
            print("\nChop control activated without initial hand data.")
            self.deactivate()

    def deactivate(self):
        super().deactivate()
        self._initial_wrist_x = None
        self._last_action_direction = None
        print("\nChop control deactivated.")

    def update(self, hand_data) -> str:
        if not self.is_active or self._initial_wrist_x is None:
            return ""

        current_wrist_x = hand_data['arm']['next_joint'][0]

        # Calculate delta from initial position
        delta_x = current_wrist_x - self._initial_wrist_x

        # Normalize delta_x to a -1.0 to 1.0 range based on a reasonable expected movement range for the chop gesture.
        # We'll use a fixed range for normalization here, e.g., 100mm total range (-50 to +50).
        # This makes the smoothed_delta_x directly comparable to the normalized thresholds.
        normalization_range = 100.0  # Example: 100mm total movement range for normalization
        normalized_delta_x = max(-1.0, min(1.0, delta_x / (normalization_range / 2)))

        smoothed_delta_x = self.normalizer.normalize_value(
            normalized_delta_x,
            -1.0, 1.0,  # Input range for normalization
            -1.0, 1.0,  # Output to a normalized range
            f"{self.control_id}_x",
            smoothing_override=self.settings["smoothing_factor"]
        )

        feedback = " Chop Ready"

        # Check for Alt+Shift+Tab (move left, negative smoothed_delta_x)
        if smoothed_delta_x < -self.settings["chop_trigger_normalized_threshold"] and self._last_action_direction != 'left':
            kb.send('alt+shift+tab')
            self._last_action_direction = 'left'
            feedback = " Alt+Shift+Tab"
        # Check for Alt+Tab (move right, positive smoothed_delta_x)
        elif smoothed_delta_x > self.settings["chop_trigger_normalized_threshold"] and self._last_action_direction != 'right':
            kb.send('alt+tab')
            self._last_action_direction = 'right'
            feedback = " Alt+Tab"
        # Reset action direction if hand returns close to initial X position
        elif abs(smoothed_delta_x) < self.settings["chop_reset_normalized_threshold"]:
            self._last_action_direction = None
            feedback = " Chop Ready (Reset)"

        return f" Delta X: {delta_x:.1f} Smoothed Norm X: {smoothed_delta_x:.2f}{feedback}"


class PoseMatcher:
    # --- Static Helper Methods for Vector Math ---
    @staticmethod
    def _euclidean_distance(v1, v2):
        """Calculates Euclidean distance between two 3D vectors/points."""
        return math.sqrt((v1[0] - v2[0]) ** 2 + (v1[1] - v2[1]) ** 2 + (v1[2] - v2[2]) ** 2)

    @staticmethod
    def _vector_from_points(p1, p2):
        """Calculates a direction vector from point p1 to p2."""
        return [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]

    @staticmethod
    def _vector_magnitude(v):
        """Calculates the magnitude (length) of a 3D vector."""
        return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)

    @staticmethod
    def _dot_product(v1, v2):
        """Calculates the dot product of two 3D vectors."""
        return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

    @staticmethod
    def _angle_between_vectors(v1, v2):
        """Calculates the angle in radians between two 3D vectors."""
        mag1 = PoseMatcher._vector_magnitude(v1)
        mag2 = PoseMatcher._vector_magnitude(v2)
        if mag1 == 0 or mag2 == 0:
            return 0.0  # Handle zero magnitude to avoid division by zero
        dot = PoseMatcher._dot_product(v1, v2)
        clamped_dot = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        return math.acos(clamped_dot)

    # --- PoseMatcher Instance Methods ---
    def __init__(self, schema_dir, similarity_tolerance=25000.0):
        self.schema_dir = schema_dir
        self.similarity_tolerance = similarity_tolerance
        self.saved_poses = self._load_saved_poses()
        print(f"Loaded {len(self.saved_poses)} saved poses for recognition.")

    def _load_saved_poses(self):
        """Loads all JSON schemas from the schema directory."""
        poses = {}
        if not os.path.exists(self.schema_dir):
            print(f"Warning: Schema directory '{self.schema_dir}' not found.")
            return poses
        for filename in os.listdir(self.schema_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.schema_dir, filename)
                with open(filepath, 'r') as f:
                    try:
                        data = json.load(f)
                        pose_name_base = os.path.splitext(filename)[0].split('_')[0]
                        if isinstance(data, list):
                            for hand_data in data:
                                unique_key = f"{pose_name_base}_hand{hand_data['id']}_{'left' if hand_data['is_left'] else 'right'}"
                                poses[unique_key] = {
                                    'normalized_data': self._normalize_hand_data(hand_data),
                                    'is_left': hand_data['is_left']
                                }
                        else:
                            unique_key = f"{pose_name_base}_hand{data['id']}_{'left' if data['is_left'] else 'right'}"
                            poses[unique_key] = {
                                'normalized_data': self._normalize_hand_data(data),
                                'is_left': data['is_left']
                            }
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error processing {filename}: {e}")
        return poses

    def _normalize_hand_data(self, hand_data):
        """Normalizes hand data relative to the palm position."""
        normalized_data = json.loads(json.dumps(hand_data))  # Deep copy
        palm_pos = normalized_data["palm_position"]
        normalized_data["palm_position"] = [0.0, 0.0, 0.0]

        if "arm" in normalized_data and normalized_data["arm"]:
            for joint_type in ["prev_joint", "next_joint"]:
                if joint_type in normalized_data["arm"] and normalized_data["arm"][joint_type]:
                    joint = normalized_data["arm"][joint_type]
                    normalized_data["arm"][joint_type] = [j - p for j, p in zip(joint, palm_pos)]

        # Ensure 'direction' key exists for the hand, providing a default if missing
        normalized_data["direction"] = hand_data.get("direction", [0.0, 0.0, 0.0])

        for digit_data in normalized_data["digits"]:
            for bone_data in digit_data["bones"]:
                for joint_type in ["prev_joint", "next_joint"]:
                    if joint_type in bone_data and bone_data[joint_type]:
                        joint = bone_data[joint_type]
                        bone_data[joint_type] = [j - p for j, p in zip(joint, palm_pos)]
                # Ensure 'direction' key exists for each bone, providing a default if missing
                bone_data["direction"] = bone_data.get("direction", [0.0, 0.0, 0.0])
        return normalized_data

    def _compare_hand_data(self, live_hand_data_norm, saved_hand_data_norm):
        """Compares two normalized hand data dictionaries. Lower score is more similar."""
        score = 0.0
        weights = {
            "grab_pinch": 50.0, "palm_normal": 500.0, "hand_direction": 300.0,
            "arm_joint": 1.0, "finger_extension": 500.0, "bone_joint": 1.0,
            "bone_direction": 50.0, "finger_spread": 100.0
        }

        score += abs(live_hand_data_norm["grab_strength"] - saved_hand_data_norm["grab_strength"]) * weights["grab_pinch"]
        score += abs(live_hand_data_norm["pinch_strength"] - saved_hand_data_norm["pinch_strength"]) * weights["grab_pinch"]
        score += self._angle_between_vectors(live_hand_data_norm["palm_normal"], saved_hand_data_norm["palm_normal"]) * weights["palm_normal"]
        score += self._angle_between_vectors(live_hand_data_norm["direction"], saved_hand_data_norm["direction"]) * weights["hand_direction"]

        if "arm" in live_hand_data_norm and "arm" in saved_hand_data_norm:
            for joint_type in ["prev_joint", "next_joint"]:
                if live_hand_data_norm["arm"].get(joint_type) and saved_hand_data_norm["arm"].get(joint_type):
                    score += self._euclidean_distance(live_hand_data_norm["arm"][joint_type], saved_hand_data_norm["arm"][joint_type]) * weights["arm_joint"]

        for d_idx, live_digit in enumerate(live_hand_data_norm["digits"]):
            if d_idx >= len(saved_hand_data_norm["digits"]): break
            saved_digit = saved_hand_data_norm["digits"][d_idx]

            if live_digit["is_extended"] != saved_digit["is_extended"]:
                score += weights["finger_extension"]

            for b_idx, live_bone in enumerate(live_digit["bones"]):
                if b_idx >= len(saved_digit["bones"]): break
                saved_bone = saved_digit["bones"][b_idx]
                if live_bone.get("prev_joint") and saved_bone.get("prev_joint"):
                    score += self._euclidean_distance(live_bone["prev_joint"], saved_bone["prev_joint"]) * weights["bone_joint"]
                if live_bone.get("next_joint") and saved_bone.get("next_joint"):
                    score += self._euclidean_distance(live_bone["next_joint"], saved_bone["next_joint"]) * weights["bone_joint"]
                if live_bone.get("direction") and saved_bone.get("direction"):  # This check is now safer due to _normalize_hand_data
                    score += self._angle_between_vectors(live_bone["direction"], saved_bone["direction"]) * weights["bone_direction"]

        return score

    def match_frame_hands(self, live_hands_data):
        """Matches live hands to saved poses."""
        recognized_matches = []
        all_hand_match_debug_info = []

        for live_hand_data in live_hands_data:
            live_hand_normalized = self._normalize_hand_data(live_hand_data)
            best_match_name, lowest_score = None, float('inf')

            for pose_name_full_key, saved_pose_info in self.saved_poses.items():
                if live_hand_data["is_left"] != saved_pose_info['is_left']:
                    continue

                score = self._compare_hand_data(live_hand_normalized, saved_pose_info['normalized_data'])
                if score < lowest_score:
                    lowest_score, best_match_name = score, pose_name_full_key

            display_name = best_match_name.split('_hand')[0] if best_match_name else "N/A"
            all_hand_match_debug_info.append({
                'hand_id': live_hand_data["id"],
                'best_match_name': display_name,
                'lowest_score': lowest_score
            })

            if best_match_name and lowest_score <= self.similarity_tolerance:
                original_pose_name = best_match_name.split('_hand')[0]
                recognized_matches.append((live_hand_data["id"], original_pose_name))

        return recognized_matches, all_hand_match_debug_info


class MyListener(leap.Listener):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']

    def __init__(self, pose_matcher_instance, control_normalizer_instance):
        super().__init__()
        self.pose_matcher = pose_matcher_instance
        self.control_normalizer = control_normalizer_instance
        self.current_hand_data = []
        self._quit_requested = False
        self._capture_requested = False
        self.recognized_poses_this_frame = []
        self.current_hand_debug_scores = []
        self.active_control_function = None
        self._pose_start_times = {}

        self.control_functions = {
            'flat': VolumeControl(self.control_normalizer),
            'neutral': CursorControl(self.control_normalizer),  # Changed trigger pose to 'neutral'
            'fist': ScrollControl(self.control_normalizer),
            'chop': ChopControl(self.control_normalizer),  # Added ChopControl
        }
        # Reference to the CursorControl instance for mode toggling
        self.cursor_control_instance = self.control_functions['neutral']
        self.cursor_toggle_key = CONTROL_SETTINGS["cursor_mode_toggle"]["toggle_key"]

    def on_connection_event(self, event):
        print("Connected to Leap Motion service.")

    def on_device_event(self, event):
        try:
            with event.device.open():
                info = event.device.get_info()
        except leap.LeapCannotOpenDeviceError:
            info = event.device.get_info()
        print(f"Found device {info.serial}")

    def toggle_cursor_mode(self):
        """Toggles the cursor control mode between 'mouse' and 'arrows'."""
        current_mode = self.cursor_control_instance._cursor_mode
        new_mode = "arrows" if current_mode == "mouse" else "mouse"
        self.cursor_control_instance.set_mode(new_mode)

    def on_tracking_event(self, event):
        try:
            hands_in_frame_data = [self._extract_hand_data(hand) for hand in event.hands]
            control_feedback = ""

            if hands_in_frame_data:
                self.recognized_poses_this_frame, self.current_hand_debug_scores = \
                    self.pose_matcher.match_frame_hands(hands_in_frame_data)

                activatable_controls = {}
                current_recognized_poses = {name for _, name in self.recognized_poses_this_frame}

                for pose_name in current_recognized_poses:
                    if pose_name not in self._pose_start_times:
                        self._pose_start_times[pose_name] = time.time()

                for pose in list(self._pose_start_times.keys()):
                    if pose not in current_recognized_poses:
                        del self._pose_start_times[pose]

                for hand_id, pose_name in self.recognized_poses_this_frame:
                    if pose_name in self.control_functions:
                        hold_time = time.time() - self._pose_start_times.get(pose_name, time.time())
                        if hold_time >= CONTROL_SETTINGS["pose_hold_duration"]:
                            activatable_controls[pose_name] = hand_id
                        elif not self.active_control_function:
                            remaining = CONTROL_SETTINGS["pose_hold_duration"] - hold_time
                            control_feedback = f" Holding '{pose_name}' ({max(0, remaining):.1f}s)"

                next_active_control = None
                controlling_hand_data = None

                current_active_pose = next((p for p, c in self.control_functions.items() if c == self.active_control_function), None)
                if current_active_pose and current_active_pose in activatable_controls:
                    next_active_control = self.active_control_function
                    hand_id = activatable_controls[current_active_pose]
                    controlling_hand_data = next((h for h in hands_in_frame_data if h['id'] == hand_id), None)
                elif activatable_controls:
                    pose_name_to_activate = list(activatable_controls.keys())[0]
                    next_active_control = self.control_functions[pose_name_to_activate]
                    hand_id = activatable_controls[pose_name_to_activate]
                    controlling_hand_data = next((h for h in hands_in_frame_data if h['id'] == hand_id), None)

                if self.active_control_function != next_active_control:
                    if self.active_control_function:
                        self.active_control_function.deactivate()
                    self.active_control_function = next_active_control
                    if self.active_control_function:
                        self.active_control_function.activate(controlling_hand_data)

                if self.active_control_function and controlling_hand_data:
                    control_feedback = self.active_control_function.update(controlling_hand_data)
                elif self.active_control_function and not controlling_hand_data:
                    self.active_control_function.deactivate()
                    self.active_control_function = None

                summary_parts = self._get_summary_parts(event.hands)
                score_parts = [f"ID:{d['hand_id']} Best:'{d['best_match_name']}' Score:{d['lowest_score']:.0f}" for d in self.current_hand_debug_scores]
                recognized_text = " Recognized: " + ", ".join([f"{name}({hid})" for hid, name in self.recognized_poses_this_frame]) if self.recognized_poses_this_frame else ""

                status_line = f"{', '.join(summary_parts)} | Tol:{self.pose_matcher.similarity_tolerance:.0f} | {', '.join(score_parts)}{recognized_text}{control_feedback}"
                sys.stdout.write("\r" + " " * 200 + "\r" + status_line)
                sys.stdout.flush()

            else:
                if self.active_control_function:
                    self.active_control_function.deactivate()
                    self.active_control_function = None
                self._pose_start_times.clear()
                sys.stdout.write("\rNo hands detected." + " " * 180 + "\r")
                sys.stdout.flush()

            self.current_hand_data = hands_in_frame_data
            if self._capture_requested:
                self._capture_requested = False
                self._save_captured_data()
        except Exception as e:
            # Add exception printing to see errors in the console without crashing
            print(f"\nCaught exception in listener callback: {type(e)}, {e}, {e.__traceback__}")

    def _extract_hand_data(self, hand):
        return {
            "id": hand.id, "is_left": hand.type == leap.HandType.Left,
            "palm_position": self._vec_to_list(hand.palm.position),
            "palm_normal": self._vec_to_list(hand.palm.normal),
            "direction": self._vec_to_list(hand.palm.direction),
            "grab_strength": hand.grab_strength, "pinch_strength": hand.pinch_strength,
            "arm": {"prev_joint": self._vec_to_list(hand.arm.prev_joint), "next_joint": self._vec_to_list(hand.arm.next_joint)},
            "digits": [{
                "type": self.finger_names[d_idx], "is_extended": digit.is_extended,
                "bones": [{
                    "type": self.bone_names[b_idx],
                    "prev_joint": self._vec_to_list(bone.prev_joint),
                    "next_joint": self._vec_to_list(bone.next_joint),
                    # --- FIX: Calculate bone direction manually ---
                    # The Leap.Bone object does not have a direct .direction attribute.
                    # We calculate it by subtracting the start joint from the end joint.
                    "direction": [
                        bone.next_joint.x - bone.prev_joint.x,
                        bone.next_joint.y - bone.prev_joint.y,
                        bone.next_joint.z - bone.prev_joint.z
                    ]
                } for b_idx, bone in enumerate(digit.bones)]
            } for d_idx, digit in enumerate(hand.digits)]
        }

    def _get_summary_parts(self, hands):
        return [f"{'L' if h.type == leap.HandType.Left else 'R'}({h.id}) Grab:{h.grab_strength:.2f} Pinch:{h.pinch_strength:.2f}" for h in hands]

    def _vec_to_list(self, vec):
        return [vec.x, vec.y, vec.z]

    def trigger_capture(self):
        self._capture_requested = True
        print("\nCapture requested. Waiting for next frame...")

    def trigger_quit(self):
        self._quit_requested = True
        print("\nQuit requested. Exiting...")

    def _save_captured_data(self):
        if not self.current_hand_data:
            print("\nNo hand data to capture.")
            return

        pose_name = input(f"\nEnter name for this {len(self.current_hand_data)}-hand pose (e.g., 'fist'): ").strip()
        if not pose_name:
            print("Capture cancelled.")
            return

        filename = os.path.join(SCHEMA_DIR, f"{pose_name}_{int(time.time())}.json")
        try:
            os.makedirs(SCHEMA_DIR, exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(self.current_hand_data, f, indent=4)
            print(f"\nPose saved to {filename}")
            print("\n--- Captured Data ---")
            print(json.dumps(self.current_hand_data, indent=2))
            print("---------------------")
            # Reload poses to include the new one immediately
            self.pose_matcher.saved_poses = self.pose_matcher._load_saved_poses()
        except Exception as e:
            print(f"Error saving pose: {e}")


def main():
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    if not os.path.exists(SCHEMA_DIR):
        os.makedirs(SCHEMA_DIR)
        print(f"Created directory: {SCHEMA_DIR}")

    pose_matcher = PoseMatcher(SCHEMA_DIR)
    control_normalizer = ControlNormalizer()
    my_listener = MyListener(pose_matcher, control_normalizer)

    kb.add_hotkey(my_listener.cursor_toggle_key, my_listener.toggle_cursor_mode)  # Hook the toggle hotkey
    kb.add_hotkey('ctrl+s', my_listener.trigger_capture)
    kb.add_hotkey('esc', my_listener.trigger_quit)

    print("\n--- Air Controls ---")
    print("Poses: 'flat' (Volume), 'neutral' (Cursor), 'fist' (Scroll), 'chop' (Alt+Tab)")
    print(f"Toggle Cursor Mode: '{my_listener.cursor_toggle_key}'")
    print("Hotkeys: [Ctrl+S] to Capture Pose | [Esc] to Quit")

    connection = leap.Connection()
    connection.add_listener(my_listener)

    try:
        with connection.open():
            connection.set_tracking_mode(leap.TrackingMode.Desktop)
            while not my_listener._quit_requested:
                time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nExiting via KeyboardInterrupt.")
    finally:
        connection.remove_listener(my_listener)
        kb.unhook_all()
        print("Application closed.")


if __name__ == "__main__":
    main()
