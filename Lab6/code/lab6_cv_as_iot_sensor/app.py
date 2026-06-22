
"""
Lab 6 - Computer Vision as IoT Sensor

One-file backend for the student lab:
- camera stream from laptop camera or IP camera URL
- snapshot capture
- short video recording
- motion capture
- image upload
- image preprocessing contact sheet
- metadata and event logging
- browser dashboard served from index.html

Run:
    uvicorn app:app --reload --host 0.0.0.0 --port 8000
Open:
    http://127.0.0.1:8000/
"""

from __future__ import annotations

import csv
import base64
import json
import threading
import time
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw_images"
PROCESSED_DIR = DATA_DIR / "processed_images"
VIDEO_DIR = DATA_DIR / "videos"
OUTPUT_DIR = ROOT / "outputs"
METADATA_CSV = OUTPUT_DIR / "image_metadata.csv"
EVENT_CSV = OUTPUT_DIR / "image_event_log.csv"
INDEX_HTML = ROOT / "index.html"

for folder in [RAW_DIR, PROCESSED_DIR, VIDEO_DIR, OUTPUT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

METADATA_FIELDS = [
    "image_id", "device_id", "timestamp", "source_type", "image_path", "processed_path",
    "width", "height", "brightness", "processing_status", "processing_time_ms", "note"
]

EVENT_FIELDS = [
    "event_id", "image_id", "timestamp", "event_type", "score", "severity", "explanation", "action_hint"
]

HOG_PEOPLE_DETECTOR = cv2.HOGDescriptor()
HOG_PEOPLE_DETECTOR.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
CAT_FACE_DETECTOR = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalcatface_extended.xml"))
YOLO_MODEL_CACHE: Dict[str, Any] = {}
CAMERA_SESSIONS: Dict[str, Any] = {}
CAMERA_SESSIONS_LOCK = threading.Lock()
EVENT_DEDUP_STATE: Dict[Tuple[str, str], float] = {}
EVENT_DEDUP_LOCK = threading.Lock()
EVENT_COOLDOWN_SECONDS = 10.0
MODEL_OPTIONS = {
    "opencv_builtin": {
        "name": "OpenCV built-in",
        "description": "Fallback nhẹ: HOG person + cat-face cascade, không cần tải model.",
        "weights": None,
    },
    "yolov8n": {
        "name": "YOLOv8n realtime",
        "description": "Nhanh, phù hợp demo realtime trên laptop.",
        "weights": "yolov8n.pt",
    },
    "yolov8s": {
        "name": "YOLOv8s strong",
        "description": "Mạnh hơn YOLOv8n, chậm hơn nhưng detect ổn hơn.",
        "weights": "yolov8s.pt",
    },
    "yolo11n": {
        "name": "YOLO11n realtime",
        "description": "Model YOLO đời mới, nhanh; cần ultralytics hỗ trợ YOLO11.",
        "weights": "yolo11n.pt",
    },
    "yolo11s": {
        "name": "YOLO11s strong",
        "description": "YOLO11 mạnh hơn bản nano; cần máy đủ tốt.",
        "weights": "yolo11s.pt",
    },
}
ANIMAL_LABELS = {"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def append_csv(path: Path, fieldnames: List[str], row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in fieldnames})


def should_log_event(source: str, event_type: str, cooldown_seconds: float = EVENT_COOLDOWN_SECONDS) -> bool:
    key = (str(source), event_type)
    now = time.time()
    with EVENT_DEDUP_LOCK:
        last_time = EVENT_DEDUP_STATE.get(key, 0.0)
        if now - last_time < cooldown_seconds:
            return False
        EVENT_DEDUP_STATE[key] = now
        return True


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def relative_url(path: Optional[Path]) -> Optional[str]:
    if not path:
        return None
    try:
        rel = path.resolve().relative_to(ROOT.resolve())
        return f"/files/{rel.as_posix()}"
    except Exception:
        return None


def validate_image_bytes(data: bytes) -> Image.Image:
    try:
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {exc}") from exc


def pil_to_bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def frame_to_jpeg_bytes(frame_bgr: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", frame_bgr)
    if not ok:
        raise RuntimeError("Could not encode frame as JPEG")
    return buffer.tobytes()


def compute_brightness(frame_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def create_processed_contact_sheet(frame_bgr: np.ndarray, image_id: str) -> Tuple[Path, float, Dict[str, Any]]:
    """Create one observable image containing four processing steps."""
    start = time.perf_counter()
    resized = cv2.resize(frame_bgr, (320, 240))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)
    edges = cv2.Canny(gray, 80, 160)

    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    threshold_bgr = cv2.cvtColor(threshold, cv2.COLOR_GRAY2BGR)
    edge_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    def label(tile: np.ndarray, text: str) -> np.ndarray:
        canvas = tile.copy()
        cv2.rectangle(canvas, (0, 0), (320, 30), (255, 255, 255), -1)
        cv2.putText(canvas, text, (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 2)
        return canvas

    top = np.hstack([label(resized, "1. RESIZE"), label(gray_bgr, "2. GRAYSCALE")])
    bottom = np.hstack([label(threshold_bgr, "3. THRESHOLD"), label(edge_bgr, "4. EDGE")])
    sheet = np.vstack([top, bottom])

    out_path = PROCESSED_DIR / f"{image_id}_processed_steps.jpg"
    cv2.imwrite(str(out_path), sheet)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    stats = {"brightness": round(compute_brightness(frame_bgr), 2), "width": int(frame_bgr.shape[1]), "height": int(frame_bgr.shape[0])}
    return out_path, elapsed_ms, stats


def get_yolo_model(model_name: str) -> Any:
    option = MODEL_OPTIONS.get(model_name)
    if not option or not option["weights"]:
        raise RuntimeError(f"Unsupported YOLO model: {model_name}")
    if model_name not in YOLO_MODEL_CACHE:
        try:
            from ultralytics import YOLO
        except Exception as exc:
            raise RuntimeError("Ultralytics is not installed. Run: pip install -r requirements.txt") from exc
        YOLO_MODEL_CACHE[model_name] = YOLO(option["weights"])
    return YOLO_MODEL_CACHE[model_name]


def yolo_detect_targets(frame_bgr: np.ndarray, model_name: str, confidence: float) -> Dict[str, Any]:
    model = get_yolo_model(model_name)
    result = model.predict(frame_bgr, conf=float(confidence), imgsz=640, verbose=False)[0]
    names = result.names
    people = []
    animals = []
    all_detections = []
    for box in result.boxes:
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        cls_id = int(box.cls[0].item())
        label = str(names.get(cls_id, cls_id))
        conf = round(float(box.conf[0].item()), 4)
        item = {
            "x": x1,
            "y": y1,
            "w": max(0, x2 - x1),
            "h": max(0, y2 - y1),
            "label": label,
            "confidence": conf,
            "model": model_name,
        }
        all_detections.append(item)
        if label == "person":
            people.append(item)
        elif label in ANIMAL_LABELS:
            animals.append(item)
    return {"people": people, "animals": animals, "detections": all_detections}


def opencv_detect_targets(frame_bgr: np.ndarray) -> Dict[str, Any]:
    scale = 1.0
    if frame_bgr.shape[1] > 640:
        scale = 640.0 / frame_bgr.shape[1]
        frame_for_detection = cv2.resize(frame_bgr, (640, int(frame_bgr.shape[0] * scale)))
    else:
        frame_for_detection = frame_bgr

    boxes, weights = HOG_PEOPLE_DETECTOR.detectMultiScale(
        frame_for_detection,
        winStride=(8, 8),
        padding=(8, 8),
        scale=1.05,
    )
    people = []
    for box, weight in zip(boxes, weights):
        x, y, w, h = [int(v / scale) for v in box]
        people.append({"x": x, "y": y, "w": w, "h": h, "label": "person", "confidence": round(float(weight), 4), "model": "opencv_builtin"})

    gray = cv2.cvtColor(frame_for_detection, cv2.COLOR_BGR2GRAY)
    animal_boxes = []
    if not CAT_FACE_DETECTOR.empty():
        cats = CAT_FACE_DETECTOR.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=3,
            minSize=(35, 35),
        )
        for box in cats:
            x, y, w, h = [int(v / scale) for v in box]
            animal_boxes.append({"x": x, "y": y, "w": w, "h": h, "label": "cat", "confidence": None, "model": "opencv_builtin"})

    return {"people": people, "animals": animal_boxes, "detections": people + animal_boxes}


def classify_motion_target(frame_bgr: np.ndarray, motion_score: float, min_area: int, model_name: str = "yolov8n", confidence: float = 0.35) -> Dict[str, Any]:
    """Confirm whether a motion frame contains person/animal labels.

    The intended strong path is YOLO via Ultralytics. OpenCV built-in detectors
    remain available as an offline fallback.
    """
    motion_detected = float(motion_score) >= float(min_area)
    selected_model = model_name if model_name in MODEL_OPTIONS else "yolov8n"
    model_error = None
    try:
        if selected_model == "opencv_builtin":
            detections = opencv_detect_targets(frame_bgr)
        else:
            detections = yolo_detect_targets(frame_bgr, selected_model, confidence)
    except Exception as exc:
        model_error = str(exc)
        selected_model = "opencv_builtin"
        detections = opencv_detect_targets(frame_bgr)

    people = detections["people"]
    animal_boxes = detections["animals"]
    person_detected = len(people) > 0
    animal_detected = len(animal_boxes) > 0
    target_labels = []
    if person_detected:
        target_labels.append("person")
    if animal_detected:
        target_labels.append("animal")

    if person_detected and animal_detected:
        target_type = "person_and_animal"
    elif person_detected:
        target_type = "person"
    elif animal_detected:
        target_type = "animal"
    elif motion_detected:
        target_type = "motion_without_person_or_animal"
    else:
        target_type = "none"

    return {
        "target_type": target_type,
        "target_labels": target_labels,
        "should_notify": person_detected or animal_detected,
        "model_name": selected_model,
        "requested_model": model_name,
        "model_error": model_error,
        "confidence": float(confidence),
        "person_detected": person_detected,
        "animal_detected": animal_detected,
        "motion_detected": motion_detected,
        "people_count": len(people),
        "people_boxes": people,
        "animal_count": len(animal_boxes),
        "animal_boxes": animal_boxes,
        "detections": detections["detections"],
        "motion_score": round(float(motion_score), 2),
        "min_area": int(min_area),
    }


def draw_detection_boxes(frame_bgr: np.ndarray, motion_classification: Dict[str, Any]) -> np.ndarray:
    annotated = frame_bgr.copy()
    for item in motion_classification.get("people_boxes", []):
        x, y, w, h = int(item["x"]), int(item["y"]), int(item["w"]), int(item["h"])
        label = f"PERSON {item.get('confidence', '')}".strip()
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 180, 0), 3)
        cv2.rectangle(annotated, (x, max(0, y - 28)), (x + max(150, len(label) * 11), y), (0, 180, 0), -1)
        cv2.putText(annotated, label, (x + 6, max(18, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    for item in motion_classification.get("animal_boxes", []):
        x, y, w, h = int(item["x"]), int(item["y"]), int(item["w"]), int(item["h"])
        label = f"ANIMAL:{item.get('label', 'animal')} {item.get('confidence', '')}".strip()
        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 140, 255), 3)
        cv2.rectangle(annotated, (x, max(0, y - 28)), (x + max(170, len(label) * 10), y), (0, 140, 255), -1)
        cv2.putText(annotated, label, (x + 6, max(18, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    status = (
        f"motion={motion_classification.get('motion_detected')} | "
        f"model={motion_classification.get('model_name')} | "
        f"score={motion_classification.get('motion_score')}"
    )
    cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 34), (20, 20, 20), -1)
    cv2.putText(annotated, status, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2)
    return annotated


def save_annotated_detection(frame_bgr: np.ndarray, image_id: str, motion_classification: Dict[str, Any]) -> Tuple[Path, str]:
    annotated = draw_detection_boxes(frame_bgr, motion_classification)
    out_path = PROCESSED_DIR / f"{image_id}_detected_boxes.jpg"
    cv2.imwrite(str(out_path), annotated)
    return out_path, relative_url(out_path)


def log_image_pipeline(frame_bgr: np.ndarray, source_type: str, device_id: str, note: str = "", write_processing_event: bool = True) -> Dict[str, Any]:
    """Save raw image, preprocess image, write metadata, and create a visual event."""
    image_id = f"img_{uuid.uuid4().hex[:10]}"
    timestamp = now_iso()
    raw_path = RAW_DIR / f"{image_id}.jpg"
    cv2.imwrite(str(raw_path), frame_bgr)

    processed_path, processing_time_ms, stats = create_processed_contact_sheet(frame_bgr, image_id)
    brightness = stats["brightness"]

    metadata_row = {
        "image_id": image_id,
        "device_id": device_id,
        "timestamp": timestamp,
        "source_type": source_type,
        "image_path": str(raw_path.relative_to(ROOT)),
        "processed_path": str(processed_path.relative_to(ROOT)),
        "width": stats["width"],
        "height": stats["height"],
        "brightness": brightness,
        "processing_status": "processed",
        "processing_time_ms": processing_time_ms,
        "note": note,
    }
    append_csv(METADATA_CSV, METADATA_FIELDS, metadata_row)

    if brightness < 70:
        event_type = "LOW_LIGHT"
        severity = "WARNING"
        explanation = "Image brightness is low; later AI inference may be less reliable."
        action_hint = "Improve lighting or review image quality before using the image for object detection."
    else:
        event_type = "IMAGE_PROCESSED"
        severity = "NORMAL"
        explanation = "Image was received, saved, preprocessed, and registered as visual data."
        action_hint = "Continue monitoring or pass the image to Lab 7 object detection."

    event_row = {
        "event_id": f"evt_{uuid.uuid4().hex[:10]}",
        "image_id": image_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "score": brightness,
        "severity": severity,
        "explanation": explanation,
        "action_hint": action_hint,
    }
    if write_processing_event:
        append_csv(EVENT_CSV, EVENT_FIELDS, event_row)

    return {
        "image_id": image_id,
        "metadata": metadata_row,
        "event": event_row,
        "raw_image_url": relative_url(raw_path),
        "processed_image_url": relative_url(processed_path),
    }


def parse_camera_source(source: str) -> Any:
    source = str(source).strip()
    return int(source) if source.isdigit() else source


def use_shared_camera(source: str) -> bool:
    source = str(source).strip()
    return source.isdigit()


def is_http_source(source: str) -> bool:
    source = str(source).strip().lower()
    return source.startswith("http://") or source.startswith("https://")


def decode_jpeg_bytes(jpeg_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise RuntimeError("Could not decode JPEG frame from HTTP stream")
    return frame


def http_stream_request(source: str) -> Request:
    headers = {
        "User-Agent": "Lab6-CV-IoT-Sensor/1.0",
        "Accept": "multipart/x-mixed-replace,image/jpeg,*/*",
    }
    request_url = source
    parts = urlsplit(source)
    if parts.username is not None:
        username = parts.username or ""
        password = parts.password or ""
        auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {auth}"
        host = parts.hostname or ""
        if parts.port:
            host = f"{host}:{parts.port}"
        request_url = urlunsplit((parts.scheme, host, parts.path, parts.query, parts.fragment))
    return Request(
        request_url,
        headers=headers,
    )


def read_http_mjpeg_frame(source: str, timeout: float = 5.0) -> Optional[np.ndarray]:
    """Read one JPEG frame from an HTTP/MJPEG stream.

    Some iOS IP camera apps show a stream in the browser but are not parsed well
    by cv2.VideoCapture. This fallback extracts the JPEG frame bytes directly.
    """
    try:
        with urlopen(http_stream_request(source), timeout=timeout) as response:
            buffer = b""
            start_time = time.perf_counter()
            while time.perf_counter() - start_time < timeout:
                chunk = response.read(4096)
                if not chunk:
                    break
                buffer += chunk
                start = buffer.find(b"\xff\xd8")
                end = buffer.find(b"\xff\xd9", start + 2)
                if start != -1 and end != -1:
                    return decode_jpeg_bytes(buffer[start:end + 2])
    except Exception:
        return None
    return None


def iter_http_mjpeg_frames(source: str) -> Iterable[np.ndarray]:
    try:
        with urlopen(http_stream_request(source), timeout=10) as response:
            buffer = b""
            while True:
                chunk = response.read(4096)
                if not chunk:
                    break
                buffer += chunk
                while True:
                    start = buffer.find(b"\xff\xd8")
                    end = buffer.find(b"\xff\xd9", start + 2)
                    if start == -1 or end == -1:
                        if start > 0:
                            buffer = buffer[start:]
                        break
                    jpeg = buffer[start:end + 2]
                    buffer = buffer[end + 2:]
                    try:
                        yield decode_jpeg_bytes(jpeg)
                    except RuntimeError:
                        continue
    except Exception:
        return


def simulated_frame(counter: int = 0, width: int = 640, height: int = 360) -> np.ndarray:
    """Fallback stream when no laptop/IP camera is available."""
    frame = np.full((height, width, 3), 245, dtype=np.uint8)
    x = 30 + (counter * 12) % max(1, width - 180)
    y = 80 + (counter * 7) % max(1, height - 170)
    cv2.rectangle(frame, (x, 120), (x + 130, 240), (40, 140, 240), -1)
    cv2.circle(frame, (width - 110, y), 38, (80, 200, 120), -1)
    cv2.putText(frame, "SIMULATED CAMERA STREAM", (25, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(frame, "Use source=0 for laptop camera or an IP camera URL", (25, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)
    return frame


def open_capture(source: str) -> Optional[cv2.VideoCapture]:
    cap = cv2.VideoCapture(parse_camera_source(source))
    if not cap.isOpened():
        return None
    return cap


class CameraSession:
    """Keep a camera source open so stream and realtime detection do not reset it."""

    def __init__(self, source: str):
        self.source = str(source)
        self.lock = threading.Lock()
        self.frame: Optional[np.ndarray] = None
        self.frames: List[Tuple[float, np.ndarray]] = []
        self.frame_count = 0
        self.source_type = "camera_session"
        self.running = True
        self.thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.thread.start()

    def _reader_loop(self) -> None:
        cap: Optional[cv2.VideoCapture] = None
        last_reopen = 0.0
        while self.running:
            if cap is None or not cap.isOpened():
                now = time.perf_counter()
                if now - last_reopen < 1.0:
                    time.sleep(0.05)
                    continue
                last_reopen = now
                cap = open_capture(self.source)
                if cap is None:
                    self.source_type = "simulated"
                    frame = simulated_frame(self.frame_count)
                    self._store_frame(frame)
                    time.sleep(0.08)
                    continue

            ok, frame = cap.read()
            if not ok or frame is None:
                if cap is not None:
                    cap.release()
                cap = None
                continue

            self.source_type = "camera_session"
            self._store_frame(frame)
            time.sleep(0.02)

        if cap is not None:
            cap.release()

    def _store_frame(self, frame: np.ndarray) -> None:
        now = time.perf_counter()
        with self.lock:
            self.frame = frame.copy()
            self.frames.append((now, self.frame))
            self.frames = self.frames[-180:]
            self.frame_count += 1

    def get_frame(self) -> Tuple[np.ndarray, str]:
        deadline = time.perf_counter() + 2.0
        while time.perf_counter() < deadline:
            with self.lock:
                if self.frame is not None:
                    return self.frame.copy(), self.source_type
            time.sleep(0.03)
        return simulated_frame(self.frame_count), "simulated"

    def get_recent_frames(self, seconds: int) -> List[np.ndarray]:
        cutoff = time.perf_counter() - max(1, seconds)
        deadline = time.perf_counter() + max(1, seconds)
        while time.perf_counter() < deadline:
            with self.lock:
                recent = [frame.copy() for ts, frame in self.frames if ts >= cutoff]
            if len(recent) >= 2:
                return recent
            time.sleep(0.05)
        frame, _ = self.get_frame()
        return [frame]


def get_camera_session(source: str) -> CameraSession:
    source = str(source).strip()
    with CAMERA_SESSIONS_LOCK:
        if source not in CAMERA_SESSIONS:
            CAMERA_SESSIONS[source] = CameraSession(source)
        return CAMERA_SESSIONS[source]


def read_one_frame(source: str = "0") -> Tuple[np.ndarray, str]:
    if use_shared_camera(source):
        return get_camera_session(source).get_frame()
    cap = open_capture(source)
    if cap is None:
        if is_http_source(source):
            frame = read_http_mjpeg_frame(source)
            if frame is not None:
                return frame, "http_mjpeg"
        return simulated_frame(0), "simulated"
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return simulated_frame(0), "simulated"
    return frame, "camera"


def stream_frames(source: str = "0") -> Iterable[bytes]:
    if use_shared_camera(source):
        session = get_camera_session(source)
        counter = 0
        while True:
            frame, source_type = session.get_frame()
            source_label = "LIVE_CAMERA_SESSION" if source_type == "camera_session" else "SIMULATED"
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 32), (255, 255, 255), -1)
            cv2.putText(frame, f"{source_label} | source={source} | frame={counter}", (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 2)
            jpg = frame_to_jpeg_bytes(frame)
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
            counter += 1
            time.sleep(0.05)

    cap = open_capture(source)
    counter = 0
    if cap is None and is_http_source(source):
        for frame in iter_http_mjpeg_frames(source):
            source_label = "HTTP_MJPEG_STREAM"
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 32), (255, 255, 255), -1)
            cv2.putText(frame, f"{source_label} | source={source} | frame={counter}", (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 2)
            jpg = frame_to_jpeg_bytes(frame)
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
            counter += 1
            time.sleep(0.02)
        counter = 0

    while True:
        if cap is None:
            frame = simulated_frame(counter)
            source_label = "SIMULATED"
        else:
            ok, frame = cap.read()
            if not ok or frame is None:
                frame = simulated_frame(counter)
                source_label = "SIMULATED_AFTER_CAMERA_ERROR"
            else:
                source_label = "LIVE_CAMERA"

        cv2.rectangle(frame, (0, 0), (frame.shape[1], 32), (255, 255, 255), -1)
        cv2.putText(frame, f"{source_label} | source={source} | frame={counter}", (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 2)
        jpg = frame_to_jpeg_bytes(frame)
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
        counter += 1
        time.sleep(0.08)


def record_short_video(source: str, seconds: int = 5) -> Dict[str, Any]:
    seconds = max(1, min(int(seconds), 30))
    cap = None if use_shared_camera(source) else open_capture(source)
    session = get_camera_session(source) if use_shared_camera(source) else None
    fps = 10
    width, height = 640, 360
    video_id = f"vid_{uuid.uuid4().hex[:10]}"
    out_path = VIDEO_DIR / f"{video_id}.mp4"
    writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    frame_count = 0
    start = time.perf_counter()

    while time.perf_counter() - start < seconds:
        if session is not None:
            frame, _ = session.get_frame()
        elif cap is None:
            frame = simulated_frame(frame_count, width, height)
        else:
            ok, frame = cap.read()
            if not ok or frame is None:
                frame = simulated_frame(frame_count, width, height)
        frame = cv2.resize(frame, (width, height))
        writer.write(frame)
        frame_count += 1
        time.sleep(1.0 / fps)

    if cap is not None:
        cap.release()
    writer.release()

    event_row = {
        "event_id": f"evt_{uuid.uuid4().hex[:10]}",
        "image_id": video_id,
        "timestamp": now_iso(),
        "event_type": "VIDEO_RECORDED",
        "score": frame_count,
        "severity": "NORMAL",
        "explanation": f"Recorded a short video clip with {frame_count} frames.",
        "action_hint": "Use the video clip for later review or image analysis.",
    }
    append_csv(EVENT_CSV, EVENT_FIELDS, event_row)
    return {"video_id": video_id, "video_path": str(out_path.relative_to(ROOT)), "video_url": relative_url(out_path), "seconds": seconds, "frames": frame_count, "event": event_row}


def motion_capture(source: str, seconds: int = 1, threshold: int = 25, min_area: int = 800, model_name: str = "yolov8n", confidence: float = 0.35) -> Dict[str, Any]:
    """Capture the most changed frame, run detector, create motion events."""
    seconds = max(1, min(int(seconds), 30))
    prev_gray = None
    best_frame = None
    best_score = 0.0
    frames_seen = 0

    if use_shared_camera(source):
        frames = get_camera_session(source).get_recent_frames(seconds)
    else:
        frames = []
        cap = open_capture(source)
        start = time.perf_counter()
        while time.perf_counter() - start < seconds:
            if cap is None:
                frame = simulated_frame(frames_seen)
            else:
                ok, frame = cap.read()
                if not ok or frame is None:
                    frame = simulated_frame(frames_seen)
            frames.append(frame)
            time.sleep(0.08)
        if cap is not None:
            cap.release()

    for frame in frames:
        frames_seen += 1
        gray = cv2.cvtColor(cv2.resize(frame, (320, 240)), cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            diff = cv2.absdiff(prev_gray, gray)
            _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            score = float(sum(cv2.contourArea(c) for c in contours))
            if score > best_score:
                best_score = score
                best_frame = frame.copy()
        prev_gray = gray

    if best_frame is None:
        best_frame = frames[-1].copy() if frames else simulated_frame(frames_seen)

    result = log_image_pipeline(
        best_frame,
        source_type="motion_capture",
        device_id=f"camera:{source}",
        note=f"motion_score={round(best_score, 2)}, threshold={threshold}, min_area={min_area}, model={model_name}, confidence={confidence}",
        write_processing_event=False,
    )
    motion_classification = classify_motion_target(best_frame, best_score, min_area, model_name=model_name, confidence=confidence)
    annotated_path, annotated_url = save_annotated_detection(best_frame, result["image_id"], motion_classification)
    motion_detected = motion_classification["motion_detected"]
    motion_events = []
    if motion_classification["person_detected"]:
        motion_events.append({
            "event_type": "PERSON_DETECTED",
            "severity": "HIGH",
            "explanation": "The selected model detected a person in the camera frame.",
            "action_hint": "Notify operator about the person event and review the captured image before taking action.",
        })
    if motion_classification["animal_detected"]:
        motion_events.append({
            "event_type": "ANIMAL_DETECTED",
            "severity": "WARNING",
            "explanation": "The selected model detected an animal in the camera frame.",
            "action_hint": "Notify operator about the animal event and review the captured image to confirm.",
        })
    if not motion_events:
        if motion_detected:
            motion_events.append({
                "event_type": "MOTION_WITHOUT_PERSON_OR_ANIMAL",
                "severity": "NORMAL",
                "explanation": "Motion was detected, but no person or animal label was confirmed.",
                "action_hint": "Log only; do not notify because neither person nor animal was detected.",
            })
        else:
            motion_events.append({
                "event_type": "NO_SIGNIFICANT_MOTION",
                "severity": "NORMAL",
                "explanation": "No significant frame difference was detected, so no person/animal notification is sent.",
                "action_hint": "Continue visual monitoring.",
            })

    motion_event_payloads = []
    logged_motion_events = []
    for event in motion_events:
        motion_event = {
            "event_id": f"evt_{uuid.uuid4().hex[:10]}",
            "image_id": result["image_id"],
            "timestamp": now_iso(),
            "event_type": event["event_type"],
            "score": round(best_score, 2),
            "severity": event["severity"],
            "explanation": event["explanation"],
            "action_hint": event["action_hint"],
        }
        should_write = should_log_event(source, motion_event["event_type"])
        motion_event["logged"] = should_write
        motion_event["cooldown_seconds"] = EVENT_COOLDOWN_SECONDS
        if should_write:
            append_csv(EVENT_CSV, EVENT_FIELDS, motion_event)
            logged_motion_events.append(motion_event)
        motion_event_payloads.append(motion_event)

    result["motion_event"] = motion_event_payloads[0]
    result["motion_events"] = motion_event_payloads
    result["logged_motion_events"] = logged_motion_events
    result["motion_detected"] = motion_detected
    result["motion_classification"] = motion_classification
    result["annotated_image_path"] = str(annotated_path.relative_to(ROOT))
    result["annotated_image_url"] = annotated_url
    result["frames_seen"] = frames_seen
    return result


app = FastAPI(title="Lab 6 - Computer Vision as IoT Sensor", description="Camera stream, snapshot, video, motion, metadata, image event and dashboard.")
app.mount("/files", StaticFiles(directory=str(ROOT)), name="files")


@app.get("/")
def home() -> FileResponse:
    return FileResponse(INDEX_HTML)


@app.get("/dashboard")
def dashboard() -> FileResponse:
    return FileResponse(INDEX_HTML)


@app.get("/camera-demo")
def camera_demo() -> RedirectResponse:
    return RedirectResponse("/")


@app.get("/image-demo")
def image_demo() -> RedirectResponse:
    return RedirectResponse("/")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "lab": "Lab 6 - Computer Vision as IoT Sensor", "outputs": {"metadata_csv": str(METADATA_CSV.relative_to(ROOT)), "event_csv": str(EVENT_CSV.relative_to(ROOT))}}


@app.get("/model-options")
def model_options() -> Dict[str, Any]:
    return {"default": "yolov8n", "items": MODEL_OPTIONS}


@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), device_id: str = "upload_client") -> Dict[str, Any]:
    data = await file.read()
    img = validate_image_bytes(data)
    return log_image_pipeline(pil_to_bgr(img), source_type="upload", device_id=device_id, note=f"filename={file.filename}")


@app.get("/snapshot")
def snapshot(source: str = Query("0", description="0 for laptop camera, or IP camera/video URL")) -> Dict[str, Any]:
    frame, source_type = read_one_frame(source)
    return log_image_pipeline(frame, source_type=source_type, device_id=f"camera:{source}", note="snapshot button")


@app.get("/record-video")
def record_video(source: str = Query("0"), seconds: int = Query(5, ge=1, le=30)) -> Dict[str, Any]:
    return record_short_video(source, seconds=seconds)


@app.get("/motion-capture")
def motion_capture_endpoint(
    source: str = Query("0"),
    seconds: int = Query(1, ge=1, le=30),
    threshold: int = Query(25, ge=1, le=255),
    min_area: int = Query(800, ge=10, le=50000),
    model_name: str = Query("yolov8n"),
    confidence: float = Query(0.35, ge=0.05, le=0.95),
) -> Dict[str, Any]:
    return motion_capture(source, seconds=seconds, threshold=threshold, min_area=min_area, model_name=model_name, confidence=confidence)


@app.get("/motion-stream")
def motion_stream(
    source: str = Query("0"),
    seconds: int = Query(1, ge=1, le=5),
    threshold: int = Query(25, ge=1, le=255),
    min_area: int = Query(800, ge=10, le=50000),
    model_name: str = Query("yolov8n"),
    confidence: float = Query(0.35, ge=0.05, le=0.95),
    interval_ms: int = Query(300, ge=100, le=5000),
) -> StreamingResponse:
    def event_generator() -> Iterable[bytes]:
        while True:
            try:
                result = motion_capture(source, seconds=seconds, threshold=threshold, min_area=min_area, model_name=model_name, confidence=confidence)
                payload = json.dumps(result, ensure_ascii=False)
                yield f"data: {payload}\n\n".encode("utf-8")
            except Exception as exc:
                payload = json.dumps({"error": str(exc), "timestamp": now_iso()}, ensure_ascii=False)
                yield f"event: error\ndata: {payload}\n\n".encode("utf-8")
            time.sleep(interval_ms / 1000)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/video_feed")
def video_feed(source: str = Query("0")) -> StreamingResponse:
    return StreamingResponse(stream_frames(source), media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/metadata")
def metadata(limit: int = 20) -> Dict[str, Any]:
    rows = read_csv(METADATA_CSV)
    return {"count": len(rows), "items": rows[-limit:]}


@app.get("/events")
def events(limit: int = 20) -> Dict[str, Any]:
    rows = read_csv(EVENT_CSV)
    return {"count": len(rows), "items": rows[-limit:]}


@app.get("/latest")
def latest() -> Dict[str, Any]:
    meta_rows = read_csv(METADATA_CSV)
    event_rows = read_csv(EVENT_CSV)
    latest_meta = meta_rows[-1] if meta_rows else None
    raw_url = processed_url = None
    if latest_meta:
        raw_url = relative_url(ROOT / latest_meta.get("image_path", ""))
        processed_url = relative_url(ROOT / latest_meta.get("processed_path", ""))
    return {"latest_metadata": latest_meta, "latest_event": event_rows[-1] if event_rows else None, "raw_image_url": raw_url, "processed_image_url": processed_url, "metadata_count": len(meta_rows), "event_count": len(event_rows)}


if __name__ == "__main__":
    frame = simulated_frame(1)
    result = log_image_pipeline(frame, source_type="script", device_id="local_smoke", note="python app.py smoke test")
    print(json.dumps(result, indent=2, ensure_ascii=False))
