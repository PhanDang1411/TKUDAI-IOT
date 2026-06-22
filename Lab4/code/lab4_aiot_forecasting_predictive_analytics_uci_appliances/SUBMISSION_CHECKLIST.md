# Submission checklist (Lab 4)

## Artifacts

- [ ] `models/forecast_model_bundle_v1.joblib`
- [ ] `outputs/forecast_metrics.json`
- [ ] `outputs/forecast_test_predictions.csv`
- [ ] `outputs/forecast_log.csv`
- [ ] `outputs/api_test_result.json`
- [ ] `figures/forecast_vs_actual.png`
- [ ] `figures/forecast_error_over_time.png`
- [ ] `figures/model_comparison_mae.png`

## API evidence

- [ ] Anh/Log `GET /health` co `model_loaded: true`
- [ ] Anh/Log `POST /forecast` co `predicted_value`, `risk_level`, `recommendation`, `safety_note`

## Report

- [ ] Tra loi cau hoi phan tich: forecasting vs anomaly, time split, MAE/RMSE/MAPE/bias, safety rule

