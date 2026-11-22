import csv
import tempfile
import unittest
from pathlib import Path

from core.gesture_recognition import classify, GestureVoter
from evaluation.evaluate import evaluate_csv


def landmarks(flags):
    """Make a simple upright synthetic hand with requested extended flags."""
    pts = [(0.5, 0.8)] * 21
    # Default folded tips are below their PIP joints.
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        pts[pip] = (0.5, 0.55); pts[tip] = (0.5, 0.72)
    for flag, tip, pip, x in zip(flags[1:], (8, 12, 16, 20), (6, 10, 14, 18), (0.4, 0.46, 0.54, 0.6)):
        if flag: pts[tip] = (x, 0.35)
    pts[3] = (0.42, 0.68); pts[4] = (0.50 if flags[0] else 0.35, 0.68)
    return pts


class CoreTests(unittest.TestCase):
    def test_six_pose_rules(self):
        cases = [((0,0,0,0,0),"Fist"),((0,1,0,0,0),"One finger"),((0,1,1,0,0),"Two fingers"),((0,1,1,1,0),"Three fingers"),((0,1,1,1,1),"Four fingers"),((1,1,1,1,1),"Open palm")]
        for flags, expected in cases:
            with self.subTest(expected=expected): self.assertEqual(classify(landmarks(flags), "Right")[0], expected)

    def test_vote_share(self):
        voter = GestureVoter(3)
        voter.update("Fist"); voter.update("Open palm")
        label, share = voter.update("Fist")
        self.assertEqual(label, "Fist"); self.assertAlmostEqual(share, 200/3)

    def test_evaluation_uses_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "samples.csv"
            with path.open("w", newline="") as out:
                writer = csv.writer(out); writer.writerow(["ground_truth","prediction"])
                writer.writerows([["Fist","Fist"],["Fist","One finger"],["Open palm","Open palm"]])
            report = evaluate_csv(str(path))
            self.assertEqual(report["samples"], 3)
            self.assertAlmostEqual(report["accuracy"], 2/3)
            self.assertEqual(report["confusion_matrix"][0][:2], [1,1])


if __name__ == "__main__": unittest.main()
