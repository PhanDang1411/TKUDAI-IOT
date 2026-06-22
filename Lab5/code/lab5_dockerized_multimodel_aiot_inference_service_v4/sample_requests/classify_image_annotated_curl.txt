curl -X POST "http://127.0.0.1:8000/classify-image-annotated?top_k=5" \
  -F "file=@sample_images/classroom_object.jpg;type=image/jpeg" \
  --output outputs/annotated_result.png
