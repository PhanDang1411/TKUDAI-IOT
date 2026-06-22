curl -X POST "http://127.0.0.1:8000/classify-image?top_k=5" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_images/classroom_object.jpg;type=image/jpeg"
