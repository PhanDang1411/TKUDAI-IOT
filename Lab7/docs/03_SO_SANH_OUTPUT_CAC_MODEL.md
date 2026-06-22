# 03. So sánh output của các model

| Nhóm model | Output chính | Dùng cho bài toán |
|---|---|---|
| YOLO Detection | bbox, class, confidence | phát hiện người, xe, vật thể, PPE, lửa/khói nếu có model chuyên dụng |
| Tracking / Counting | object_id, trajectory, count | đếm người, xe, vật qua vạch |
| Pose Landmark | body keypoints | tư thế, fitness, té ngã ở mức gợi ý |
| Hand / Gesture | hand landmarks, gesture label | điều khiển bằng cử chỉ |
| Face Landmark | face points, eye/mouth landmarks | attention, ngủ gật, biểu cảm ở mức gợi ý |
| OCR | text, text bbox, confidence | đọc biển số, thẻ, hóa đơn, nhãn |
| Segmentation | mask, region area | tách vật thể, đo vùng bệnh lá, vùng lỗi sản phẩm |
| OpenCV Motion | motion mask, diff score | phát hiện chuyển động đơn giản |

Điểm cần chốt:

```text
YOLO không phải toàn bộ Computer Vision.
YOLO chỉ là một nhánh: Object Detection.
Mỗi loại model có kiểu output khác nhau và phục vụ quyết định khác nhau.
```
