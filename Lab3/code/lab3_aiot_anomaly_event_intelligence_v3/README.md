# LAB 3: Anomaly Detection & Event Intelligence cho chuỗi thời gian IoT

## 1. Lab này khác Lab 2 ở đâu?

- **Lab 2 = Data Pipeline**: làm cho telemetry đủ sạch, đủ đúng schema, đủ feature để AI dùng được.
- **Lab 3 = Event Pipeline**: dùng dữ liệu đã sẵn sàng để phát hiện bất thường và biến kết quả model thành `event_type`, `severity`, `decision`, `anomaly_event_log.csv` và API `/detect-anomaly`.

Luồng chính của project:

```text
Clean telemetry
→ feature window
→ anomaly model
→ anomaly_score
→ threshold
→ event_type
→ severity
→ alert / safety decision
→ anomaly_event_log.csv
→ API /detect-anomaly
```

## 2. Dataset

Bài mẫu dùng dataset public từ Numenta Anomaly Benchmark (NAB):

- Dataset: `ambient_temperature_system_failure.csv`
- Nguồn: https://github.com/numenta/NAB/tree/master/data/realKnownCause
- File raw: https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/ambient_temperature_system_failure.csv
- Label windows: https://raw.githubusercontent.com/numenta/NAB/master/labels/combined_windows.json

Nếu máy không có Internet, project dùng file sample kèm theo trong `data/`.

## 3. Cấu trúc project

```text
lab3_aiot_anomaly_event_intelligence_v3/
├─ data/                         # dữ liệu public hoặc sample fallback
├─ notebooks/                    # notebook hướng dẫn từng bước
├─ src/
│  ├─ download_data.py            # tải dữ liệu public NAB
│  ├─ train_anomaly.py            # train/test Isolation Forest + autoencoder demo
│  ├─ app.py                      # FastAPI deploy model
│  ├─ test_api.py                 # test API sau khi deploy bằng uvicorn
│  ├─ test_api_local.py           # test API logic không cần mở port
│  ├─ plot_results.py             # vẽ biểu đồ kết quả
│  └─ utils.py                    # hàm dùng chung
├─ models/                       # model .joblib sau khi train
├─ outputs/                      # metrics, prediction, anomaly_event_log, api_test_result
├─ figures/                      # biểu đồ kết quả
├─ diagrams/                     # hình minh họa trong tài liệu
└─ requirements.txt
```

## 4. Cài môi trường

```bash
cd lab3_aiot_anomaly_event_intelligence_v3
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Cài thư viện:

```bash
pip install -r requirements.txt
```

## 5. Chạy bài mẫu bằng script

Tải dataset public hoặc dùng fallback sample:

```bash
python src/download_data.py
```

Train, test, đánh giá model:

```bash
python src/train_anomaly.py
```

Vẽ biểu đồ:

```bash
python src/plot_results.py
```

Kết quả cần thấy:

```text
models/anomaly_model_bundle_iforest_v2.joblib
models/isolation_forest_iforest_v1.joblib
models/mlp_autoencoder_demo.joblib
outputs/iforest_metrics.json
outputs/autoencoder_metrics.json
outputs/iforest_test_predictions.csv
outputs/anomaly_event_log.csv
figures/anomaly_detection_result.png
figures/anomaly_score_over_time.png
```

## 6. Chạy notebook

```bash
jupyter notebook notebooks/01_anomaly_detection_event_intelligence.ipynb
```

Chạy từng cell từ trên xuống. Sau mỗi phần, đọc kỹ mục **Cần quan sát gì** và **Cần phân tích gì**.

## 7. Deploy model bằng FastAPI

Sau khi train model xong:

```bash
uvicorn src.app:app --reload
```

Mở trình duyệt:

```text
http://127.0.0.1:8000/docs
```

Test API bằng script ở terminal khác:

```bash
python src/test_api.py
```

Nếu máy không mở được local port, test logic API bằng:

```bash
python src/test_api_local.py
```

## 8. Kiểm tra hoàn thành

Bạn hoàn thành bài mẫu khi có đủ:

- Notebook chạy hết không lỗi.
- Có `iforest_metrics.json` và `autoencoder_metrics.json`.
- Có `anomaly_event_log.csv`.
- Có `api_test_result.json`.
- Có ít nhất 2 biểu đồ trong `figures/`.
- API `/health` trả `model_loaded: true`.
- API `/detect-anomaly` trả `anomaly_score`, `threshold_used`, `is_anomaly`, `event_type`, `severity`, `decision`.
- Bạn giải thích được: **test model khác deploy model ở điểm nào**.
- Bạn giải thích được: **anomaly_score chưa phải decision cuối cùng**.
