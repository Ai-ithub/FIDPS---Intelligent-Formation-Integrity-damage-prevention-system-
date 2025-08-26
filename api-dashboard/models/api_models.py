# FIDPS API Models
# Pydantic models for API request/response validation

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# Enums for validation
class SeverityLevel(str, Enum):
    critical = "critical"
    warning = "warning"
    info = "info"

class AlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"

class ValidationStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    warning = "warning"

class SystemHealth(str, Enum):
    healthy = "healthy"
    warning = "warning"
    degraded = "degraded"
    unhealthy = "unhealthy"
    unknown = "unknown"

# Core Data Models
class DrillingSensorData(BaseModel):
    """Model for drilling sensor data"""
    id: Optional[str] = None
    well_id: str = Field(..., description="Unique identifier for the well")
    timestamp: datetime = Field(..., description="Timestamp of the sensor reading")
    depth: float = Field(..., ge=0, description="Current drilling depth in meters")
    
    # MWD/LWD sensor readings
    weight_on_bit: Optional[float] = Field(None, ge=0, description="Weight on bit in klbs")
    rotary_speed: Optional[float] = Field(None, ge=0, description="Rotary speed in RPM")
    torque: Optional[float] = Field(None, ge=0, description="Torque in ft-lbs")
    flow_rate: Optional[float] = Field(None, ge=0, description="Flow rate in gpm")
    standpipe_pressure: Optional[float] = Field(None, ge=0, description="Standpipe pressure in psi")
    
    # Formation evaluation
    gamma_ray: Optional[float] = Field(None, ge=0, description="Gamma ray reading in API units")
    resistivity: Optional[float] = Field(None, ge=0, description="Resistivity in ohm-m")
    neutron_porosity: Optional[float] = Field(None, ge=0, le=100, description="Neutron porosity in %")
    bulk_density: Optional[float] = Field(None, ge=0, description="Bulk density in g/cm3")
    photoelectric_factor: Optional[float] = Field(None, ge=0, description="Photoelectric factor")
    
    # Drilling parameters
    rate_of_penetration: Optional[float] = Field(None, ge=0, description="Rate of penetration in ft/hr")
    mud_weight: Optional[float] = Field(None, ge=0, description="Mud weight in ppg")
    mud_temperature: Optional[float] = Field(None, description="Mud temperature in °F")
    
    # Pressure measurements
    pore_pressure: Optional[float] = Field(None, ge=0, description="Pore pressure in psi")
    fracture_pressure: Optional[float] = Field(None, ge=0, description="Fracture pressure in psi")
    equivalent_circulating_density: Optional[float] = Field(None, ge=0, description="ECD in ppg")
    
    # Additional metadata
    data_source: Optional[str] = Field(None, description="Source of the data (WITSML, CSV, etc.)")
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="Data quality score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "well_id": "WELL-001",
                "timestamp": "2024-01-15T10:30:00Z",
                "depth": 1500.5,
                "weight_on_bit": 25.5,
                "rotary_speed": 120.0,
                "torque": 8500.0,
                "flow_rate": 350.0,
                "standpipe_pressure": 2800.0,
                "gamma_ray": 75.2,
                "resistivity": 12.5,
                "neutron_porosity": 18.5,
                "bulk_density": 2.35,
                "rate_of_penetration": 45.2,
                "mud_weight": 10.5,
                "pore_pressure": 3200.0,
                "fracture_pressure": 4500.0,
                "data_source": "WITSML",
                "quality_score": 95.5
            }
        }

class AnomalyAlert(BaseModel):
    """Model for anomaly alerts"""
    id: Optional[str] = None
    well_id: str = Field(..., description="Well identifier where anomaly was detected")
    timestamp: datetime = Field(..., description="When the anomaly was detected")
    anomaly_type: str = Field(..., description="Type of anomaly detected")
    severity: SeverityLevel = Field(..., description="Severity level of the anomaly")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score of the detection")
    description: str = Field(..., description="Human-readable description of the anomaly")
    
    # Alert management
    status: AlertStatus = Field(AlertStatus.active, description="Current status of the alert")
    acknowledged_at: Optional[datetime] = Field(None, description="When the alert was acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Who acknowledged the alert")
    resolved_at: Optional[datetime] = Field(None, description="When the alert was resolved")
    
    # Technical details
    affected_parameters: List[str] = Field(default_factory=list, description="Parameters affected by the anomaly")
    threshold_values: Optional[Dict[str, float]] = Field(None, description="Threshold values that were exceeded")
    actual_values: Optional[Dict[str, float]] = Field(None, description="Actual values that triggered the alert")
    
    # ML model information
    model_name: Optional[str] = Field(None, description="Name of the ML model that detected the anomaly")
    model_version: Optional[str] = Field(None, description="Version of the ML model")
    
    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions to address the anomaly")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "well_id": "WELL-001",
                "timestamp": "2024-01-15T10:35:00Z",
                "anomaly_type": "pressure_anomaly",
                "severity": "warning",
                "confidence": 0.85,
                "description": "Abnormal pressure increase detected at 1500m depth",
                "status": "active",
                "affected_parameters": ["standpipe_pressure", "pore_pressure"],
                "threshold_values": {"standpipe_pressure": 3000.0},
                "actual_values": {"standpipe_pressure": 3250.0},
                "model_name": "pressure_anomaly_detector",
                "model_version": "v1.2.0",
                "recommended_actions": [
                    "Monitor pressure trends closely",
                    "Consider reducing mud weight",
                    "Prepare for potential kick"
                ]
            }
        }

class ValidationResult(BaseModel):
    """Model for data validation results"""
    id: Optional[str] = None
    well_id: str = Field(..., description="Well identifier")
    timestamp: datetime = Field(..., description="When validation was performed")
    data_source: str = Field(..., description="Source of the validated data")
    
    # Validation results
    status: ValidationStatus = Field(..., description="Overall validation status")
    data_quality_score: float = Field(..., ge=0, le=100, description="Overall data quality score")
    
    # Detailed validation metrics
    completeness_score: Optional[float] = Field(None, ge=0, le=100, description="Data completeness score")
    accuracy_score: Optional[float] = Field(None, ge=0, le=100, description="Data accuracy score")
    consistency_score: Optional[float] = Field(None, ge=0, le=100, description="Data consistency score")
    timeliness_score: Optional[float] = Field(None, ge=0, le=100, description="Data timeliness score")
    
    # Validation details
    total_records: int = Field(..., ge=0, description="Total number of records validated")
    valid_records: int = Field(..., ge=0, description="Number of valid records")
    invalid_records: int = Field(..., ge=0, description="Number of invalid records")
    
    # Issues found
    validation_errors: List[str] = Field(default_factory=list, description="List of validation errors")
    validation_warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    
    # Processing metadata
    processing_time_ms: Optional[float] = Field(None, ge=0, description="Processing time in milliseconds")
    validator_version: Optional[str] = Field(None, description="Version of the validation engine")
    
    @validator('valid_records')
    def valid_records_not_exceed_total(cls, v, values):
        if 'total_records' in values and v > values['total_records']:
            raise ValueError('valid_records cannot exceed total_records')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "well_id": "WELL-001",
                "timestamp": "2024-01-15T10:30:00Z",
                "data_source": "WITSML",
                "status": "passed",
                "data_quality_score": 92.5,
                "completeness_score": 95.0,
                "accuracy_score": 90.0,
                "consistency_score": 88.0,
                "timeliness_score": 97.0,
                "total_records": 1000,
                "valid_records": 925,
                "invalid_records": 75,
                "validation_errors": [
                    "Missing depth values in 25 records",
                    "Invalid pressure readings in 15 records"
                ],
                "validation_warnings": [
                    "Timestamp gaps detected in 35 records"
                ],
                "processing_time_ms": 150.5,
                "validator_version": "v2.1.0"
            }
        }

class SystemStatus(BaseModel):
    """Model for system status information"""
    id: Optional[str] = None
    service: str = Field(..., description="Name of the service")
    status: str = Field(..., description="Current status of the service")
    timestamp: datetime = Field(..., description="When the status was recorded")
    
    # Health metrics
    cpu_usage: Optional[float] = Field(None, ge=0, le=100, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, ge=0, le=100, description="Memory usage percentage")
    disk_usage: Optional[float] = Field(None, ge=0, le=100, description="Disk usage percentage")
    
    # Service-specific metrics
    uptime_seconds: Optional[int] = Field(None, ge=0, description="Service uptime in seconds")
    request_count: Optional[int] = Field(None, ge=0, description="Total request count")
    error_count: Optional[int] = Field(None, ge=0, description="Total error count")
    response_time_ms: Optional[float] = Field(None, ge=0, description="Average response time in ms")
    
    # Additional details
    version: Optional[str] = Field(None, description="Service version")
    environment: Optional[str] = Field(None, description="Environment (dev, staging, prod)")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional service-specific information")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "service": "kafka-ml-service",
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "disk_usage": 12.8,
                "uptime_seconds": 86400,
                "request_count": 15420,
                "error_count": 12,
                "response_time_ms": 125.5,
                "version": "v1.0.0",
                "environment": "production",
                "additional_info": {
                    "kafka_lag": 0,
                    "model_accuracy": 0.95,
                    "predictions_per_minute": 150
                }
            }
        }

class DashboardMetrics(BaseModel):
    """Model for dashboard overview metrics"""
    active_wells: int = Field(..., ge=0, description="Number of currently active wells")
    total_anomalies_today: int = Field(..., ge=0, description="Total anomalies detected today")
    critical_alerts: int = Field(..., ge=0, description="Number of active critical alerts")
    data_quality_score: float = Field(..., ge=0, le=100, description="Average data quality score")
    system_health: SystemHealth = Field(..., description="Overall system health status")
    last_updated: datetime = Field(..., description="When metrics were last updated")
    
    # Additional metrics
    total_data_points_today: Optional[int] = Field(None, ge=0, description="Total data points processed today")
    average_processing_time: Optional[float] = Field(None, ge=0, description="Average processing time in ms")
    ml_model_accuracy: Optional[float] = Field(None, ge=0, le=1, description="Current ML model accuracy")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "active_wells": 5,
                "total_anomalies_today": 12,
                "critical_alerts": 2,
                "data_quality_score": 94.5,
                "system_health": "healthy",
                "last_updated": "2024-01-15T10:30:00Z",
                "total_data_points_today": 125000,
                "average_processing_time": 85.2,
                "ml_model_accuracy": 0.92
            }
        }

# Request/Response Models
class WellSummaryRequest(BaseModel):
    """Request model for well summary"""
    well_id: str = Field(..., description="Well identifier")
    include_anomalies: bool = Field(True, description="Include anomaly statistics")
    include_validation: bool = Field(True, description="Include validation status")

class AnomalyAcknowledgeRequest(BaseModel):
    """Request model for acknowledging anomalies"""
    acknowledged_by: str = Field(..., description="User who is acknowledging the anomaly")
    notes: Optional[str] = Field(None, description="Optional notes about the acknowledgment")

class DataQueryRequest(BaseModel):
    """Request model for querying historical data"""
    well_id: Optional[str] = Field(None, description="Filter by well ID")
    start_time: Optional[datetime] = Field(None, description="Start time for data query")
    end_time: Optional[datetime] = Field(None, description="End time for data query")
    limit: int = Field(1000, ge=1, le=10000, description="Maximum number of records to return")
    parameters: Optional[List[str]] = Field(None, description="Specific parameters to include")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Response Models
class APIResponse(BaseModel):
    """Generic API response model"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Items per page")
    pages: int = Field(..., ge=1, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., ge=0, description="Service uptime in seconds")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Status of service dependencies")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }