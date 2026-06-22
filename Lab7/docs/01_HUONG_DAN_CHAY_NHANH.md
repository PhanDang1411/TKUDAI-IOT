# 01. Hướng dẫn chạy nhanh

## 1. Cài môi trường

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux/WSL
source .venv/bin/activate
pip install -r requirements_core.txt
```

## 2. Chạy thử không cần camera

```bash
python run_model_zoo_demo.py
```

Quan sát:
- `RUN_TEST_LOG.txt` có dòng `LOCAL_PIPELINE_TEST_PASS`.
- `data/captures/` có ảnh kết quả cho nhiều task.
- `outputs/model_zoo_demo_report.json` có báo cáo số record của từng task.

## 3. Chạy dashboard

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Mở:

```text
http://127.0.0.1:8000/
```

## 4. Chạy bằng camera laptop

- Ô nguồn camera để `0`.
- Chọn task.
- Bấm `Bắt đầu stream`.
- Làm theo hướng dẫn trong khung màu xanh.

## 5. Khi camera không chạy

- Kiểm tra camera có đang bị Zoom/Teams/Meet chiếm không.
- Thử đổi nguồn camera từ `0` sang `1`.
- Nếu vẫn lỗi, hệ thống dùng stream mô phỏng để quan sát output.
