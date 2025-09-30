# Kafka Stack with Monitoring and UI

This project sets up a modular Apache Kafka environment using Docker Compose. It includes multiple Kafka brokers, Zookeeper, Schema Registry, Kafka UI, a custom CSV producer, and monitoring tools (Prometheus + Grafana).

---

## 🚀 Services Overview

| Service           | Description                                                                 |
|------------------|-----------------------------------------------------------------------------|
| Zookeeper         | Coordinates Kafka brokers                                                   |
| Kafka (1 & 2)     | Distributed message brokers                                                 |
| Schema Registry   | Manages Avro schemas for Kafka messages                                     |
| Kafka UI          | Web interface for managing Kafka clusters                                   |
| Producer (CSV)    | Custom producer that sends CSV data to Kafka topics                         |
| Kafka Exporter    | Exposes Kafka metrics for Prometheus                                        |
| Prometheus        | Collects and stores metrics                                                 |
| Grafana           | Visualizes metrics from Prometheus                                          |

---

## 🛠️ Getting Started

### Prerequisites
- Docker
- Docker Compose

Kafka UI: http://localhost:8282

Schema Registry: http://localhost:8081

Prometheus: http://localhost:9090

Grafana: http://localhost:3000

Username: admin

Password: admin

# Kafka CSV Producer

This Python script reads real-time data from a DataFrame, filters it based on a retention tier, and sends each row as a message to a Kafka topic. It is designed to run continuously and integrate with a modular Kafka stack.

---

## 🚀 Features

- Filters data using a `retention_tier` column
- Sends filtered rows to a Kafka topic
- Logs each message sent
- Saves filtered data to a CSV file for backup or inspection

---

## 🛠️ Requirements

- Python 3.8+
- `kafka-python` library
- Kafka broker running at `kafka:9092`
- Environment variable `KAFKA_TOPIC` (optional)

---

## 📦 Installation

Install dependencies:
```bash
pip install kafka-python pandas

# Kafka Producer Container

This Docker image runs a Python script (`real-tim.py`) that reads real-time data, filters it, and sends messages to a Kafka topic. It is designed to integrate with a Kafka stack and run as a containerized service.

---

## 🛠️ Features

- Filters data using a `retention_tier` column
- Sends filtered rows to a Kafka topic
- Uses `kafka-python` for Kafka communication
- Containerized for easy deployment

---

## 📦 Requirements

- Docker
- Kafka broker running at `kafka:9092`
- Environment variable `KAFKA_TOPIC` (optional)

---

## ⚙️ Build the Image

```bash
docker build -t kafka-producer-csv .

# Prometheus Configuration for Kafka Exporter

This configuration enables Prometheus to scrape metrics from the Kafka Exporter service, which exposes Kafka broker metrics for monitoring and visualization.

---

## 📦 File Overview

- **prometheus.yml**: Main configuration file for Prometheus
- **Job Name**: `kafka-exporter`
- **Scrape Interval**: Every 15 seconds
- **Target**: `kafka-exporter:9308` (default port for Kafka Exporter)

---

## 🛠️ Setup Instructions

1. Ensure the Kafka Exporter container is running and accessible at `kafka-exporter:9308`.
2. Mount this configuration file into your Prometheus container:
   ```yaml
   volumes:
     - ./prometheus.yml:/etc/prometheus/prometheus.yml


 SensorReading Avro Schema

This Avro schema defines the structure of sensor data messages used in a Kafka-based data pipeline. It ensures consistent serialization and deserialization of sensor readings across producers and consumers.

---

## 📦 Schema Overview

- **Type**: Record
- **Name**: `SensorReading`
- **Namespace**: `com.example.sensors`
- **Purpose**: Captures timestamped temperature and humidity readings from IoT sensors

---