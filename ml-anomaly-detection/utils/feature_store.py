#!/usr/bin/env python3
"""
FIDPS Real-Time Feature Store
FR-301: Real-Time Feature Store for ML model serving

This module implements a Redis-based feature store to maintain consistency
between features used in training and features used in online inference.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import redis
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class FeatureDefinition:
    """Definition of a feature"""
    name: str
    feature_type: str  # 'numeric', 'categorical', 'time_series', 'derived'
    data_type: str  # 'float', 'int', 'string', 'bool'
    description: str = ""
    default_value: Optional[Union[float, int, str, bool]] = None
    transformation: Optional[str] = None  # e.g., 'log', 'sqrt', 'normalize'
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class FeatureVector:
    """Feature vector for a single entity"""
    entity_id: str  # e.g., well_id
    timestamp: datetime
    features: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class RealTimeFeatureStore:
    """
    Real-Time Feature Store using Redis
    
    Maintains feature consistency between training and serving:
    - Stores feature definitions
    - Caches computed features
    - Provides feature versioning
    - Ensures feature consistency
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        namespace: str = "fidps_features",
        ttl_seconds: int = 3600
    ):
        self.redis = redis_client
        self.namespace = namespace
        self.ttl_seconds = ttl_seconds
        self.logger = logging.getLogger(__name__)
        
        # Feature registry (in-memory cache)
        self.feature_registry: Dict[str, FeatureDefinition] = {}
        
        # Load feature definitions from Redis
        self._load_feature_definitions()
    
    def _load_feature_definitions(self):
        """Load feature definitions from Redis"""
        try:
            definitions_key = f"{self.namespace}:definitions"
            definitions_data = self.redis.get(definitions_key)
            
            if definitions_data:
                definitions_dict = json.loads(definitions_data)
                for name, def_data in definitions_dict.items():
                    self.feature_registry[name] = FeatureDefinition(**def_data)
                
                self.logger.info(f"Loaded {len(self.feature_registry)} feature definitions")
        except Exception as e:
            self.logger.warning(f"Error loading feature definitions: {e}")
    
    def register_feature(self, feature_def: FeatureDefinition):
        """
        Register a feature definition
        
        Args:
            feature_def: Feature definition
        """
        self.feature_registry[feature_def.name] = feature_def
        
        # Persist to Redis
        try:
            definitions_key = f"{self.namespace}:definitions"
            definitions_data = self.redis.get(definitions_key)
            
            if definitions_data:
                definitions_dict = json.loads(definitions_data)
            else:
                definitions_dict = {}
            
            definitions_dict[feature_def.name] = asdict(feature_def)
            
            self.redis.set(
                definitions_key,
                json.dumps(definitions_dict),
                ex=None  # No expiration for definitions
            )
            
            self.logger.info(f"Registered feature: {feature_def.name}")
            
        except Exception as e:
            self.logger.error(f"Error registering feature {feature_def.name}: {e}")
    
    def get_feature(
        self,
        entity_id: str,
        feature_name: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[Any]:
        """
        Get a feature value for an entity
        
        Args:
            entity_id: Entity identifier (e.g., well_id)
            feature_name: Name of the feature
            timestamp: Timestamp (if None, gets latest)
        
        Returns:
            Feature value or None if not found
        """
        try:
            if timestamp:
                feature_key = f"{self.namespace}:feature:{entity_id}:{feature_name}:{timestamp.isoformat()}"
            else:
                feature_key = f"{self.namespace}:feature:{entity_id}:{feature_name}:latest"
            
            feature_data = self.redis.get(feature_key)
            
            if feature_data:
                feature_dict = json.loads(feature_data)
                return feature_dict.get('value')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting feature {feature_name} for {entity_id}: {e}")
            return None
    
    def set_feature(
        self,
        entity_id: str,
        feature_name: str,
        value: Any,
        timestamp: Optional[datetime] = None
    ):
        """
        Set a feature value for an entity
        
        Args:
            entity_id: Entity identifier
            feature_name: Name of the feature
            value: Feature value
            timestamp: Timestamp (if None, uses current time)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            # Validate feature exists
            if feature_name not in self.feature_registry:
                self.logger.warning(f"Feature {feature_name} not registered, registering with default definition")
                self.register_feature(FeatureDefinition(
                    name=feature_name,
                    feature_type='numeric',
                    data_type=type(value).__name__
                ))
            
            # Get feature definition
            feature_def = self.feature_registry[feature_name]
            
            # Validate value
            if not self._validate_feature_value(value, feature_def):
                self.logger.warning(f"Invalid value for feature {feature_name}: {value}")
                return
            
            # Store feature value
            feature_key = f"{self.namespace}:feature:{entity_id}:{feature_name}:{timestamp.isoformat()}"
            latest_key = f"{self.namespace}:feature:{entity_id}:{feature_name}:latest"
            
            feature_data = {
                'value': value,
                'timestamp': timestamp.isoformat(),
                'entity_id': entity_id,
                'feature_name': feature_name
            }
            
            # Store with timestamp
            self.redis.set(
                feature_key,
                json.dumps(feature_data),
                ex=self.ttl_seconds
            )
            
            # Update latest
            self.redis.set(
                latest_key,
                json.dumps(feature_data),
                ex=self.ttl_seconds
            )
            
            # Add to entity feature list
            entity_features_key = f"{self.namespace}:entity:{entity_id}:features"
            self.redis.sadd(entity_features_key, feature_name)
            self.redis.expire(entity_features_key, self.ttl_seconds)
            
        except Exception as e:
            self.logger.error(f"Error setting feature {feature_name} for {entity_id}: {e}")
    
    def get_feature_vector(
        self,
        entity_id: str,
        feature_names: List[str],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get a feature vector for an entity
        
        Args:
            entity_id: Entity identifier
            feature_names: List of feature names to retrieve
            timestamp: Timestamp (if None, gets latest)
        
        Returns:
            Dictionary of feature name -> value
        """
        feature_vector = {}
        
        for feature_name in feature_names:
            value = self.get_feature(entity_id, feature_name, timestamp)
            
            if value is None:
                # Use default value if available
                if feature_name in self.feature_registry:
                    feature_def = self.feature_registry[feature_name]
                    value = feature_def.default_value
            
            feature_vector[feature_name] = value
        
        return feature_vector
    
    def set_feature_vector(
        self,
        entity_id: str,
        features: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        """
        Set multiple features for an entity
        
        Args:
            entity_id: Entity identifier
            features: Dictionary of feature name -> value
            timestamp: Timestamp (if None, uses current time)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        for feature_name, value in features.items():
            self.set_feature(entity_id, feature_name, value, timestamp)
    
    def compute_features(
        self,
        raw_data: Dict[str, Any],
        entity_id: str,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Compute features from raw data
        
        Args:
            raw_data: Raw sensor/operational data
            entity_id: Entity identifier
            timestamp: Timestamp
        
        Returns:
            Dictionary of computed features
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        computed_features = {}
        
        # Basic features (direct mapping)
        basic_features = [
            'weight_on_bit', 'rotary_speed', 'flow_rate', 'mud_weight',
            'standpipe_pressure', 'torque', 'depth', 'temperature'
        ]
        
        for feature_name in basic_features:
            if feature_name in raw_data:
                computed_features[feature_name] = raw_data[feature_name]
        
        # Derived features
        computed_features.update(self._compute_derived_features(raw_data))
        
        # Time-based features
        computed_features.update(self._compute_time_features(raw_data, timestamp))
        
        # Statistical features (if historical data available)
        computed_features.update(self._compute_statistical_features(entity_id, raw_data))
        
        # Store computed features
        self.set_feature_vector(entity_id, computed_features, timestamp)
        
        return computed_features
    
    def _compute_derived_features(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute derived features from raw data"""
        derived = {}
        
        # Hydraulic horsepower
        if 'flow_rate' in raw_data and 'standpipe_pressure' in raw_data:
            flow_gpm = raw_data['flow_rate']
            pressure_psi = raw_data.get('standpipe_pressure', 0)
            hhp = (flow_gpm * pressure_psi) / 1714
            derived['hydraulic_horsepower'] = hhp
        
        # Specific energy
        if 'weight_on_bit' in raw_data and 'rotary_speed' in raw_data:
            wob = raw_data['weight_on_bit']
            rpm = raw_data['rotary_speed']
            derived['specific_energy'] = wob * rpm / 1000.0 if rpm > 0 else 0
        
        # Differential pressure
        if 'standpipe_pressure' in raw_data and 'formation_pressure' in raw_data:
            derived['differential_pressure'] = (
                raw_data['standpipe_pressure'] - raw_data.get('formation_pressure', 0)
            )
        
        # Flow rate per area
        if 'flow_rate' in raw_data and 'depth' in raw_data:
            # Simplified: assume annular area increases with depth
            area = 0.1 + (raw_data['depth'] / 10000) * 0.05
            derived['flow_velocity'] = raw_data['flow_rate'] / (area * 60) if area > 0 else 0
        
        return derived
    
    def _compute_time_features(
        self,
        raw_data: Dict[str, Any],
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Compute time-based features"""
        time_features = {}
        
        # Hour of day (cyclic)
        hour = timestamp.hour
        time_features['hour_sin'] = np.sin(2 * np.pi * hour / 24)
        time_features['hour_cos'] = np.cos(2 * np.pi * hour / 24)
        
        # Day of week (cyclic)
        day_of_week = timestamp.weekday()
        time_features['day_sin'] = np.sin(2 * np.pi * day_of_week / 7)
        time_features['day_cos'] = np.cos(2 * np.pi * day_of_week / 7)
        
        return time_features
    
    def _compute_statistical_features(
        self,
        entity_id: str,
        raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute statistical features from historical data"""
        statistical = {}
        
        try:
            # Get recent feature values from Redis
            window_size = 100  # Last 100 values
            
            for feature_name in ['weight_on_bit', 'rotary_speed', 'flow_rate', 'mud_weight']:
                if feature_name not in raw_data:
                    continue
                
                # Get historical values (simplified - in production would query time-series DB)
                historical_key = f"{self.namespace}:history:{entity_id}:{feature_name}"
                historical_data = self.redis.lrange(historical_key, -window_size, -1)
                
                if historical_data:
                    values = [json.loads(v)['value'] for v in historical_data]
                    
                    if len(values) > 0:
                        statistical[f'{feature_name}_mean'] = np.mean(values)
                        statistical[f'{feature_name}_std'] = np.std(values)
                        statistical[f'{feature_name}_min'] = np.min(values)
                        statistical[f'{feature_name}_max'] = np.max(values)
                        
                        # Z-score
                        current_value = raw_data[feature_name]
                        mean_val = statistical[f'{feature_name}_mean']
                        std_val = statistical[f'{feature_name}_std']
                        if std_val > 0:
                            statistical[f'{feature_name}_zscore'] = (current_value - mean_val) / std_val
                
                # Store current value in history
                history_value = {
                    'value': raw_data[feature_name],
                    'timestamp': datetime.now().isoformat()
                }
                self.redis.lpush(historical_key, json.dumps(history_value))
                self.redis.ltrim(historical_key, 0, window_size - 1)
                self.redis.expire(historical_key, self.ttl_seconds * 24)  # Keep for 24 hours
        
        except Exception as e:
            self.logger.debug(f"Error computing statistical features: {e}")
        
        return statistical
    
    def _validate_feature_value(self, value: Any, feature_def: FeatureDefinition) -> bool:
        """Validate feature value against definition"""
        # Type check
        expected_type = feature_def.data_type
        if expected_type == 'float' and not isinstance(value, (int, float)):
            return False
        elif expected_type == 'int' and not isinstance(value, int):
            return False
        elif expected_type == 'string' and not isinstance(value, str):
            return False
        elif expected_type == 'bool' and not isinstance(value, bool):
            return False
        
        # Validation rules
        if feature_def.validation_rules:
            rules = feature_def.validation_rules
            
            # Min/max for numeric
            if expected_type in ['float', 'int']:
                if 'min' in rules and value < rules['min']:
                    return False
                if 'max' in rules and value > rules['max']:
                    return False
        
        return True
    
    def get_feature_schema(self) -> Dict[str, Any]:
        """Get feature schema (all registered features)"""
        schema = {}
        
        for name, feature_def in self.feature_registry.items():
            schema[name] = {
                'type': feature_def.feature_type,
                'data_type': feature_def.data_type,
                'description': feature_def.description,
                'default_value': feature_def.default_value,
                'transformation': feature_def.transformation
            }
        
        return schema
    
    def clear_entity_features(self, entity_id: str):
        """Clear all features for an entity"""
        try:
            entity_features_key = f"{self.namespace}:entity:{entity_id}:features"
            feature_names = self.redis.smembers(entity_features_key)
            
            for feature_name in feature_names:
                feature_name = feature_name.decode('utf-8')
                pattern = f"{self.namespace}:feature:{entity_id}:{feature_name}:*"
                
                # Find all keys matching pattern
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
            
            self.redis.delete(entity_features_key)
            
        except Exception as e:
            self.logger.error(f"Error clearing features for {entity_id}: {e}")

