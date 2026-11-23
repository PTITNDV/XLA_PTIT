"""Run: python -m unittest discover -s tests -v"""
from pathlib import Path
import unittest
from unittest.mock import patch
import cv2
import numpy as np
import pandas as pd
from coin_counter.pipeline import Config, process, read_image
from coin_counter.evaluation import evaluate


def scene(coins, background=25, foreground=200):
    image = np.full((400, 600, 3), background, np.uint8)
    for x, y, radius in coins:
        cv2.circle(image, (x, y), radius, (foreground,) * 3, -1)
    return image


class PipelineTests(unittest.TestCase):
    def test_real_four_coins_same_count_is_not_enough(self):
        image = read_image(Path(__file__).parent / "fixtures" / "four_coins.jpg")
        result = process(image)
        self.assertEqual(result["count"], 4)
        # Previous code also returned four, but one was a background fragment.
        # Check one distinct object at each real coin, not just the total.
        remaining = list(result["rows"])
        for x, y in [(124, 48), (218, 91), (47, 93), (131, 159)]:
            closest = min(remaining, key=lambda row: np.hypot(row["center_x"] - x, row["center_y"] - y))
            self.assertLess(np.hypot(closest["center_x"] - x, closest["center_y"] - y), 10)
            self.assertGreater(closest["circularity"], .75)
            self.assertFalse(closest["touches_border"])
            remaining.remove(closest)

    def test_empty_both_polarities(self):
        for value in (0, 255):
            self.assertEqual(process(scene([], value))["count"], 0)

    def test_separated_and_mixed_sizes(self):
        image = scene([(90, 90, 24), (250, 110, 65), (460, 220, 42)])
        self.assertEqual(process(image)["count"], 3)

    def test_watershed_splits_touching_pair_and_triple(self):
        for coins in ([(190, 200, 60), (308, 200, 60)],
                      [(130, 200, 60), (248, 200, 60), (366, 200, 60)],
                      [(220, 200, 75), (328, 200, 35)]):
            image = scene(coins)
            result = process(image)
            self.assertEqual(result["before_count"], 1)
            self.assertEqual(result["count"], len(coins))

    def test_diameter_area_and_calibration(self):
        result = process(scene([(240, 200, 60)]), Config(mm_per_pixel=.2))
        self.assertEqual(result["count"], 1)
        row = result["rows"][0]
        self.assertLess(abs(row["area_px2"] - np.pi * 60**2) / (np.pi * 60**2), .06)
        self.assertAlmostEqual(row["equiv_diameter_px"], 120, delta=3)
        self.assertAlmostEqual(row["diameter_mm"], 24, delta=.6)
        self.assertAlmostEqual(row["area_mm2"], row["area_px2"] * .04, places=2)

    def test_dark_coins_and_border_flag(self):
        self.assertEqual(process(scene([(220, 200, 60)], 230, 60))["count"], 1)
        rows = process(scene([(0, 200, 60), (300, 200, 50)]))["rows"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(row["touches_border"] for row in rows), 1)

    def test_noise_is_not_a_coin(self):
        image = scene([(220, 200, 60)])
        for x in range(30, 550, 40):
            cv2.circle(image, (x, 30), 2, (220, 220, 220), -1)
        self.assertEqual(process(image)["count"], 1)

    def test_invalid_image(self):
        for data in (b"", b"not a png"):
            with self.assertRaises(ValueError):
                read_image(data)

    def test_manifest_cannot_escape_dataset(self):
        manifest = pd.DataFrame([{"image_name": "../outside.png", "actual_count": 1, "group": "test"}])
        with patch("coin_counter.evaluation.pd.read_csv", return_value=manifest):
            with self.assertRaises(ValueError):
                evaluate(Path(__file__).resolve().parents[1] / "dataset" / "demo")


if __name__ == "__main__":
    unittest.main()
