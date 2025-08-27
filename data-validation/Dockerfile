# FIDPS Data Validation Service Dockerfile
FROM flink:1.18.0-scala_2.12-java11

# Set working directory
WORKDIR /opt/flink/app

# Install Python and pip
USER root
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Download and install Flink Kafka connector
RUN wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.18.0/flink-sql-connector-kafka-1.18.0.jar

# Download and install Flink JSON format
RUN wget -P /opt/flink/lib/ https://repo1.maven.org/maven2/org/apache/flink/flink-json/1.18.0/flink-json-1.18.0.jar

# Copy application code
COPY flink-validation-job.py .
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create directories for logs and data
RUN mkdir -p /opt/flink/app/logs /opt/flink/app/data

# Set environment variables
ENV PYTHONPATH=/opt/flink/app
ENV FLINK_HOME=/opt/flink
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# Configure Flink
COPY flink-conf.yaml /opt/flink/conf/flink-conf.yaml

# Set proper permissions
RUN chown -R flink:flink /opt/flink/app
RUN chmod +x scripts/*.sh

# Switch back to flink user
USER flink

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8081/overview || exit 1

# Expose ports
EXPOSE 8081 6123 6124 6125

# Default command
CMD ["/opt/flink/app/scripts/start-validation-job.sh"]