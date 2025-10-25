# csv_ingestor.py
import pandas as pd
from kafka import KafkaProducer
import json
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Kafka config
KAFKA_TOPIC = "historical-data"
file_path = "./historical_data.csv"
# Load CSV
def load_csv(file_path):
    logging.info(f"Loading CSV file: {file_path}")
    return pd.read_csv(file_path)

# Send rows to Kafka
def send_to_kafka(df):
    producer = KafkaProducer(bootstrap_servers=['kafka:9092'],    
                             api_version=(2, 1),
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    for idx, row in df.iterrows():
        message = row.to_dict()
        producer.send(KAFKA_TOPIC, value=message)
        if idx % 1000 == 0:
            logging.info(f"Sent {idx} records to Kafka")
        time.sleep(0.001)  # Optional throttle
    producer.flush()
    logging.info("All records sent successfully.")

if __name__ == "__main__":
    df = load_csv("./historical_data.csv")
    send_to_kafka(df)
