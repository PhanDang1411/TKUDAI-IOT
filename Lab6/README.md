# Lab 6 - Computer Vision as IoT Sensor

Lab 6 triển khai camera/ảnh như một cảm biến IoT trực quan. Project chính nằm tại:

```text
Lab6/code/lab6_cv_as_iot_sensor/
```

## Nội dung chính

- Live stream từ camera laptop hoặc IP camera.
- Snapshot, ghi video ngắn và xử lý ảnh cơ bản.
- Motion scoring để chọn frame quan trọng.
- YOLO object detection để nhận diện riêng `person` và `animal`.
- Bounding box cho người/động vật trên ảnh kết quả.
- Realtime event bằng server-sent events.
- Event cooldown để tránh spam log khi cùng một đối tượng xuất hiện liên tục.

## Chạy nhanh

```powershell
cd Lab6\code\lab6_cv_as_iot_sensor
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Mở dashboard:

```text
http://127.0.0.1:8000
```

Xem hướng dẫn chi tiết trong `code/lab6_cv_as_iot_sensor/README.md`.
