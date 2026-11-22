"""Download the official MediaPipe Hand Landmarker task model once for offline use."""
from pathlib import Path
from urllib.request import urlopen

URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
TARGET = Path(__file__).parent / "models" / "hand_landmarker.task"

if __name__ == "__main__":
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        print(f"Model already exists: {TARGET}")
    else:
        print("Downloading MediaPipe Hand Landmarker model...")
        with urlopen(URL, timeout=60) as response, TARGET.open("wb") as output:
            output.write(response.read())
        print(f"Saved {TARGET}")
