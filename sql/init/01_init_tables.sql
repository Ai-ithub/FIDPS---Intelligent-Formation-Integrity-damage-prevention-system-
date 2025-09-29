-- FIDPS Database Initialization Script
-- Creates tables for operational data storage

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS operational;
CREATE SCHEMA IF NOT EXISTS real_time;
CREATE SCHEMA IF NOT EXISTS historical;

-- Real-time operational data table
CREATE TABLE IF NOT EXISTS real_time.mwd_lwd_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    well_id VARCHAR(50) NOT NULL,
    depth_m DECIMAL(10,2),
    hook_load_klbs DECIMAL(8,2),
    weight_on_bit_klbs DECIMAL(8,2),
    torque_kft_lbs DECIMAL(8,2),
    rpm DECIMAL(6,2),
    flow_rate_gpm DECIMAL(8,2),
    standpipe_pressure_psi DECIMAL(8,2),
    mud_weight_ppg DECIMAL(6,2),
    temperature_degf DECIMAL(6,2),
    gamma_ray_api DECIMAL(8,2),
    resistivity_ohmm DECIMAL(10,4),
    neutron_porosity_percent DECIMAL(6,2),
    bulk_density_gcc DECIMAL(6,3),
    caliper_inches DECIMAL(6,3),
    bit_wear_percent DECIMAL(5,2),
    vibration_level DECIMAL(6,3),
    mud_motor_differential_pressure_psi DECIMAL(8,2),
    equivalent_circulating_density_ppg DECIMAL(6,2),
    annular_pressure_psi DECIMAL(8,2),
    formation_pressure_psi DECIMAL(8,2),
    pore_pressure_gradient_ppg DECIMAL(6,3),
    fracture_gradient_ppg DECIMAL(6,3),
    data_retention_tier VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create hypertable for time-series data
SELECT create_hypertable('real_time.mwd_lwd_data', 'timestamp', if_not_exists => TRUE);

-- Historical data table
CREATE TABLE IF NOT EXISTS historical.mwd_lwd_data (
    LIKE real_time.mwd_lwd_data INCLUDING ALL
);

-- Create hypertable for historical data
SELECT create_hypertable('historical.mwd_lwd_data', 'timestamp', if_not_exists => TRUE);

-- Equipment status table
CREATE TABLE IF NOT EXISTS operational.equipment_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    well_id VARCHAR(50) NOT NULL,
    equipment_type VARCHAR(50) NOT NULL,
    equipment_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('operational', 'warning', 'critical', 'offline')),
    health_score DECIMAL(5,2) CHECK (health_score >= 0 AND health_score <= 100),
    maintenance_due BOOLEAN DEFAULT FALSE,
    last_maintenance TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Alarm events table
CREATE TABLE IF NOT EXISTS operational.alarm_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    well_id VARCHAR(50) NOT NULL,
    alarm_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    parameter_name VARCHAR(100),
    parameter_value DECIMAL(15,4),
    threshold_value DECIMAL(15,4),
    description TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Damage assessment table
CREATE TABLE IF NOT EXISTS operational.damage_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    well_id VARCHAR(50) NOT NULL,
    damage_type VARCHAR(50) NOT NULL,
    severity_score DECIMAL(5,2) CHECK (severity_score >= 0 AND severity_score <= 10),
    affected_depth_start_m DECIMAL(10,2),
    affected_depth_end_m DECIMAL(10,2),
    predicted_impact TEXT,
    recommended_actions TEXT,
    confidence_level DECIMAL(5,2) CHECK (confidence_level >= 0 AND confidence_level <= 100),
    model_version VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Data quality metrics table
CREATE TABLE IF NOT EXISTS operational.data_quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    data_source VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    quality_score DECIMAL(5,2) CHECK (quality_score >= 0 AND quality_score <= 100),
    anomaly_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_mwd_lwd_timestamp ON real_time.mwd_lwd_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_mwd_lwd_well_id ON real_time.mwd_lwd_data (well_id);
CREATE INDEX IF NOT EXISTS idx_mwd_lwd_depth ON real_time.mwd_lwd_data (depth_m);

CREATE INDEX IF NOT EXISTS idx_historical_timestamp ON historical.mwd_lwd_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_historical_well_id ON historical.mwd_lwd_data (well_id);

CREATE INDEX IF NOT EXISTS idx_equipment_timestamp ON operational.equipment_status (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_equipment_well_id ON operational.equipment_status (well_id);
CREATE INDEX IF NOT EXISTS idx_equipment_type ON operational.equipment_status (equipment_type);

CREATE INDEX IF NOT EXISTS idx_alarm_timestamp ON operational.alarm_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alarm_well_id ON operational.alarm_events (well_id);
CREATE INDEX IF NOT EXISTS idx_alarm_severity ON operational.alarm_events (severity);
CREATE INDEX IF NOT EXISTS idx_alarm_resolved ON operational.alarm_events (resolved);

CREATE INDEX IF NOT EXISTS idx_damage_timestamp ON operational.damage_assessments (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_damage_well_id ON operational.damage_assessments (well_id);
CREATE INDEX IF NOT EXISTS idx_damage_type ON operational.damage_assessments (damage_type);

CREATE INDEX IF NOT EXISTS idx_quality_timestamp ON operational.data_quality_metrics (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_quality_source ON operational.data_quality_metrics (data_source);

-- Create retention policies for time-series data
-- Keep real-time data for 7 days
SELECT add_retention_policy('real_time.mwd_lwd_data', INTERVAL '7 days', if_not_exists => TRUE);

-- Keep historical data for 2 years
SELECT add_retention_policy('historical.mwd_lwd_data', INTERVAL '2 years', if_not_exists => TRUE);

-- Create continuous aggregates for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS real_time.mwd_lwd_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    well_id,
    AVG(depth_m) as avg_depth,
    AVG(hook_load_klbs) as avg_hook_load,
    AVG(weight_on_bit_klbs) as avg_wob,
    AVG(torque_kft_lbs) as avg_torque,
    AVG(rpm) as avg_rpm,
    AVG(flow_rate_gpm) as avg_flow_rate,
    AVG(standpipe_pressure_psi) as avg_standpipe_pressure,
    AVG(mud_weight_ppg) as avg_mud_weight,
    AVG(temperature_degf) as avg_temperature,
    COUNT(*) as record_count
FROM real_time.mwd_lwd_data
GROUP BY hour, well_id;

-- Grant permissions
GRANT USAGE ON SCHEMA real_time TO fidps_user;
GRANT USAGE ON SCHEMA historical TO fidps_user;
GRANT USAGE ON SCHEMA operational TO fidps_user;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA real_time TO fidps_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA historical TO fidps_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA operational TO fidps_user;

GRANT SELECT ON real_time.mwd_lwd_hourly TO fidps_user;

-- Insert sample data for testing
INSERT INTO real_time.mwd_lwd_data (
    timestamp, well_id, depth_m, hook_load_klbs, weight_on_bit_klbs, 
    torque_kft_lbs, rpm, flow_rate_gpm, standpipe_pressure_psi, 
    mud_weight_ppg, temperature_degf, data_retention_tier
) VALUES (
    NOW(), 'WELL-001', 1500.00, 250.5, 35.2, 12.8, 120.0, 450.0, 
    2800.0, 9.2, 185.5, 'Real-Time'
);

COMMIT;