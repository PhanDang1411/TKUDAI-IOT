from __future__ import annotations

import io
import os
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from PIL import Image, UnidentifiedImageError

from app.schemas import AnomalyRequest, ForecastRequest, RiskRequest
from app.sensor_inference import detect_anomaly_rule, forecast_moving_average, risk_from_forecast
from app.vision_inference import VisionClassifier
from app.logging_utils import append_csv_log

MODEL_DIR = os.getenv("MODEL_DIR", "models")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
VISION_MODEL_PATH = os.getenv("VISION_MODEL_PATH", "models/vision/squeezenet1.1-7.onnx")
VISION_LABELS_PATH = os.getenv("VISION_LABELS_PATH", "models/vision/imagenet_classes.txt")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))

app = FastAPI(
    title="Lab 5 - Dockerized Multi-Model AIoT Inference Service",
    version="1.1.0",
    description=(
        "AIoT inference service with sensor endpoints, a lightweight ONNX vision model, "
        "and a simple browser UI for image upload."
    )
)

vision_model = VisionClassifier(VISION_MODEL_PATH, VISION_LABELS_PATH)


def _decode_uploaded_image(file_bytes: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Cannot decode image. Please upload a valid image file.")


async def _read_image_upload(file: UploadFile) -> tuple[bytes, Image.Image]:
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Max upload size is {MAX_UPLOAD_BYTES} bytes.")
    return content, _decode_uploaded_image(content)


@app.get("/")
def root():
    return {
        "service": "Lab 5 Dockerized Multi-Model AIoT Inference Service",
        "docs": "/docs",
        "image_upload_demo": "/classify-image-demo",
        "endpoints": [
            "/health", "/model-info", "/detect-anomaly", "/forecast", "/predict-risk",
            "/vision/model-info", "/classify-image", "/classify-image-annotated", "/classify-image-demo"
        ]
    }


@app.get("/health")
def health():
    return {
        "service_status": "ok",
        "model_dir": MODEL_DIR,
        "output_dir": OUTPUT_DIR,
        "vision_model_loaded": vision_model.loaded
    }


@app.get("/model-info")
def model_info():
    return {
        "service_type": "multi_model_aiot_inference",
        "sensor_models": {
            "anomaly": "zscore_fallback_v1",
            "forecast": "moving_average_baseline_v1"
        },
        "vision_model": vision_model.info(),
        "model_format_learning_path": [
            "Start with framework-native models: PyTorch .pt/.pth and TensorFlow .keras/SavedModel.",
            "Then convert or export to portable inference formats such as ONNX or lightweight edge formats such as TFLite.",
            "Use Docker to package runtime, dependencies, model files, and API behavior into a reproducible service."
        ],
        "note": "Lab 5 focuses on deployment/inference. Stronger sensor models are trained in Lab 3 and Lab 4."
    }


@app.post("/detect-anomaly")
def detect_anomaly(payload: AnomalyRequest):
    result = detect_anomaly_rule(payload.current_value, payload.recent_values, payload.threshold_z)
    append_csv_log(Path(OUTPUT_DIR) / "service_log.csv", {
        "endpoint": "/detect-anomaly",
        "target": payload.target,
        "status": "ok",
        "summary": result["event"]["severity"]
    })
    return result


@app.post("/forecast")
def forecast(payload: ForecastRequest):
    try:
        result = forecast_moving_average(payload.recent_values, payload.horizon_minutes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    append_csv_log(Path(OUTPUT_DIR) / "service_log.csv", {
        "endpoint": "/forecast",
        "target": payload.target,
        "status": "ok",
        "summary": result["model_output"]["predicted_value"]
    })
    return result


@app.post("/predict-risk")
def predict_risk(payload: RiskRequest):
    result = risk_from_forecast(payload.predicted_value, payload.warning_threshold, payload.high_threshold)
    append_csv_log(Path(OUTPUT_DIR) / "service_log.csv", {
        "endpoint": "/predict-risk",
        "target": payload.target,
        "status": "ok",
        "summary": result["decision"]["risk_level"]
    })
    return result


@app.get("/vision/model-info")
def vision_model_info():
    return vision_model.info()


@app.post("/classify-image")
async def classify_image(file: UploadFile = File(...), top_k: int = Query(default=5, ge=1, le=10)):
    if not vision_model.loaded:
        raise HTTPException(status_code=503, detail=vision_model.info())
    _, image = await _read_image_upload(file)
    try:
        result = vision_model.classify(image, top_k=top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    top1 = result["model_output"]["predictions"][0]
    append_csv_log(Path(OUTPUT_DIR) / "vision_inference_log.csv", {
        "endpoint": "/classify-image",
        "filename": file.filename or "unknown",
        "content_type": file.content_type or "unknown",
        "status": "ok",
        "top1_class": top1["class_name"],
        "top1_confidence": top1["confidence"],
        "inference_time_ms": result["model_output"]["inference_time_ms"]
    })
    return result


@app.post("/classify-image-annotated")
async def classify_image_annotated(file: UploadFile = File(...), top_k: int = Query(default=5, ge=1, le=10)):
    """Return the uploaded image with the top-1 prediction drawn on it."""
    if not vision_model.loaded:
        raise HTTPException(status_code=503, detail=vision_model.info())
    _, image = await _read_image_upload(file)
    result = vision_model.classify(image, top_k=top_k)
    annotated = vision_model.annotate_image(image, result)
    buf = io.BytesIO()
    annotated.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/classify-image-demo", response_class=HTMLResponse)
def classify_image_demo():
    return """
<!DOCTYPE html>
<html lang="vi">
<head>
  <mecharset="UTF-8" />
  <title>Lab 5 - Image Classification UI</title>
  <style>
    :root { --blue:#0b3a75; --orange:#f28c28; --light:#f6f8fb; --border:#d8dee9; }
    body { font-family: Arial, sans-serif; max-width: 1080px; margin: 28px auto; line-height: 1.45; color:#1f2937; }
    h1 { color: var(--blue); margin-bottom: 6px; }
    .sub { color:#4b5563; margin-top:0; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap:18px; margin-top:16px; }
    .card { border:1px solid var(--border); border-radius:14px; padding:18px; background:white; box-shadow:0 1px 3px rgba(0,0,0,0.05); }
    .hint { background:#fff7ed; border-left:5px solid var(--orange); padding:12px 14px; border-radius:8px; }
    img { max-width:100%; max-height:420px; display:block; margin-top:12px; border:1px solid var(--border); border-radius:10px; }
    button { padding:10px 16px; cursor:pointer; border:0; border-radius:8px; background:var(--blue); color:white; font-weight:bold; }
    input { margin:8px 0 12px 0; }
    table { border-collapse: collapse; width:100%; margin-top:10px; }
    td, th { border-bottom:1px solid #e5e7eb; padding:8px; text-align:left; }
    th { background:var(--light); }
    .pill { display:inline-block; padding:4px 8px; border-radius:999px; background:#e0f2fe; color:#075985; font-weight:bold; }
    pre { background:#111827; color:#f9fafb; padding:12px; overflow:auto; border-radius:10px; font-size:12px; }
    .error { color:#b91c1c; font-weight:bold; }
    @media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <h1>Lab 5 - Giao diện kiểm thử AI service bằng ảnh</h1>
  <p class="sub">Tải lên một ảnh để service gọi model ảnh nhẹ ONNX SqueezeNet ImageNet-1K và trả về top-k class.</p>
  <div class="hint">
    <b>Gợi ý phân tích:</b> endpoint này đang inference, không train lại model. Khi top-1 chưa chắc đúng, cần đọc thêm top-5 và confidence trước khi kết luận.
  </div>

  <div class="card">
    <input id="file" type="file" accept="image/*" />
    <button onclick="classifyImage()">Upload và phân loại ảnh</button>
    <span id="status" class="pill">Chưa thực hiện inference</span>
  </div>

  <div class="grid">
    <div class="card">
      <h3>Ảnh gốc</h3>
      <img id="preview" style="display:none" />
      <p id="previewHint">Chưa có ảnh đầu vào.</p>
    </div>
    <div class="card">
      <h3>Ảnh kết quả có nhãn dự đoán</h3>
      <img id="annotated" style="display:none" />
      <p id="annotatedHint">Sau khi gọi model, ảnh kết quả sẽ hiển thị nhãn top-1 và confidence.</p>
    </div>
  </div>

  <div class="card">
    <h3>Top-k predictions</h3>
    <div id="top1"></div>
    <table id="predTable" style="display:none">
      <thead><tr><th>Rank</th><th>Class</th><th>Confidence</th></tr></thead>
      <tbody></tbody>
    </table>
  </div>

  <div class="card">
    <h3>JSON response</h3>
    <pre id="result">Chưa có kết quả.</pre>
  </div>

<script>
async function classifyImage() {
  const fileInput = document.getElementById('file');
  const result = document.getElementById('result');
  const preview = document.getElementById('preview');
  const annotated = document.getElementById('annotated');
  const status = document.getElementById('status');
  const predTable = document.getElementById('predTable');
  const tbody = predTable.querySelector('tbody');
  const top1Div = document.getElementById('top1');
  if (!fileInput.files.length) {
    result.textContent = 'Hãy chọn một ảnh trước.';
    return;
  }
  const file = fileInput.files[0];
  preview.src = URL.createObjectURL(file);
  preview.style.display = 'block';
  document.getElementById('previewHint').style.display = 'none';
  status.textContent = 'Đang gọi model...';
  status.style.background = '#fef3c7';
  status.style.color = '#92400e';

  const formDa= new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/classify-image?top_k=5', { method: 'POST', body: formDa});
    const data = await res.json();
    if (!res.ok) {
      status.textContent = 'Lỗi';
      status.style.background = '#fee2e2';
      status.style.color = '#991b1b';
      result.textContent = JSON.stringify(data, null, 2);
      return;
    }
    result.textContent = JSON.stringify(data, null, 2);
    const preds = data.model_output.predictions;
    const top = preds[0];
    top1Div.innerHTML = `<b>Top-1:</b> ${top.class_name} <span class="pill">${(top.confidence * 100).toFixed(1)}%</span>`;
    tbody.innerHTML = '';
    preds.forEach(p => {
      const row = document.createElement('tr');
      row.innerHTML = `<td>${p.rank}</td><td>${p.class_name}</td><td>${(p.confidence * 100).toFixed(2)}%</td>`;
      tbody.appendChild(row);
    });
    predTable.style.display = 'table';

    const formData2 = new FormData();
    formData2.append('file', file);
    const imgRes = await fetch('/classify-image-annotated?top_k=5', { method: 'POST', body: formData2 });
    if (imgRes.ok) {
      const blob = await imgRes.blob();
      annotated.src = URL.createObjectURL(blob);
      annotated.style.display = 'block';
      document.getElementById('annotatedHint').style.display = 'none';
    }
    status.textContent = 'Hoàn thành';
    status.style.background = '#dcfce7';
    status.style.color = '#166534';
  } catch (err) {
    status.textContent = 'Lỗi';
    status.style.background = '#fee2e2';
    status.style.color = '#991b1b';
    result.innerHTML = '<span class="error">Không gọi được API: ' + err + '</span>';
  }
}
</script>
</body>
</html>
"""
