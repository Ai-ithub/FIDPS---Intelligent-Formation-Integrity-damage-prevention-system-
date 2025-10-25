# validator-service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install pandas kafka-python pandera psycopg2-binary pymongo boto3 

CMD ["python", "validator-service.py"]
