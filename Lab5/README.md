# Lab 5 V4 - Dockerized Multi-Model AI Inference Service for AIoT

Lab 5 V4 đóng gói một AI inference service có nhiều loại input: telemetry JSON và ảnh upload. Project dùng FastAPI, Docker, Docker Compose và một model ảnh nhẹ ONNX để minh họa quá trình đưa model vào service triển khai.

## 1. Mục tiêu project

- Chạy AI service local trước khi dùng Docker.
- Test endpoint sensor: `/detect-anomaly`, `/forecast`, `/predict-risk`.
- Test endpoint ảnh: `/classify-image`, `/classify-image-annotated`.
- Test giao diện upload ảnh: `/classify-image-demo`.
- Build Docker image và chạy container.
- Quan sát Docker Desktop Images, Containers, Logs.
- So sánh chạy local và chạy bằng Docker.

## 2. Model ảnh

Project dùng **SqueezeNet ONNX pretrained ImageNet-1K** để demo phân loại ảnh 1000 class. Đây là model nhẹ, phù hợp chạy CPU và tải nhanh trong lớp học.

Model không được nhúng sẵn trong zip để giữ dung lượng nhỏ. Tải model bằng lệnh:

```bash
python scripts/download_vision_model.py
```

Sau khi tải, cần có:

```text
models/vision/squeezenet1.1-7.onnx
models/vision/imagenet_classes.txt
```

## 3. Cấu trúc project

```text
app/                 FastAPI application
models/vision/       ONNX model và class labels
sample_images/       Ảnh mẫu để test upload
sample_requests/     JSON mẫu để gọi API sensor
outputs/             Log inference
scripts/             Script tải model và smoke test
docs/                Tài liệu chạy, quan sát, Docker, model format
Dockerfile           Công thức build image
docker-compose.yml   Cấu hình chạy service bằng Compose
RUN_GUIDE.md         Hướng dẫn chạy nhanh
```

## 4. Chạy local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_vision_model.py
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_vision_model.py
uvicorn app.main:app --reload
```

Mở:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/classify-image-demo
```

## 5. Build và chạy Docker

```bash
docker build -t lab5-aiot-inference:v4 .
docker run --rm --name lab5-aiot-api -p 8000:8000 \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/models/vision:/app/models/vision \
  lab5-aiot-inference:v4
```

Windows PowerShell:

```powershell
docker run --rm --name lab5-aiot-api -p 8000:8000 `
  -v ${PWD}/outputs:/app/outputs `
  -v ${PWD}/models/vision:/app/models/vision `
  lab5-aiot-inference:v4
```

## 6. Chạy bằng Docker Compose

```bash
docker compose up --build
```

Dừng service:

```bash
docker compose down
```

## 7. Hướng dẫn quan sát kết quả

Đọc trước file:

```text
docs/HUONG_DAN_CHAY_VA_QUAN_SAT.md
```

File này giải thích rõ:

- Chạy lệnh nào.
- Sau khi chạy cần nhìn ở đâu.
- Kết quả đúng trông như thế nào.
- Kết quả đó có ý nghĩa gì trong hệ thống AIoT.

## 8. Tài liệu bổ sung

```text
docs/DUONG_DI_MODEL_TRONG_THUC_TE.md
docs/docker_environment_comparison.md
docs/docker_desktop_gui_beginner.md
docs/docker_ubuntu_engine_beginner.md
docs/submission_checklist_v4.md
docs/model_formats_for_students.md
```

## 9. Smoke test local

```bash
python scripts/smoke_test_local.py
```

Kết quả mong đợi:

```text
LOCAL_PIPELINE_TEST_PASS
```

## 10. Sản phẩm cần nộp

- Ảnh `/health` local.
- Ảnh `/classify-image-demo` local sau khi upload ảnh.
- Ảnh Docker Desktop Images.
- Ảnh Docker Desktop Containers Running.
- Ảnh Docker Desktop Logs.
- Ảnh Swagger `/docs` khi chạy container.
- Ảnh `/classify-image-demo` khi chạy container.
- File log trong `outputs/`.
- Bảng so sánh chạy local và Docker.
