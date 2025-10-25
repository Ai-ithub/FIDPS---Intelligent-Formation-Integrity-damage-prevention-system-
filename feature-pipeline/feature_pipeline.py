import pandas as pd
import psycopg2
from psycopg2 import OperationalError
from sklearn.preprocessing import StandardScaler, OneHotEncoder, PolynomialFeatures
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import boto3
from botocore.client import Config
from datetime import datetime
import io
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# PostgreSQL connection
PG_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "dbname": "mlflowdb",
    "user": "mehrnoor",
    "password": "mehrnoor"
}

def load_data_from_postgres():
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        query = "SELECT * FROM well_measurements WHERE is_valid = TRUE;"
        df = pd.read_sql(query, conn)
        conn.close()
        logging.info(f"Loaded {len(df)} rows from PostgreSQL.")
        return df
    except OperationalError as e:
        logging.error(f"PostgreSQL connection failed: {e}")
        return pd.DataFrame()

def create_feature_pipeline(numeric_features, categorical_features):
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="mean")),
        ("scaler", StandardScaler())
    ])
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features)
        ]
    )
    interaction = Pipeline(steps=[
        ("poly", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False))
    ])
    full_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("interaction", interaction)
    ])
    return full_pipeline

def upload_to_s3(df_transformed, bucket_name="processed-data"):
    s3 = boto3.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )
    try:
        s3.head_bucket(Bucket=bucket_name)
    except Exception:
        s3.create_bucket(Bucket=bucket_name)
        logging.info(f"Created bucket '{bucket_name}'")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_key = f"features_v_{timestamp}.parquet"
    parquet_buffer = io.BytesIO()
    df_transformed.to_parquet(parquet_buffer, index=False)
    s3.put_object(Bucket=bucket_name, Key=file_key, Body=parquet_buffer.getvalue())
    logging.info(f"Uploaded {file_key} to S3 bucket '{bucket_name}'")

if __name__ == "__main__":
    df = load_data_from_postgres()
    if df.empty:
        logging.warning("No data found in PostgreSQL.")
        exit(0)

    numeric_features = ["ecd", "rpm", "depth"]
    categorical_features = ["well_id"]

    pipeline = create_feature_pipeline(numeric_features, categorical_features)
    transformed = pipeline.fit_transform(df)
    transformed_df = pd.DataFrame(
        transformed,
        columns=pipeline.named_steps["interaction"].named_steps["poly"].get_feature_names_out()
    )

    upload_to_s3(transformed_df)
