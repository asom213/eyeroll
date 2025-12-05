# Eye Roll Scroll

Prototype computer vision script that listens for an eye-roll gesture and scrolls the active page upward. Built for quick experimentation with Instagram or other browser contexts.

## How it works
- Uses [MediaPipe Face Mesh](https://developers.google.com/mediapipe/solutions/vision/face_mesh) to locate facial landmarks around the eyes and irises.
- Computes an *eye-roll score* based on the iris height relative to the eyelid bounds. When your iris moves near the top of the eye for consecutive frames, a gesture is registered.
- On detection, a callback is fired. The default desktop demo calls `pyautogui.scroll()` to move the page up.

## Project layout
- `src/eye_roll_scroll.py`: core logic for estimating eye-roll score and running the webcam loop.
- `requirements.txt`: Python dependencies (OpenCV, MediaPipe, PyAutoGUI).

## Running the desktop demo
> Requires Python 3.10+, a webcam, and a GUI session (PyAutoGUI cannot scroll in headless environments).

1. Install dependencies: `python -m pip install -r requirements.txt`
2. Launch the detector: `python -m src.eye_roll_scroll`
3. You should see a webcam preview titled **Eye Roll Scroll** with an overlay text like `Eye-roll score: 0.00`.
4. Roll your eyes upward; once the score stays above the threshold for a few frames, the active window should scroll up.
5. Press <kbd>Esc</kbd> to exit.

### Quick testing tips
- Run from a well-lit room so Face Mesh can find your eyes quickly.
- If nothing happens, ensure the terminal is focused on a scrollable page (e.g., browser tab or document) so PyAutoGUI can send scroll events.
- To confirm gesture detection without scrolling, temporarily change the `on_trigger` callback in `EyeRollDetector.run_camera` (e.g., `lambda: print("triggered")`) and watch the console output instead of page movement.

### Tuning
Edit the `EyeRollConfig` values in `src/eye_roll_scroll.py` if you need more/less sensitivity:
- `roll_threshold`: higher = less sensitive to upward gaze.
- `frames_required`: number of consecutive frames above the threshold before a gesture fires.
- `debounce_seconds`: minimum time between scroll actions.
- `scroll_amount`: pixels scrolled per gesture via PyAutoGUI.

## Chrome extension approach (concept)
If you prefer to keep detection off-device or inside the browser:
- Keep this Python detector running locally and expose events via WebSocket, then have a Chrome extension listen and scroll.
- Or build a WebAssembly model for gaze estimation in a content script and trigger `window.scrollBy` on detection. The algorithm described in `src/eye_roll_scroll.py` can be translated to JavaScript using the same landmark geometry.

## Safety and privacy
No frames are stored; all processing happens locally. Disable the script or close the webcam when not in use.
