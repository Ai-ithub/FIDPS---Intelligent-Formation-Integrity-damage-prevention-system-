FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install kafka-python psycopg2-binary pymongo pandas  pandera sqlalchemy 

CMD ["python", "D3-csv_ingestor.py"]
