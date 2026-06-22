# 07. Câu hỏi và yêu cầu thay đổi tham số

## Yêu cầu thực hành

1. Chạy ít nhất 4 task khác nhau trong Model Zoo.
2. Với mỗi task, chụp màn hình kết quả và ghi lại output chính.
3. Thay đổi ít nhất 2 tham số và nhận xét tác động.
4. Ghi nhận một trường hợp đúng, một trường hợp sai hoặc không ổn định.
5. Đề xuất một ý tưởng BTL dựa trên một task đã thử.

## Tham số cần thử

| Task | Tham số | Giá trị gợi ý |
|---|---|---|
| Detection | confidence | 0.25 / 0.50 / 0.70 |
| Detection | classes | person / bottle / cell phone |
| Stream | detect_every | 1 / 3 / 5 |
| Pose | min_conf | 0.3 / 0.5 / 0.7 |
| OCR | khoảng cách chữ | gần / vừa / xa |
| Segmentation | alpha | 0.2 / 0.5 / 0.8 |
| Motion | motion_threshold | 15 / 25 / 40 |

## Câu hỏi hiểu bản chất

1. Vì sao không nên gọi mọi bài toán thị giác là YOLO?
2. Output của detection, pose, OCR và segmentation khác nhau thế nào?
3. Vì sao tracking cần nhớ trạng thái qua nhiều frame?
4. Vì sao OCR dễ sai khi chữ nhỏ hoặc nghiêng?
5. Vì sao segmentation phù hợp để đo diện tích vùng bệnh lá hơn bbox?
6. Với BTL của nhóm, task nào phù hợp nhất? Vì sao?
7. Khi nào pretrained model cần train/fine-tune lại?
8. Nếu model chạy giật, nên giảm tham số nào trước?
9. Vì sao cần event/log thay vì chỉ hiển thị ảnh?
10. Output của Lab 7 mở rộng có thể đưa vào Lab 8 reasoning như thế nào?
