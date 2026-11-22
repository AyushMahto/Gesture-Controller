"""Safe, opt-in desktop command dispatch."""
import time


class CommandController:
    def __init__(self, enabled: bool = False, cooldown: float = 1.0):
        self.enabled, self.cooldown = enabled, cooldown
        self.last_command_at = 0.0
        self.armed = True
        self.executed = 0

    def rearm(self) -> None:
        self.armed = True

    def dispatch(self, gesture: str) -> str:
        if not self.armed:
            return "Waiting for gesture release"
        if not self.enabled:
            return "Preview only"
        now = time.monotonic()
        if now - self.last_command_at < self.cooldown:
            return "Cooling down"
        try:
            import pyautogui
            if gesture == "Fist":
                pyautogui.press("volumemute")
            elif gesture == "One finger":
                pyautogui.press("right")
            elif gesture == "Two fingers":
                pyautogui.press("left")
            elif gesture == "Three fingers":
                pyautogui.press("space")
            elif gesture == "Four fingers":
                pyautogui.press("volumedown")
            elif gesture == "Open palm":
                pyautogui.press("volumeup")
            else:
                return "No mapped command"
        except Exception as exc:
            return f"Command error: {exc}"
        self.last_command_at, self.executed, self.armed = now, self.executed + 1, False
        return "Command sent"
