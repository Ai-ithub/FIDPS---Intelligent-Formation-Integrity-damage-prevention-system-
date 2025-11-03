-- Additional tables needed for API dashboard
-- These tables match the models used in the API

-- Sensor data table (simplified view for API)
CREATE TABLE IF NOT EXISTS sensor_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    well_id VARCHAR(50) NOT NULL,
    depth DECIMAL(10,2),
    weight_on_bit DECIMAL(8,2),
    rotary_speed DECIMAL(6,2),
    torque DECIMAL(8,2),
    flow_rate DECIMAL(8,2),
    standpipe_pressure DECIMAL(8,2),
    hookload DECIMAL(8,2),
    block_height DECIMAL(8,2),
    gamma_ray DECIMAL(8,2),
    resistivity DECIMAL(10,4),
    neutron_porosity DECIMAL(6,2),
    bulk_density DECIMAL(6,3),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp ON sensor_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sensor_data_well_id ON sensor_data (well_id);

-- Anomaly alerts table
CREATE TABLE IF NOT EXISTS anomaly_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    well_id VARCHAR(50) NOT NULL,
    anomaly_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence DECIMAL(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    description TEXT,
    affected_parameters TEXT[],
    recommended_actions TEXT[],
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved')),
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp ON anomaly_alerts (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_well_id ON anomaly_alerts (well_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_severity ON anomaly_alerts (severity);
CREATE INDEX IF NOT EXISTS idx_anomaly_status ON anomaly_alerts (status);

-- Validation results table  
CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    well_id VARCHAR(50) NOT NULL,
    validation_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('passed', 'failed', 'warning')),
    errors TEXT[],
    warnings TEXT[],
    data_quality_score DECIMAL(5,4) CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_validation_timestamp ON validation_results (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_validation_well_id ON validation_results (well_id);
CREATE INDEX IF NOT EXISTS idx_validation_status ON validation_results (status);

-- System status table (for MongoDB but keeping a backup in PostgreSQL)
CREATE TABLE IF NOT EXISTS system_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('healthy', 'degraded', 'unhealthy', 'offline')),
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    disk_usage DECIMAL(5,2),
    uptime INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_system_status_timestamp ON system_status (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_status_service ON system_status (service);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON sensor_data TO fidps_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON anomaly_alerts TO fidps_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON validation_results TO fidps_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON system_status TO fidps_user;

-- Insert sample data for testing
INSERT INTO sensor_data (
    timestamp, well_id, depth, weight_on_bit, rotary_speed, 
    torque, flow_rate, standpipe_pressure, hookload
) VALUES 
    (NOW() - INTERVAL '5 minutes', 'WELL-001', 1500.00, 35.2, 120.0, 12.8, 450.0, 2800.0, 250.5),
    (NOW() - INTERVAL '10 minutes', 'WELL-001', 1495.00, 34.8, 118.0, 12.5, 448.0, 2785.0, 248.2),
    (NOW() - INTERVAL '15 minutes', 'WELL-002', 2100.00, 38.5, 125.0, 14.2, 465.0, 2950.0, 265.0);

INSERT INTO anomaly_alerts (
    timestamp, well_id, anomaly_type, severity, confidence, 
    description, affected_parameters, recommended_actions, status
) VALUES 
    (NOW() - INTERVAL '30 minutes', 'WELL-001', 'High Vibration', 'high', 0.92,
     'Abnormal vibration levels detected', ARRAY['vibration_level', 'torque'],
     ARRAY['Reduce RPM', 'Check bit condition'], 'active'),
    (NOW() - INTERVAL '1 hour', 'WELL-002', 'Pressure Anomaly', 'critical', 0.95,
     'Standpipe pressure exceeds normal range', ARRAY['standpipe_pressure'],
     ARRAY['Reduce flow rate', 'Check for blockage'], 'acknowledged');

INSERT INTO validation_results (
    timestamp, well_id, validation_type, status, errors, warnings, data_quality_score
) VALUES 
    (NOW() - INTERVAL '5 minutes', 'WELL-001', 'Sensor Check', 'passed', ARRAY[]::TEXT[], ARRAY[]::TEXT[], 0.98),
    (NOW() - INTERVAL '10 minutes', 'WELL-002', 'Data Completeness', 'warning', ARRAY[]::TEXT[], 
     ARRAY['Missing gamma ray data'], 0.85);

COMMIT;

