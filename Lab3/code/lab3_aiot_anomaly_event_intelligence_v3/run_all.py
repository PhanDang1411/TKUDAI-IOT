from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def _run(args: list[str]) -> None:
    print("\n==>", " ".join(args))
    subprocess.check_call(args, cwd=str(PROJECT_ROOT))


def _check_artifacts() -> None:
    must_have = [
        "models/anomaly_model_bundle_iforest_v2.joblib",
        "models/isolation_forest_iforest_v1.joblib",
        "models/mlp_autoencoder_demo.joblib",
        "outputs/iforest_metrics.json",
        "outputs/autoencoder_metrics.json",
        "outputs/iforest_test_predictions.csv",
        "outputs/autoencoder_test_predictions.csv",
        "outputs/anomaly_event_log.csv",
        "outputs/api_test_result.json",
        "figures/anomaly_detection_result.png",
        "figures/anomaly_score_over_time.png",
    ]
    missing = [p for p in must_have if not (PROJECT_ROOT / p).exists()]
    print("\n=== Artifact check ===")
    if missing:
        print("MISSING:")
        for p in missing:
            print("-", p)
        raise SystemExit(2)
    print("OK: all expected artifacts exist.")


def main() -> None:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    py = sys.executable
    _run([py, "src/download_data.py"])
    _run([py, "src/train_anomaly.py"])
    _run([py, "src/plot_results.py"])
    _run([py, "src/test_api_local.py"])
    _check_artifacts()


if __name__ == "__main__":
    main()

