# CHECKLIST NỘP BÀI - LAB 5 V4

## 1. Minh chứng chạy local

- Ảnh chụp `/health` khi chạy local.
- Ảnh chụp `/docs` khi chạy local.
- Ảnh chụp `/classify-image-demo` sau khi upload ảnh local.
- File `outputs/service_log.csv` hoặc `outputs/vision_inference_log.csv`.

## 2. Minh chứng Docker Desktop

- Ảnh tab Images có image `lab5-aiot-inference:v4`.
- Ảnh tab Containers có container `lab5-aiot-api` đang Running.
- Ảnh tab Logs trong container.
- Ảnh `/docs` khi service chạy trong container.
- Ảnh `/classify-image-demo` khi service chạy trong container.

## 3. Minh chứng Docker terminal hoặc Compose

- Lệnh đã dùng để build image.
- Lệnh đã dùng để run container hoặc `docker compose up --build`.
- Ảnh hoặc text log cho thấy service chạy thành công.

## 4. Báo cáo ngắn

Báo cáo cần có các mục sau:

1. Mục tiêu của Lab 5.
2. Sơ đồ đường đi của model: model gốc -> định dạng triển khai -> API -> Docker.
3. Bảng so sánh chạy local và chạy Docker.
4. Kết quả test API cảm biến.
5. Kết quả test upload ảnh.
6. Nhận xét về lợi ích và giới hạn của Docker.
7. Nhận xét về giới hạn của model ảnh ImageNet general classifier.

## 5. Câu hỏi kiểm tra

1. Vì sao cần chạy local trước khi build Docker image?
2. Image khác container ở điểm nào?
3. Docker Desktop khác Docker Engine trên Ubuntu server ở điểm nào?
4. Vì sao cần volume khi ghi log?
5. Vì sao cần map port `8000:8000`?
6. Pretrained model khác model tự train ở điểm nào?
7. ONNX giải quyết vấn đề gì khi triển khai model?
8. Nếu model ảnh chưa được tải, endpoint `/classify-image` sẽ gặp vấn đề gì?
9. Nếu Docker chạy được nhưng trình duyệt không mở API được, cần kiểm tra những điểm nào?
10. Trong doanh nghiệp, vì sao cần model version và image tag?
