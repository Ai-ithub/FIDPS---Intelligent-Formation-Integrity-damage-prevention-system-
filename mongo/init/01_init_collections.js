// FIDPS MongoDB Initialization Script
// Creates collections and indexes for anomaly data and document storage

// Switch to FIDPS database
db = db.getSiblingDB('fidps_anomalies');

// Create collections
db.createCollection('anomaly_events', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'well_id', 'anomaly_type', 'severity'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Timestamp of the anomaly event'
                },
                well_id: {
                    bsonType: 'string',
                    description: 'Well identifier'
                },
                anomaly_type: {
                    bsonType: 'string',
                    enum: ['data_quality', 'equipment_failure', 'formation_damage', 'drilling_dysfunction', 'sensor_malfunction'],
                    description: 'Type of anomaly detected'
                },
                severity: {
                    bsonType: 'string',
                    enum: ['low', 'medium', 'high', 'critical'],
                    description: 'Severity level of the anomaly'
                },
                confidence_score: {
                    bsonType: 'double',
                    minimum: 0,
                    maximum: 1,
                    description: 'ML model confidence score'
                },
                affected_parameters: {
                    bsonType: 'array',
                    description: 'List of affected drilling parameters'
                },
                raw_data: {
                    bsonType: 'object',
                    description: 'Raw sensor data at time of anomaly'
                },
                model_output: {
                    bsonType: 'object',
                    description: 'ML model prediction details'
                },
                investigation_status: {
                    bsonType: 'string',
                    enum: ['pending', 'investigating', 'resolved', 'false_positive'],
                    description: 'Current investigation status'
                }
            }
        }
    }
});

db.createCollection('ml_model_logs', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'model_name', 'model_version', 'execution_time'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Model execution timestamp'
                },
                model_name: {
                    bsonType: 'string',
                    description: 'Name of the ML model'
                },
                model_version: {
                    bsonType: 'string',
                    description: 'Version of the ML model'
                },
                execution_time: {
                    bsonType: 'double',
                    description: 'Model execution time in milliseconds'
                },
                input_features: {
                    bsonType: 'object',
                    description: 'Input features used for prediction'
                },
                predictions: {
                    bsonType: 'object',
                    description: 'Model predictions and probabilities'
                },
                performance_metrics: {
                    bsonType: 'object',
                    description: 'Model performance metrics'
                }
            }
        }
    }
});

db.createCollection('data_quality_reports', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'data_source', 'quality_metrics'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Report generation timestamp'
                },
                data_source: {
                    bsonType: 'string',
                    description: 'Source of the data being evaluated'
                },
                quality_metrics: {
                    bsonType: 'object',
                    description: 'Data quality metrics and scores'
                },
                issues_detected: {
                    bsonType: 'array',
                    description: 'List of data quality issues found'
                },
                recommendations: {
                    bsonType: 'array',
                    description: 'Recommended actions to improve data quality'
                }
            }
        }
    }
});

db.createCollection('simulation_results', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'simulation_id', 'simulation_type', 'results'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Simulation execution timestamp'
                },
                simulation_id: {
                    bsonType: 'string',
                    description: 'Unique simulation identifier'
                },
                simulation_type: {
                    bsonType: 'string',
                    enum: ['formation_damage', 'drilling_optimization', 'equipment_failure', 'wellbore_stability'],
                    description: 'Type of simulation performed'
                },
                input_parameters: {
                    bsonType: 'object',
                    description: 'Input parameters for the simulation'
                },
                results: {
                    bsonType: 'object',
                    description: 'Simulation results and outputs'
                },
                execution_time: {
                    bsonType: 'double',
                    description: 'Simulation execution time in seconds'
                }
            }
        }
    }
});

db.createCollection('system_logs', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['timestamp', 'level', 'component', 'message'],
            properties: {
                timestamp: {
                    bsonType: 'date',
                    description: 'Log entry timestamp'
                },
                level: {
                    bsonType: 'string',
                    enum: ['DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'],
                    description: 'Log level'
                },
                component: {
                    bsonType: 'string',
                    description: 'System component that generated the log'
                },
                message: {
                    bsonType: 'string',
                    description: 'Log message'
                },
                metadata: {
                    bsonType: 'object',
                    description: 'Additional metadata for the log entry'
                }
            }
        }
    }
});

// Create indexes for better query performance

// Anomaly events indexes
db.anomaly_events.createIndex({ 'timestamp': -1 });
db.anomaly_events.createIndex({ 'well_id': 1, 'timestamp': -1 });
db.anomaly_events.createIndex({ 'anomaly_type': 1, 'timestamp': -1 });
db.anomaly_events.createIndex({ 'severity': 1, 'timestamp': -1 });
db.anomaly_events.createIndex({ 'investigation_status': 1 });
db.anomaly_events.createIndex({ 'confidence_score': -1 });

// ML model logs indexes
db.ml_model_logs.createIndex({ 'timestamp': -1 });
db.ml_model_logs.createIndex({ 'model_name': 1, 'timestamp': -1 });
db.ml_model_logs.createIndex({ 'model_version': 1, 'timestamp': -1 });
db.ml_model_logs.createIndex({ 'execution_time': -1 });

// Data quality reports indexes
db.data_quality_reports.createIndex({ 'timestamp': -1 });
db.data_quality_reports.createIndex({ 'data_source': 1, 'timestamp': -1 });

// Simulation results indexes
db.simulation_results.createIndex({ 'timestamp': -1 });
db.simulation_results.createIndex({ 'simulation_id': 1 });
db.simulation_results.createIndex({ 'simulation_type': 1, 'timestamp': -1 });
db.simulation_results.createIndex({ 'execution_time': -1 });

// System logs indexes
db.system_logs.createIndex({ 'timestamp': -1 });
db.system_logs.createIndex({ 'level': 1, 'timestamp': -1 });
db.system_logs.createIndex({ 'component': 1, 'timestamp': -1 });

// Create TTL indexes for automatic data cleanup
// Keep anomaly events for 1 year
db.anomaly_events.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 31536000 });

// Keep ML model logs for 6 months
db.ml_model_logs.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 15552000 });

// Keep data quality reports for 3 months
db.data_quality_reports.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 7776000 });

// Keep simulation results for 1 year
db.simulation_results.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 31536000 });

// Keep system logs for 30 days
db.system_logs.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 2592000 });

// Insert sample documents for testing
db.anomaly_events.insertOne({
    timestamp: new Date(),
    well_id: 'WELL-001',
    anomaly_type: 'equipment_failure',
    severity: 'high',
    confidence_score: 0.85,
    affected_parameters: ['hook_load', 'torque', 'vibration_level'],
    raw_data: {
        hook_load_klbs: 275.3,
        torque_kft_lbs: 18.5,
        vibration_level: 4.2,
        timestamp: new Date()
    },
    model_output: {
        predicted_failure_type: 'drill_string_failure',
        time_to_failure_hours: 2.5,
        recommended_actions: ['reduce_wob', 'check_drill_string']
    },
    investigation_status: 'pending',
    created_at: new Date()
});

db.ml_model_logs.insertOne({
    timestamp: new Date(),
    model_name: 'formation_damage_predictor',
    model_version: 'v1.2.0',
    execution_time: 125.5,
    input_features: {
        mud_weight_ppg: 9.2,
        flow_rate_gpm: 450.0,
        temperature_degf: 185.5,
        formation_pressure_psi: 3200.0
    },
    predictions: {
        damage_probability: 0.15,
        damage_type: 'skin_damage',
        severity_score: 2.3
    },
    performance_metrics: {
        accuracy: 0.92,
        precision: 0.88,
        recall: 0.90
    },
    created_at: new Date()
});

db.system_logs.insertOne({
    timestamp: new Date(),
    level: 'INFO',
    component: 'kafka_consumer',
    message: 'Successfully processed batch of MWD/LWD data',
    metadata: {
        batch_size: 1000,
        processing_time_ms: 45,
        topic: 'mwd_lwd_data',
        partition: 0,
        offset: 12345
    }
});

print('MongoDB collections and indexes created successfully!');
print('Sample documents inserted for testing.');