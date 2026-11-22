# HandWave

HandWave is an offline, webcam-based gesture interface for common presentation and media controls. The app starts in preview mode. Computer actions require a separate explicit confirmation each session.

## Problem and objectives

Hands-free computer interaction can help presenters and users with limited access to physical controls. This project detects six hand poses, maps them to keyboard/media commands, and provides transparent runtime measurements plus a workflow for independently labelled recognition evaluation.

## Features

- 21-point hand landmark tracking using MediaPipe Hand Landmarker.
- HandWave's own geometric finger-extension rules and six-pose mapping.
- Majority voting, hold duration, cooldown, one command per gesture, and release-to-rearm.
- Dashboard, live preview, runtime performance display, labelled CSV evaluation, and settings.
- Local processing only; no external API or cloud inference.

**Model boundary:** MediaPipe's pretrained Hand Landmarker model locates the hand and estimates the 21 landmarks. It does not classify HandWave gestures. The gesture labels come from this project's explicit landmark geometry rules in `core/gesture_recognition.py`; the stability percentage is a rolling vote share, not model confidence.

## Technology

Python, OpenCV, MediaPipe Tasks, NumPy (MediaPipe dependency), PyAutoGUI, Tkinter, Pillow, and scikit-learn for evaluation. Charts use a lightweight Tk canvas and are based on measurements from the running session.

## Architecture

- `app.py`: Tkinter pages and a background camera/inference worker.
- `core/gesture_recognition.py`: geometric classification and majority voter.
- `core/command_controller.py`: opt-in, cooldown-limited command dispatch.
- `core/performance_monitor.py`: measured FPS, latency and hand rate.
- `evaluation/evaluate.py`: labelled-sample metrics and confusion matrix.
- `download_model.py`: retrieves the official MediaPipe task model for local use.

## Installation

Use Python 3.11 or 3.12 for broad compatibility with the established MediaPipe 0.10 release line. Newer MediaPipe releases may support newer Python versions. From this directory:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python download_model.py
```

The model download is a one-time setup step. Once installed, camera inference runs locally/offline. Windows may require allowing camera access in Privacy settings.

## Run

```powershell
python app.py
```

Select **Live recognition → Start camera**. Preview is the default. To send computer actions, explicitly choose **Enable computer actions…** and confirm. Close the app or press Stop to end camera use.

## Gesture mapping

| Gesture | Command |
|---|---|
| Fist | Mute / unmute |
| One finger | Next slide (Right Arrow) |
| Two fingers | Previous slide (Left Arrow) |
| Three fingers | Play / pause (Space) |
| Four fingers | Volume down |
| Open palm | Volume up |

PowerPoint or another presentation app must be in the foreground to receive slide keys. Media key support depends on the host operating system. Keep the hand visible until the configured hold duration is reached, then remove it to rearm.

## Metrics and evaluation

Runtime metrics are calculated during camera execution: FPS, per-frame inference latency, latency range, hand detection rate, rolling gesture stability, gesture observations, sent commands, and session duration. They describe runtime behavior, not classification quality.

Recognition-quality metrics require manual ground truth. Fill `evaluation/test_samples.csv` with independently labelled examples and predictions (allowed labels are listed in `evaluation/evaluate.py`), optionally including participant, lighting, distance, hand and orientation context. Then run:

```powershell
python -m evaluation.evaluate evaluation/test_samples.csv --report reports/evaluation.json
```

The report includes accuracy, per-gesture precision/recall/F1/support and a confusion matrix. The header-only CSV is a template; it contains no claimed test results. For a useful study, record multiple participants, lighting levels, distances, hands and orientations, and keep each participant's samples identifiable.

## Settings

Webcam index, detection/tracking confidence, hold duration, cooldown, and landmark display can be changed in Settings. Changes apply to the next camera start. Actions still require explicit enabling each session.

## Limitations

Rule-based extension checks are sensitive to hand rotation, occlusion, unusual articulation and camera perspective. The current thumb rule uses horizontal displacement, while four fingers use vertical tip/PIP comparisons. Poor lighting, camera focus and frame rate affect landmark availability. Key mappings and media key support vary by OS and target application. Evaluation quality depends on representative manually labelled samples.

## Future scope

Improve rotation tolerance with normalized joint angles, add user-calibrated thresholds, support multiple hands, and expand evaluation with a carefully consented multi-user dataset. Any change to gesture rules should be measured against held-out manual labels.
