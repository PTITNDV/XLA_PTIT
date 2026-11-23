"""CLI: python evaluate.py --dataset dataset/demo --output results/demo"""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
from coin_counter.evaluation import evaluate, summarize
from coin_counter.pipeline import Config


def main():
    parser = argparse.ArgumentParser(description="Evaluate the fixed coin-counting pipeline.")
    parser.add_argument("--dataset", default="dataset/demo")
    parser.add_argument("--output", default="results/evaluation")
    args = parser.parse_args()
    config = Config()
    results = evaluate(args.dataset, config)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    results.to_csv(output / "details.csv", index=False, encoding="utf-8-sig")
    summary = summarize(results)
    summary.to_csv(output / "summary.csv", index=False, encoding="utf-8-sig")
    summarize(results, True).to_csv(output / "by_group.csv", index=False, encoding="utf-8-sig")
    (output / "config.json").write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"Saved results: {output.resolve()}")


if __name__ == "__main__":
    main()
