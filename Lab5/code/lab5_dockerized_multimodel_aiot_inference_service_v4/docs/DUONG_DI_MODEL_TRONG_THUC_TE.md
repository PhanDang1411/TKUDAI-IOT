# ĐƯỜNG ĐI CỦA MODEL TRONG HỆ THỐNG THỰC TẾ

Tài liệu này tách riêng phần model để tránh hiểu nhầm rằng ONNX là điểm bắt đầu. Trong hệ thống thực tế, model thường bắt đầu từ quá trình huấn luyện trong một framework, sau đó mới được đóng gói thành service và triển khai.

## 1. Đường đi tổng quát

```text
Dữ liệu huấn luyện
-> train model trong framework
-> lưu model ở định dạng gốc
-> kiểm thử inference local
-> chuyển đổi hoặc tối ưu định dạng nếu cần
-> đóng gói vào API service
-> build Docker image
-> chạy container
-> ghi log, giám sát, cập nhật version
```

Ý nghĩa:

- Giai đoạn train quyết định model học được gì.
- Giai đoạn inference quyết định model phục vụ hệ thống như thế nào.
- Giai đoạn deployment quyết định model có chạy ổn định trên môi trường khác hay không.

## 2. Định dạng model gốc

| Nguồn model | Định dạng thường gặp | Đặc điểm |
|---|---|---|
| PyTorch | `.pt`, `.pth`, `state_dict` | Phù hợp nghiên cứu và train deep learning; khi load có thể cần đúng kiến trúc model Python |
| TensorFlow/Keras | `.keras`, SavedModel, `.h5` | Phù hợp hệ sinh thái TensorFlow; có đường chuyển sang TensorFlow Lite |
| scikit-learn | `.joblib`, `.pkl` | Phù hợp model cổ điển như Linear, Random Forest, Gradient Boosting |

Câu hỏi gợi mở:

- Nếu chỉ gửi file `.pth` nhưng thiếu class định nghĩa model, quá trình load model có thể gặp lỗi gì?
- Nếu model `.joblib` được lưu bằng một version scikit-learn khác, việc deploy có thể rủi ro ở điểm nào?

## 3. Vì sao xuất hiện ONNX?

ONNX là định dạng mở để biểu diễn model theo hướng dễ trao đổi giữa các framework và runtime. Trong Lab 5, ONNX được dùng cho model ảnh vì mục tiêu là inference nhẹ, dễ chạy CPU và dễ đóng gói vào Docker.

Lợi ích:

- Giảm phụ thuộc vào framework huấn luyện ban đầu.
- Có thể dùng ONNX Runtime để chạy inference.
- Phù hợp khi cần triển khai model trong service độc lập.

Đánh đổi:

- Không phải mọi operator đều chuyển đổi hoàn hảo.
- Cần kiểm tra kết quả trước và sau khi convert.
- Debug có thể khó hơn so với framework gốc.

## 4. Các định dạng nhẹ khác

| Định dạng/hướng tối ưu | Dùng khi nào | Lợi ích | Đánh đổi |
|---|---|---|---|
| TensorFlow Lite | Mobile, Android, edge device | Nhẹ, hợp thiết bị yếu | Phải convert từ TensorFlow/Keras, có thể giới hạn operator |
| Quantized ONNX | CPU/edge inference | Model nhỏ hơn, inference có thể nhanh hơn | Có thể giảm độ chính xác |
| TorchScript | Triển khai trong hệ PyTorch | Giữ gần hệ PyTorch | Ít portable hơn ONNX |
| OpenVINO | Intel CPU/iGPU/VPU | Tối ưu tốt cho phần cứng Intel | Phụ thuộc toolchain và phần cứng |

## 5. Model ảnh trong Lab 5

Lab 5 dùng SqueezeNet ONNX pretrained ImageNet-1K. Đây là model ảnh nhẹ để kiểm thử inference service. Model này không được train lại trong Lab 5.

Mục tiêu học tập:

- Hiểu cách model đã huấn luyện sẵn được đưa vào API.
- Hiểu endpoint upload ảnh nhận file, tiền xử lý ảnh, chạy model, trả top-k class.
- Hiểu Docker đóng gói runtime, API, thư viện và đường dẫn model.

Giới hạn cần nhận thức:

- ImageNet classifier là model tổng quát, không phải model chuyên ngành.
- 1000 class không có nghĩa là nhận diện được mọi vật thể trong đời sống.
- Kết quả model cần được đọc cùng confidence và bối cảnh sử dụng.

## 6. Chuẩn doanh nghiệp thường gặp

Trong môi trường doanh nghiệp, service AI thường cần các thành phần sau:

| Thành phần | Vai trò |
|---|---|
| API contract | Quy định input/output rõ ràng |
| Model version | Biết service đang dùng model nào |
| Docker image tag | Quản lý phiên bản triển khai |
| Registry | Nơi lưu và phân phối image |
| Health check | Kiểm tra service còn sống hay không |
| Logs | Truy vết request, lỗi, thời gian inference |
| Monitoring | Theo dõi latency, lỗi, tài nguyên |
| Rollback | Quay lại phiên bản trước nếu bản mới lỗi |

Câu hỏi gợi mở:

- Nếu đổi model mới nhưng giữ nguyên API, service phía ngoài có cần sửa không?
- Nếu model mới cho kết quả tệ hơn, cần quay lại phiên bản cũ bằng cách nào?
- Nếu latency tăng mạnh sau khi đổi model, log nào cần được đọc trước?
