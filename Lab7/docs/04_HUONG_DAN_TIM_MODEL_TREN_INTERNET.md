# 04. Hướng dẫn tìm pretrained model trên Internet

## 1. Từ khóa tìm kiếm gợi ý

```text
YOLO fire smoke detection pretrained .pt
YOLO fall detection pretrained model
YOLO PPE detection helmet vest pretrained
YOLO plant disease detection pretrained
MediaPipe pose landmarker python live stream
EasyOCR webcam python example
SAM segmentation python example
```

## 2. Kiểm tra trước khi tải model

- Model dùng cho task nào?
- Có class names rõ không?
- Có file weights không?
- Có hướng dẫn inference không?
- License có cho phép dùng trong BTL/demo không?
- Model train trên dữ liệu nào?
- Có phù hợp với camera và môi trường của nhóm không?

## 3. Đặt model vào project

```text
models/pretrained/<ten_model>.pt
models/pretrained/<ten_model>.onnx
models/pretrained/<ten_model>.task
```

Sau đó cập nhật `model_zoo_config.json` hoặc nhập đường dẫn model trong dashboard.

## 4. Khuyến cáo

Pretrained model chỉ giúp bắt đầu nhanh. Khi triển khai thật, cần kiểm chứng trên dữ liệu tự thu và thường cần train hoặc fine-tune lại.
