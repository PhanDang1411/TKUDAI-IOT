# Kaggle setup (upload dataset + import notebook)

Muc tieu: ban chi can upload dataset UCI (`energydata_complete.csv`) va import notebook runner de chay full Lab 4.

## 1) Chuan bi file upload

- Nen ca thu muc `lab4_aiot_forecasting_predictive_analytics_uci_appliances/` thanh 1 file zip.
- Dataset UCI dat san file `energydata_complete.csv`.

## 2) Tren Kaggle Notebook

1. Tao notebook moi.
2. Add data:
   - Upload zip project.
   - Upload file dataset `energydata_complete.csv` (hoac them dataset UCI ban da co).
3. Import notebook:
   - `kaggle_lab4_runner.ipynb` (nam trong project zip).

## 3) Chay notebook

Notebook da co san cac cell:

- Giai nen project vao `/kaggle/working/lab4`.
- Tim `project_dir` tu `requirements.txt`.
- Chep `energydata_complete.csv` vao `data/` (neu tim thay trong `/kaggle/input`).
- Cai dependencies.
- Chay 1 lenh: `python run_all.py`.
- Kiem tra artifacts va dong goi `lab4_submission_ready.zip`.

## 4) Ket qua can co

- `models/forecast_model_bundle_v1.joblib`
- `outputs/forecast_metrics.json`
- `outputs/forecast_test_predictions.csv`
- `outputs/forecast_log.csv`
- `outputs/api_test_result.json`
- `figures/forecast_vs_actual.png`
- `figures/forecast_error_over_time.png`
- `figures/model_comparison_mae.png`

