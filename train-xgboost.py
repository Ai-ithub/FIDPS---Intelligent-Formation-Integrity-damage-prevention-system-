import os
import pandas as pd
import mlflow
import mlflow.xgboost
import optuna
from glob import glob
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score
from xgboost import XGBClassifier
import os
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"

import boto3
from botocore.exceptions import ClientError

# MinIO credentials and endpoint
minio_endpoint = "http://localhost:9000"
access_key = "minioadmin"
secret_key = "minioadmin"
bucket_name = "mlflow-artifacts"

# Create S3 client for MinIO
s3 = boto3.client(
    "s3",
    endpoint_url=minio_endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
)

# Check if bucket exists, create if not
try:
    s3.head_bucket(Bucket=bucket_name)
    print(f"✅ Bucket '{bucket_name}' already exists.")
except ClientError as e:
    if e.response['Error']['Code'] == '404':
        s3.create_bucket(Bucket=bucket_name)
        print(f"🪣 Bucket '{bucket_name}' created successfully.")
    else:
        print(f"❌ Error checking bucket: {e}")

# -----------------------------
# 🔧 MLflow Setup
# -----------------------------
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("XGBoost_Classification")

# -----------------------------
# 🧼 Data Preprocessing
# -----------------------------
def preprocess_data(df):
    df = df.copy()
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').astype('int64') // 1e9
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype('category').cat.codes
    return df.fillna(0)

def load_parquet_data(base_path, label, limit_folders=90):
    data_frames = []
    folders = os.listdir(base_path)[:limit_folders]
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        if os.path.isdir(folder_path):
            parquet_files = glob(os.path.join(folder_path, "*.parquet"))
            for file in parquet_files:
                df = pd.read_parquet(file)
                df['label'] = label
                data_frames.append(df)
    return pd.concat(data_frames, ignore_index=True)

# -----------------------------
# 🚀 Main Execution
# -----------------------------
def main():
    # Load and preprocess
    path_dt02 = "ml_training_dataD2"
    path_dt04 = "ml_training_dataD4"
    df_dt02 = load_parquet_data(path_dt02, label=0)
    df_dt04 = load_parquet_data(path_dt04, label=1)
    data = pd.concat([df_dt02, df_dt04], ignore_index=True)

    X = preprocess_data(data.drop(columns=['label']))
    y = data['label']
    X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # -----------------------------
    # 🔍 Hyperparameter Optimization
    # -----------------------------
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 1000),
            "max_depth": trial.suggest_int("max_depth", 3, 15),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "gamma": trial.suggest_float("gamma", 0, 5),
            "reg_alpha": trial.suggest_float("reg_alpha", 0, 5),
            "reg_lambda": trial.suggest_float("reg_lambda", 0, 5),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "random_state": 42,
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "n_jobs": -1,
            "tree_method": "hist",
            "device": "cuda",
        }
        model = XGBClassifier(**params)
        model.fit(X_train, y_train)
        preds = model.predict(X_valid)
        return accuracy_score(y_valid, preds)

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=45)
    best_params = study.best_trial.params
    best_params.update({"tree_method": "hist", "device": "cuda"})

    # -----------------------------
    # 🧪 Final Model Training + MLflow Logging
    # -----------------------------
    with mlflow.start_run():
        model = XGBClassifier(**best_params)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_valid)

        # Log parameters
        mlflow.log_params(best_params)

        # Log metrics
        mlflow.log_metric("accuracy", accuracy_score(y_valid, y_pred))
        mlflow.log_metric("f1_score", f1_score(y_valid, y_pred))
        mlflow.log_metric("rmse", mean_squared_error(y_valid, y_pred))
        mlflow.log_metric("r2_score", r2_score(y_valid, y_pred))

        # Log model to MinIO (S3)
        mlflow.xgboost.log_model(model, artifact_path="model")

if __name__ == "__main__":
    main()
