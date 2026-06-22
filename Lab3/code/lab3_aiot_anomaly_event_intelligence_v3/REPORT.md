# Lab 3 Report (mẫu 1–2 trang)

Project: `lab3_aiot_anomaly_event_intelligence_v3`  
Mục tiêu: Anomaly Detection & Event Intelligence cho chuỗi thời gian IoT (NAB ambient temperature).

## 1) Lab 3 đang phát hiện bất thường hay dự báo tương lai?

Lab 3 là **phát hiện bất thường (anomaly detection)** trên telemetry hiện tại/quá khứ gần. Output chính là `anomaly_score`, `is_anomaly` và event vận hành (severity/decision). Lab 3 **không** dự báo giá trị tương lai như forecasting.

## 2) Vì sao dữ liệu IoT cần chia train/test theo thời gian?

Chuỗi thời gian có tính phụ thuộc theo thời gian (seasonality, drift, regime). Nếu random split sẽ gây **data leakage**: mô hình “nhìn thấy tương lai” trong train, làm metric ảo. Vì vậy cần **chronological split** (train quá khứ, test tương lai).

## 3) Precision thấp gây rủi ro gì cho người vận hành?

Precision thấp → nhiều **false positive** (báo động sai) → **alert fatigue**, người vận hành giảm niềm tin và có thể bỏ qua cả cảnh báo thật, tăng rủi ro vận hành.

## 4) Recall thấp gây rủi ro gì cho hệ thống?

Recall thấp → nhiều **false negative** (bỏ sót anomaly) → lỗi thật không được phát hiện kịp thời, có thể gây hỏng thiết bị, mất an toàn, hoặc tổn thất năng lượng/chất lượng dịch vụ.

## 5) MSE trong Autoencoder có ý nghĩa gì?

Autoencoder học tái tạo “pattern bình thường”. **Reconstruction MSE** cao nghĩa là window hiện tại khó tái tạo theo pattern bình thường → có khả năng bất thường (pattern deviation).

## 6) anomaly_score khác decision như thế nào?

- `anomaly_score`: output định lượng của model (mức “lạ” so với bình thường).
- `decision`: quyết định vận hành/safety (tạo alert, warning, chỉ log, hay không làm gì).

Decision không nên phụ thuộc chỉ vào score; còn cần rule vận hành, ngữ cảnh, độ tin cậy, và chính sách an toàn.

## 7) Vì sao anomaly cao chưa chắc được phép điều khiển thiết bị?

Anomaly cao có thể do: sensor lỗi, stuck, spike nhiễu, drift cảm biến… Nếu tự động điều khiển dựa trên dữ liệu sai có thể gây hành vi nguy hiểm. Trong hệ thống thật cần **human-in-the-loop** hoặc **safety rule** trước khi tác động thiết bị.

## 8) Nếu triển khai thật, cần thêm safety rule nào?

Gợi ý các safety rule thường dùng:

- **Rate limiting / cooldown**: giảm tần suất tạo alert liên tiếp.
- **Hysteresis**: tránh bật/tắt liên tục quanh ngưỡng.
- **Cross-check sensor**: so sánh với sensor dự phòng/nguồn khác.
- **Graceful degradation**: khi sensor nghi lỗi → chuyển sang chế độ an toàn (fail-safe).
- **Minimum evidence window**: yêu cầu anomaly kéo dài N điểm hoặc N phút trước khi nâng severity.
- **Override manual**: cho phép vận hành xác nhận/huỷ cảnh báo.

## 9) Nếu cảnh báo quá nhiều, giảm alert fatigue bằng cách nào?

- Dùng **cooldown**, **aggregation** (gộp nhiều điểm anomaly thành 1 event).
- Thêm rule “chỉ nâng severity khi kéo dài” (persistence).
- Điều chỉnh threshold theo chính sách (ưu tiên precision vs recall theo rủi ro).
- Phân loại event_type để lọc trên dashboard (stuck/spike/deviation).

## 10) Nhóm sẽ hiển thị gì trên dashboard ngoài giá trị cảm biến?

- `anomaly_score` và `threshold_used` theo thời gian.
- Event stream: `event_type`, `severity`, `decision`, `explanation`.
- Thống kê vận hành: số alert/ngày, top device, thời lượng anomaly.
- “Sensor health” (stuck candidate, missing data, drift indicator).

## Phân biệt test model offline vs deploy model online

- **Offline test (notebook/script)**: chạy batch trên tập test có label để tính Precision/Recall/F1, vẽ biểu đồ, phân tích false alert/missed anomaly.
- **Online deploy (API)**: nhận telemetry history, tính feature và trả JSON theo schema (`model_output` + `event`) để hệ thống khác tiêu thụ; cần latency thấp, schema ổn định, và safety note.

## Kết quả cần nộp (tham chiếu)

- `outputs/iforest_metrics.json`, `outputs/autoencoder_metrics.json`
- `outputs/anomaly_event_log.csv`, `outputs/api_test_result.json`
- `figures/anomaly_detection_result.png`, `figures/anomaly_score_over_time.png`

