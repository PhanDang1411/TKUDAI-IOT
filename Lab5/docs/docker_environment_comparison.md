# PHÂN BIỆT DOCKER DESKTOP, WSL UBUNTU VÀ DOCKER ENGINE TRÊN UBUNTU

## 1. Ba môi trường dễ nhầm lẫn

Các cụm từ sau cùng liên quan đến Docker nhưng không giống nhau:

1. Docker Desktop trên Windows.
2. Docker CLI trong Ubuntu WSL.
3. Docker Engine cài trực tiếp trên Ubuntu server hoặc Ubuntu máy ảo.

## 2. Bảng so sánh

| Tiêu chí | Docker Desktop trên Windows | Docker trong WSL Ubuntu | Docker Engine trên Ubuntu server/VM |
|---|---|---|---|
| Bản chất | Ứng dụng desktop có GUI và Docker engine tích hợp | Terminal Linux trong Windows, thường kết nối Docker Desktop engine | Docker Engine cài trực tiếp trên hệ điều hành Ubuntu |
| Giao diện | Có Images, Containers, Logs, Volumes | Chủ yếu dùng lệnh | Chủ yếu dùng lệnh |
| Phù hợp | Học tập, demo, development trên laptop | Làm quen Linux workflow | Server, lab doanh nghiệp, cloud VM |
| Có cần WSL không | Trên Windows thường dùng WSL 2 backend | Có | Không nếu đã chạy Ubuntu thật/VM/server |
| Gần thực tế server | Trung bình | Khá gần | Gần nhất |

## 3. Docker Desktop trên Windows

Docker Desktop cung cấp giao diện để quan sát image, container, logs, port và volumes. Trên Windows, Docker Desktop thường dùng WSL 2 backend để chạy Linux containers. Môi trường này phù hợp cho học tập vì giảm độ khó khi mới làm quen Docker.

Cần quan sát trong Lab 5:

- Tab Images có image `lab5-aiot-inference:v4`.
- Tab Containers có container `lab5-aiot-api` đang Running.
- Tab Logs có log Uvicorn.
- Trình duyệt mở được `/docs` và `/classify-image-demo`.

## 4. Docker trong WSL Ubuntu

Ubuntu WSL là môi trường Linux chạy trong Windows. Khi Docker Desktop bật WSL Integration, lệnh `docker` trong Ubuntu WSL có thể gọi Docker engine do Docker Desktop quản lý.

Ý nghĩa học tập:

- Làm quen cú pháp Linux.
- Gần với thao tác trên server hơn Docker Desktop GUI.
- Hạn chế lỗi do khác biệt đường dẫn Windows/Linux nếu project đặt trong filesystem WSL.

## 5. Docker Engine trên Ubuntu server hoặc VM

Đây là hướng triển khai gần thực tế doanh nghiệp hơn. Docker Engine được cài trực tiếp trên Ubuntu. Không có Docker Desktop GUI. Toàn bộ thao tác thường thực hiện bằng terminal, script, CI/CD hoặc công cụ orchestration.

Luồng tư duy:

```text
Cài Docker Engine
-> pull/build image
-> run container hoặc docker compose up
-> mở port
-> kiểm tra logs
-> cấu hình restart policy
-> giám sát service
```

## 6. Kết luận cần nhớ

- Docker Desktop thuận tiện cho học tập và development trên laptop.
- WSL Ubuntu giúp Windows có trải nghiệm gần Linux server.
- Ubuntu server/VM với Docker Engine là hướng triển khai gần môi trường doanh nghiệp hơn.
- Bản chất cần nắm là image, container, port, volume, log và version; giao diện sử dụng có thể thay đổi theo môi trường.
