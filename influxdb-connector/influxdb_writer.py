#!/usr/bin/env python3
"""
FIDPS InfluxDB Connector
Writes high-frequency time-series data to InfluxDB (FR-1.7)
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

try:
    from influxdb_client import InfluxDBClient, Point, WriteOptions
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    logging.warning("influxdb-client not installed. Run: pip install influxdb-client")
    InfluxDBClient = None

from kafka import KafkaConsumer
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfluxDBWriter:
    """Writer for time-series data to InfluxDB"""
    
    def __init__(
        self,
        url: str = None,
        token: str = None,
        org: str = None,
        bucket: str = None
    ):
        """
        Initialize InfluxDB writer
        
        Args:
            url: InfluxDB URL (default: from env or http://localhost:8086)
            token: InfluxDB token (default: from env)
            org: Organization name (default: from env or 'fidps')
            bucket: Bucket name (default: from env or 'fidps_metrics')
        """
        self.url = url or os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.token = token or os.getenv('INFLUXDB_TOKEN', '')
        self.org = org or os.getenv('INFLUXDB_ORG', 'fidps')
        self.bucket = bucket or os.getenv('INFLUXDB_BUCKET', 'fidps_metrics')
        
        self.client = None
        self.write_api = None
        
        if InfluxDBClient:
            try:
                self.client = InfluxDBClient(
                    url=self.url,
                    token=self.token,
                    org=self.org
                )
                self.write_api = self.client.write_api(write_options=WriteOptions(
                    batch_size=500,
                    flush_interval=10000,  # 10 seconds
                    jitter_interval=2000,
                    retry_interval=5000
                ))
                logger.info(f"Connected to InfluxDB at {self.url}")
            except Exception as e:
                logger.error(f"Failed to connect to InfluxDB: {e}")
    
    def write_sensor_data(
        self,
        well_id: str,
        timestamp: datetime,
        measurements: Dict[str, float],
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Write sensor data point to InfluxDB
        
        Args:
            well_id: Well identifier
            timestamp: Measurement timestamp
            measurements: Dictionary of measurement_name -> value
            tags: Optional tags (well_id, data_source, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.write_api:
            logger.error("InfluxDB client not initialized")
            return False
        
        try:
            # Create point with measurement
            point = Point("sensor_data") \
                .tag("well_id", well_id) \
                .time(timestamp)
            
            # Add tags
            if tags:
                for key, value in tags.items():
                    point = point.tag(key, str(value))
            
            # Add fields (measurements)
            for field, value in measurements.items():
                if isinstance(value, (int, float)):
                    point = point.field(field, float(value))
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, record=point)
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")
            return False
    
    def write_batch(
        self,
        data_points: List[Dict[str, Any]]
    ) -> int:
        """
        Write multiple data points in batch
        
        Args:
            data_points: List of dicts with keys: well_id, timestamp, measurements, tags
        
        Returns:
            Number of successfully written points
        """
        if not self.write_api:
            logger.error("InfluxDB client not initialized")
            return 0
        
        points = []
        
        try:
            for dp in data_points:
                well_id = dp['well_id']
                timestamp = dp['timestamp']
                measurements = dp.get('measurements', {})
                tags = dp.get('tags', {})
                
                point = Point("sensor_data") \
                    .tag("well_id", well_id) \
                    .time(timestamp)
                
                for key, value in tags.items():
                    point = point.tag(key, str(value))
                
                for field, value in measurements.items():
                    if isinstance(value, (int, float)):
                        point = point.field(field, float(value))
                
                points.append(point)
            
            # Write batch
            self.write_api.write(bucket=self.bucket, record=points)
            
            logger.info(f"Wrote {len(points)} data points to InfluxDB")
            return len(points)
            
        except Exception as e:
            logger.error(f"Error writing batch to InfluxDB: {e}")
            return 0
    
    def close(self):
        """Close InfluxDB connections"""
        if self.write_api:
            self.write_api.close()
        if self.client:
            self.client.close()
        logger.info("InfluxDB connections closed")

class KafkaToInfluxDBConnector:
    """Kafka consumer that writes data to InfluxDB"""
    
    def __init__(
        self,
        kafka_bootstrap_servers: str = None,
        kafka_topics: List[str] = None,
        influxdb_writer: InfluxDBWriter = None
    ):
        """
        Initialize Kafka-to-InfluxDB connector
        
        Args:
            kafka_bootstrap_servers: Kafka bootstrap servers
            kafka_topics: List of Kafka topics to consume
            influxdb_writer: InfluxDBWriter instance
        """
        self.kafka_bootstrap_servers = kafka_bootstrap_servers or \
            os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        
        self.kafka_topics = kafka_topics or [
            'mwd-lwd-data',
            'sensor-data',
            'csv-mwd-lwd-data'
        ]
        
        self.influxdb_writer = influxdb_writer or InfluxDBWriter()
        
        self.consumer = None
        self.running = False
        
        logger.info(f"Initialized Kafka-to-InfluxDB connector for topics: {self.kafka_topics}")
    
    def start(self):
        """Start consuming from Kafka and writing to InfluxDB"""
        try:
            self.consumer = KafkaConsumer(
                *self.kafka_topics,
                bootstrap_servers=self.kafka_bootstrap_servers,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                group_id='influxdb-connector',
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            self.running = True
            logger.info("Started Kafka-to-InfluxDB connector")
            
            for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    data = message.value
                    
                    # Extract data from Kafka message
                    well_id = data.get('well_id', 'unknown')
                    timestamp_str = data.get('timestamp', datetime.now().isoformat())
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Extract measurements (all numeric fields except metadata)
                    measurements = {}
                    exclude_fields = ['well_id', 'timestamp', 'damage_type', 'anomaly_type']
                    
                    for key, value in data.items():
                        if key not in exclude_fields and isinstance(value, (int, float)):
                            measurements[key] = value
                    
                    # Extract tags
                    tags = {
                        'data_source': message.topic,
                        'kafka_partition': message.partition,
                        'kafka_offset': message.offset
                    }
                    
                    # Add optional tags
                    if 'damage_type' in data:
                        tags['damage_type'] = data['damage_type']
                    if 'anomaly_type' in data:
                        tags['anomaly_type'] = data['anomaly_type']
                    
                    # Write to InfluxDB
                    self.influxdb_writer.write_sensor_data(
                        well_id=well_id,
                        timestamp=timestamp,
                        measurements=measurements,
                        tags=tags
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop the connector"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.influxdb_writer:
            self.influxdb_writer.close()
        logger.info("Kafka-to-InfluxDB connector stopped")

if __name__ == "__main__":
    # Example usage
    connector = KafkaToInfluxDBConnector()
    try:
        connector.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        connector.stop()

