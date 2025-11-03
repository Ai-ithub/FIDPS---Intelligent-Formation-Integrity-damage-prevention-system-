"""
API Configuration
"""
import os
from typing import Dict, Any

class APIConfig:
    """Configuration settings for FIDPS API Dashboard"""
    
    # Server Configuration
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Database Configuration
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "fidps_operational")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "fidps_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "fidps_password")
    
    # MongoDB Configuration
    MONGODB_HOST: str = os.getenv("MONGODB_HOST", "localhost")
    MONGODB_PORT: int = int(os.getenv("MONGODB_PORT", "27017"))
    MONGODB_DB: str = os.getenv("MONGODB_DB", "fidps_anomalies")
    MONGODB_USER: str = os.getenv("MONGODB_USER", "fidps_admin")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD", "fidps_mongo_password")
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "fidps_redis_password")
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_CONSUMER_GROUP: str = os.getenv("KAFKA_CONSUMER_GROUP", "api-dashboard")
    
    # Dashboard Settings
    DASHBOARD_TITLE: str = os.getenv("DASHBOARD_TITLE", "FIDPS Dashboard")
    REFRESH_INTERVAL: int = int(os.getenv("REFRESH_INTERVAL", "30"))
    MAX_CHART_POINTS: int = int(os.getenv("MAX_CHART_POINTS", "100"))
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    WS_MAX_CONNECTIONS: int = int(os.getenv("WS_MAX_CONNECTIONS", "100"))
    
    # Monitoring Configuration
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9091"))
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """Get database configuration dictionary"""
        return {
            "postgres": {
                "host": cls.POSTGRES_HOST,
                "port": cls.POSTGRES_PORT,
                "database": cls.POSTGRES_DB,
                "user": cls.POSTGRES_USER,
                "password": cls.POSTGRES_PASSWORD,
            },
            "mongodb": {
                "host": cls.MONGODB_HOST,
                "port": cls.MONGODB_PORT,
                "database": cls.MONGODB_DB,
                "user": cls.MONGODB_USER,
                "password": cls.MONGODB_PASSWORD,
            },
            "redis": {
                "host": cls.REDIS_HOST,
                "port": cls.REDIS_PORT,
                "password": cls.REDIS_PASSWORD,
            },
        }
    
    @classmethod
    def get_kafka_config(cls) -> Dict[str, Any]:
        """Get Kafka configuration dictionary"""
        return {
            "bootstrap_servers": cls.KAFKA_BOOTSTRAP_SERVERS,
            "consumer_group": cls.KAFKA_CONSUMER_GROUP,
        }

