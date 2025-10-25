# ========================================
# 1️⃣ Imports and Configuration
# ========================================
import os
import time
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import boto3
import mlflow
import mlflow.keras

from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping

# MLflow + MinIO environment setup
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("LSTM_MudViscosity_Prediction")

# Ensure S3 bucket exists
s3 = boto3.client("s3", endpoint_url="http://localhost:9000",
                  aws_access_key_id="minioadmin",
                  aws_secret_access_key="minioadmin")
bucket_name = "mlflow-artifacts"
try:
    s3.head_bucket(Bucket=bucket_name)
except:
    s3.create_bucket(Bucket=bucket_name)

# ========================================
# 2️⃣ Data Loading and Preprocessing
# ========================================
def load_all_parquet_files(root_dir, limit_folders=90):
    all_data = []
    folders = os.listdir(root_dir)[:limit_folders]
    for folder in folders:
        folder_path = os.path.join(root_dir, folder)
        if os.path.isdir(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith(".parquet"):
                    df = pd.read_parquet(os.path.join(folder_path, file))
                    all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

def create_sequences(data, seq_length):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        xs.append(data[i:i+seq_length])
        ys.append(data[i+seq_length])
    return np.array(xs), np.array(ys)

# Load and scale data
data = load_all_parquet_files("ml_training_data")
features = ['mud_viscosity', 'mud_density', 'pressure_diff']
scaler = MinMaxScaler()
scaled_data = scaler.fit_transform(data[features])

seq_length = 50
X_seq, y_seq = create_sequences(scaled_data, seq_length)
X = X_seq
y = y_seq[:, 0]  # target: mud_viscosity

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# ========================================
# 3️⃣ Model Building
# ========================================
model = Sequential([
    LSTM(64, input_shape=(seq_length, X.shape[2])),
    Dense(1)
])
model.compile(optimizer='adam', loss='mse')

# ========================================
# 4️⃣ Training and Evaluation
# ========================================
early_stop = EarlyStopping(patience=3, restore_best_weights=True)

with mlflow.start_run(run_name="LSTM_Model_Run"):
    # Log parameters
    mlflow.log_params({
        "sequence_length": seq_length,
        "lstm_units": 64,
        "optimizer": "adam",
        "loss": "mse",
        "epochs": 5,
        "batch_size": 32
    })

    # 🧩 Start timer before training
    start_time = time.time()

    # Train model
    model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_split=0.2,
        callbacks=[early_stop]
    )

    # 🧩 Compute duration
    duration = time.time() - start_time

    # Evaluate
    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    mlflow.log_metrics({
        "rmse": rmse,
        "r2_score": r2,
        "mae": mae,
        "train_time_sec": duration    # 🧩 optional: log training time to MLflow
    })

    # ✅ Log model with input example (simplified — safe without input_example)
    mlflow.keras.log_model(model, artifact_path="model")

    # ========================================
    # 5️⃣ Artifact Logging
    # ========================================
    artifact_dir = "artifacts"
    os.makedirs(artifact_dir, exist_ok=True)

    # Markdown summary
    version_tag = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_md = f"""# Model Performance Summary

**Version:** {version_tag}

| Metric            | Value     |
|-------------------|-----------|
| RMSE              | {rmse:.4f} |
| R² Score          | {r2:.4f}  |
| MAE               | {mae:.4f} |
| Train Time (sec)  | {duration:.2f} |
"""
    metrics_path = os.path.join(artifact_dir, "metrics.md")
    with open(metrics_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
    mlflow.log_artifact(metrics_path)

    # Model summary
    summary_path = os.path.join(artifact_dir, "model_summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        model.summary(print_fn=lambda x: f.write(x + "\n"))
    mlflow.log_artifact(summary_path)

    # Prediction plot
    plt.figure(figsize=(10, 4))
    plt.plot(y_test[:200], label='Actual')
    plt.plot(y_pred[:200], label='Predicted')
    plt.title("Actual vs Predicted Mud Viscosity")
    plt.xlabel("Time Steps")
    plt.ylabel("Scaled Value")
    plt.legend()
    plt.tight_layout()
    plot_path = os.path.join(artifact_dir, "prediction_plot.png")
    plt.savefig(plot_path)
    mlflow.log_artifact(plot_path)
