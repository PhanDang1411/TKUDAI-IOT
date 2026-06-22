# Lab 8 v3 - LLM Reasoning & Context-aware Decision for AIoT

## Chạy nhanh

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
python run_lab8_demo.py
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Mở trình duyệt: http://127.0.0.1:8000/

## Ý tưởng chính

Dashboard có ba tầng so sánh:

1. Sensor only: chỉ cảm biến và rule cứng.
2. Sensor + AI models: thêm evidence từ Lab 3 anomaly, Lab 4 forecasting, Lab 6 motion/camera, Lab 7 vision.
3. Sensor + AI models + LLM: LLM tổng hợp context, giải thích, trả JSON decision, sau đó safety gate kiểm tra.

## Chế độ chạy LLM

- `mock`: luôn chạy được, không cần Internet/API key/Ollama.
- `local`: gọi Ollama tại `http://localhost:11434`, ví dụ model `qwen3:1.7b`.
- `api`: placeholder/fallback để giảng viên gắn API cloud nếu muốn.
