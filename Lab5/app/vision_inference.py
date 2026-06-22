from __future__ import annotations

import time
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import onnxruntime as ort
except Exception:  # pragma: no cover - optional runtime dependency
    ort = None


DEFAULT_LABELS = [f"class_{i}" for i in range(1000)]


class VisionClassifier:
    """Lightweight ONNX SqueezeNet image classifier for ImageNet-1K.

    This project deliberately uses a small ONNX model for the deploy stage.
    Students first learn normal framework-specific model formats in the lab
    document, then see why a portable inference format such as ONNX is useful
    when the model has to run inside a Dockerized service.
    """

    def __init__(self, model_path: str, labels_path: str):
        self.model_path = Path(model_path)
        self.labels_path = Path(labels_path)
        self.model_name = "squeezenet1.1_onnx_imagenet1k"
        self.model_version = "vision_squeezenet_onnx_v2"
        self.training_framework = "original model exported to ONNX; this lab performs inference only"
        self.input_size = 224
        self.session = None
        self.input_name = None
        self.labels = self._load_labels(labels_path)
        self.status_message = "not_loaded"
        self._load_model()

    def _load_labels(self, labels_path: str) -> List[str]:
        p = Path(labels_path)
        if not p.exists():
            return DEFAULT_LABELS
        lines = [line.strip() for line in p.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
        if len(lines) >= 1000:
            return lines[:1000]
        return lines + [f"class_{i}" for i in range(len(lines), 1000)]

    def _load_model(self) -> None:
        if ort is None:
            self.status_message = "onnxruntime is not installed"
            return
        if not self.model_path.exists():
            self.status_message = f"model file not found: {self.model_path}"
            return
        providers = ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(str(self.model_path), providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        self.status_message = "loaded"

    @property
    def loaded(self) -> bool:
        return self.session is not None

    def info(self) -> Dict[str, Any]:
        return {
            "model_loaded": self.loaded,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "task": "image_classification",
            "num_classes": 1000,
            "input_size": f"{self.input_size}x{self.input_size}",
            "runtime": "onnxruntime_cpu",
            "model_format": "ONNX",
            "model_path": str(self.model_path),
            "labels_loaded": self.labels != DEFAULT_LABELS,
            "status_message": self.status_message,
            "download_hint": "Run: python scripts/download_vision_model.py",
            "student_note": "The image model is not trained in Lab 5. Lab 5 teaches inference, API, UI, Docker, and model packaging."
        }

    def preprocess(self, image: Image.Image) -> np.ndarray:
        image = image.convert("RGB")
        # Resize shorter side to 256 then center crop 224x224.
        w, h = image.size
        if w < h:
            new_w = 256
            new_h = int(h * 256 / w)
        else:
            new_h = 256
            new_w = int(w * 256 / h)
        image = image.resize((new_w, new_h))
        left = (new_w - self.input_size) // 2
        top = (new_h - self.input_size) // 2
        image = image.crop((left, top, left + self.input_size, top + self.input_size))
        arr = np.asarray(image).astype("float32") / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype="float32")
        std = np.array([0.229, 0.224, 0.225], dtype="float32")
        arr = (arr - mean) / std
        arr = np.transpose(arr, (2, 0, 1))  # CHW
        arr = np.expand_dims(arr, axis=0).astype("float32")
        return arr

    @staticmethod
    def softmax(x: np.ndarray) -> np.ndarray:
        x = x.astype("float64")
        x = x - np.max(x)
        e = np.exp(x)
        return e / np.sum(e)

    def classify(self, image: Image.Image, top_k: int = 5) -> Dict[str, Any]:
        if not self.loaded:
            raise RuntimeError(self.status_message)
        top_k = max(1, min(int(top_k), 10))
        t0 = time.perf_counter()
        batch = self.preprocess(image)
        outputs = self.session.run(None, {self.input_name: batch})
        logits = np.asarray(outputs[0]).reshape(-1)
        probs = self.softmax(logits)
        idx = probs.argsort()[-top_k:][::-1]
        predictions = []
        for rank, class_id in enumerate(idx, start=1):
            predictions.append({
                "rank": rank,
                "class_id": int(class_id),
                "class_name": self.labels[int(class_id)],
                "confidence": round(float(probs[int(class_id)]), 6)
            })
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        confidence = predictions[0]["confidence"] if predictions else 0.0
        if confidence >= 0.65:
            confidence_level = "HIGH"
        elif confidence >= 0.35:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"
        return {
            "model_output": {
                "task": "image_classification",
                "model_name": self.model_name,
                "model_version": self.model_version,
                "model_format": "ONNX",
                "top_k": top_k,
                "predictions": predictions,
                "inference_time_ms": round(elapsed_ms, 3)
            },
            "decision": {
                "confidence_level": confidence_level,
                "recommendation": "REVIEW_TOP_K_RESULTS" if confidence_level != "HIGH" else "USE_WITH_CONTEXT",
                "safety_note": "This is a general ImageNet-1K classifier, not a domain-specific safety, medical, or plant-disease model."
            }
        }

    @staticmethod
    def annotate_image(image: Image.Image, result: Dict[str, Any]) -> Image.Image:
        """Return a copy of the uploaded image with the top-1 class rendered on it."""
        canvas = image.convert("RGB").copy()
        draw = ImageDraw.Draw(canvas)
        preds = result.get("model_output", {}).get("predictions", [])
        if preds:
            top1 = preds[0]
            label = f"Top-1: {top1['class_name']} ({top1['confidence'] * 100:.1f}%)"
            line2 = f"Model: {result['model_output'].get('model_name', 'vision_model')}"
        else:
            label = "No prediction"
            line2 = ""
        font = ImageFont.load_default()
        padding = 10
        # New Pillow versions support textbbox; fall back if unavailable.
        try:
            box1 = draw.textbbox((0, 0), label, font=font)
            box2 = draw.textbbox((0, 0), line2, font=font)
            text_w = max(box1[2] - box1[0], box2[2] - box2[0])
            text_h = (box1[3] - box1[1]) + (box2[3] - box2[1]) + 8
        except Exception:
            text_w = max(len(label), len(line2)) * 7
            text_h = 34
        rect = [0, 0, min(canvas.width, text_w + padding * 2), min(canvas.height, text_h + padding * 2)]
        draw.rectangle(rect, fill=(0, 0, 0))
        draw.text((padding, padding), label, fill=(255, 255, 255), font=font)
        if line2:
            draw.text((padding, padding + 18), line2, fill=(220, 220, 220), font=font)
        return canvas
