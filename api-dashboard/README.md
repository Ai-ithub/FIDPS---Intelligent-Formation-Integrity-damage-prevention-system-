# FIDPS API Dashboard

The FIDPS API Dashboard is a real-time web-based monitoring and visualization system for the Formation Integrity Damage Prevention System (FIDPS). It provides comprehensive monitoring of drilling operations, anomaly detection, and system health through both REST APIs and WebSocket connections.

## Features

### Real-time Dashboard
- **Live Data Visualization**: Real-time charts for sensor data (WOB, RPM, ROP, torque, pressure, temperature)
- **Anomaly Monitoring**: Live anomaly alerts with severity levels and confidence scores
- **System Health**: Real-time system status and service health monitoring
- **Well Management**: Overview of all active wells with current status
- **Data Quality**: Real-time data validation results and quality metrics

### REST API Endpoints
- **Dashboard Metrics**: `/api/v1/dashboard/metrics` - Overall system metrics
- **Wells Management**: `/api/v1/wells` - List all wells and their status
- **Sensor Data**: `/api/v1/wells/{well_id}/data` - Real-time and historical sensor data
- **Anomaly Alerts**: `/api/v1/anomalies/active` - Active anomaly alerts
- **Data Validation**: `/api/v1/data/validation` - Data quality validation results
- **System Status**: `/api/v1/system/status` - Overall system health

### WebSocket Endpoints
- **Dashboard Stream**: `/ws/dashboard/{client_id}` - Real-time dashboard updates
- **Well Data Stream**: `/ws/well/{well_id}/{client_id}` - Well-specific data streaming
- **Anomaly Alerts**: `/ws/anomalies/{client_id}` - Real-time anomaly notifications
- **System Status**: `/ws/system-status/{client_id}` - Live system health updates

## Architecture

### Components
- **FastAPI Application**: High-performance async web framework
- **WebSocket Manager**: Real-time bidirectional communication
- **Data Sources**: PostgreSQL, MongoDB, Redis, Kafka
- **Frontend**: HTML5, JavaScript, Chart.js for visualization
- **Monitoring**: Prometheus metrics integration

### Data Flow
1. **Sensor Data**: Kafka → PostgreSQL/Redis → API/WebSocket → Dashboard
2. **Anomaly Alerts**: ML Service → MongoDB → API/WebSocket → Dashboard
3. **System Metrics**: Prometheus → API → Dashboard
4. **Data Validation**: Flink → PostgreSQL → API → Dashboard

## Installation

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Access to FIDPS infrastructure (Kafka, databases)

### Local Development

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   ```bash
   # Database Configuration
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=fidps_operational
   POSTGRES_USER=fidps_user
   POSTGRES_PASSWORD=fidps_password_2024
   
   MONGODB_HOST=localhost
   MONGODB_PORT=27017
   MONGODB_DB=fidps_anomalies
   MONGODB_USER=root
   MONGODB_PASSWORD=fidps_mongo_password_2024
   
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   
   # Kafka Configuration
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   KAFKA_SENSOR_DATA_TOPIC=sensor-data
   KAFKA_ANOMALY_ALERTS_TOPIC=anomaly-alerts
   KAFKA_SYSTEM_STATUS_TOPIC=system-status
   
   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   API_WORKERS=1
   API_RELOAD=true
   
   # Dashboard Configuration
   DASHBOARD_TITLE=FIDPS Dashboard
   DASHBOARD_REFRESH_INTERVAL=5000
   DASHBOARD_MAX_DATA_POINTS=100
   
   # WebSocket Configuration
   WEBSOCKET_HEARTBEAT_INTERVAL=30
   WEBSOCKET_MAX_CONNECTIONS=100
   
   # Monitoring
   PROMETHEUS_METRICS_PORT=9091
   LOG_LEVEL=INFO
   ```

3. **Run Application**:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

### Docker Deployment

1. **Build Image**:
   ```bash
   docker build -t fidps-api-dashboard .
   ```

2. **Run with Docker Compose**:
   ```bash
   docker-compose up api-dashboard
   ```

## Usage

### Web Dashboard

1. **Access Dashboard**: Open `http://localhost:8000` in your browser
2. **Navigation**: Use the sidebar to switch between different views:
   - **Overview**: System-wide metrics and alerts
   - **Wells**: Individual well monitoring and data
   - **Anomalies**: Anomaly alert management
   - **Data Quality**: Data validation results
   - **System**: System health and service status

### API Usage

#### Get Dashboard Metrics
```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/metrics"
```

#### Get Well Data
```bash
curl -X GET "http://localhost:8000/api/v1/wells/WELL001/data?limit=100"
```

#### Get Active Anomalies
```bash
curl -X GET "http://localhost:8000/api/v1/anomalies/active"
```

#### Acknowledge Anomaly
```bash
curl -X POST "http://localhost:8000/api/v1/anomalies/acknowledge" \
  -H "Content-Type: application/json" \
  -d '{"anomaly_id": "anomaly_123", "acknowledged_by": "operator1", "notes": "Investigated and resolved"}'
```

### WebSocket Usage

#### JavaScript Client Example
```javascript
// Connect to dashboard WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/dashboard/client123');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    switch(data.type) {
        case 'sensor_data':
            updateSensorCharts(data.data);
            break;
        case 'anomaly_alert':
            showAnomalyAlert(data.data);
            break;
        case 'system_status':
            updateSystemStatus(data.data);
            break;
    }
};

// Subscribe to specific well data
ws.send(JSON.stringify({
    action: 'subscribe',
    well_id: 'WELL001'
}));
```

## API Documentation

### Interactive API Docs
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Health Checks
- **Application Health**: `http://localhost:8000/health`
- **Prometheus Metrics**: `http://localhost:8000/metrics`

## Monitoring and Logging

### Metrics
The dashboard exposes Prometheus metrics on port 9091:
- Request counts and latencies
- WebSocket connection counts
- Database query performance
- Error rates and types

### Logging
Structured logging with configurable levels:
- **INFO**: General application flow
- **WARNING**: Potential issues
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging information

### Health Checks
- Database connectivity
- Kafka connectivity
- Redis connectivity
- Service dependencies

## Development

### Project Structure
```
api-dashboard/
├── app.py                 # Main FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── models/
│   ├── __init__.py
│   └── api_models.py     # Pydantic data models
├── routes/
│   ├── __init__.py
│   ├── api_routes.py     # REST API endpoints
│   └── websocket_routes.py # WebSocket endpoints
├── templates/
│   ├── __init__.py
│   └── dashboard.html    # Dashboard HTML template
├── static/
│   └── js/
│       └── dashboard.js  # Dashboard JavaScript
└── logs/                 # Application logs
```

### Code Quality
- **Formatting**: Black code formatter
- **Linting**: Flake8 for code quality
- **Import Sorting**: isort for import organization
- **Type Checking**: mypy for static type analysis

### Testing
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify database credentials and connectivity
   - Check if databases are running and accessible
   - Review connection pool settings

2. **WebSocket Connection Issues**:
   - Check firewall settings for WebSocket ports
   - Verify WebSocket endpoint URLs
   - Monitor connection limits and timeouts

3. **High Memory Usage**:
   - Adjust data retention settings
   - Optimize query limits and pagination
   - Monitor WebSocket connection counts

4. **Slow Dashboard Loading**:
   - Check database query performance
   - Verify Redis cache functionality
   - Monitor network latency

### Debug Mode
Enable debug mode for detailed logging:
```bash
export LOG_LEVEL=DEBUG
uvicorn app:app --reload --log-level debug
```

## Security

### Best Practices
- Environment variables for sensitive configuration
- Input validation and sanitization
- Rate limiting for API endpoints
- CORS configuration for web security
- Secure WebSocket connections

### Authentication
The dashboard currently operates in a trusted network environment. For production deployment, consider implementing:
- JWT token authentication
- Role-based access control
- API key management
- SSL/TLS encryption

## Performance

### Optimization
- Redis caching for frequently accessed data
- Connection pooling for databases
- Async/await for non-blocking operations
- Efficient WebSocket message handling
- Prometheus metrics for performance monitoring

### Scaling
- Horizontal scaling with multiple workers
- Load balancing for high availability
- Database read replicas for query performance
- CDN for static assets

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation for API changes
4. Use meaningful commit messages
5. Test thoroughly before submitting changes

## License

This project is part of the FIDPS (Formation Integrity Damage Prevention System) and is proprietary software.