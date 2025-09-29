#!/bin/bash

# FIDPS Data Validation Service Startup Script
# This script starts the Flink data validation job

set -e

echo "Starting FIDPS Data Validation Service..."
echo "=========================================="

# Set environment variables
export FLINK_HOME=/opt/flink
export PYTHONPATH=/opt/flink/app:$PYTHONPATH
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Create necessary directories
mkdir -p /opt/flink/app/logs
mkdir -p /opt/flink/app/data/checkpoints
mkdir -p /opt/flink/app/data/savepoints

# Function to wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service_name to be ready at $host:$port..."
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            echo "✓ $service_name is ready"
            return 0
        fi
        
        attempt=$((attempt + 1))
        echo "Waiting for $service_name... (attempt $attempt/$max_attempts)"
        sleep 2
    done
    
    echo "✗ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Wait for required services
echo "Checking dependencies..."
wait_for_service kafka 9092 "Kafka"
wait_for_service postgres 5432 "PostgreSQL"
wait_for_service mongo 27017 "MongoDB"
wait_for_service redis 6379 "Redis"

# Start Flink cluster in standalone mode
echo "Starting Flink cluster..."
$FLINK_HOME/bin/start-cluster.sh

# Wait for Flink to be ready
wait_for_service localhost 8081 "Flink JobManager"

# Create Kafka topics if they don't exist
echo "Creating Kafka topics..."
topics=(
    "data-validation-results"
    "data-quality-metrics"
    "validation-alerts"
    "validation-errors"
)

for topic in "${topics[@]}"; do
    echo "Creating topic: $topic"
    kafka-topics.sh --create \
        --topic $topic \
        --bootstrap-server kafka:9092 \
        --partitions 3 \
        --replication-factor 1 \
        --if-not-exists \
        --config cleanup.policy=delete \
        --config retention.ms=604800000 || echo "Topic $topic might already exist"
done

# Submit the validation job
echo "Submitting FIDPS Data Validation job..."
$FLINK_HOME/bin/flink run \
    --python /opt/flink/app/flink-validation-job.py \
    --jobmanager localhost:8081 \
    --parallelism 4 \
    --detached

# Check job status
echo "Checking job status..."
sleep 10
$FLINK_HOME/bin/flink list --running

# Setup log monitoring
echo "Setting up log monitoring..."
tail -f /opt/flink/log/*.log &
LOG_PID=$!

# Health check function
health_check() {
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/overview)
    if [ "$response" = "200" ]; then
        return 0
    else
        return 1
    fi
}

# Monitor job health
echo "Starting health monitoring..."
while true; do
    if health_check; then
        echo "$(date): FIDPS Data Validation service is healthy"
    else
        echo "$(date): FIDPS Data Validation service health check failed"
        # Attempt to restart the job
        echo "Attempting to restart validation job..."
        $FLINK_HOME/bin/flink run \
            --python /opt/flink/app/flink-validation-job.py \
            --jobmanager localhost:8081 \
            --parallelism 4 \
            --detached || echo "Failed to restart job"
    fi
    sleep 30
done &
HEALTH_PID=$!

# Graceful shutdown handler
shutdown() {
    echo "Shutting down FIDPS Data Validation service..."
    
    # Stop health monitoring
    kill $HEALTH_PID 2>/dev/null || true
    
    # Stop log monitoring
    kill $LOG_PID 2>/dev/null || true
    
    # Cancel running jobs
    echo "Cancelling running jobs..."
    $FLINK_HOME/bin/flink list --running | grep -E '^[a-f0-9]{32}' | awk '{print $1}' | while read job_id; do
        echo "Cancelling job: $job_id"
        $FLINK_HOME/bin/flink cancel $job_id
    done
    
    # Stop Flink cluster
    echo "Stopping Flink cluster..."
    $FLINK_HOME/bin/stop-cluster.sh
    
    echo "FIDPS Data Validation service stopped"
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

echo "FIDPS Data Validation service is running"
echo "Web UI available at: http://localhost:8081"
echo "Metrics available at: http://localhost:9249/metrics"
echo "Press Ctrl+C to stop"

# Keep the script running
wait