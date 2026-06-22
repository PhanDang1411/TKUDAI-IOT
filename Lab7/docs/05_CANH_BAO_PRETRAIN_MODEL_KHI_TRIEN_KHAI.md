# 05. Cảnh báo khi dùng pretrained model

Pretrained model rất hữu ích để demo nhanh, nhưng không nên xem là mô hình triển khai ổn định ngay.

## Rủi ro thường gặp

1. Camera trong thực tế khác camera trong dữ liệu train.
2. Ánh sáng, góc quay, khoảng cách, nền ảnh thay đổi.
3. Class names không đúng bài toán.
4. Model nhận sai nhưng confidence vẫn có thể cao.
5. Model quá nặng, realtime bị giật.
6. Không rõ license hoặc nguồn dữ liệu train.

## Khi nào cần train/fine-tune lại?

- Bài toán có đối tượng chuyên ngành: lửa/khói, PPE, bệnh lá cây, lỗi sản phẩm.
- Camera cố định trong môi trường cụ thể.
- Cần giảm false alarm hoặc missed detection.
- Cần chạy ổn định để báo cáo BTL hoặc demo capstone.

## Quy tắc an toàn

```text
Model output → event → rule/safety check → dashboard/human review → action
```

Không cho model điều khiển actuator trực tiếp nếu chưa có rule an toàn.
