import sys
import types
import time
import unittest


def _install_stub_modules():
    if "cv2" not in sys.modules:
        sys.modules["cv2"] = types.ModuleType("cv2")

    if "pyautogui" not in sys.modules:
        stub_pyautogui = types.ModuleType("pyautogui")
        stub_pyautogui.scroll = lambda amount: amount
        sys.modules["pyautogui"] = stub_pyautogui

    if "mediapipe" not in sys.modules:
        mp = types.ModuleType("mediapipe")

        face_mesh_module = types.ModuleType("face_mesh")

        class FaceMesh:
            def __init__(self, *_, **__):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def process(self, frame):
                return types.SimpleNamespace(multi_face_landmarks=None)

        face_mesh_module.FaceMesh = FaceMesh
        mp.solutions = types.SimpleNamespace(face_mesh=face_mesh_module)

        landmark_pb2 = types.SimpleNamespace(NormalizedLandmark=object)
        mp.framework = types.SimpleNamespace(formats=types.SimpleNamespace(landmark_pb2=landmark_pb2))

        sys.modules["mediapipe"] = mp


_install_stub_modules()

from src.eye_roll_scroll import EyeRollConfig, EyeRollDetector


class FakeLandmark:
    def __init__(self, y: float):
        self.y = y


class EyeRollDetectorTests(unittest.TestCase):
    def test_eye_roll_score_uses_vertical_ratio(self):
        landmarks = [FakeLandmark(0.0) for _ in range(474)]
        landmarks[EyeRollDetector.LEFT_EYE_TOP] = FakeLandmark(0.2)
        landmarks[EyeRollDetector.LEFT_EYE_BOTTOM] = FakeLandmark(0.8)
        landmarks[EyeRollDetector.LEFT_IRIS_CENTER] = FakeLandmark(0.1)

        detector = EyeRollDetector(EyeRollConfig())
        left_score, right_score = detector.process_landmarks(landmarks)

        self.assertAlmostEqual(left_score, (0.2 - 0.1) / (0.8 - 0.2))
        self.assertEqual(right_score, 0.0)

    def test_trigger_requires_consecutive_frames(self):
        config = EyeRollConfig(roll_threshold=0.5, frames_required=2, debounce_seconds=0)
        detector = EyeRollDetector(config)

        self.assertFalse(detector.should_trigger(0.6, now=1.0))
        self.assertTrue(detector.should_trigger(0.7, now=1.1))

    def test_trigger_respects_debounce(self):
        config = EyeRollConfig(roll_threshold=0.5, frames_required=1, debounce_seconds=1.0)
        detector = EyeRollDetector(config)

        self.assertTrue(detector.should_trigger(0.6, now=10.0))
        self.assertFalse(detector.should_trigger(0.7, now=10.5))
        self.assertTrue(detector.should_trigger(0.8, now=11.1))


if __name__ == "__main__":
    unittest.main()
