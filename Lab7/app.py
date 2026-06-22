from __future__ import annotations

import csv
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from vision_engines import ZooState, run_task

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CAPTURE_DIR = DATA_DIR / "captures"
SAMPLE_DIR = DATA_DIR / "sample_images"
OUTPUT_DIR = BASE_DIR / "outputs"
STATIC_DIRS = [CAPTURE_DIR, SAMPLE_DIR, OUTPUT_DIR]
for d in [DATA_DIR, CAPTURE_DIR, SAMPLE_DIR, OUTPUT_DIR, BASE_DIR / "models" / "pretrained"]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Lab 7 Extended - Computer Vision Model Zoo for AIoT")
app.mount("/captures", StaticFiles(directory=str(CAPTURE_DIR)), name="captures")
app.mount("/sample_images", StaticFiles(directory=str(SAMPLE_DIR)), name="sample_images")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

GLOBAL_STATES: Dict[str, ZooState] = {}

TASK_DESCRIPTIONS = {
    "detection": "YOLO/object detection: bbox, class, confidence.",
    "tracking_counting": "Tracking/counting: object_id, trajectory, line count.",
    "pose_landmark": "Pose landmark: body keypoints for posture/action analysis.",
    "hand_gesture": "Hand/gesture: hand landmarks and simple gesture label.",
    "face_landmark": "Face landmark: face points for attention/drowsiness exploration.",
    "ocr": "OCR: read text from image/camera snapshot.",
    "segmentation": "Segmentation: mask/region output instead of only bbox.",
    "opencv_motion": "OpenCV motion: frame difference as non-deep-learning baseline.",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def append_csv(path: Path, row: Dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    keys = list(row.keys())
    if exists:
        try:
            with path.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
            if header:
                keys = header
        except Exception:
            pass
    with path.open('a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def log_result(task: str, records, event, image_id: str, annotated_path: str, elapsed_ms: float):
    event_id = str(uuid.uuid4())[:8]
    append_csv(OUTPUT_DIR / "model_zoo_event_log.csv", {
        "event_id": event_id,
        "timestamp": now_iso(),
        "task": task,
        "event_type": event.get("event_type", "MODEL_ZOO_RESULT"),
        "severity": event.get("severity", "NORMAL"),
        "num_records": event.get("num_records", len(records)),
        "image_id": image_id,
        "annotated_path": annotated_path,
        "elapsed_ms": round(elapsed_ms, 2),
        "explanation": event.get("explanation", ""),
        "action_hint": event.get("action_hint", ""),
    })
    log_map = {
        "detection": "detection_log.csv",
        "tracking_counting": "tracking_count_log.csv",
        "pose_landmark": "pose_log.csv",
        "hand_gesture": "gesture_log.csv",
        "face_landmark": "face_log.csv",
        "ocr": "ocr_log.csv",
        "segmentation": "segmentation_log.csv",
        "opencv_motion": "motion_log.csv",
    }
    for r in records:
        row = {
            "record_id": str(uuid.uuid4())[:8],
            "timestamp": now_iso(),
            "task": task,
            "image_id": image_id,
            "annotated_path": annotated_path,
            "elapsed_ms": round(elapsed_ms, 2),
            "record_json": json.dumps(r, ensure_ascii=False),
        }
        append_csv(OUTPUT_DIR / log_map.get(task, "task_log.csv"), row)


def open_capture(source: str):
    try:
        if str(source).isdigit():
            cap = cv2.VideoCapture(int(source))
        else:
            cap = cv2.VideoCapture(source)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            return cap
    except Exception:
        pass
    return None


def synthetic_frame(counter: int = 0) -> np.ndarray:
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (32, 37, 45)
    cv2.putText(img, "LAB 7 MODEL ZOO", (150, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (230,230,230), 2)
    x = 80 + (counter * 9) % 420
    cv2.rectangle(img, (x, 160), (x+120, 300), (60, 160, 255), -1)
    cv2.circle(img, (420, 260), 60, (80, 220, 120), -1)
    cv2.putText(img, "AIOT LAB 7", (210, 410), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 2)
    return img


def encode_jpg(frame: np.ndarray, quality: int = 75) -> bytes:
    ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise RuntimeError("Could not encode frame")
    return buf.tobytes()


@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "ok", "service": "lab7_cv_model_zoo", "time": now_iso()}


@app.get("/tasks")
def tasks():
    return {"tasks": TASK_DESCRIPTIONS}


@app.get("/video_feed")
def video_feed(
    task: str = Query("detection"),
    source: str = Query("0"),
    conf: float = Query(0.35),
    detect_every: int = Query(3),
    classes: str = Query(""),
    model_path: str = Query("yolov8n.pt"),
    session_id: str = Query("default"),
):
    state = GLOBAL_STATES.setdefault(session_id + '_' + task, ZooState())

    def gen():
        cap = open_capture(source)
        counter = 0
        last_annotated = None
        try:
            while True:
                if cap is None:
                    frame = synthetic_frame(counter)
                else:
                    ok, frame = cap.read()
                    if not ok or frame is None:
                        frame = synthetic_frame(counter)
                start = time.perf_counter()
                if counter % max(1, detect_every) == 0 or last_annotated is None:
                    annotated, records, event = run_task(task, frame, state=state, conf=conf, classes=classes, model_path=model_path)
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    # log only every 15 frames to avoid huge CSV files
                    if counter % 15 == 0:
                        image_id = f"stream_{session_id}_{counter}"
                        log_result(task, records, event, image_id, "stream", elapsed_ms)
                    last_annotated = annotated
                else:
                    annotated = last_annotated
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encode_jpg(annotated, 72) + b"\r\n"
                counter += 1
                time.sleep(0.04)
        finally:
            if cap is not None:
                cap.release()
    return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.post("/run_task")
async def run_task_upload(
    file: UploadFile = File(...),
    task: str = Query("detection"),
    conf: float = Query(0.35),
    classes: str = Query(""),
    model_path: str = Query("yolov8n.pt"),
):
    raw = await file.read()
    arr = np.frombuffer(raw, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return JSONResponse({"error": "Could not decode image"}, status_code=400)
    image_id = str(uuid.uuid4())[:8]
    raw_path = CAPTURE_DIR / f"{image_id}_raw.jpg"
    annotated_path = CAPTURE_DIR / f"{image_id}_{task}.jpg"
    cv2.imwrite(str(raw_path), frame)
    state = GLOBAL_STATES.setdefault("upload_" + task, ZooState())
    start = time.perf_counter()
    annotated, records, event = run_task(task, frame, state=state, conf=conf, classes=classes, model_path=model_path)
    elapsed_ms = (time.perf_counter() - start) * 1000
    cv2.imwrite(str(annotated_path), annotated)
    log_result(task, records, event, image_id, str(annotated_path.relative_to(BASE_DIR)), elapsed_ms)
    return {
        "image_id": image_id,
        "task": task,
        "raw_image_url": f"/captures/{raw_path.name}",
        "annotated_image_url": f"/captures/{annotated_path.name}",
        "elapsed_ms": round(elapsed_ms, 2),
        "records": records,
        "event": event,
    }


@app.get("/run_sample")
def run_sample(task: str = "detection", conf: float = 0.35, classes: str = ""):
    frame = synthetic_frame(3)
    image_id = str(uuid.uuid4())[:8]
    annotated_path = CAPTURE_DIR / f"sample_{image_id}_{task}.jpg"
    state = GLOBAL_STATES.setdefault("sample_" + task, ZooState())
    start = time.perf_counter()
    annotated, records, event = run_task(task, frame, state=state, conf=conf, classes=classes)
    elapsed_ms = (time.perf_counter() - start) * 1000
    cv2.imwrite(str(annotated_path), annotated)
    log_result(task, records, event, image_id, str(annotated_path.relative_to(BASE_DIR)), elapsed_ms)
    return {"task": task, "annotated_image_url": f"/captures/{annotated_path.name}", "elapsed_ms": round(elapsed_ms,2), "records": records, "event": event}


@app.get("/logs/{name}")
def get_log(name: str):
    safe = ''.join(ch for ch in name if ch.isalnum() or ch in ['_', '-', '.'])
    path = OUTPUT_DIR / safe
    if not path.exists():
        return {"rows": [], "message": f"{safe} does not exist yet"}
    with path.open('r', encoding='utf-8') as f:
        return {"name": safe, "content": f.read()[-12000:]}
