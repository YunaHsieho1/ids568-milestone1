# Cloud Function Deployment

1. Copy the trained model into this folder before deploying:
   ```bash
   cp ../model.pkl .
   ```
2. Deploy (replace `REGION` and `FUNCTION_NAME`):
   ```bash
   gcloud functions deploy FUNCTION_NAME \
     --gen2 \
     --runtime=python311 \
     --region=REGION \
     --source=. \
     --entry-point=predict \
     --trigger-http \
     --allow-unauthenticated
   ```
3. Invoke:
   ```bash
   curl -X POST YOUR_FUNCTION_URL \
     -H "Content-Type: application/json" \
     -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
   ```
