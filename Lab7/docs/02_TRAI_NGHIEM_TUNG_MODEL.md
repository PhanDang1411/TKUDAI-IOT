# 02. Trải nghiệm từng nhóm model

## Trạm 1: Object Detection

Mục tiêu: quan sát bbox, class và confidence.

Thao tác:
1. Chọn `Object Detection - YOLO / bbox`.
2. Bấm `Bắt đầu stream`.
3. Đưa chai nước, điện thoại, laptop hoặc người lên camera.
4. Quan sát bbox và confidence.
5. Đổi confidence từ `0.25` sang `0.50` và `0.70`.

Câu hỏi:
- Khi tăng confidence, số bbox thay đổi thế nào?
- Vật nhỏ hoặc xa camera có dễ bị bỏ sót không?

## Trạm 2: Tracking & Counting

Mục tiêu: hiểu detection theo từng frame khác tracking qua nhiều frame.

Thao tác:
1. Chọn `Tracking & Counting`.
2. Di chuyển người hoặc vật qua vạch ngang.
3. Quan sát ID và count.

Câu hỏi:
- ID có ổn định khi vật di chuyển nhanh không?
- Counting cần tracking vì sao?

## Trạm 3: Pose Landmark

Thao tác:
1. Chọn `Pose Landmark`.
2. Đứng trước camera.
3. Giơ tay, ngồi, cúi người.

Câu hỏi:
- Pose landmark khác bbox ở điểm nào?
- Nếu dùng phát hiện té ngã, một frame có đủ không?

## Trạm 4: Hand / Gesture

Thao tác:
1. Chọn `Hand / Gesture`.
2. Giơ bàn tay trước camera.
3. Thử các cử chỉ: open palm, thumbs-up, victory.

Câu hỏi:
- Gesture có thể dùng làm lệnh điều khiển IoT không?
- Cần rule an toàn nào trước khi điều khiển thiết bị?

## Trạm 5: Face Landmark

Thao tác:
1. Chọn `Face Landmark`.
2. Nhìn vào camera, quay trái/phải, thử nhắm mắt.

Câu hỏi:
- Face landmark có thể dùng cho attention/drowsiness không?
- Cần lưu ý gì về quyền riêng tư?

## Trạm 6: OCR

Thao tác:
1. Chọn `OCR`.
2. Đưa giấy có chữ lớn trước camera hoặc upload ảnh chữ.
3. Quan sát text nhận được.

Câu hỏi:
- Vì sao chữ nhỏ, nghiêng, mờ dễ sai?
- Nếu dùng cho biển số xe cần thêm bước gì?

## Trạm 7: Segmentation

Thao tác:
1. Chọn `Segmentation`.
2. Upload ảnh có vật thể rõ.
3. Quan sát mask và vùng được tô màu.

Câu hỏi:
- Mask khác bbox thế nào?
- Bài toán nào cần mask thay vì bbox?

## Trạm 8: OpenCV Motion

Thao tác:
1. Chọn `OpenCV Motion baseline`.
2. Di chuyển vật trước camera.
3. Quan sát vùng chuyển động.

Câu hỏi:
- Motion detection có phải AI model không?
- Vì sao motion detection vẫn hữu ích trong AIoT?
