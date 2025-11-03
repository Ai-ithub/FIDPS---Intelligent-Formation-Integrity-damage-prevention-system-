#!/usr/bin/env python3
"""
FIDPS Kafka ML Service
This service consumes MWD/LWD data from Kafka topics, applies machine learning models
for anomaly detection, and publishes results back to Kafka.
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import signal
import sys
import os

# Kafka
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

# Data processing
import pandas as pd
import numpy as np

# Database connections
import psycopg2
from pymongo import MongoClient
import redis

# ML Models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.anomaly_detector import (
    EnsembleAnomalyDetector,
    IsolationForestAnomalyDetector,
    LSTMAnomalyDetector,
    AnomalyResult,
    AnomalyType,
    AnomalySeverity,
    ModelManager
)

# Configuration
import yaml

class KafkaMLService:
    """Kafka-based ML service for real-time anomaly detection"""
    
    def __init__(self, config_path: str = 'config/ml-config.yaml'):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Kafka clients
        self.consumer = None
        self.producer = None
        
        # Database connections
        self.postgres_pool = None  # Connection pool (preferred)
        self.postgres_conn = None  # Single connection (deprecated, for backward compatibility)
        self.mongo_client = None
        self.redis_client = None
        
        # ML Models
        self.models = {}
        self.model_last_trained = {}
        
        # Service state
        self.running = False
        self.threads = []
        
        # Data buffers
        self.data_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Metrics
        self.metrics = {
            'messages_processed': 0,
            'anomalies_detected': 0,
            'model_predictions': 0,
            'errors': 0,
            'last_processed': None
        }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Default configuration if file not found
            return {
                'kafka': {
                    'bootstrap_servers': 'localhost:9092',
                    'consumer_group_id': 'fidps-ml-service',
                    'input_topics': ['mwd-lwd-data', 'csv-mwd-lwd-data', 'witsml-data'],
                    'output_topics': {
                        'anomalies': 'ml-anomalies',
                        'predictions': 'ml-predictions',
                        'alerts': 'ml-alerts'
                    }
                },
                'databases': {
                    'postgres': {
                        'host': 'localhost',
                        'port': 5432,
                        'database': 'fidps_operational',
                        'username': 'fidps_user',
                        'password': 'fidps_password'
                    },
                    'mongodb': {
                        'url': 'mongodb://localhost:27017',
                        'database': 'fidps_anomalies'
                    },
                    'redis': {
                        'host': 'localhost',
                        'port': 6379,
                        'db': 0
                    }
                },
                'ml': {
                    'model_type': 'ensemble',
                    'retrain_interval_hours': 24,
                    'buffer_size': 1000,
                    'batch_size': 100
                }
            }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/ml-service.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def _connect_kafka(self) -> None:
        """Initialize Kafka consumer and producer"""
        try:
            # Consumer
            self.consumer = KafkaConsumer(
                *self.config['kafka']['input_topics'],
                bootstrap_servers=self.config['kafka']['bootstrap_servers'],
                group_id=self.config['kafka']['consumer_group_id'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                consumer_timeout_ms=1000
            )
            
            # Producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.config['kafka']['bootstrap_servers'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                acks='all',
                retries=3
            )
            
            self.logger.info("Kafka connections established")
            
        except Exception as e:
            self.logger.error(f"Error connecting to Kafka: {e}")
            raise
    
    def _connect_databases(self) -> None:
        """Initialize database connections"""
        try:
            # PostgreSQL with connection pooling
            from utils.db_pool import PostgreSQLPool
            pg_config = self.config['databases']['postgres']
            self.postgres_pool = PostgreSQLPool(
                host=pg_config['host'],
                port=pg_config['port'],
                database=pg_config['database'],
                user=pg_config['username'],
                password=pg_config['password'],
                min_size=int(os.getenv('DB_CONNECTION_POOL_MIN_SIZE', '2')),
                max_size=int(os.getenv('DB_CONNECTION_POOL_MAX_SIZE', '10'))
            )
            self.postgres_pool.initialize()
            # Keep a reference for backward compatibility (deprecated)
            self.postgres_conn = self.postgres_pool.get_connection()
            
            # MongoDB
            mongo_config = self.config['databases']['mongodb']
            self.mongo_client = MongoClient(mongo_config['url'])
            self.mongo_db = self.mongo_client[mongo_config['database']]
            
            # Redis
            redis_config = self.config['databases']['redis']
            self.redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                db=redis_config['db'],
                decode_responses=True
            )
            
            self.logger.info("Database connections established")
            
        except Exception as e:
            self.logger.error(f"Error connecting to databases: {e}")
            raise
    
    def _initialize_models(self) -> None:
        """Initialize ML models"""
        try:
            model_type = self.config['ml']['model_type']
            
            if model_type == 'ensemble':
                self.models['primary'] = EnsembleAnomalyDetector()
            elif model_type == 'isolation_forest':
                self.models['primary'] = IsolationForestAnomalyDetector()
            elif model_type == 'lstm':
                self.models['primary'] = LSTMAnomalyDetector()
            else:
                # Default to ensemble
                self.models['primary'] = EnsembleAnomalyDetector()
            
            # Try to load pre-trained models
            self._load_pretrained_models()
            
            self.logger.info(f"ML models initialized: {model_type}")
            
        except Exception as e:
            self.logger.error(f"Error initializing models: {e}")
            raise
    
    def _load_pretrained_models(self) -> None:
        """Load pre-trained models if available"""
        model_dir = 'models/saved'
        os.makedirs(model_dir, exist_ok=True)
        
        try:
            model_path = os.path.join(model_dir, 'primary_model.pkl')
            if os.path.exists(model_path):
                self.models['primary'] = ModelManager.load_model(model_path)
                self.logger.info("Pre-trained model loaded successfully")
            else:
                self.logger.info("No pre-trained model found, will train on first data batch")
        except Exception as e:
            self.logger.warning(f"Could not load pre-trained model: {e}")
    
    def _save_model(self, model_name: str) -> None:
        """Save trained model to disk"""
        try:
            model_dir = 'models/saved'
            os.makedirs(model_dir, exist_ok=True)
            model_path = os.path.join(model_dir, f'{model_name}_model.pkl')
            
            ModelManager.save_model(self.models[model_name], model_path)
            self.logger.info(f"Model {model_name} saved to {model_path}")
        except Exception as e:
            self.logger.error(f"Error saving model {model_name}: {e}")
    
    def _process_message(self, message) -> None:
        """Process a single Kafka message"""
        try:
            # Parse message
            data = message.value
            topic = message.topic
            
            # Add to buffer
            with self.buffer_lock:
                self.data_buffer.append({
                    'topic': topic,
                    'timestamp': datetime.now(),
                    'data': data
                })
                
                # Process batch if buffer is full
                if len(self.data_buffer) >= self.config['ml']['batch_size']:
                    self._process_batch()
            
            self.metrics['messages_processed'] += 1
            self.metrics['last_processed'] = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.metrics['errors'] += 1
    
    def _process_batch(self) -> None:
        """Process a batch of data for anomaly detection"""
        try:
            # Get current buffer
            current_batch = self.data_buffer.copy()
            self.data_buffer.clear()
            
            if not current_batch:
                return
            
            # Convert to DataFrame
            df_data = []
            for item in current_batch:
                row = item['data'].copy()
                row['source_topic'] = item['topic']
                row['processing_timestamp'] = item['timestamp']
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # Ensure required columns exist
            if 'timestamp' not in df.columns:
                df['timestamp'] = pd.to_datetime('now')
            if 'well_id' not in df.columns:
                df['well_id'] = 'unknown'
            
            # Check if model needs training/retraining
            self._check_model_training(df)
            
            # Apply anomaly detection
            if 'primary' in self.models and hasattr(self.models['primary'], 'is_fitted') and self.models['primary'].is_fitted:
                anomalies = self.models['primary'].predict(df)
                
                # Process detected anomalies
                for anomaly in anomalies:
                    self._handle_anomaly(anomaly)
                
                self.metrics['model_predictions'] += 1
                self.metrics['anomalies_detected'] += len(anomalies)
                
                self.logger.info(f"Processed batch of {len(df)} records, detected {len(anomalies)} anomalies")
            else:
                self.logger.warning("Model not trained yet, skipping prediction")
            
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            self.metrics['errors'] += 1
    
    def _check_model_training(self, df: pd.DataFrame) -> None:
        """Check if model needs training or retraining"""
        try:
            model_name = 'primary'
            retrain_interval = timedelta(hours=self.config['ml']['retrain_interval_hours'])
            
            # Check if model exists and is fitted
            if model_name not in self.models:
                return
            
            model = self.models[model_name]
            needs_training = False
            
            # Check if model has never been trained
            if not hasattr(model, 'is_fitted') or not model.is_fitted:
                needs_training = True
                reason = "initial training"
            
            # Check if model needs retraining based on time
            elif model_name in self.model_last_trained:
                last_trained = self.model_last_trained[model_name]
                if datetime.now() - last_trained > retrain_interval:
                    needs_training = True
                    reason = "scheduled retraining"
            
            if needs_training:
                self.logger.info(f"Starting model training: {reason}")
                self._train_model(model_name, df)
        
        except Exception as e:
            self.logger.error(f"Error checking model training: {e}")
    
    def _train_model(self, model_name: str, df: pd.DataFrame) -> None:
        """Train or retrain a model"""
        try:
            # Get additional training data from database if needed
            training_data = self._get_training_data(df)
            
            if len(training_data) < 100:  # Minimum data requirement
                self.logger.warning(f"Insufficient data for training ({len(training_data)} records)")
                return
            
            # Train model
            self.models[model_name].fit(training_data)
            self.model_last_trained[model_name] = datetime.now()
            
            # Save trained model
            self._save_model(model_name)
            
            self.logger.info(f"Model {model_name} trained successfully on {len(training_data)} records")
            
        except Exception as e:
            self.logger.error(f"Error training model {model_name}: {e}")
    
    def _get_training_data(self, current_df: pd.DataFrame) -> pd.DataFrame:
        """Get training data from current batch and historical data"""
        try:
            # Start with current data
            training_data = current_df.copy()
            
            # Get historical data from PostgreSQL using connection pool
            if hasattr(self, 'postgres_pool') and self.postgres_pool:
                conn = None
                try:
                    conn = self.postgres_pool.get_connection()
                    query = """
                    SELECT timestamp, well_id, depth, hook_load, weight_on_bit, torque, rpm, 
                           flow_rate, standpipe_pressure, mud_weight, temperature, gamma_ray, 
                           resistivity, neutron_porosity, bulk_density, caliper
                    FROM real_time_mwd_lwd_data 
                    WHERE timestamp >= NOW() - INTERVAL '7 days'
                    ORDER BY timestamp DESC
                    LIMIT 5000
                    """
                    
                    historical_df = pd.read_sql(query, conn)
                    if not historical_df.empty:
                        training_data = pd.concat([training_data, historical_df], ignore_index=True)
                finally:
                    if conn:
                        self.postgres_pool.put_connection(conn)
            elif hasattr(self, 'postgres_conn') and self.postgres_conn:
                # Fallback to old connection (backward compatibility)
                query = """
                SELECT timestamp, well_id, depth, hook_load, weight_on_bit, torque, rpm, 
                       flow_rate, standpipe_pressure, mud_weight, temperature, gamma_ray, 
                       resistivity, neutron_porosity, bulk_density, caliper
                FROM real_time_mwd_lwd_data 
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                ORDER BY timestamp DESC
                LIMIT 5000
                """
                
                historical_df = pd.read_sql(query, self.postgres_conn)
                if not historical_df.empty:
                    training_data = pd.concat([training_data, historical_df], ignore_index=True)
            
            # Remove duplicates and sort
            training_data = training_data.drop_duplicates().sort_values('timestamp')
            
            return training_data
            
        except Exception as e:
            self.logger.error(f"Error getting training data: {e}")
            return current_df
    
    def _handle_anomaly(self, anomaly: AnomalyResult) -> None:
        """Handle detected anomaly"""
        try:
            # Convert to dictionary for JSON serialization
            anomaly_dict = {
                'timestamp': anomaly.timestamp.isoformat(),
                'well_id': anomaly.well_id,
                'anomaly_type': anomaly.anomaly_type.value,
                'severity': anomaly.severity.value,
                'confidence': anomaly.confidence,
                'features': anomaly.features,
                'description': anomaly.description,
                'recommendations': anomaly.recommendations,
                'model_name': anomaly.model_name,
                'detection_timestamp': datetime.now().isoformat()
            }
            
            # Send to Kafka topics
            self._publish_anomaly(anomaly_dict)
            
            # Store in MongoDB
            self._store_anomaly_mongodb(anomaly_dict)
            
            # Cache in Redis for quick access
            self._cache_anomaly_redis(anomaly_dict)
            
            # Send alerts for high severity anomalies
            if anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
                self._send_alert(anomaly_dict)
            
            self.logger.info(f"Anomaly handled: {anomaly.anomaly_type.value} - {anomaly.severity.value}")
            
        except Exception as e:
            self.logger.error(f"Error handling anomaly: {e}")
    
    def _publish_anomaly(self, anomaly_dict: Dict[str, Any]) -> None:
        """Publish anomaly to Kafka topics"""
        try:
            # Publish to anomalies topic
            self.producer.send(
                self.config['kafka']['output_topics']['anomalies'],
                value=anomaly_dict
            )
            
            # Publish to predictions topic
            prediction_data = {
                'timestamp': anomaly_dict['timestamp'],
                'well_id': anomaly_dict['well_id'],
                'prediction_type': 'anomaly_detection',
                'result': anomaly_dict,
                'model_name': anomaly_dict['model_name']
            }
            
            self.producer.send(
                self.config['kafka']['output_topics']['predictions'],
                value=prediction_data
            )
            
            self.producer.flush()
            
        except Exception as e:
            self.logger.error(f"Error publishing anomaly to Kafka: {e}")
    
    def _store_anomaly_mongodb(self, anomaly_dict: Dict[str, Any]) -> None:
        """Store anomaly in MongoDB"""
        try:
            collection = self.mongo_db.anomaly_events
            collection.insert_one(anomaly_dict)
        except Exception as e:
            self.logger.error(f"Error storing anomaly in MongoDB: {e}")
    
    def _cache_anomaly_redis(self, anomaly_dict: Dict[str, Any]) -> None:
        """Cache anomaly in Redis"""
        try:
            key = f"anomaly:{anomaly_dict['well_id']}:{anomaly_dict['timestamp']}"
            self.redis_client.setex(key, 3600, json.dumps(anomaly_dict))  # 1 hour TTL
            
            # Update latest anomaly for well
            latest_key = f"latest_anomaly:{anomaly_dict['well_id']}"
            self.redis_client.setex(latest_key, 86400, json.dumps(anomaly_dict))  # 24 hour TTL
            
        except Exception as e:
            self.logger.error(f"Error caching anomaly in Redis: {e}")
    
    def _send_alert(self, anomaly_dict: Dict[str, Any]) -> None:
        """Send alert for high severity anomalies"""
        try:
            alert_data = {
                'alert_type': 'anomaly_detection',
                'severity': anomaly_dict['severity'],
                'timestamp': datetime.now().isoformat(),
                'well_id': anomaly_dict['well_id'],
                'message': f"High severity anomaly detected: {anomaly_dict['description']}",
                'anomaly_data': anomaly_dict
            }
            
            # Send to alerts topic
            self.producer.send(
                self.config['kafka']['output_topics']['alerts'],
                value=alert_data
            )
            
            self.producer.flush()
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
    
    def _metrics_reporter(self) -> None:
        """Background thread to report metrics"""
        while self.running:
            try:
                # Log metrics
                self.logger.info(f"Metrics: {self.metrics}")
                
                # Store metrics in Redis
                metrics_key = "ml_service_metrics"
                self.redis_client.setex(metrics_key, 300, json.dumps(self.metrics))  # 5 min TTL
                
                time.sleep(60)  # Report every minute
                
            except Exception as e:
                self.logger.error(f"Error reporting metrics: {e}")
                time.sleep(60)
    
    def start(self) -> None:
        """Start the ML service"""
        try:
            self.logger.info("Starting FIDPS ML Service...")
            
            # Initialize connections
            self._connect_kafka()
            self._connect_databases()
            self._initialize_models()
            
            # Set running flag
            self.running = True
            
            # Start metrics reporter thread
            metrics_thread = threading.Thread(target=self._metrics_reporter, daemon=True)
            metrics_thread.start()
            self.threads.append(metrics_thread)
            
            # Main processing loop
            self.logger.info("ML Service started, waiting for messages...")
            
            while self.running:
                try:
                    # Poll for messages
                    message_batch = self.consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            if not self.running:
                                break
                            self._process_message(message)
                    
                    # Process any remaining data in buffer periodically
                    with self.buffer_lock:
                        if len(self.data_buffer) > 0:
                            # Process partial batch if it's been waiting too long
                            oldest_item = min(self.data_buffer, key=lambda x: x['timestamp'])
                            if datetime.now() - oldest_item['timestamp'] > timedelta(minutes=5):
                                self._process_batch()
                
                except KeyboardInterrupt:
                    self.logger.info("Received interrupt signal")
                    break
                except Exception as e:
                    self.logger.error(f"Error in main loop: {e}")
                    time.sleep(5)  # Brief pause before retrying
            
        except Exception as e:
            self.logger.error(f"Error starting ML service: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the ML service"""
        self.logger.info("Stopping FIDPS ML Service...")
        
        # Set running flag to False
        self.running = False
        
        # Process any remaining data
        with self.buffer_lock:
            if self.data_buffer:
                self._process_batch()
        
        # Close connections
        if self.consumer:
            self.consumer.close()
        
        if self.producer:
            self.producer.close()
        
        if hasattr(self, 'postgres_pool') and self.postgres_pool:
            self.postgres_pool.close_all()
        elif hasattr(self, 'postgres_conn') and self.postgres_conn:
            self.postgres_conn.close()
        
        if self.mongo_client:
            self.mongo_client.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=5)
        
        self.logger.info("ML Service stopped")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal, stopping service...")
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start service
    try:
        service = KafkaMLService()
        service.start()
    except Exception as e:
        logging.error(f"Failed to start ML service: {e}")
        sys.exit(1)