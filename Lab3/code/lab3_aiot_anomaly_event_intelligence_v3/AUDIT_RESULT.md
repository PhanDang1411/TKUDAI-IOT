# Audit kết quả Lab 3

## Kết luận

Gói hiện tại đáp ứng mức **Bắt buộc** của đề Lab 3:

- Chạy đúng pipeline mẫu.
- Có notebook đã execute.
- Có Isolation Forest, metrics, predictions.
- Có Autoencoder demo.
- Có anomaly event log.
- Có API `/health`, `/model-info`, `/detect-anomaly` và file test API local.
- Có 2 biểu đồ trong `figures/`.
- Có report phân tích.

## Điểm đã sửa sau khi kiểm lại

- Notebook gốc ban đầu chưa được execute. Đã chạy bằng `jupyter nbconvert --execute --inplace`; kết quả 11/11 code cells chạy thành công, không có error.
- Gói `lab3_submission_ready.zip` ban đầu chưa gồm thư mục `notebooks/`. Đã cập nhật quy trình đóng gói để đưa notebook đã chạy vào file nộp.

## Lưu ý về mức điểm

Phần này đang làm theo mức **Bắt buộc** của đề: dùng dataset NAB mẫu. Nếu muốn nhắm mức **Khá/Giỏi**, cần thêm một mở rộng rõ ràng như:

- Ánh xạ sang use-case nhóm cụ thể.
- Điều chỉnh severity/decision rule theo use-case.
- Thêm cooldown hoặc aggregation để giảm alert fatigue.
- So sánh thêm model/threshold policy.

