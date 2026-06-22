# HƯỚNG DẪN CHẠY VÀ QUAN SÁT KẾT QUẢ - LAB 5 V4

Tài liệu này hướng dẫn thao tác chạy hệ thống theo từng bước. Mỗi bước đều có ba phần: **lệnh chạy**, **kết quả cần quan sát**, và **ý nghĩa của kết quả**. Mục tiêu không chỉ là chạy cho ra kết quả, mà là hiểu một AI inference service vận hành như thế nào khi chuyển từ môi trường local sang Docker.

---

## 1. Kiểm tra cấu trúc project

Chạy trong thư mục gốc của project:

```bash
ls
```

Kết quả cần quan sát:

```text
app/
models/
sample_images/
sample_requests/
outputs/
scripts/
docs/
Dockerfile
docker-compose.yml
requirements.txt
RUN_GUIDE.md
```

Ý nghĩa:

- `app/`: mã nguồn FastAPI service.
- `models/`: nơi lưu model hoặc cấu hình model.
- `sample_images/`: ảnh mẫu dùng để kiểm thử vision model.
- `sample_requests/`: JSON mẫu để gọi API cảm biến.
- `outputs/`: nơi ghi log sau mỗi lần inference.
- `Dockerfile`: công thức build Docker image.
- `docker-compose.yml`: cấu hình chạy service bằng Docker Compose.

Câu hỏi gợi mở:

- Nếu thiếu thư mục `models/vision`, endpoint ảnh có thể hoạt động không?
- Nếu thiếu thư mục `outputs`, container có ghi log ra máy host được không?

---

## 2. Chạy local trước khi dùng Docker

Mục tiêu của bước này là kiểm tra code, thư viện, model và API khi chưa có Docker. Nếu local chưa chạy được, Docker sẽ làm lỗi khó phân tích hơn.

### 2.1. Tạo môi trường Python

WSL/Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Kết quả cần quan sát:

- Không có lỗi khi cài thư viện.
- Có thể import FastAPI, ONNX Runtime, Pillow.

Kiểm tra nhanh:

```bash
python -c "import fastapi, onnxruntime, PIL; print('IMPORT_OK')"
```

Ý nghĩa:

- Local runtime đã đủ thư viện để chạy API.
- Nếu bước này lỗi, cần sửa môi trường Python trước khi build Docker.

### 2.2. Tải model ảnh nhẹ

```bash
python scripts/download_vision_model.py
```

Kết quả cần quan sát:

```text
models/vision/squeezenet1.1-7.onnx
models/vision/imagenet_classes.txt
```

Ý nghĩa:

- File `.onnx` là model ảnh đã huấn luyện sẵn.
- File `imagenet_classes.txt` ánh xạ class id sang tên class.
- Lab 5 dùng model ảnh cho inference, không train lại model ảnh.

Câu hỏi gợi mở:

- Nếu model weights không có trong project, container có tự suy luận ảnh được không?
- Nếu lớp học không có Internet, cần chuẩn bị model weights từ trước ở đâu?

### 2.3. Chạy FastAPI local

```bash
uvicorn app.main:app --reload
```

Mở trình duyệt:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/classify-image-demo
```

Kết quả cần quan sát ở `/health`:

```json
{
  "service_status": "ok",
  "vision_model_loaded": true
}
```

Ý nghĩa:

- API đã chạy.
- Vision model đã được load nếu `vision_model_loaded = true`.
- Nếu `vision_model_loaded = false`, cần kiểm tra file model trong `models/vision`.

---

## 3. Quan sát service qua API cảm biến

### 3.1. Test endpoint `/forecast`

```bash
curl -X POST http://127.0.0.1:8000/forecast \
  -H "Content-Type: application/json" \
  -d @sample_requests/forecast_request.json
```

Kết quả cần quan sát:

- JSON trả về có `predicted_value`.
- Có `risk_level` hoặc `recommendation`.
- File `outputs/service_log.csv` có thêm dòng log.

Ý nghĩa:

- Đây là inference trên dữ liệu số/time-series.
- Output của model chưa phải hành động điều khiển trực tiếp; hệ thống cần decision rule và safety rule.

### 3.2. Test endpoint `/detect-anomaly`

```bash
curl -X POST http://127.0.0.1:8000/detect-anomaly \
  -H "Content-Type: application/json" \
  -d @sample_requests/detect_anomaly_request.json
```

Kết quả cần quan sát:

- JSON có `anomaly_score` hoặc `severity`.
- File `outputs/service_log.csv` có thêm log.

Ý nghĩa:

- Endpoint này mô phỏng luồng Lab 3: telemetry -> anomaly/risk -> decision.

---

## 4. Quan sát service qua ảnh upload

### 4.1. Test bằng giao diện web

Mở:

```text
http://127.0.0.1:8000/classify-image-demo
```

Thao tác:

1. Chọn một ảnh trong máy hoặc dùng ảnh trong `sample_images/`.
2. Bấm nút upload/classify.
3. Quan sát ảnh gốc, ảnh có nhãn dự đoán và bảng top-k class.

Kết quả cần quan sát:

- Ảnh gốc hiển thị ở khung bên trái.
- Ảnh kết quả có gắn nhãn top-1.
- Bảng kết quả có `rank`, `class_id`, `class_name`, `confidence`.
- File `outputs/vision_inference_log.csv` có thêm dòng log.

Ý nghĩa:

- Đây là inference với dữ liệu ảnh.
- Model trả xác suất cho nhiều class, không chỉ một nhãn duy nhất.
- Top-1 sai không đồng nghĩa toàn bộ output vô ích; cần đọc top-5 và confidence.

Câu hỏi gợi mở:

- Vì sao API trả top-5 thay vì chỉ top-1?
- Nếu confidence cao nhất chỉ khoảng 0.25, có nên dùng kết quả để ra quyết định tự động không?
- Vì sao ImageNet classifier tổng quát không thay thế được model chuyên ngành như nhận diện bệnh lá cây?

### 4.2. Test ảnh bằng lệnh curl

```bash
curl -X POST "http://127.0.0.1:8000/classify-image?top_k=5" \
  -F "file=@sample_images/classroom_object.jpg;type=image/jpeg"
```

Kết quả cần quan sát:

- JSON response trả về `predictions`.
- Có `inference_time_ms`.

Ý nghĩa:

- Giao diện web và curl đều gọi cùng một backend API.
- Frontend chỉ giúp thao tác trực quan hơn; inference thật nằm ở backend.

---

## 5. Build Docker image

Dừng server local nếu đang chạy. Sau đó build image:

```bash
docker build -t lab5-aiot-inference:v4 .
```

Kiểm tra image:

```bash
docker images
```

Kết quả cần quan sát:

```text
REPOSITORY              TAG
lab5-aiot-inference     v4
```

Ý nghĩa:

- Docker đã đóng gói code, thư viện, Dockerfile và lệnh chạy service thành image.
- Image là gói triển khai; container là instance đang chạy từ image.

Câu hỏi gợi mở:

- Nếu sửa code trong `app/`, có cần build lại image không?
- Nếu model được mount bằng volume, có cần build lại image khi đổi model không?

---

## 6. Chạy bằng Docker Desktop GUI

### 6.1. Kiểm tra Docker Desktop

Mở Docker Desktop và kiểm tra:

```text
Settings -> General -> Use the WSL 2 based engine
Settings -> Resources -> WSL Integration -> bật Ubuntu nếu dùng WSL
```

Kết quả cần quan sát:

- Docker Desktop ở trạng thái Running.
- Có thể mở tab Images và Containers.

### 6.2. Chạy image bằng giao diện

Sau khi build image:

1. Mở Docker Desktop.
2. Vào tab **Images**.
3. Chọn image `lab5-aiot-inference:v4`.
4. Bấm **Run**.
5. Đặt container name: `lab5-aiot-api`.
6. Cấu hình port: Host port `8000` -> Container port `8000`.
7. Nếu giao diện hỗ trợ volume, mount:
   - `outputs` trên máy host -> `/app/outputs`
   - `models/vision` trên máy host -> `/app/models/vision`
8. Bấm **Run**.
9. Vào tab **Containers** để kiểm tra container đang Running.
10. Mở tab **Logs** để quan sát log server.

Kết quả cần quan sát:

- Container `lab5-aiot-api` ở trạng thái Running.
- Logs có dòng Uvicorn đang chạy ở `0.0.0.0:8000`.
- Trình duyệt truy cập được `http://127.0.0.1:8000/docs`.

Ý nghĩa:

- Docker Desktop giúp quan sát image/container/logs bằng giao diện.
- Bản chất service vẫn chạy trong container; giao diện chỉ là công cụ quản lý trực quan.

### 6.3. Test upload ảnh trong container

Mở:

```text
http://127.0.0.1:8000/classify-image-demo
```

Kết quả cần quan sát:

- Giao diện upload ảnh hoạt động khi service chạy trong container.
- Ảnh kết quả và top-k class giống luồng local.
- Log inference được ghi vào `outputs/vision_inference_log.csv` trên host nếu mount volume đúng.

---

## 7. Chạy bằng Docker trong WSL/Linux terminal

```bash
docker run --rm --name lab5-aiot-api -p 8000:8000 \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/models/vision:/app/models/vision \
  lab5-aiot-inference:v4
```

Kết quả cần quan sát:

- Terminal hiển thị log Uvicorn.
- Docker Desktop cũng nhìn thấy container đang chạy, nếu đang dùng Docker Desktop backend.
- Trình duyệt truy cập được `/docs` và `/classify-image-demo`.

Ý nghĩa:

- WSL terminal giúp thao tác gần môi trường Linux server hơn.
- Docker Desktop trên Windows có thể cung cấp engine, còn Ubuntu WSL là môi trường terminal để gọi Docker CLI.

---

## 8. Chạy bằng Docker Compose

```bash
docker compose up --build
```

Dừng service:

```bash
docker compose down
```

Kết quả cần quan sát:

- Compose tự build và chạy service theo `docker-compose.yml`.
- Có thể kiểm tra bằng `docker compose ps`.
- Logs hiển thị bằng `docker compose logs -f`.

Ý nghĩa:

- Compose giúp thay thế lệnh `docker run` dài bằng một file cấu hình.
- Khi hệ thống có thêm dashboard, MQTT broker hoặc database, Compose giúp mô tả nhiều container cùng lúc.

---

## 9. So sánh không Docker và có Docker

### 9.1. Không Docker

Điền bảng sau sau khi chạy local:

| Tiêu chí quan sát | Kết quả ghi nhận |
|---|---|
| Python version | |
| Lỗi cài thư viện nếu có | |
| Có load được vision model không | |
| API `/health` có chạy không | |
| Upload ảnh có thành công không | |
| Log ghi ở đâu | |

### 9.2. Có Docker

Điền bảng sau sau khi chạy container:

| Tiêu chí quan sát | Kết quả ghi nhận |
|---|---|
| Image name/tag | |
| Container name | |
| Port mapping | |
| Volume mapping | |
| API `/health` có chạy không | |
| Upload ảnh trong container có thành công không | |
| Log có ghi ra host không | |

Kết luận cần rút ra:

- Docker giúp kiểm soát môi trường chạy.
- Docker không thay thế kiểm thử code.
- Docker chỉ có giá trị khi image, model, volume, port và log được cấu hình rõ ràng.

---

## 10. Lỗi thường gặp và cách quan sát

| Hiện tượng | Cần kiểm tra | Lệnh hoặc vị trí quan sát |
|---|---|---|
| Không mở được API | Container có chạy không, port mapping đúng không | `docker ps`, Docker Desktop Containers |
| API báo model ảnh chưa load | Có file ONNX trong `models/vision` không | `ls models/vision` |
| Upload ảnh lỗi | Định dạng/kích thước file | Chọn ảnh JPG/PNG nhỏ hơn giới hạn |
| Container chạy nhưng không có log trên host | Volume outputs đã mount đúng chưa | Docker Desktop Volumes hoặc `docker inspect` |
| Build image quá lâu | Mạng, cache, package Python | Docker build logs |
| Chạy local được nhưng Docker lỗi | File path, COPY trong Dockerfile, volume | Docker logs |

---

## 11. Minh chứng cần nộp

1. Ảnh chụp API `/health` khi chạy local.
2. Ảnh chụp giao diện `/classify-image-demo` sau khi upload ảnh local.
3. Ảnh Docker Desktop tab Images có image `lab5-aiot-inference:v4`.
4. Ảnh Docker Desktop tab Containers có container `lab5-aiot-api` đang Running.
5. Ảnh Docker Desktop Logs của container.
6. Ảnh Swagger `/docs` khi service chạy trong container.
7. Ảnh giao diện `/classify-image-demo` khi service chạy trong container.
8. File `outputs/service_log.csv` hoặc `outputs/vision_inference_log.csv`.
9. Bảng so sánh không Docker và có Docker.
10. Trả lời câu hỏi phân tích trong tài liệu lab.
