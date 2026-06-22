# Hướng dẫn chạy từng bước

1. Giải nén project.
2. Tạo môi trường ảo.
3. Cài requirements.
4. Chạy `python run_lab8_demo.py`. Nếu thấy `LOCAL_PIPELINE_TEST_PASS` thì nền đã chạy.
5. Chạy `uvicorn app:app --reload --host 0.0.0.0 --port 8000`.
6. Mở `http://127.0.0.1:8000/`.
7. Chọn kịch bản, bấm `Next step` hoặc `Start timeline`.
8. Chỉnh sensor bằng slider và bấm `Apply sensors`.
9. Bấm `So sánh 3 tầng` để thấy khác biệt giữa không có AI model, có AI model, và có LLM.
