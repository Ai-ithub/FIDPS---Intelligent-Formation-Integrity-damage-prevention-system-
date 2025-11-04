#!/usr/bin/env python3
"""
FIDPS Data Validation Pipeline using Apache Flink
This module implements real-time data quality checks for MWD/LWD data streams
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.datastream.connectors import FlinkKafkaConsumer, FlinkKafkaProducer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream.functions import MapFunction, FilterFunction, ProcessFunction
from pyflink.datastream.state import ValueStateDescriptor
from pyflink.common.time import Time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Data validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class DataQualityMetric(Enum):
    """Data quality metrics"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"

@dataclass
class ValidationRule:
    """Data validation rule definition"""
    rule_id: str
    field_name: str
    rule_type: str
    parameters: Dict
    severity: ValidationSeverity
    description: str

@dataclass
class ValidationResult:
    """Validation result for a data record"""
    record_id: str
    timestamp: datetime
    rule_id: str
    field_name: str
    severity: ValidationSeverity
    metric: DataQualityMetric
    is_valid: bool
    error_message: Optional[str]
    actual_value: Optional[str]
    expected_value: Optional[str]

class MWDLWDDataValidator:
    """MWD/LWD specific data validation rules"""
    
    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> List[ValidationRule]:
        """Initialize MWD/LWD specific validation rules"""
        return [
            # Range validation rules
            ValidationRule(
                rule_id="depth_range",
                field_name="depth_ft",
                rule_type="range",
                parameters={"min": 0, "max": 50000},
                severity=ValidationSeverity.ERROR,
                description="Depth must be between 0 and 50,000 feet"
            ),
            ValidationRule(
                rule_id="hook_load_range",
                field_name="hook_load_klbs",
                rule_type="range",
                parameters={"min": 0, "max": 2000},
                severity=ValidationSeverity.ERROR,
                description="Hook load must be between 0 and 2,000 klbs"
            ),
            ValidationRule(
                rule_id="wob_range",
                field_name="weight_on_bit_klbs",
                rule_type="range",
                parameters={"min": 0, "max": 100},
                severity=ValidationSeverity.ERROR,
                description="Weight on bit must be between 0 and 100 klbs"
            ),
            ValidationRule(
                rule_id="rpm_range",
                field_name="rpm",
                rule_type="range",
                parameters={"min": 0, "max": 300},
                severity=ValidationSeverity.ERROR,
                description="RPM must be between 0 and 300"
            ),
            ValidationRule(
                rule_id="flow_rate_range",
                field_name="flow_rate_gpm",
                rule_type="range",
                parameters={"min": 0, "max": 2000},
                severity=ValidationSeverity.ERROR,
                description="Flow rate must be between 0 and 2,000 GPM"
            ),
            ValidationRule(
                rule_id="temperature_range",
                field_name="temperature_degf",
                rule_type="range",
                parameters={"min": 32, "max": 500},
                severity=ValidationSeverity.WARNING,
                description="Temperature should be between 32°F and 500°F"
            ),
            
            # Null/Missing value checks
            ValidationRule(
                rule_id="timestamp_required",
                field_name="timestamp",
                rule_type="not_null",
                parameters={},
                severity=ValidationSeverity.CRITICAL,
                description="Timestamp is required"
            ),
            ValidationRule(
                rule_id="well_id_required",
                field_name="well_id",
                rule_type="not_null",
                parameters={},
                severity=ValidationSeverity.CRITICAL,
                description="Well ID is required"
            ),
            
            # Data consistency rules
            ValidationRule(
                rule_id="depth_monotonic",
                field_name="depth_ft",
                rule_type="monotonic_increasing",
                parameters={"tolerance": 10},
                severity=ValidationSeverity.WARNING,
                description="Depth should generally increase over time"
            ),
            
            # Statistical outlier detection (Z-score)
            ValidationRule(
                rule_id="zscore_weight_on_bit",
                field_name="weight_on_bit_klbs",
                rule_type="zscore",
                parameters={"threshold": 3.0},
                severity=ValidationSeverity.WARNING,
                description="Weight on bit Z-score outlier detection"
            ),
            ValidationRule(
                rule_id="zscore_flow_rate",
                field_name="flow_rate_gpm",
                rule_type="zscore",
                parameters={"threshold": 3.0},
                severity=ValidationSeverity.WARNING,
                description="Flow rate Z-score outlier detection"
            ),
            ValidationRule(
                rule_id="zscore_pressure",
                field_name="standpipe_pressure",
                rule_type="zscore",
                parameters={"threshold": 3.0},
                severity=ValidationSeverity.ERROR,
                description="Pressure Z-score outlier detection"
            ),
            
            # IQR (Interquartile Range) outlier detection
            ValidationRule(
                rule_id="iqr_torque",
                field_name="torque",
                rule_type="iqr",
                parameters={"factor": 1.5},
                severity=ValidationSeverity.WARNING,
                description="Torque IQR outlier detection"
            ),
            ValidationRule(
                rule_id="iqr_temperature",
                field_name="temperature_degf",
                rule_type="iqr",
                parameters={"factor": 1.5},
                severity=ValidationSeverity.WARNING,
                description="Temperature IQR outlier detection"
            ),
            
            # Physical consistency checks
            ValidationRule(
                rule_id="physical_pressure_depth",
                field_name="standpipe_pressure",
                rule_type="physical_consistency",
                parameters={"related_field": "depth_ft", "relation": "linear", "min_gradient": 0.4, "max_gradient": 0.6},
                severity=ValidationSeverity.ERROR,
                description="Pressure should correlate with depth"
            ),
            ValidationRule(
                rule_id="physical_wob_torque",
                field_name="torque",
                rule_type="physical_consistency",
                parameters={"related_field": "weight_on_bit_klbs", "relation": "correlation", "min_correlation": 0.5},
                severity=ValidationSeverity.WARNING,
                description="Torque should correlate with weight on bit"
            ),
            ValidationRule(
                rule_id="physical_flow_pressure",
                field_name="standpipe_pressure",
                rule_type="physical_consistency",
                parameters={"related_field": "flow_rate_gpm", "relation": "quadratic", "min_coefficient": 0.001},
                severity=ValidationSeverity.WARNING,
                description="Pressure should increase with flow rate"
            ),
            
            # Data freshness rules
            ValidationRule(
                rule_id="data_freshness",
                field_name="timestamp",
                rule_type="freshness",
                parameters={"max_age_minutes": 5},
                severity=ValidationSeverity.WARNING,
                description="Data should not be older than 5 minutes"
            ),
            
            # Format validation
            ValidationRule(
                rule_id="well_id_format",
                field_name="well_id",
                rule_type="regex",
                parameters={"pattern": r"^[A-Z0-9-]+$"},
                severity=ValidationSeverity.ERROR,
                description="Well ID must contain only uppercase letters, numbers, and hyphens"
            )
        ]
    
    def validate_record(self, record: Dict) -> List[ValidationResult]:
        """Validate a single MWD/LWD record against all rules"""
        results = []
        record_id = f"{record.get('well_id', 'unknown')}_{record.get('timestamp', 'unknown')}"
        
        for rule in self.validation_rules:
            result = self._apply_validation_rule(record, rule, record_id)
            if result:
                results.append(result)
        
        return results
    
    def _apply_validation_rule(self, record: Dict, rule: ValidationRule, record_id: str) -> Optional[ValidationResult]:
        """Apply a single validation rule to a record"""
        field_value = record.get(rule.field_name)
        
        try:
            if rule.rule_type == "range":
                return self._validate_range(record_id, rule, field_value)
            elif rule.rule_type == "not_null":
                return self._validate_not_null(record_id, rule, field_value)
            elif rule.rule_type == "regex":
                return self._validate_regex(record_id, rule, field_value)
            elif rule.rule_type == "freshness":
                return self._validate_freshness(record_id, rule, field_value)
            elif rule.rule_type == "monotonic_increasing":
                return self._validate_monotonic(record_id, rule, field_value, record)
            elif rule.rule_type == "zscore":
                return self._validate_zscore(record_id, rule, field_value, record)
            elif rule.rule_type == "iqr":
                return self._validate_iqr(record_id, rule, field_value, record)
            elif rule.rule_type == "physical_consistency":
                return self._validate_physical_consistency(record_id, rule, field_value, record)
            
        except Exception as e:
            logger.error(f"Error applying validation rule {rule.rule_id}: {str(e)}")
            return ValidationResult(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                severity=ValidationSeverity.ERROR,
                metric=DataQualityMetric.VALIDITY,
                is_valid=False,
                error_message=f"Validation rule execution failed: {str(e)}",
                actual_value=str(field_value),
                expected_value=None
            )
        
        return None
    
    def _validate_range(self, record_id: str, rule: ValidationRule, value) -> Optional[ValidationResult]:
        """Validate numeric range"""
        if value is None:
            return None
        
        try:
            numeric_value = float(value)
            min_val = rule.parameters.get("min")
            max_val = rule.parameters.get("max")
            
            is_valid = True
            error_msg = None
            
            if min_val is not None and numeric_value < min_val:
                is_valid = False
                error_msg = f"Value {numeric_value} is below minimum {min_val}"
            elif max_val is not None and numeric_value > max_val:
                is_valid = False
                error_msg = f"Value {numeric_value} is above maximum {max_val}"
            
            if not is_valid:
                return ValidationResult(
                    record_id=record_id,
                    timestamp=datetime.utcnow(),
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    severity=rule.severity,
                    metric=DataQualityMetric.VALIDITY,
                    is_valid=False,
                    error_message=error_msg,
                    actual_value=str(numeric_value),
                    expected_value=f"[{min_val}, {max_val}]"
                )
        except (ValueError, TypeError):
            return ValidationResult(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                severity=rule.severity,
                metric=DataQualityMetric.VALIDITY,
                is_valid=False,
                error_message=f"Invalid numeric value: {value}",
                actual_value=str(value),
                expected_value="numeric value"
            )
        
        return None
    
    def _validate_not_null(self, record_id: str, rule: ValidationRule, value) -> Optional[ValidationResult]:
        """Validate that field is not null or empty"""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return ValidationResult(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                severity=rule.severity,
                metric=DataQualityMetric.COMPLETENESS,
                is_valid=False,
                error_message="Field is null or empty",
                actual_value=str(value),
                expected_value="non-null value"
            )
        return None
    
    def _validate_regex(self, record_id: str, rule: ValidationRule, value) -> Optional[ValidationResult]:
        """Validate field against regex pattern"""
        if value is None:
            return None
        
        import re
        pattern = rule.parameters.get("pattern")
        if not re.match(pattern, str(value)):
            return ValidationResult(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                severity=rule.severity,
                metric=DataQualityMetric.VALIDITY,
                is_valid=False,
                error_message=f"Value does not match pattern {pattern}",
                actual_value=str(value),
                expected_value=f"pattern: {pattern}"
            )
        return None
    
    def _validate_freshness(self, record_id: str, rule: ValidationRule, value) -> Optional[ValidationResult]:
        """Validate data freshness"""
        if value is None:
            return None
        
        try:
            if isinstance(value, str):
                timestamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                timestamp = value
            
            max_age = timedelta(minutes=rule.parameters.get("max_age_minutes", 5))
            age = datetime.utcnow() - timestamp.replace(tzinfo=None)
            
            if age > max_age:
                return ValidationResult(
                    record_id=record_id,
                    timestamp=datetime.utcnow(),
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    severity=rule.severity,
                    metric=DataQualityMetric.TIMELINESS,
                    is_valid=False,
                    error_message=f"Data is {age.total_seconds()/60:.1f} minutes old",
                    actual_value=str(timestamp),
                    expected_value=f"within {max_age.total_seconds()/60} minutes"
                )
        except Exception as e:
            return ValidationResult(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                severity=rule.severity,
                metric=DataQualityMetric.VALIDITY,
                is_valid=False,
                error_message=f"Invalid timestamp format: {str(e)}",
                actual_value=str(value),
                expected_value="ISO format timestamp"
            )
        
        return None
    
    def _validate_monotonic(self, record_id: str, rule: ValidationRule, value, record: Dict) -> Optional[ValidationResult]:
        """Validate monotonic increasing values (requires state management in Flink)"""
        # This would be implemented using Flink's state management
        # For now, return None as this requires stateful processing
        return None
    
    def _validate_zscore(self, record_id: str, rule: ValidationRule, value, record: Dict) -> Optional[ValidationResult]:
        """Validate using Z-score outlier detection"""
        if value is None:
            return None
        
        try:
            numeric_value = float(value)
            threshold = rule.parameters.get("threshold", 3.0)
            
            # Calculate Z-score (requires historical data - simplified for now)
            # In production, this would use Flink's state to maintain historical statistics
            mean_value = self._get_historical_mean(rule.field_name)
            std_value = self._get_historical_std(rule.field_name)
            
            if mean_value is None or std_value is None or std_value == 0:
                return None  # Not enough data for Z-score calculation
            
            z_score = abs((numeric_value - mean_value) / std_value)
            
            if z_score > threshold:
                return ValidationResult(
                    record_id=record_id,
                    timestamp=datetime.utcnow(),
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    severity=rule.severity,
                    metric=DataQualityMetric.VALIDITY,
                    is_valid=False,
                    error_message=f"Z-score {z_score:.2f} exceeds threshold {threshold}",
                    actual_value=str(numeric_value),
                    expected_value=f"within {threshold} standard deviations"
                )
            
        except (ValueError, TypeError):
            return ValidationResult(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                severity=rule.severity,
                metric=DataQualityMetric.VALIDITY,
                is_valid=False,
                error_message=f"Invalid numeric value: {value}",
                actual_value=str(value),
                expected_value="numeric value"
            )
        
        return None
    
    def _validate_iqr(self, record_id: str, rule: ValidationRule, value, record: Dict) -> Optional[ValidationResult]:
        """Validate using Interquartile Range (IQR) outlier detection"""
        if value is None:
            return None
        
        try:
            numeric_value = float(value)
            factor = rule.parameters.get("factor", 1.5)
            
            # Calculate IQR bounds (requires historical data)
            q1 = self._get_historical_quartile(rule.field_name, 0.25)
            q3 = self._get_historical_quartile(rule.field_name, 0.75)
            
            if q1 is None or q3 is None:
                return None  # Not enough data for IQR calculation
            
            iqr = q3 - q1
            lower_bound = q1 - factor * iqr
            upper_bound = q3 + factor * iqr
            
            if numeric_value < lower_bound or numeric_value > upper_bound:
                return ValidationResult(
                    record_id=record_id,
                    timestamp=datetime.utcnow(),
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    severity=rule.severity,
                    metric=DataQualityMetric.VALIDITY,
                    is_valid=False,
                    error_message=f"Value {numeric_value:.2f} outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]",
                    actual_value=str(numeric_value),
                    expected_value=f"[{lower_bound:.2f}, {upper_bound:.2f}]"
                )
            
        except (ValueError, TypeError):
            return ValidationResult(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                severity=rule.severity,
                metric=DataQualityMetric.VALIDITY,
                is_valid=False,
                error_message=f"Invalid numeric value: {value}",
                actual_value=str(value),
                expected_value="numeric value"
            )
        
        return None
    
    def _validate_physical_consistency(
        self,
        record_id: str,
        rule: ValidationRule,
        value,
        record: Dict
    ) -> Optional[ValidationResult]:
        """Validate physical consistency between related fields (FR-201)"""
        if value is None:
            return None
        
        try:
            numeric_value = float(value)
            related_field = rule.parameters.get("related_field")
            relation = rule.parameters.get("relation", "linear")
            
            if related_field not in record:
                return None  # Related field not available
            
            related_value = float(record[related_field])
            
            is_valid = True
            error_msg = None
            
            if relation == "linear":
                # Linear relationship: y = a * x + b
                min_gradient = rule.parameters.get("min_gradient", 0.0)
                max_gradient = rule.parameters.get("max_gradient", float('inf'))
                
                if related_value > 0:
                    gradient = numeric_value / related_value
                    if gradient < min_gradient or gradient > max_gradient:
                        is_valid = False
                        error_msg = f"Gradient {gradient:.3f} outside acceptable range [{min_gradient}, {max_gradient}]"
            
            elif relation == "correlation":
                # Correlation check (requires historical data)
                min_correlation = rule.parameters.get("min_correlation", 0.5)
                correlation = self._get_historical_correlation(rule.field_name, related_field)
                
                if correlation is not None and abs(correlation) < min_correlation:
                    is_valid = False
                    error_msg = f"Correlation {correlation:.3f} below minimum {min_correlation}"
            
            elif relation == "quadratic":
                # Quadratic relationship: y = a * x^2 + b
                min_coefficient = rule.parameters.get("min_coefficient", 0.0)
                
                if related_value > 0:
                    coefficient = numeric_value / (related_value ** 2)
                    if coefficient < min_coefficient:
                        is_valid = False
                        error_msg = f"Coefficient {coefficient:.6f} below minimum {min_coefficient}"
            
            if not is_valid:
                return ValidationResult(
                    record_id=record_id,
                    timestamp=datetime.utcnow(),
                    rule_id=rule.rule_id,
                    field_name=rule.field_name,
                    severity=rule.severity,
                    metric=DataQualityMetric.CONSISTENCY,
                    is_valid=False,
                    error_message=error_msg,
                    actual_value=str(numeric_value),
                    expected_value=f"physically consistent with {related_field}"
                )
            
        except (ValueError, TypeError, KeyError) as e:
            return ValidationResult(
                record_id=record_id,
                timestamp=datetime.utcnow(),
                rule_id=rule.rule_id,
                field_name=rule.field_name,
                severity=rule.severity,
                metric=DataQualityMetric.VALIDITY,
                is_valid=False,
                error_message=f"Physical consistency check error: {str(e)}",
                actual_value=str(value),
                expected_value="physically consistent value"
            )
        
        return None
    
    def _get_historical_mean(self, field_name: str) -> Optional[float]:
        """Get historical mean value (simplified - in production uses Flink state)"""
        # This would use Flink's state management to maintain running statistics
        # For now, return None (indicating not enough data)
        return None
    
    def _get_historical_std(self, field_name: str) -> Optional[float]:
        """Get historical standard deviation (simplified)"""
        # This would use Flink's state management
        return None
    
    def _get_historical_quartile(self, field_name: str, quartile: float) -> Optional[float]:
        """Get historical quartile value (simplified)"""
        # This would use Flink's state management
        return None
    
    def _get_historical_correlation(self, field1: str, field2: str) -> Optional[float]:
        """Get historical correlation between two fields (simplified)"""
        # This would use Flink's state management
        return None

class DataValidationMapFunction(MapFunction):
    """Flink MapFunction for data validation"""
    
    def __init__(self):
        self.validator = MWDLWDDataValidator()
    
    def map(self, value: str) -> str:
        """Process each record through validation"""
        try:
            # Parse JSON record
            record = json.loads(value)
            
            # Validate record
            validation_results = self.validator.validate_record(record)
            
            # Create validation summary
            validation_summary = {
                "original_record": record,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "total_validations": len(validation_results),
                "errors": len([r for r in validation_results if r.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]),
                "warnings": len([r for r in validation_results if r.severity == ValidationSeverity.WARNING]),
                "validation_results": [
                    {
                        "rule_id": r.rule_id,
                        "field_name": r.field_name,
                        "severity": r.severity.value,
                        "metric": r.metric.value,
                        "is_valid": r.is_valid,
                        "error_message": r.error_message,
                        "actual_value": r.actual_value,
                        "expected_value": r.expected_value
                    } for r in validation_results
                ]
            }
            
            return json.dumps(validation_summary)
            
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            error_result = {
                "original_record": value,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "processing_error": str(e),
                "total_validations": 0,
                "errors": 1,
                "warnings": 0,
                "validation_results": []
            }
            return json.dumps(error_result)

class QualityMetricsAggregator(ProcessFunction):
    """Aggregate data quality metrics over time windows"""
    
    def __init__(self):
        self.metrics_state = None
    
    def open(self, runtime_context):
        """Initialize state"""
        metrics_descriptor = ValueStateDescriptor("quality_metrics", Types.STRING())
        self.metrics_state = runtime_context.get_state(metrics_descriptor)
    
    def process_element(self, value, ctx, out):
        """Process validation results and aggregate metrics"""
        try:
            validation_data = json.loads(value)
            
            # Get current metrics from state
            current_metrics = self.metrics_state.value()
            if current_metrics:
                metrics = json.loads(current_metrics)
            else:
                metrics = {
                    "total_records": 0,
                    "total_errors": 0,
                    "total_warnings": 0,
                    "error_rate": 0.0,
                    "warning_rate": 0.0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            # Update metrics
            metrics["total_records"] += 1
            metrics["total_errors"] += validation_data.get("errors", 0)
            metrics["total_warnings"] += validation_data.get("warnings", 0)
            metrics["error_rate"] = metrics["total_errors"] / metrics["total_records"]
            metrics["warning_rate"] = metrics["total_warnings"] / metrics["total_records"]
            metrics["last_updated"] = datetime.utcnow().isoformat()
            
            # Update state
            self.metrics_state.update(json.dumps(metrics))
            
            # Emit metrics periodically
            if metrics["total_records"] % 100 == 0:  # Every 100 records
                out.collect(json.dumps(metrics))
                
        except Exception as e:
            logger.error(f"Error aggregating metrics: {str(e)}")

def create_flink_validation_job():
    """Create and configure the Flink data validation job"""
    
    # Create execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(4)
    env.enable_checkpointing(60000)  # Checkpoint every minute
    
    # Kafka consumer properties
    kafka_props = {
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'fidps-validation-consumer',
        'auto.offset.reset': 'latest'
    }
    
    # Create Kafka consumer for input data
    kafka_consumer = FlinkKafkaConsumer(
        topics=['mwd-lwd-data', 'csv-mwd-lwd-data', 'witsml-data'],
        deserialization_schema=SimpleStringSchema(),
        properties=kafka_props
    )
    
    # Create data stream
    data_stream = env.add_source(kafka_consumer)
    
    # Apply validation
    validated_stream = data_stream.map(DataValidationMapFunction(), output_type=Types.STRING())
    
    # Aggregate quality metrics
    metrics_stream = validated_stream.process(QualityMetricsAggregator(), output_type=Types.STRING())
    
    # Kafka producer properties
    kafka_producer_props = {
        'bootstrap.servers': 'kafka:9092'
    }
    
    # Create Kafka producers for output
    validation_results_producer = FlinkKafkaProducer(
        topic='data-validation-results',
        serialization_schema=SimpleStringSchema(),
        producer_config=kafka_producer_props
    )
    
    quality_metrics_producer = FlinkKafkaProducer(
        topic='data-quality-metrics',
        serialization_schema=SimpleStringSchema(),
        producer_config=kafka_producer_props
    )
    
    # Send results to Kafka topics
    validated_stream.add_sink(validation_results_producer)
    metrics_stream.add_sink(quality_metrics_producer)
    
    # Execute the job
    env.execute("FIDPS Data Validation Pipeline")

if __name__ == "__main__":
    logger.info("Starting FIDPS Data Validation Pipeline")
    create_flink_validation_job()