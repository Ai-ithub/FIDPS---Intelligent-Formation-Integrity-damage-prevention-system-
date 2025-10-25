FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir pandas scikit-learn psycopg2-binary boto3 pyarrow

CMD ["python", "feature_pipeline.py"]
