FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_DIR=/app/models \
    OUTPUT_DIR=/app/outputs \
    VISION_MODEL_PATH=/app/models/vision/squeezenet1.1-7.onnx \
    VISION_LABELS_PATH=/app/models/vision/imagenet_classes.txt

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY models/ models/
COPY sample_requests/ sample_requests/
COPY sample_images/ sample_images/
COPY scripts/ scripts/
COPY docs/ docs/
COPY optional_examples/ optional_examples/
COPY README.md RUN_GUIDE.md ./

RUN mkdir -p /app/outputs /app/models/vision

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
