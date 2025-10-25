FROM python:3.11-slim

# نصب پکیج‌های لازم
RUN pip install --no-cache-dir mlflow psycopg2-binary boto3

WORKDIR /app

# پورت سرور MLflow
EXPOSE 5000

# دستور پیش‌فرض
CMD ["mlflow", "server", "--host", "0.0.0.0"]
