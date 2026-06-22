# CHẠY LAB 5 BẰNG DOCKER DESKTOP GUI

Mục tiêu của phần này là quan sát Docker bằng giao diện: image nằm ở đâu, container chạy ở đâu, log xem ở đâu, service mở port như thế nào.

## 1. Kiểm tra Docker Desktop

Mở Docker Desktop và kiểm tra:

```text
Settings -> General -> Use the WSL 2 based engine
Settings -> Resources -> WSL Integration -> bật Ubuntu nếu dùng WSL
```

Kiểm tra bằng terminal:

```bash
docker --version
docker run hello-world
```

## 2. Build image trước

Docker Desktop có thể quan sát image sau khi image được build. Chạy trong thư mục project:

```bash
docker build -t lab5-aiot-inference:v4 .
```

Sau khi build, mở Docker Desktop -> Images. Cần thấy image:

```text
lab5-aiot-inference:v4
```

## 3. Run image bằng giao diện

Thao tác:

1. Vào tab Images.
2. Chọn image `lab5-aiot-inference:v4`.
3. Bấm Run.
4. Đặt container name: `lab5-aiot-api`.
5. Map port: host `8000` -> container `8000`.
6. Nếu giao diện có phần volume, mount:
   - `outputs` -> `/app/outputs`
   - `models/vision` -> `/app/models/vision`
7. Bấm Run.

Nếu hộp thoại Run không hiển thị rõ phần volume, có thể chạy container bằng terminal hoặc Compose rồi quay lại Docker Desktop để quan sát.

## 4. Quan sát container

Mở Docker Desktop -> Containers.

Cần quan sát:

- Container `lab5-aiot-api` ở trạng thái Running.
- Port hiển thị dạng `8000:8000`.
- Có nút mở logs.

Mở Logs và tìm các dòng tương tự:

```text
Uvicorn running on http://0.0.0.0:8000
Application startup complete
```

Ý nghĩa:

- Service đang chạy bên trong container.
- Port 8000 trong container đã được map ra port 8000 trên máy host.

## 5. Test bằng trình duyệt

Mở:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/classify-image-demo
```

Cần quan sát:

- `/health` trả `service_status: ok`.
- `/docs` hiển thị API Swagger.
- `/classify-image-demo` cho phép chọn ảnh, upload và xem kết quả.

## 6. Ảnh minh chứng cần chụp

1. Tab Images có image `lab5-aiot-inference:v4`.
2. Tab Containers có container `lab5-aiot-api` đang Running.
3. Tab Logs có log Uvicorn.
4. Trình duyệt mở `/docs`.
5. Giao diện `/classify-image-demo` sau khi upload ảnh.
