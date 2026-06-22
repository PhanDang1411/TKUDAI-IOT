# ĐỊNH DẠNG MODEL TRONG TRIỂN KHAI AI

## 1. Không bắt đầu bằng ONNX

Model thường được train trong một framework cụ thể. Sau khi train xong, model được lưu ở định dạng gốc của framework đó. Khi đưa vào triển khai, định dạng triển khai được lựa chọn dựa trên runtime, phần cứng, tốc độ inference, kích thước model và khả năng bảo trì.

## 2. Định dạng model thường gặp

| Framework | Định dạng thường gặp | Ý nghĩa |
|---|---|---|
| PyTorch | `.pt`, `.pth`, `state_dict` | Lưu trọng số và/hoặc trạng thái model trong hệ PyTorch |
| TensorFlow/Keras | `.keras`, SavedModel, `.h5` | Lưu model trong hệ sinh thái TensorFlow/Keras |
| scikit-learn | `.joblib`, `.pkl` | Lưu model ML cổ điển trong Python |
| ONNX | `.onnx` | Định dạng mở để trao đổi và chạy inference bằng ONNX Runtime |
| TensorFlow Lite | `.tflite` | Định dạng nhẹ cho mobile và edge device |

## 3. Đường chuyển đổi triển khai

```text
PyTorch/TensorFlow/scikit-learn model
-> kiểm thử inference trong framework gốc
-> xuất sang ONNX/TFLite nếu cần
-> kiểm tra sai khác sau chuyển đổi
-> đóng gói runtime vào API service
-> build Docker image
-> triển khai container
```

## 4. Lợi ích và đánh đổi

| Hướng triển khai | Lợi ích | Đánh đổi |
|---|---|---|
| Dùng framework gốc | Dễ debug, gần code train | Runtime nặng, phụ thuộc framework |
| ONNX Runtime | Portable hơn, gọn hơn cho inference | Cần convert và kiểm tra operator |
| TFLite | Phù hợp mobile/edge | Có thể cần quantization, giới hạn operator |
| Quantization | Model nhỏ và nhanh hơn | Có thể giảm độ chính xác |

## 5. Câu hỏi gợi mở

1. Nếu một model chỉ chạy được trong đúng môi trường train ban đầu, quá trình triển khai có bền vững không?
2. Vì sao cần kiểm tra kết quả trước và sau khi chuyển sang ONNX?
3. Khi nào nên ưu tiên model nhẹ thay vì model có độ chính xác cao hơn?
4. Với thiết bị biên, kích thước model và latency ảnh hưởng thế nào đến hệ thống?
