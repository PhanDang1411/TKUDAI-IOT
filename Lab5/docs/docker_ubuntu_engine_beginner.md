# DOCKER ENGINE TRÊN UBUNTU SERVER/VM

Phần này trình bày hướng triển khai gần môi trường doanh nghiệp hơn. Docker Engine được cài trực tiếp trên Ubuntu server hoặc Ubuntu máy ảo. Không dùng Docker Desktop GUI.

## 1. Khác biệt so với Docker Desktop

| Nội dung | Docker Desktop | Docker Engine trên Ubuntu |
|---|---|---|
| Môi trường | Laptop cá nhân, có GUI | Server/VM Linux, chủ yếu terminal |
| Quản lý container | GUI và CLI | CLI, script, CI/CD |
| Mục tiêu | Học tập, phát triển, demo | Triển khai, vận hành, tự động hóa |
| Quan sát logs | Docker Desktop Logs hoặc CLI | `docker logs`, `docker compose logs` |
| Quản lý service lâu dài | Có thể dùng nhưng thiên local dev | Dùng restart policy, systemd, CI/CD, orchestration |

## 2. Luồng triển khai cơ bản

```text
Cài Docker Engine
-> copy project lên server
-> build image hoặc pull image từ registry
-> chạy container
-> mở port
-> kiểm tra health check
-> xem logs
-> cấu hình restart policy
```

## 3. Lệnh cơ bản

```bash
docker build -t lab5-aiot-inference:v4 .
docker run -d --name lab5-aiot-api --restart unless-stopped \
  -p 8000:8000 \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/models/vision:/app/models/vision \
  lab5-aiot-inference:v4
```

Kiểm tra:

```bash
docker ps
docker logs -f lab5-aiot-api
curl http://127.0.0.1:8000/health
```

## 4. Khi dùng Docker Compose

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
docker compose down
```

Ý nghĩa:

- `up -d`: chạy nền.
- `ps`: xem service đang chạy.
- `logs -f`: theo dõi logs realtime.
- `down`: dừng và gỡ container do Compose tạo.

## 5. Câu hỏi gợi mở

1. Vì sao server doanh nghiệp thường không dùng Docker Desktop GUI?
2. Vì sao cần `--restart unless-stopped` khi chạy service lâu dài?
3. Nếu model được cập nhật, nên đổi image tag hay ghi đè tag cũ?
4. Nếu port 8000 không truy cập được từ máy khác, cần kiểm tra firewall, security group hay Docker port mapping?
