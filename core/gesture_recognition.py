"""Rule-based gesture recognition over MediaPipe's 21 hand landmarks."""
from collections import Counter, deque
from typing import Sequence
from config import GESTURES


def extended_fingers(points: Sequence[tuple[float, float]], handedness: str) -> tuple[int, int, int, int, int]:
    """Return thumb/index/middle/ring/pinky extension flags using normalized coordinates."""
    if len(points) != 21:
        raise ValueError("Expected exactly 21 landmarks")
    # Thumb uses horizontal displacement; fingers use tip vs. PIP y, tolerant of modest tilt.
    thumb = points[4][0] > points[3][0] if handedness.lower() == "right" else points[4][0] < points[3][0]
    fingers = [points[tip][1] < points[pip][1] for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18))]
    return (int(thumb), *(int(v) for v in fingers))


def classify(points: Sequence[tuple[float, float]], handedness: str) -> tuple[str, int]:
    flags = extended_fingers(points, handedness)
    return GESTURES.get(flags, "Unrecognized"), sum(flags)


class GestureVoter:
    def __init__(self, window: int = 9):
        self.samples: deque[str] = deque(maxlen=max(1, window))

    def update(self, label: str | None) -> tuple[str, float]:
        self.samples.append(label or "No hand")
        winner, count = Counter(self.samples).most_common(1)[0]
        return winner, count / len(self.samples) * 100
