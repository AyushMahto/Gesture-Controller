"""Runtime measurements collected from actual camera frames."""
from collections import deque
import time


class PerformanceMonitor:
    def __init__(self):
        self.started = time.monotonic()
        self.latencies = deque(maxlen=300)
        self.fps_values = deque(maxlen=300)
        self.gestures: dict[str, int] = {}
        self.frames = self.detected = 0
        self.last_frame = None

    def record(self, latency_ms: float, found_hand: bool):
        now = time.monotonic()
        self.frames += 1
        self.detected += int(found_hand)
        self.latencies.append(latency_ms)
        if self.last_frame:
            self.fps_values.append(1 / max(now - self.last_frame, 1e-6))
        self.last_frame = now

    def gesture(self, label: str):
        if label not in ("No hand", "Unrecognized"):
            self.gestures[label] = self.gestures.get(label, 0) + 1

    def snapshot(self):
        vals = list(self.latencies)
        return {"fps": sum(self.fps_values) / len(self.fps_values) if self.fps_values else 0,
                "latency_avg": sum(vals) / len(vals) if vals else 0,
                "latency_min": min(vals, default=0), "latency_max": max(vals, default=0),
                "detection_rate": 100 * self.detected / self.frames if self.frames else 0,
                "duration": time.monotonic() - self.started, "frames": self.frames}
