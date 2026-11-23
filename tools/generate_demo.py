"""Reproducible synthetic examples; not a real-world accuracy dataset."""
import csv
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def generate(destination=None):
    target = Path(destination) if destination else ROOT / "dataset" / "demo"
    target.mkdir(parents=True, exist_ok=True)
    cases = [
        ("empty.png", "empty", []),
        ("single.png", "separated", [(260, 230, 62)]),
        ("separated.png", "separated", [(130, 130, 45), (310, 140, 60), (500, 140, 42), (200, 350, 65), (450, 340, 55)]),
        ("touching_pair.png", "touching", [(240, 240, 70), (378, 240, 70)]),
        ("touching_three.png", "touching", [(200, 240, 65), (328, 240, 65), (456, 240, 65)]),
        ("mixed_sizes.png", "mixed_sizes", [(120, 130, 25), (250, 140, 65), (420, 140, 40), (160, 350, 70), (420, 350, 30)]),
        ("touching_mixed.png", "touching", [(260, 240, 75), (368, 240, 35)]),
        ("border.png", "border", [(0, 220, 65), (300, 230, 55)]),
        ("dark_coins.png", "polarity", [(180, 200, 55), (390, 260, 70)]),
        ("noise.png", "noise", [(160, 230, 60), (400, 250, 70)]),
        ("overlap_limit.png", "overlap_limit", [(270, 230, 75), (345, 230, 75)]),
    ]
    rng = np.random.default_rng(123)
    records = []
    for name, group, coins in cases:
        dark = group == "polarity"
        image = np.full((480, 640, 3), 225 if dark else 28, np.uint8)
        for x, y, radius in coins:
            cv2.circle(image, (x, y), radius, (65, 75, 85) if dark else (155, 180, 205), -1)
            cv2.circle(image, (x, y), max(2, radius - 6), (90, 100, 110) if dark else (175, 195, 220), 2)
            cv2.putText(image, "1", (x - 10, y + 12), cv2.FONT_HERSHEY_SIMPLEX, .8,
                        (110, 120, 130) if dark else (140, 155, 175), 2, cv2.LINE_AA)
        if group == "noise":
            image = np.clip(image.astype(float) + rng.normal(0, 7, image.shape), 0, 255).astype(np.uint8)
            for _ in range(40):
                cv2.circle(image, (int(rng.integers(640)), int(rng.integers(480))), 2, (210, 210, 210), -1)
        cv2.imencode(".png", image)[1].tofile(target / name)
        records.append({"image_name": name, "actual_count": len(coins), "group": group,
                        "notes": "synthetic; overlap_limit is outside core scope"})
    with (target / "ground_truth.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["image_name", "actual_count", "group", "notes"])
        writer.writeheader()
        writer.writerows(records)
    return target


if __name__ == "__main__":
    print(generate())
