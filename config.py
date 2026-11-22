"""HandWave runtime defaults."""
from dataclasses import dataclass


@dataclass
class Settings:
    webcam_index: int = 0
    detection_confidence: float = 0.55
    tracking_confidence: float = 0.55
    hold_seconds: float = 0.75
    cooldown_seconds: float = 1.0
    actions_enabled: bool = False
    show_landmarks: bool = True
    camera_width: int = 960
    camera_height: int = 540


GESTURES = {
    (0, 0, 0, 0, 0): "Fist",
    (0, 1, 0, 0, 0): "One finger",
    (0, 1, 1, 0, 0): "Two fingers",
    (0, 1, 1, 1, 0): "Three fingers",
    (0, 1, 1, 1, 1): "Four fingers",
    (1, 1, 1, 1, 1): "Open palm",
}

COMMANDS = {
    "Fist": "Mute / unmute", "One finger": "Next slide",
    "Two fingers": "Previous slide", "Three fingers": "Play / pause",
    "Four fingers": "Volume down", "Open palm": "Volume up",
}
