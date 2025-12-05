"""Eye roll detection demo that scrolls up when you look up.

This prototype uses MediaPipe Face Mesh for landmark detection and a simple
geometric heuristic to identify when the iris rides toward the top of the eye.
Run directly for a desktop demo:

```
python -m src.eye_roll_scroll
```
"""
from __future__ import annotations

import dataclasses
import time
from collections import deque
from typing import Callable, Deque, Iterable, Tuple

import cv2
import mediapipe as mp
import pyautogui


@dataclasses.dataclass
class EyeRollConfig:
    """Runtime tunables for the detector."""

    roll_threshold: float = 0.65
    frames_required: int = 3
    debounce_seconds: float = 1.0
    scroll_amount: int = 500


class EyeRollDetector:
    """Estimate when eyes roll upward using MediaPipe landmarks."""

    LEFT_EYE_TOP = 159
    LEFT_EYE_BOTTOM = 145
    LEFT_IRIS_CENTER = 468

    RIGHT_EYE_TOP = 386
    RIGHT_EYE_BOTTOM = 374
    RIGHT_IRIS_CENTER = 473

    def __init__(self, config: EyeRollConfig | None = None) -> None:
        self.config = config or EyeRollConfig()
        self._mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self._recent_scores: Deque[float] = deque(maxlen=self.config.frames_required)
        self._last_triggered: float = 0.0

    @staticmethod
    def _eye_roll_score(
        landmarks: Iterable[mp.framework.formats.landmark_pb2.NormalizedLandmark],
        eye_top: int,
        eye_bottom: int,
        iris_center: int,
    ) -> float:
        top_y = landmarks[eye_top].y
        bottom_y = landmarks[eye_bottom].y
        iris_y = landmarks[iris_center].y

        eye_height = bottom_y - top_y
        if eye_height <= 0:
            return 0.0

        return (top_y - iris_y) / eye_height

    def process_landmarks(self, landmarks) -> Tuple[float, float]:
        """Return (left_score, right_score) for the given face landmarks."""

        left = self._eye_roll_score(
            landmarks, self.LEFT_EYE_TOP, self.LEFT_EYE_BOTTOM, self.LEFT_IRIS_CENTER
        )
        right = self._eye_roll_score(
            landmarks, self.RIGHT_EYE_TOP, self.RIGHT_EYE_BOTTOM, self.RIGHT_IRIS_CENTER
        )
        return left, right

    def should_trigger(self, score: float, now: float | None = None) -> bool:
        now = now or time.time()
        if now - self._last_triggered < self.config.debounce_seconds:
            return False

        self._recent_scores.append(score)
        if len(self._recent_scores) < self.config.frames_required:
            return False

        above_threshold = all(s >= self.config.roll_threshold for s in self._recent_scores)
        if not above_threshold:
            return False

        self._last_triggered = now
        self._recent_scores.clear()
        return True

    def run_camera(self, on_trigger: Callable[[], None] | None = None) -> None:
        on_trigger = on_trigger or (lambda: pyautogui.scroll(self.config.scroll_amount))

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Cannot open webcam.")

        with self._mp_face_mesh as face_mesh:
            while True:
                success, frame = cap.read()
                if not success:
                    break

                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb_frame)

                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0].landmark
                    left, right = self.process_landmarks(landmarks)
                    score = max(left, right)
                    if self.should_trigger(score):
                        on_trigger()

                    cv2.putText(
                        frame,
                        f"Eye-roll score: {score:.2f}",
                        (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )

                cv2.imshow("Eye Roll Scroll", frame)
                if cv2.waitKey(5) & 0xFF == 27:
                    break

        cap.release()
        cv2.destroyAllWindows()


def main() -> None:
    detector = EyeRollDetector()
    detector.run_camera()


if __name__ == "__main__":
    main()
