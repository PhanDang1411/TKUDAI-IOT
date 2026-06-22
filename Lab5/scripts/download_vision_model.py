#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.request import urlretrieve

MODEL_URLS = [
    # GitHub ONNX Model Zoo LFS/raw mirror. Model size is about 4.73 MB.
    "https://github.com/onnx/models/raw/main/validated/vision/classification/squeezenet/model/squeezenet1.1-7.onnx",
    # Fallback: historical raw URL sometimes works depending on repository changes.
    "https://github.com/onnx/models/raw/master/validated/vision/classification/squeezenet/model/squeezenet1.1-7.onnx",
]
LABEL_URLS = [
    "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt",
    "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json",
]


def download_first(urls, dest: Path) -> None:
    last_exc = None
    for url in urls:
        try:
            print(f"Downloading {url}\n -> {dest}")
            urlretrieve(url, dest)
            if dest.exists() and dest.stat().st_size > 1024:
                print(f"OK: {dest} ({dest.stat().st_size / 1024 / 1024:.2f} MB)")
                return
        except Exception as exc:
            print(f"FAILED: {url}: {exc}")
            last_exc = exc
    raise RuntimeError(f"All downloads failed for {dest}: {last_exc}")


def normalize_labels(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if text.startswith("["):
        import json
        labels = json.loads(text)
        path.write_text("\n".join(labels) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download lightweight SqueezeNet ONNX model and ImageNet labels.")
    parser.add_argument("--out-dir", default="models/vision")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / "squeezenet1.1-7.onnx"
    labels_path = out_dir / "imagenet_classes.txt"
    if not model_path.exists():
        download_first(MODEL_URLS, model_path)
    else:
        print(f"Model already exists: {model_path}")
    if not labels_path.exists():
        download_first(LABEL_URLS, labels_path)
        normalize_labels(labels_path)
    else:
        print(f"Labels already exist: {labels_path}")
    print("Done. Now run: uvicorn app.main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
