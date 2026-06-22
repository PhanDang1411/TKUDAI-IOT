# RUN GUIDE - LAB 5 V4

Mục tiêu của file này là hướng dẫn chạy project và xác định rõ cần quan sát gì sau mỗi bước. Khi gặp lỗi, ưu tiên đọc phần log và bảng debug cuối file.

## 0. Chuẩn bị

Yêu cầu tối thiểu:

- Python 3.10 hoặc mới hơn.
- Docker Desktop trên Windows hoặc Docker Engine trên Ubuntu.
- Trình duyệt để mở FastAPI Swagger và giao diện upload ảnh.
- Thư mục project đặt ở nơi dễ truy cập. Với WSL, nên đặt trong filesystem Linux, ví dụ `~/aiot/lab5`.

Kiểm tra nhanh:

```bash
python --version
docker --version
docker compose version
```

## 1. Chạy local trước Docker

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

Mở trình duyệt:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/classify-image-demo
```

Cần quan sát:

- `/health` trả `service_status: ok`.
- `vision_model_loaded` là `true` nếu đã tải model ONNX.
- `/docs` hiển thị các endpoint.
- `/classify-image-demo` có giao diện chọn ảnh.

Ý nghĩa:

- Code và thư viện đã chạy đúng ở môi trường local.
- Đây là mốc kiểm thử trước khi chuyển sang Docker.

## 2. Test API cảm biến

```bash
curl -X POST http://127.0.0.1:8000/forecast \
  -H "Content-Type: application/json" \
  -d @sample_requests/forecast_request.json

curl -X POST http://127.0.0.1:8000/detect-anomaly \
  -H "Content-Type: application/json" \
  -d @sample_requests/detect_anomaly_request.json
```

Cần quan sát:

- API trả JSON.
- File `outputs/service_log.csv` có thêm dòng mới.

Ý nghĩa:

- Service xử lý được dữ liệu dạng telemetry JSON.
- Log giúp kiểm tra endpoint nào đã được gọi.

## 3. Test upload ảnh

Mở:

```text
http://127.0.0.1:8000/classify-image-demo
```

Thao tác:

1. Chọn ảnh trong `sample_images/` hoặc ảnh bất kỳ.
2. Bấm upload/classify.
3. Quan sát top-k class, confidence và ảnh annotated.

Cần quan sát:

- Bảng top-k prediction.
- Ảnh kết quả có nhãn top-1.
- File `outputs/vision_inference_log.csv` có thêm dòng log.

Ý nghĩa:

- Service đang chạy inference ảnh bằng model ONNX nhẹ.
- Giao diện chỉ là lớp tương tác; backend vẫn là API `/classify-image` và `/classify-image-annotated`.

## 4. Build Docker image

Dừng server local nếu đang giữ port 8000. Sau đó chạy:

```bash
docker build -t lab5-aiot-inference:v4 .
docker images
```

Cần quan sát:

- Có image `lab5-aiot-inference` với tag `v4`.
- Build không báo lỗi cài package.

Ý nghĩa:

- Docker image đã đóng gói runtime Python, source code và lệnh chạy service.

## 5. Chạy bằng Docker Desktop GUI

1. Mở Docker Desktop.
2. Vào tab Images.
3. Chọn image `lab5-aiot-inference:v4`.
4. Bấm Run.
5. Đặt container name: `lab5-aiot-api`.
6. Map port: host `8000` -> container `8000`.
7. Mount volume nếu giao diện hỗ trợ:
   - `outputs` -> `/app/outputs`
   - `models/vision` -> `/app/models/vision`
8. Mở tab Containers để kiểm tra container Running.
9. Mở Logs để xem Uvicorn log.
10. Mở `http://127.0.0.1:8000/classify-image-demo` để test upload ảnh.

Cần quan sát:

- Docker Desktop hiển thị container đang Running.
- Logs có dòng service đang chạy.
- Trình duyệt truy cập được API.

Ý nghĩa:

- Docker Desktop giúp quan sát trực quan image, container, port và log.
- Cách này phù hợp cho bước làm quen ban đầu.

## 6. Chạy bằng terminal WSL/Linux

```bash
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

Cần quan sát:

- Terminal hiển thị log Uvicorn.
- `http://127.0.0.1:8000/health` hoạt động.
- Log CSV xuất hiện trong thư mục `outputs` trên host.

Ý nghĩa:

- Terminal workflow gần với môi trường server Linux hơn Docker Desktop GUI.
- Volume cho phép dữ liệu sinh trong container được lưu lại trên host.

## 7. Chạy bằng Docker Compose

```bash
docker compose up --build
```

Dừng:

```bash
docker compose down
```

Quan sát:

```bash
docker compose ps
docker compose logs -f
```

Ý nghĩa:

- Compose giúp mô tả cách chạy service bằng `docker-compose.yml`.
- Khi thêm dashboard, MQTT broker hoặc database, Compose dễ quản lý hơn nhiều lệnh `docker run` riêng lẻ.

## 8. Khi chạy xong cần đọc kết quả ở đâu?

| Kết quả | Vị trí quan sát | Mục đích |
|---|---|---|
| API sống hay không | `/health` | Kiểm tra service status |
| Danh sách endpoint | `/docs` | Biết API có thể gọi gì |
| Model đang dùng | `/model-info`, `/vision/model-info` | Kiểm tra model/version/format |
| Forecast/anomaly JSON | `/forecast`, `/detect-anomaly` | Kiểm tra inference telemetry |
| Upload ảnh trực quan | `/classify-image-demo` | Kiểm tra inference ảnh |
| Log cảm biến | `outputs/service_log.csv` | Kiểm tra lịch sử gọi sensor endpoint |
| Log ảnh | `outputs/vision_inference_log.csv` | Kiểm tra lịch sử upload ảnh |
| Container logs | Docker Desktop Logs hoặc `docker logs` | Debug service khi lỗi |

## 9. So sánh không Docker và có Docker

Sau khi chạy local và Docker, hoàn thành bảng sau trong báo cáo:

| Tiêu chí | Chạy local | Chạy Docker |
|---|---|---|
| Cài thư viện | | |
| Đường dẫn model | | |
| Truy cập API | | |
| Ghi log | | |
| Khả năng chạy lại trên máy khác | | |
| Dễ debug | | |
| Gần môi trường triển khai doanh nghiệp | | |

Kết luận cần nêu:

- Docker không thay thế kiểm thử local.
- Docker giúp chuẩn hóa môi trường và giảm lỗi khác biệt giữa các máy.
- Docker có giá trị khi image, model, port, volume, health check và log được cấu hình rõ ràng.

## 10. Debug nhanh

| Lỗi | Cách kiểm tra |
|---|---|
| API không mở được | `docker ps`, port mapping, logs |
| Port 8000 bị chiếm | Dừng service local hoặc đổi host port |
| Vision model chưa load | Kiểm tra `models/vision/squeezenet1.1-7.onnx` |
| Log không xuất hiện ở host | Kiểm tra volume `outputs:/app/outputs` |
| Build chậm | Kiểm tra mạng và Docker cache |
| Upload ảnh lỗi | Kiểm tra file ảnh, dung lượng, định dạng JPG/PNG |

## 11. Minh chứng cần nộp

1. Ảnh `/health` khi chạy local.
2. Ảnh `/classify-image-demo` sau khi upload ảnh local.
3. Ảnh Docker Desktop tab Images có image `lab5-aiot-inference:v4`.
4. Ảnh Docker Desktop tab Containers có container đang Running.
5. Ảnh Docker Desktop Logs.
6. Ảnh Swagger `/docs` khi chạy bằng Docker.
7. Ảnh `/classify-image-demo` khi chạy bằng Docker.
8. File log trong `outputs/`.
9. Bảng so sánh local và Docker.
