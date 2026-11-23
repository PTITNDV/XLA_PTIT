"""Evaluate the fixed processing pipeline against a dataset manifest."""
from pathlib import Path
import pandas as pd
from .pipeline import Config, process, read_image


def evaluate(dataset, config=None):
    root = Path(dataset).resolve()
    truth = pd.read_csv(root / "ground_truth.csv")
    if not {"image_name", "actual_count", "group"}.issubset(truth.columns) or truth.empty:
        raise ValueError("ground_truth.csv cần có dữ liệu và các cột image_name, actual_count, group.")
    records = []
    for row in truth.to_dict("records"):
        filename = str(row["image_name"])
        path = (root / filename).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"Đường dẫn ảnh vượt ngoài bộ dữ liệu: {filename}")
        actual = float(row["actual_count"])
        if actual < 0 or not actual.is_integer():
            raise ValueError(f"actual_count phải là số nguyên không âm: {filename}")
        image = read_image(path)
        result = process(image, config or Config())
        delta = result["count"] - int(actual)
        records.append({"image_name": filename, "group": row["group"],
            "actual_count": int(actual), "predicted_count": result["count"], "error": delta,
            "absolute_error": abs(delta), "exact": int(delta == 0), "under": int(delta < 0),
            "over": int(delta > 0), "elapsed_ms": result["elapsed_ms"]})
    return pd.DataFrame(records)


def summarize(frame, by_group=False):
    grouped = frame.groupby("group", dropna=False) if by_group else frame.assign(dataset="all").groupby("dataset")
    return grouped.agg(
        images=("exact", "size"), MAE=("absolute_error", "mean"),
        exact_percent=("exact", lambda s: 100 * s.mean()),
        under_percent=("under", lambda s: 100 * s.mean()),
        over_percent=("over", lambda s: 100 * s.mean()),
        mean_ms=("elapsed_ms", "mean")).reset_index().round(3)
