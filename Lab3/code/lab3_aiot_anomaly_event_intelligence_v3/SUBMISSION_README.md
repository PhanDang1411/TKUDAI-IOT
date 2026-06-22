# Lab 3 - Gói nộp bài

## Nội dung đã hoàn thành

- Notebook gốc `notebooks/01_anomaly_detection_event_intelligence.ipynb` đã chạy hết, 11/11 code cells có output và không có error.
- Train/test Isolation Forest theo chuỗi thời gian.
- Sinh metrics: `outputs/iforest_metrics.json`.
- Sinh event log: `outputs/anomaly_event_log.csv`.
- Chạy Autoencoder demo và sinh `outputs/autoencoder_metrics.json`.
- Vẽ 2 biểu đồ trong `figures/`.
- Test API logic bằng FastAPI TestClient và sinh `outputs/api_test_result.json`.
- Chuẩn bị report trả lời câu hỏi phân tích trong `REPORT.md`.

## Chạy lại toàn bộ bài

```bash
python run_all.py
```

Lệnh này sẽ chạy:

```bash
python src/download_data.py
python src/train_anomaly.py
python src/plot_results.py
python src/test_api_local.py
```

## Test API thực tế nếu cần chụp Swagger

```bash
uvicorn src.app:app --reload
```

Sau đó mở:

```text
http://127.0.0.1:8000/docs
```

Cần chụp:

- `GET /health` có `model_loaded: true`.
- `POST /detect-anomaly` có `model_output` và `event`.

## File nên nộp

- `REPORT.md`
- `outputs/iforest_metrics.json`
- `outputs/autoencoder_metrics.json`
- `outputs/anomaly_event_log.csv`
- `outputs/api_test_result.json`
- `figures/anomaly_detection_result.png`
- `figures/anomaly_score_over_time.png`
- Source code trong `src/`
- `requirements.txt`
- `README.md`
- `notebooks/01_anomaly_detection_event_intelligence.ipynb`
