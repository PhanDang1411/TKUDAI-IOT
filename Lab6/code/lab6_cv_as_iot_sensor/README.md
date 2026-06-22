# Lab 6 - Computer Vision as IoT Sensor

Lab này đưa camera/ảnh vào hệ thống AIoT như một cảm biến trực quan. Mục tiêu là chạy được live stream, chụp ảnh, ghi video, phát hiện chuyển động, xử lý ảnh cơ bản, ghi metadata, sinh event và quan sát trên dashboard HTML.

Trong luồng motion capture, hệ thống không chỉ báo "có chuyển động" ngay lập tức. Pipeline mới chạy theo thứ tự:

```text
camera frame → motion scoring/chọn frame → YOLO object detection → tách nhãn person/animal → bounding box → realtime event
```

Backend hỗ trợ chọn model:

- `YOLOv8n realtime`: nhanh, phù hợp demo realtime trên laptop.
- `YOLOv8s strong`: mạnh hơn, detect ổn hơn nhưng chậm hơn.
- `YOLO11n realtime`: model đời mới, nhanh nếu môi trường ultralytics hỗ trợ.
- `YOLO11s strong`: mạnh hơn bản nano, cần máy tốt hơn.
- `OpenCV fallback`: HOG person + cat-face cascade, dùng khi chưa cài/tải được YOLO.

Lần đầu chọn YOLO, thư viện Ultralytics có thể tự tải file `.pt`; các lần sau dùng cache local.

Logic thông báo tách riêng:

- Detect có người: sinh event `PERSON_DETECTED` và thông báo người.
- Detect có con vật: sinh event `ANIMAL_DETECTED` và thông báo động vật.
- Detect có cả người và con vật: sinh 2 event riêng `PERSON_DETECTED` và `ANIMAL_DETECTED`, không gộp chung.
- Có chuyển động nhưng không xác nhận người/con vật: sinh event `MOTION_WITHOUT_PERSON_OR_ANIMAL`, chỉ ghi log, không nên thông báo.
- Không đủ chuyển động và không có người/con vật: sinh event `NO_SIGNIFICANT_MOTION`.

Luồng này giúp event gần với vận hành IoT hơn: motion vẫn được tính để biết mức thay đổi của khung hình, nhưng YOLO là phần quyết định thông báo người/động vật. Ảnh kết quả có bounding box: màu xanh cho người, màu cam cho động vật.

Để giảm rủi ro khi demo realtime:

- Camera laptop dùng `CameraSession`, giữ camera mở ổn định thay vì mỗi request mở/tắt lại camera.
- Event realtime có cooldown 10 giây cho từng loại event/source, tránh spam `PERSON_DETECTED` hoặc `ANIMAL_DETECTED` liên tục.
- UI vẫn cập nhật trạng thái detect liên tục, nhưng CSV chỉ ghi log khi hết cooldown hoặc có event mới cần ghi.

## Cấu trúc file chính

```text
app.py              # backend FastAPI: stream, snapshot, video, motion, preprocess, metadata, event
index.html          # giao diện dashboard: stream, upload ảnh, quan sát ảnh/metadata/event
run_lab6_demo.py    # chạy thử nhanh không cần camera thật
run_laptop_camera_demo.py # chạy snapshot/video/motion bằng camera laptop source 0
```

## Chạy nhanh

```bash
python -m venv .venv
# Windows
.venv\Scriptsctivate
# macOS/Linux/WSL
source .venv/bin/activate
pip install -r requirements.txt
python run_lab6_demo.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Mở trình duyệt:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/docs
```

## Demo bằng camera laptop

1. Đóng các app đang dùng camera như Zoom, Teams, OBS nếu camera bị chiếm.
2. Chạy kiểm tra nhanh bằng camera laptop:

```bash
python run_laptop_camera_demo.py
```

3. Chạy dashboard:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

4. Mở `http://127.0.0.1:8000/`, giữ `Camera source = 0`, rồi demo theo thứ tự:

- `Bật stream`: chứng minh lấy hình trực tiếp từ camera laptop.
- `Chụp snapshot`: lưu ảnh gốc, ảnh xử lý bốn bước và metadata.
- `Ghi video 5s`: lưu video ngắn vào `data/videos/`.
- `Motion + detect người/động vật riêng`: chọn frame theo motion score, chạy YOLO và sinh thông báo riêng cho `person`/`animal`.
- `Bật monitor realtime`: mở server-sent events từ `/motion-stream`, backend tự kiểm tra motion + detect liên tục và đẩy kết quả lên UI.

Trên UI, khu vực `Trạng thái thông báo motion` có 2 ô riêng:

- `Thông báo người`: chỉ chuyển sang `CÓ NGƯỜI` khi backend ghi event `PERSON_DETECTED`.
- `Thông báo động vật`: chỉ chuyển sang `CÓ ĐỘNG VẬT` khi backend ghi event `ANIMAL_DETECTED`.
- `Ảnh detect bounding box`: hiển thị frame đã khoanh đối tượng bằng model đã chọn.
- Trạng thái `log=đã ghi` nghĩa là event vừa được ghi vào CSV; `log=cooldown/không ghi lặp` nghĩa là vẫn detect thấy đối tượng nhưng hệ thống không ghi trùng quá dày.

Có thể tinh chỉnh motion trực tiếp trên giao diện:

- `seconds`: thời gian quan sát chuyển động.
- `threshold`: độ nhạy khác biệt giữa hai frame; thấp hơn thì nhạy hơn.
- `min_area`: diện tích chuyển động tối thiểu; thấp hơn thì dễ bắt chuyển động nhỏ hơn.
- `confidence`: ngưỡng tin cậy của YOLO; cao hơn thì ít false alert hơn nhưng dễ bỏ sót hơn.
- `Detection model`: chọn model nhanh/mạnh tùy máy.

Mặc định `seconds = 1` để phản hồi nhanh hơn. Nếu để `seconds = 8`, hệ thống sẽ phải quan sát đủ 8 giây rồi mới trả kết quả, nên không phù hợp demo realtime.

## Cần quan sát sau khi chạy

- `data/raw_images/`: ảnh gốc từ upload/snapshot/motion.
- `data/processed_images/`: ảnh tổng hợp bốn bước xử lý.
- `data/videos/`: video ngắn ghi từ camera hoặc stream mô phỏng.
- `outputs/image_metadata.csv`: metadata của ảnh.
- `outputs/image_event_log.csv`: event sinh từ ảnh/camera.
- Dashboard tại `/`: live stream, ảnh gốc, ảnh xử lý, bảng metadata và event.
