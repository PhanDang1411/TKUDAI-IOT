# Lab 7 - CV Model Zoo AIoT

## Giới thiệu

Dự án này là bài thực hành Lab 7 thuộc học phần Triển khai, phát triển ứng dụng AI và IoT.
Mục tiêu của bài lab là xây dựng hệ thống AIoT sử dụng nhiều mô hình Computer Vision, trong đó có YOLO để phát hiện đối tượng và MediaPipe để phân tích pose/landmark.

Lab 7 tập trung vào việc tích hợp các mô hình thị giác máy tính vào một hệ thống AIoT có giao diện web và API, giúp camera trở thành một cảm biến thông minh trong hệ thống giám sát.

## Mục tiêu bài lab

Sau khi hoàn thành Lab 7, có thể:

* Hiểu khái niệm CV Model Zoo trong hệ thống AIoT.
* Tích hợp YOLO vào hệ thống nhận diện đối tượng.
* Sử dụng YOLO để phát hiện người hoặc vật thể trong ảnh/camera.
* Sử dụng MediaPipe để phân tích pose landmark.
* Sử dụng OpenCV để đọc ảnh, camera hoặc video.
* Sử dụng FastAPI để xây dựng API xử lý ảnh.
* Trả kết quả nhận diện dưới dạng JSON.
* Ghi log sự kiện và lưu ảnh kết quả.
* Hiểu cách AI hỗ trợ IoT giám sát theo thời gian thực.

## Công nghệ sử dụng

* Python
* FastAPI
* Uvicorn
* OpenCV
* YOLO
* MediaPipe
* HTML/CSS/JavaScript
* Git/GitHub

## Chức năng chính

* Upload ảnh để xử lý bằng mô hình AI.
* Nhận diện đối tượng bằng YOLO.
* Phát hiện người trong ảnh hoặc camera.
* Có thể lọc chỉ nhận diện class `person`.
* Phân tích pose landmark bằng MediaPipe.
* Hiển thị ảnh gốc và ảnh đã xử lý.
* Trả kết quả xử lý dưới dạng JSON.
* Ghi log sự kiện vào thư mục `outputs/`.
* Lưu ảnh kết quả vào thư mục `captures/`.

## Ý tưởng hệ thống

Camera hoặc ảnh đầu vào được xem như một nguồn dữ liệu IoT.
Hệ thống sử dụng YOLO để phát hiện đối tượng, sau đó chuyển kết quả nhận diện thành dữ liệu sự kiện phục vụ giám sát thông minh.

Luồng xử lý chính:

```text
Camera / Image
→ OpenCV
→ YOLO Object Detection
→ Detection Result
→ Event Log
→ Dashboard / API
```

## Cách cài đặt

### Bước 1: Tạo môi trường ảo

```bash
python -m venv .venv
```

### Bước 2: Kích hoạt môi trường ảo

Trên Windows:

```bash
.venv\Scripts\activate
```

### Bước 3: Cài đặt thư viện

```bash
pip install -r requirements.txt
```

## Cách chạy chương trình

Chạy server FastAPI:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Sau đó mở trình duyệt và truy cập:

```text
http://127.0.0.1:8000
```

Có thể kiểm tra API tại:

```text
http://127.0.0.1:8000/docs
```

## Ví dụ kết quả JSON

```json
{
  "task": "object_detection",
  "engine": "yolo",
  "num_records": 1,
  "records": [
    {
      "label": "person",
      "confidence": 0.86,
      "class_id": 0
    }
  ],
  "event": {
    "severity": "INFO",
    "message": "Detected person in frame"
  }
}
```

## Kết quả đầu ra

Hệ thống có thể tạo ra:

* Ảnh đã được YOLO nhận diện đối tượng.
* Bounding box quanh người hoặc vật thể.
* Kết quả JSON gồm label, confidence, class_id.
* Log sự kiện trong thư mục `outputs/`.
* Ảnh kết quả trong thư mục `captures/`.

<img width="1917" height="880" alt="image" src="https://github.com/user-attachments/assets/45ad3ace-d7ab-40f7-8709-4e4b41a54370" />

