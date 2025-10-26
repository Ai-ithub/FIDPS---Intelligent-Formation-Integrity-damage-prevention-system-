import json, logging, time, pandas as pd
from kafka import KafkaConsumer
import pandera as pa
from pandera import Column, DataFrameSchema, Check
import psycopg2
from psycopg2 import OperationalError
from pymongo import MongoClient, errors as mongo_errors
import uuid
from botocore.exceptions import ClientError
import boto3
from botocore.client import Config
import os

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Kafka
TOPIC = "raw-sensor-data"
BOOTSTRAP_SERVERS = ["kafka:9092"]

# PostgreSQL
PG_CONFIG = {
    "host": "postgres", "port": 5432, "dbname": "mlflowdb",
    "user": "mehrnoor", "password": "mehrnoor"
}

# MongoDB
MONGO_URI = "mongodb://mongo:27017"
MONGO_DB = "sensor_data"
MONGO_COLLECTION = "validation_failures"

# Pandera schema
schema = DataFrameSchema({
    "ECD": Column(float, Check.in_range(0, 1000), nullable=False),
    "RPM": Column(float, nullable=False),
    "timestamp": Column(pa.DateTime, nullable=False),
    "depth": Column(float, Check.ge(0), nullable=False)
})

# Retry helper
def retry(func, args, max_attempts=3, delay=1):
    for attempt in range(max_attempts):
        try:
            func(*args)
            return True
        except Exception as e:
            logging.warning(f"Attempt {attempt+1} failed: {e}")
            time.sleep(delay * (2 ** attempt))
    return False

# PostgreSQL connection
def connect_postgres():
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        conn.autocommit = True
        logging.info("Connected to PostgreSQL")
        ensure_table_exists(conn)
        return conn
    except OperationalError as e:
        logging.error(f"PostgreSQL connection failed: {e}")
        return None

# Ensure table exists
def ensure_table_exists(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS well_measurements (
                measurement_id UUID PRIMARY KEY,
                well_id TEXT,
                timestamp TIMESTAMP,
                depth FLOAT,
                rpm FLOAT,
                ecd FLOAT,
                is_valid BOOLEAN
            );
        """)
        logging.info("Ensured table 'well_measurements' exists.")

# MongoDB connection
def connect_mongo():
    try:
        client = MongoClient(MONGO_URI)
        logging.info("Connected to MongoDB")
        return client[MONGO_DB][MONGO_COLLECTION]
    except mongo_errors.PyMongoError as e:
        logging.error(f"MongoDB connection failed: {e}")
        return None

# PostgreSQL insert
def insert_postgres(conn, data):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO well_measurements (
                measurement_id, well_id, timestamp, depth, rpm, ecd, is_valid
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            str(uuid.uuid4()),
            data.get("well_id", "UNKNOWN"),
            data.get("timestamp"),
            data.get("depth"),
            data.get("RPM"),
            data.get("ECD"),
            True
        ))

# MongoDB insert
def insert_mongo(collection, data):
    document = {
        "original_data": data,
        "validation_error": data.get("validation_error", "Unknown"),
        "timestamp": data.get("timestamp")
    }
    collection.insert_one(document)

# Kafka consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS, api_version=(2, 1),
    auto_offset_reset="earliest",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    group_id="validator-router-group"
)

# S3 client
bucket_name = os.environ.get("S3_BUCKET", "real-time-data")
s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

# Ensure bucket exists
try:
    s3.head_bucket(Bucket=bucket_name)
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchBucket':
        s3.create_bucket(Bucket=bucket_name)
        logging.info(f"Bucket '{bucket_name}' created.")

# Upload sample file
if os.path.exists('./data/real_time_data.csv'):
    s3.upload_file('./data/real_time_data.csv', bucket_name, 'real_time_data.csv')

pg_conn = connect_postgres()
mongo_collection = connect_mongo()

# Processing loop

def preprocess_data(data):
    df = pd.DataFrame([data])

    # تبدیل timestamp به datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # تبدیل رشته به عدد در صورت نیاز
    for col in ["ECD", "RPM", "depth"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

# حلقه‌ی پردازش Kafka
for msg in consumer:
    data = msg.value
    logging.info(f"Received message: {data}")

    df = preprocess_data(data)

    try:
        schema.validate(df)
        data["is_valid"] = True
    except pa.errors.SchemaError as e:
        data["is_valid"] = False
        data["validation_error"] = str(e)
        logging.warning(f"Validation failed: {e.failure_cases}")

    if data["is_valid"]:
        if pg_conn:
            retry(insert_postgres, [pg_conn, data])
    else:
        if mongo_collection:
            retry(insert_mongo, [mongo_collection, data])

    logging.info(f"Processed message: is_valid={data['is_valid']}")