import json
import time
import requests
from kafka import KafkaProducer



# Load config
with open('witsml-source.json') as f:
    config = json.load(f)

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092','broker1:9092,broker2:9092,broker3:9092'],api_version=(2,1,3),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

headers = {'Authorization': f"Bearer {config['token']}"}

def fetch_data():
    try:
        response = requests.get(config['endpoint'], headers=headers)
        if response.status_code == 200:
            return response.json()  # Replace with XML parsing if needed
        else:
            print(f"Failed to fetch: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    return []


def stream():
    while True:
        data = fetch_data()
        producer.send('json-witsml-topic', data)
        time.sleep(5)

if __name__ == "__main__":
    stream()
