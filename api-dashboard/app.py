# FIDPS REST API and Dashboard
# FastAPI application for real-time monitoring and visualization

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
from datetime import datetime, timedelta
import os
import time
from contextlib import asynccontextmanager

# Database and messaging imports
import asyncpg
import motor.motor_asyncio
import aioredis
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
import threading
import queue

# Monitoring and metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry

# Initialize structured logging
try:
    from utils.logging_config import setup_logging, get_logger
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    # Fallback to basic logging if structured logging not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Metrics
registry = CollectorRegistry()
api_requests = Counter('fidps_api_requests_total', 'Total API requests', ['method', 'endpoint'], registry=registry)
api_response_time = Histogram('fidps_api_response_time_seconds', 'API response time', ['endpoint'], registry=registry)
active_connections = Gauge('fidps_websocket_connections', 'Active WebSocket connections', registry=registry)
anomalies_detected = Counter('fidps_anomalies_detected_total', 'Total anomalies detected', ['severity'], registry=registry)
data_points_processed = Counter('fidps_data_points_processed_total', 'Total data points processed', ['source'], registry=registry)

# Pydantic models
class DrillingSensorData(BaseModel):
    timestamp: datetime
    well_id: str
    depth: float
    weight_on_bit: float
    rotary_speed: float
    torque: float
    flow_rate: float
    standpipe_pressure: float
    hookload: float
    block_height: float
    gamma_ray: Optional[float] = None
    resistivity: Optional[float] = None
    neutron_porosity: Optional[float] = None
    bulk_density: Optional[float] = None

class AnomalyAlert(BaseModel):
    id: str
    timestamp: datetime
    well_id: str
    anomaly_type: str
    severity: str
    confidence: float
    description: str
    affected_parameters: List[str]
    recommended_actions: List[str]
    status: str = "active"

class ValidationResult(BaseModel):
    timestamp: datetime
    well_id: str
    validation_type: str
    status: str
    errors: List[str]
    warnings: List[str]
    data_quality_score: float

class SystemStatus(BaseModel):
    timestamp: datetime
    service: str
    status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: int

class DashboardMetrics(BaseModel):
    active_wells: int
    total_anomalies_today: int
    critical_alerts: int
    data_quality_score: float
    system_health: str
    last_updated: datetime

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # client_id -> [subscription_types]
        self.data_queue = queue.Queue()
        self._client_id_counter = 0  # Monotonically increasing counter to prevent ID collisions
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        if not client_id:
            # Use monotonically increasing counter to ensure unique IDs even after disconnections
            # This prevents collisions when clients disconnect and reconnect
            self._client_id_counter += 1
            client_id = f"client_{self._client_id_counter}"
        
        # Ensure client_id is unique (in case it was provided but already exists)
        while client_id in self.active_connections:
            self._client_id_counter += 1
            client_id = f"client_{self._client_id_counter}"
        
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = []
        active_connections.set(len(self.active_connections))
        logger.info(f"WebSocket connected ({client_id}). Total connections: {len(self.active_connections)}")
        return client_id
    
    def disconnect(self, websocket_or_client_id):
        # Handle both WebSocket and client_id for backward compatibility
        if isinstance(websocket_or_client_id, str):
            client_id = websocket_or_client_id
        else:
            # Find client_id by WebSocket
            client_id = None
            for cid, ws in self.active_connections.items():
                if ws == websocket_or_client_id:
                    client_id = cid
                    break
        
        if client_id and client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id and client_id in self.subscriptions:
            del self.subscriptions[client_id]
        active_connections.set(len(self.active_connections))
        if client_id:
            logger.info(f"WebSocket disconnected ({client_id}). Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket_or_client_id):
        if isinstance(websocket_or_client_id, str):
            client_id = websocket_or_client_id
            if client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to client {client_id}: {e}")
                    self.disconnect(client_id)
        else:
            websocket = websocket_or_client_id
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected.append(client_id)
        
        # Remove disconnected connections
        for client_id in disconnected:
            self.disconnect(client_id)
    
    def add_subscription(self, client_id: str, subscription_type: str):
        """Add a subscription for a client"""
        if client_id in self.subscriptions:
            if subscription_type not in self.subscriptions[client_id]:
                self.subscriptions[client_id].append(subscription_type)
                logger.info(f"Client {client_id} subscribed to {subscription_type}")
    
    def remove_subscription(self, client_id: str, subscription_type: str):
        """Remove a subscription for a client"""
        if client_id in self.subscriptions:
            if subscription_type in self.subscriptions[client_id]:
                self.subscriptions[client_id].remove(subscription_type)
                logger.info(f"Client {client_id} unsubscribed from {subscription_type}")
    
    async def broadcast_to_subscription(self, subscription_type: str, message: str):
        """Broadcast message only to clients subscribed to a specific type"""
        disconnected = []
        for client_id, subs in self.subscriptions.items():
            if subscription_type in subs and client_id in self.active_connections:
                try:
                    await self.active_connections[client_id].send_text(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to client {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Remove disconnected connections
        for client_id in disconnected:
            self.disconnect(client_id)

# Database connections
class DatabaseManager:
    def __init__(self):
        self.postgres_pool = None
        self.mongodb_client = None
        self.mongodb_db = None
        self.redis_client = None
    
    async def initialize(self):
        # Import retry utilities
        from utils.retry import retry_async, get_retry_config
        import asyncpg.exceptions as pg_exceptions
        import motor.errors as mongo_errors
        import redis.exceptions as redis_exceptions
        
        retry_config = get_retry_config()
        
        # PostgreSQL connection with retry
        async def init_postgres():
            self.postgres_pool = await asyncpg.create_pool(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', 5432)),
                database=os.getenv('POSTGRES_DB', 'fidps'),
                user=os.getenv('POSTGRES_USER', 'fidps_user'),
                password=os.getenv('POSTGRES_PASSWORD', 'fidps_password'),
                min_size=int(os.getenv('DB_CONNECTION_POOL_MIN_SIZE', '5')),
                max_size=int(os.getenv('DB_CONNECTION_POOL_MAX_SIZE', '20'))
            )
            logger.info("PostgreSQL connection pool created")
        
        try:
            await retry_async(
                init_postgres,
                config=retry_config,
                exception_types=(
                    pg_exceptions.PostgresConnectionError,
                    pg_exceptions.PostgresError,
                    ConnectionError,
                    OSError
                )
            )
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool after retries: {e}")
        
        # MongoDB connection with retry
        async def init_mongodb():
            mongodb_url = f"mongodb://{os.getenv('MONGODB_USER', 'fidps_user')}:{os.getenv('MONGODB_PASSWORD', 'fidps_password')}@{os.getenv('MONGODB_HOST', 'localhost')}:{os.getenv('MONGODB_PORT', 27017)}"
            self.mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
            self.mongodb_db = self.mongodb_client[os.getenv('MONGODB_DB', 'fidps')]
            # Test connection
            await self.mongodb_client.admin.command('ping')
            logger.info("MongoDB connection established")
        
        try:
            await retry_async(
                init_mongodb,
                config=retry_config,
                exception_types=(
                    mongo_errors.ServerSelectionTimeoutError,
                    ConnectionError,
                    OSError
                )
            )
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB after retries: {e}")
        
        # Redis connection with retry
        async def init_redis():
            redis_url = f"redis://:{os.getenv('REDIS_PASSWORD', 'redis_password')}@{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}"
            self.redis_client = await aioredis.from_url(redis_url)
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established")
        
        try:
            await retry_async(
                init_redis,
                config=retry_config,
                exception_types=(
                    redis_exceptions.ConnectionError,
                    redis_exceptions.TimeoutError,
                    ConnectionError,
                    OSError
                )
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis after retries: {e}")
    
    async def close(self):
        if self.postgres_pool:
            await self.postgres_pool.close()
        if self.mongodb_client:
            self.mongodb_client.close()
        if self.redis_client:
            await self.redis_client.close()

# Kafka consumer for real-time data
class KafkaDataConsumer:
    def __init__(self, connection_manager: ConnectionManager, db_manager: DatabaseManager):
        self.connection_manager = connection_manager
        self.db_manager = db_manager
        self.consumers = {}
        self.running = False
    
    def start_consumers(self):
        self.running = True
        
        # Start consumers for different topics
        topics = [
            'mwd-lwd-data',
            'csv-mwd-lwd-data', 
            'witsml-data',
            'data-validation-results',
            'ml-anomalies',
            'ml-predictions',
            'ml-alerts'
        ]
        
        for topic in topics:
            thread = threading.Thread(target=self._consume_topic, args=(topic,))
            thread.daemon = True
            thread.start()
            logger.info(f"Started consumer for topic: {topic}")
    
    def _consume_topic(self, topic: str):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                group_id=f'api-dashboard-{topic}',
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=False  # Manual commit for error handling
            )
            
            self.consumers[topic] = consumer
            dlq_topic = f"{topic}-dlq"  # Dead Letter Queue topic
            
            max_retries = 3
            retry_count = {}
            
            for message in consumer:
                if not self.running:
                    break
                
                message_id = f"{message.topic}_{message.partition}_{message.offset}"
                
                try:
                    data = message.value
                    data['topic'] = topic
                    data['timestamp'] = datetime.now().isoformat()
                    
                    # Update metrics
                    data_points_processed.labels(source=topic).inc()
                    
                    # Broadcast to WebSocket connections
                    asyncio.run_coroutine_threadsafe(
                        self.connection_manager.broadcast(json.dumps(data)),
                        asyncio.get_event_loop()
                    )
                    
                    # Store in cache for API endpoints
                    asyncio.run_coroutine_threadsafe(
                        self._cache_data(topic, data),
                        asyncio.get_event_loop()
                    )
                    
                    # Commit offset on success
                    consumer.commit()
                    
                    # Reset retry count on success
                    if message_id in retry_count:
                        del retry_count[message_id]
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error for message from {topic}: {e}")
                    # Send to DLQ immediately for JSON errors
                    self._send_to_dlq(dlq_topic, message, f"JSON decode error: {str(e)}")
                    consumer.commit()
                    
                except Exception as e:
                    logger.error(f"Error processing message from {topic}: {e}")
                    
                    # Retry logic
                    current_retries = retry_count.get(message_id, 0)
                    if current_retries < max_retries:
                        retry_count[message_id] = current_retries + 1
                        logger.info(f"Retrying message {message_id} (attempt {current_retries + 1}/{max_retries})")
                        # Don't commit - will retry on next poll
                        time.sleep(2 ** current_retries)  # Exponential backoff
                    else:
                        # Max retries reached - send to DLQ
                        logger.error(f"Max retries reached for message {message_id}, sending to DLQ")
                        self._send_to_dlq(dlq_topic, message, f"Processing error after {max_retries} retries: {str(e)}")
                        consumer.commit()
                        if message_id in retry_count:
                            del retry_count[message_id]
                    
        except Exception as e:
            logger.error(f"Error in Kafka consumer for {topic}: {e}")
    
    def _send_to_dlq(self, dlq_topic: str, original_message, error_reason: str):
        """Send failed message to Dead Letter Queue"""
        try:
            # Create DLQ producer if not exists
            if not hasattr(self, 'dlq_producer'):
                from kafka import KafkaProducer
                self.dlq_producer = KafkaProducer(
                    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                    value_serializer=lambda x: json.dumps(x).encode('utf-8')
                )
            
            # Send to DLQ with error metadata
            dlq_message = {
                'original_topic': original_message.topic,
                'original_partition': original_message.partition,
                'original_offset': original_message.offset,
                'original_timestamp': original_message.timestamp,
                'error_reason': error_reason,
                'failed_at': datetime.now().isoformat(),
                'original_value': original_message.value if hasattr(original_message.value, '__dict__') else str(original_message.value)
            }
            
            self.dlq_producer.send(dlq_topic, value=dlq_message)
            self.dlq_producer.flush()
            logger.info(f"Message sent to DLQ: {dlq_topic}")
            
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {e}")
    
    async def _cache_data(self, topic: str, data: dict):
        if self.db_manager.redis_client:
            try:
                # Cache latest data for each topic
                await self.db_manager.redis_client.setex(
                    f"latest_{topic}",
                    300,  # 5 minutes TTL
                    json.dumps(data)
                )
                
                # Cache recent data list (last 100 items)
                await self.db_manager.redis_client.lpush(f"recent_{topic}", json.dumps(data))
                await self.db_manager.redis_client.ltrim(f"recent_{topic}", 0, 99)
                
            except Exception as e:
                logger.error(f"Error caching data for {topic}: {e}")
    
    def stop_consumers(self):
        self.running = False
        for consumer in self.consumers.values():
            consumer.close()

# Global instances
connection_manager = ConnectionManager()
db_manager = DatabaseManager()
kafka_consumer = None

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting FIDPS API Dashboard...")
    await db_manager.initialize()
    
    global kafka_consumer
    kafka_consumer = KafkaDataConsumer(connection_manager, db_manager)
    kafka_consumer.start_consumers()
    
    yield
    
    # Shutdown
    logger.info("Shutting down FIDPS API Dashboard...")
    if kafka_consumer:
        kafka_consumer.stop_consumers()
    await db_manager.close()

# FastAPI app initialization
app = FastAPI(
    title="FIDPS API Dashboard",
    description="Formation Integrity Damage Prevention System - Real-time Monitoring API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
# Get allowed origins from environment variable, default to localhost for development
cors_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:80,http://localhost"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],  # Only allow specified origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Security - JWT authentication is handled in auth.py
# Import auth dependencies when needed: from auth import RequireAny, RequireAdmin, etc.

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Middleware for metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = datetime.now()
    
    response = await call_next(request)
    
    # Update metrics
    api_requests.labels(method=request.method, endpoint=request.url.path).inc()
    response_time = (datetime.now() - start_time).total_seconds()
    api_response_time.labels(endpoint=request.url.path).observe(response_time)
    
    return response

# Include routers
from routes.api_routes import router as api_router
from routes.websocket_routes import router as websocket_router

# Include auth router
try:
    from auth_routes import router as auth_router
    app.include_router(auth_router)
except ImportError:
    logger.warning("Auth routes not available - authentication disabled")

app.include_router(api_router)
app.include_router(websocket_router)

# Static files and templates
from fastapi.templating import Jinja2Templates
from fastapi import Request

templates = Jinja2Templates(directory="templates")

# Health check endpoints
@app.get("/health")
async def health_check():
    """Liveness probe - checks if service is running"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe - checks if service is ready to accept traffic"""
    import asyncpg.exceptions as pg_exceptions
    
    services_status = {}
    overall_healthy = True
    
    # Check PostgreSQL
    if db_manager.postgres_pool:
        try:
            async with db_manager.postgres_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            services_status["postgres"] = "connected"
        except Exception as e:
            services_status["postgres"] = f"error: {str(e)}"
            overall_healthy = False
    else:
        services_status["postgres"] = "disconnected"
        overall_healthy = False
    
    # Check MongoDB
    if db_manager.mongodb_client:
        try:
            await db_manager.mongodb_client.admin.command('ping')
            services_status["mongodb"] = "connected"
        except Exception as e:
            services_status["mongodb"] = f"error: {str(e)}"
            overall_healthy = False
    else:
        services_status["mongodb"] = "disconnected"
        overall_healthy = False
    
    # Check Redis
    if db_manager.redis_client:
        try:
            await db_manager.redis_client.ping()
            services_status["redis"] = "connected"
        except Exception as e:
            services_status["redis"] = f"error: {str(e)}"
            overall_healthy = False
    else:
        services_status["redis"] = "disconnected"
        overall_healthy = False
    
    # Check Kafka
    if kafka_consumer and kafka_consumer.running:
        services_status["kafka"] = "connected"
    else:
        services_status["kafka"] = "disconnected"
        overall_healthy = False
    
    status_code = 200 if overall_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall_healthy else "not_ready",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "services": services_status
        }
    )

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(registry), media_type="text/plain")

# Dashboard home page
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve the main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "message": "FIDPS Dashboard API", 
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/",
            "api_docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "websocket": "/ws/dashboard/{client_id}"
        }
    }

# WebSocket endpoint for real-time dashboard updates
@app.websocket("/ws/dashboard/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time data streaming (legacy - routes handled in websocket_routes)"""
    await connection_manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo back for connection testing
            await connection_manager.send_personal_message(f"Echo: {data}", client_id)
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        connection_manager.disconnect(client_id)

# API endpoint to get latest sensor data
@app.get("/api/v1/sensor-data/latest/{well_id}")
async def get_latest_sensor_data(well_id: str):
    """Get latest sensor data for a specific well"""
    try:
        if db_manager.redis_client:
            # Try to get from cache first
            cached_data = await db_manager.redis_client.get(f"latest_mwd-lwd-data")
            if cached_data:
                data = json.loads(cached_data)
                if data.get('well_id') == well_id:
                    return data
        
        # Fallback to database query
        if db_manager.postgres_pool:
            async with db_manager.postgres_pool.acquire() as conn:
                query = """
                    SELECT * FROM sensor_data 
                    WHERE well_id = $1 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                row = await conn.fetchrow(query, well_id)
                if row:
                    return dict(row)
        
        raise HTTPException(status_code=404, detail="No data found for well")
        
    except Exception as e:
        logger.error(f"Error getting latest sensor data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# API endpoint to get recent anomalies
@app.get("/api/v1/anomalies/recent")
async def get_recent_anomalies(limit: int = 50):
    """Get recent anomaly alerts"""
    try:
        if db_manager.redis_client:
            # Get from cache
            cached_anomalies = await db_manager.redis_client.lrange("recent_ml-anomalies", 0, limit-1)
            if cached_anomalies:
                return [json.loads(anomaly) for anomaly in cached_anomalies]
        
        # Fallback to database
        if db_manager.mongodb_db:
            cursor = db_manager.mongodb_db.anomalies.find().sort("timestamp", -1).limit(limit)
            anomalies = await cursor.to_list(length=limit)
            # Convert ObjectId to string for JSON serialization
            for anomaly in anomalies:
                anomaly['_id'] = str(anomaly['_id'])
            return anomalies
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting recent anomalies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# API endpoint to get dashboard metrics
@app.get("/api/v1/dashboard/metrics")
async def get_dashboard_metrics():
    """Get dashboard summary metrics"""
    try:
        metrics = {
            "active_wells": 0,
            "total_anomalies_today": 0,
            "critical_alerts": 0,
            "data_quality_score": 0.0,
            "system_health": "unknown",
            "last_updated": datetime.now().isoformat()
        }
        
        # Get metrics from database
        if db_manager.postgres_pool:
            async with db_manager.postgres_pool.acquire() as conn:
                # Count active wells
                active_wells = await conn.fetchval(
                    "SELECT COUNT(DISTINCT well_id) FROM sensor_data WHERE timestamp > NOW() - INTERVAL '1 hour'"
                )
                metrics["active_wells"] = active_wells or 0
        
        if db_manager.mongodb_db:
            # Count today's anomalies
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            total_anomalies = await db_manager.mongodb_db.anomalies.count_documents({
                "timestamp": {"$gte": today}
            })
            metrics["total_anomalies_today"] = total_anomalies
            
            # Count critical alerts
            critical_alerts = await db_manager.mongodb_db.anomalies.count_documents({
                "severity": "critical",
                "status": "active"
            })
            metrics["critical_alerts"] = critical_alerts
        
        # Determine system health
        if metrics["critical_alerts"] > 0:
            metrics["system_health"] = "critical"
        elif metrics["total_anomalies_today"] > 10:
            metrics["system_health"] = "warning"
        else:
            metrics["system_health"] = "healthy"
        
        # Mock data quality score (would be calculated from actual data quality metrics)
        metrics["data_quality_score"] = 0.95
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# API endpoint to get well list
@app.get("/api/v1/wells")
async def get_wells():
    """Get list of all wells"""
    try:
        if db_manager.postgres_pool:
            async with db_manager.postgres_pool.acquire() as conn:
                query = """
                    SELECT DISTINCT well_id, 
                           MAX(timestamp) as last_data_time,
                           COUNT(*) as data_points
                    FROM sensor_data 
                    GROUP BY well_id 
                    ORDER BY last_data_time DESC
                """
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting wells: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )