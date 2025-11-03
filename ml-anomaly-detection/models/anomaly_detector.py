#!/usr/bin/env python3
"""
FIDPS Anomaly Detection Models
This module contains machine learning models for detecting anomalies in drilling operations
using real-time MWD/LWD data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import joblib
import warnings
warnings.filterwarnings('ignore')

# ML Libraries
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# Deep Learning
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, LSTM, Dropout, Input, RepeatVector, TimeDistributed
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

# Time Series
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller

class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    EQUIPMENT_FAILURE = "equipment_failure"
    FORMATION_DAMAGE = "formation_damage"
    DRILLING_DYSFUNCTION = "drilling_dysfunction"
    WELLBORE_INSTABILITY = "wellbore_instability"
    FLUID_LOSS = "fluid_loss"
    KICK_DETECTION = "kick_detection"
    STUCK_PIPE = "stuck_pipe"
    VIBRATION_ANOMALY = "vibration_anomaly"
    TEMPERATURE_ANOMALY = "temperature_anomaly"
    PRESSURE_ANOMALY = "pressure_anomaly"

class DamageType(Enum):
    """Formation Damage Types (FR-2.2)"""
    CLAY_IRON_CONTROL = "DT-01"
    DRILLING_INDUCED = "DT-02"
    FLUID_LOSS = "DT-03"
    SCALE_SLUDGE = "DT-04"
    NEAR_WELLBORE_EMULSIONS = "DT-05"
    ROCK_FLUID_INTERACTION = "DT-06"
    COMPLETION_DAMAGE = "DT-07"
    STRESS_CORROSION = "DT-08"
    SURFACE_FILTRATION = "DT-09"
    ULTRA_CLEAN_FLUIDS = "DT-10"

class AnomalySeverity(Enum):
    """Severity levels for detected anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    timestamp: datetime
    well_id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    confidence: float
    features: Dict[str, float]
    description: str
    recommendations: List[str]
    model_name: str
    # Damage Type Classification (FR-2.2)
    damage_type: Optional[DamageType] = None
    damage_type_probability: float = 0.0
    damage_type_confidence: float = 0.0

class MWDLWDFeatureExtractor:
    """Extract features from MWD/LWD data for anomaly detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def extract_statistical_features(self, data: pd.DataFrame, window_size: int = 50) -> Dict[str, float]:
        """Extract statistical features from time series data"""
        features = {}
        
        # Basic statistical features
        for column in data.select_dtypes(include=[np.number]).columns:
            if column in ['timestamp', 'well_id']:
                continue
                
            values = data[column].dropna()
            if len(values) > 0:
                features[f'{column}_mean'] = values.mean()
                features[f'{column}_std'] = values.std()
                features[f'{column}_min'] = values.min()
                features[f'{column}_max'] = values.max()
                features[f'{column}_median'] = values.median()
                features[f'{column}_skew'] = values.skew()
                features[f'{column}_kurtosis'] = values.kurtosis()
                
                # Rolling statistics
                if len(values) >= window_size:
                    rolling = values.rolling(window=window_size)
                    features[f'{column}_rolling_mean'] = rolling.mean().iloc[-1]
                    features[f'{column}_rolling_std'] = rolling.std().iloc[-1]
                    features[f'{column}_rolling_min'] = rolling.min().iloc[-1]
                    features[f'{column}_rolling_max'] = rolling.max().iloc[-1]
        
        return features
    
    def extract_drilling_specific_features(self, data: pd.DataFrame) -> Dict[str, float]:
        """Extract drilling-specific features"""
        features = {}
        
        # Mechanical Specific Energy (MSE)
        if all(col in data.columns for col in ['weight_on_bit', 'torque', 'rpm', 'rop']):
            wob = data['weight_on_bit']
            torque = data['torque']
            rpm = data['rpm']
            rop = data['rop']
            
            # MSE calculation
            mse = (wob + (4 * np.pi * torque * rpm) / (rop * 1000)) / 1000
            features['mse_mean'] = mse.mean()
            features['mse_std'] = mse.std()
            features['mse_max'] = mse.max()
        
        # Drilling efficiency indicators
        if 'rop' in data.columns and 'rpm' in data.columns:
            features['rop_rpm_ratio'] = (data['rop'] / data['rpm']).mean()
        
        if 'weight_on_bit' in data.columns and 'rop' in data.columns:
            features['wob_rop_ratio'] = (data['weight_on_bit'] / data['rop']).mean()
        
        # Hydraulic features
        if all(col in data.columns for col in ['flow_rate', 'standpipe_pressure']):
            features['hydraulic_power'] = (data['flow_rate'] * data['standpipe_pressure']).mean()
        
        # Formation evaluation features
        if 'gamma_ray' in data.columns:
            gr = data['gamma_ray']
            features['gr_trend'] = np.polyfit(range(len(gr)), gr, 1)[0]  # Linear trend
        
        if 'resistivity' in data.columns:
            res = data['resistivity']
            features['resistivity_variation'] = res.std() / res.mean() if res.mean() != 0 else 0
        
        return features
    
    def extract_temporal_features(self, data: pd.DataFrame) -> Dict[str, float]:
        """Extract temporal features"""
        features = {}
        
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data = data.sort_values('timestamp')
            
            # Time-based features
            time_diffs = data['timestamp'].diff().dt.total_seconds()
            features['avg_sampling_rate'] = time_diffs.mean()
            features['sampling_rate_std'] = time_diffs.std()
            
            # Data completeness
            expected_samples = (data['timestamp'].max() - data['timestamp'].min()).total_seconds() / time_diffs.mean()
            features['data_completeness'] = len(data) / expected_samples if expected_samples > 0 else 1.0
        
        return features

class IsolationForestAnomalyDetector:
    """Isolation Forest based anomaly detector"""
    
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.feature_extractor = MWDLWDFeatureExtractor()
        self.is_fitted = False
        self.logger = logging.getLogger(__name__)
    
    def fit(self, data: pd.DataFrame) -> None:
        """Train the anomaly detection model"""
        try:
            # Extract features
            features = self._extract_features(data)
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Train model
            self.model.fit(features_scaled)
            self.is_fitted = True
            
            self.logger.info(f"Isolation Forest model trained on {len(features)} samples")
            
        except Exception as e:
            self.logger.error(f"Error training Isolation Forest model: {e}")
            raise
    
    def predict(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies in new data"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        results = []
        
        try:
            # Extract features
            features = self._extract_features(data)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Predict anomalies
            predictions = self.model.predict(features_scaled)
            scores = self.model.decision_function(features_scaled)
            
            # Process results
            for i, (pred, score) in enumerate(zip(predictions, scores)):
                if pred == -1:  # Anomaly detected
                    timestamp = data.iloc[i]['timestamp'] if 'timestamp' in data.columns else datetime.now()
                    well_id = data.iloc[i]['well_id'] if 'well_id' in data.columns else 'unknown'
                    
                    # Determine severity based on score
                    severity = self._determine_severity(score)
                    
                    # Create anomaly result
                    result = AnomalyResult(
                        timestamp=timestamp,
                        well_id=well_id,
                        anomaly_type=AnomalyType.DRILLING_DYSFUNCTION,
                        severity=severity,
                        confidence=abs(score),
                        features=dict(zip(features.columns, features.iloc[i])),
                        description=f"Isolation Forest detected anomaly with score {score:.3f}",
                        recommendations=self._generate_recommendations(AnomalyType.DRILLING_DYSFUNCTION, severity),
                        model_name="IsolationForest"
                    )
                    
                    results.append(result)
            
            self.logger.info(f"Detected {len(results)} anomalies in {len(data)} samples")
            
        except Exception as e:
            self.logger.error(f"Error predicting anomalies: {e}")
            raise
        
        return results
    
    def _extract_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Extract features from raw data"""
        all_features = []
        
        # Process data in chunks for feature extraction
        chunk_size = 100
        for i in range(0, len(data), chunk_size):
            chunk = data.iloc[i:i+chunk_size]
            
            # Extract different types of features
            stat_features = self.feature_extractor.extract_statistical_features(chunk)
            drilling_features = self.feature_extractor.extract_drilling_specific_features(chunk)
            temporal_features = self.feature_extractor.extract_temporal_features(chunk)
            
            # Combine all features
            combined_features = {**stat_features, **drilling_features, **temporal_features}
            all_features.append(combined_features)
        
        return pd.DataFrame(all_features).fillna(0)
    
    def _determine_severity(self, score: float) -> AnomalySeverity:
        """Determine anomaly severity based on score"""
        if score < -0.5:
            return AnomalySeverity.CRITICAL
        elif score < -0.3:
            return AnomalySeverity.HIGH
        elif score < -0.1:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _generate_recommendations(self, anomaly_type: AnomalyType, severity: AnomalySeverity) -> List[str]:
        """Generate recommendations based on anomaly type and severity"""
        recommendations = {
            AnomalyType.DRILLING_DYSFUNCTION: {
                AnomalySeverity.CRITICAL: [
                    "Stop drilling operations immediately",
                    "Investigate drilling parameters",
                    "Check equipment condition",
                    "Contact drilling supervisor"
                ],
                AnomalySeverity.HIGH: [
                    "Reduce drilling parameters",
                    "Monitor closely",
                    "Prepare for potential issues"
                ],
                AnomalySeverity.MEDIUM: [
                    "Monitor drilling parameters",
                    "Consider parameter adjustment"
                ],
                AnomalySeverity.LOW: [
                    "Continue monitoring",
                    "Log for future reference"
                ]
            }
        }
        
        return recommendations.get(anomaly_type, {}).get(severity, ["Monitor situation"])

class LSTMAnomalyDetector:
    """LSTM-based anomaly detector for time series data"""
    
    def __init__(self, sequence_length: int = 50, encoding_dim: int = 32):
        self.sequence_length = sequence_length
        self.encoding_dim = encoding_dim
        self.model = None
        self.scaler = StandardScaler()
        self.feature_extractor = MWDLWDFeatureExtractor()
        self.is_fitted = False
        self.threshold = None
        self.logger = logging.getLogger(__name__)
    
    def _build_model(self, input_dim: int) -> Model:
        """Build LSTM autoencoder model"""
        # Encoder
        input_layer = Input(shape=(self.sequence_length, input_dim))
        encoded = LSTM(self.encoding_dim, return_sequences=True)(input_layer)
        encoded = Dropout(0.2)(encoded)
        encoded = LSTM(self.encoding_dim // 2, return_sequences=False)(encoded)
        encoded = Dropout(0.2)(encoded)
        
        # Decoder
        decoded = RepeatVector(self.sequence_length)(encoded)
        decoded = LSTM(self.encoding_dim // 2, return_sequences=True)(decoded)
        decoded = Dropout(0.2)(decoded)
        decoded = LSTM(self.encoding_dim, return_sequences=True)(decoded)
        decoded = TimeDistributed(Dense(input_dim))(decoded)
        
        # Create model
        autoencoder = Model(input_layer, decoded)
        autoencoder.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        
        return autoencoder
    
    def _create_sequences(self, data: np.ndarray) -> np.ndarray:
        """Create sequences for LSTM training"""
        sequences = []
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data[i:i + self.sequence_length])
        return np.array(sequences)
    
    def fit(self, data: pd.DataFrame, validation_split: float = 0.2, epochs: int = 100) -> None:
        """Train the LSTM anomaly detection model"""
        try:
            # Prepare data
            numeric_data = data.select_dtypes(include=[np.number]).fillna(0)
            scaled_data = self.scaler.fit_transform(numeric_data)
            
            # Create sequences
            sequences = self._create_sequences(scaled_data)
            
            if len(sequences) == 0:
                raise ValueError("Not enough data to create sequences")
            
            # Build model
            self.model = self._build_model(sequences.shape[2])
            
            # Callbacks
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)
            ]
            
            # Train model
            history = self.model.fit(
                sequences, sequences,
                epochs=epochs,
                batch_size=32,
                validation_split=validation_split,
                callbacks=callbacks,
                verbose=0
            )
            
            # Calculate threshold for anomaly detection
            predictions = self.model.predict(sequences)
            mse = np.mean(np.power(sequences - predictions, 2), axis=(1, 2))
            self.threshold = np.percentile(mse, 95)  # 95th percentile as threshold
            
            self.is_fitted = True
            self.logger.info(f"LSTM model trained on {len(sequences)} sequences, threshold: {self.threshold:.4f}")
            
        except Exception as e:
            self.logger.error(f"Error training LSTM model: {e}")
            raise
    
    def predict(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies using LSTM autoencoder"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        results = []
        
        try:
            # Prepare data
            numeric_data = data.select_dtypes(include=[np.number]).fillna(0)
            scaled_data = self.scaler.transform(numeric_data)
            
            # Create sequences
            sequences = self._create_sequences(scaled_data)
            
            if len(sequences) == 0:
                return results
            
            # Predict and calculate reconstruction error
            predictions = self.model.predict(sequences)
            mse = np.mean(np.power(sequences - predictions, 2), axis=(1, 2))
            
            # Detect anomalies
            anomalies = mse > self.threshold
            
            # Process results
            for i, (is_anomaly, error) in enumerate(zip(anomalies, mse)):
                if is_anomaly:
                    data_idx = i + self.sequence_length - 1
                    timestamp = data.iloc[data_idx]['timestamp'] if 'timestamp' in data.columns else datetime.now()
                    well_id = data.iloc[data_idx]['well_id'] if 'well_id' in data.columns else 'unknown'
                    
                    # Determine severity based on reconstruction error
                    severity = self._determine_severity_lstm(error)
                    
                    # Create anomaly result
                    result = AnomalyResult(
                        timestamp=timestamp,
                        well_id=well_id,
                        anomaly_type=AnomalyType.FORMATION_DAMAGE,
                        severity=severity,
                        confidence=min(error / self.threshold, 1.0),
                        features={'reconstruction_error': error, 'threshold': self.threshold},
                        description=f"LSTM detected anomaly with reconstruction error {error:.4f}",
                        recommendations=self._generate_recommendations_lstm(severity),
                        model_name="LSTM_Autoencoder"
                    )
                    
                    results.append(result)
            
            self.logger.info(f"LSTM detected {len(results)} anomalies in {len(sequences)} sequences")
            
        except Exception as e:
            self.logger.error(f"Error predicting with LSTM: {e}")
            raise
        
        return results
    
    def _determine_severity_lstm(self, error: float) -> AnomalySeverity:
        """Determine severity based on reconstruction error"""
        ratio = error / self.threshold
        
        if ratio > 3.0:
            return AnomalySeverity.CRITICAL
        elif ratio > 2.0:
            return AnomalySeverity.HIGH
        elif ratio > 1.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _generate_recommendations_lstm(self, severity: AnomalySeverity) -> List[str]:
        """Generate recommendations for LSTM-detected anomalies"""
        recommendations = {
            AnomalySeverity.CRITICAL: [
                "Immediate investigation required",
                "Check formation integrity",
                "Review drilling fluid properties",
                "Consider well control measures"
            ],
            AnomalySeverity.HIGH: [
                "Monitor formation parameters closely",
                "Adjust drilling parameters",
                "Prepare contingency plans"
            ],
            AnomalySeverity.MEDIUM: [
                "Continue monitoring",
                "Review recent drilling activities"
            ],
            AnomalySeverity.LOW: [
                "Log for trend analysis",
                "Continue normal operations"
            ]
        }
        
        return recommendations.get(severity, ["Monitor situation"])

class EnsembleAnomalyDetector:
    """Ensemble of multiple anomaly detection models"""
    
    def __init__(self):
        self.models = {
            'isolation_forest': IsolationForestAnomalyDetector(),
            'lstm': LSTMAnomalyDetector(),
            'one_class_svm': OneClassSVM(kernel='rbf', gamma='scale', nu=0.1)
        }
        self.weights = {'isolation_forest': 0.4, 'lstm': 0.4, 'one_class_svm': 0.2}
        self.is_fitted = False
        self.logger = logging.getLogger(__name__)
    
    def fit(self, data: pd.DataFrame) -> None:
        """Train all models in the ensemble"""
        try:
            self.logger.info("Training ensemble models...")
            
            # Train Isolation Forest
            self.models['isolation_forest'].fit(data)
            
            # Train LSTM
            self.models['lstm'].fit(data)
            
            # Train One-Class SVM (simplified for this example)
            numeric_data = data.select_dtypes(include=[np.number]).fillna(0)
            if len(numeric_data) > 0:
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(numeric_data)
                self.models['one_class_svm'].fit(scaled_data)
                self.scaler_svm = scaler
            
            self.is_fitted = True
            self.logger.info("Ensemble models trained successfully")
            
        except Exception as e:
            self.logger.error(f"Error training ensemble: {e}")
            raise
    
    def predict(self, data: pd.DataFrame) -> List[AnomalyResult]:
        """Predict anomalies using ensemble voting"""
        if not self.is_fitted:
            raise ValueError("Ensemble must be fitted before prediction")
        
        try:
            # Get predictions from each model
            if_results = self.models['isolation_forest'].predict(data)
            lstm_results = self.models['lstm'].predict(data)
            
            # Combine results (simplified ensemble logic)
            all_results = if_results + lstm_results
            
            # Remove duplicates and aggregate
            final_results = self._aggregate_results(all_results, data)
            
            self.logger.info(f"Ensemble detected {len(final_results)} anomalies")
            
            return final_results
            
        except Exception as e:
            self.logger.error(f"Error in ensemble prediction: {e}")
            raise
    
    def _aggregate_results(self, results: List[AnomalyResult], data: pd.DataFrame = None) -> List[AnomalyResult]:
        """Aggregate results from multiple models"""
        # Group by timestamp and well_id
        grouped = {}
        
        for result in results:
            key = (result.timestamp, result.well_id)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(result)
        
        # Aggregate grouped results
        final_results = []
        for key, group in grouped.items():
            if len(group) > 1:  # Multiple models detected anomaly
                # Take the highest severity
                max_severity_result = max(group, key=lambda x: list(AnomalySeverity).index(x.severity))
                max_severity_result.confidence = min(sum(r.confidence for r in group) / len(group), 1.0)
                max_severity_result.description = f"Ensemble detection ({len(group)} models agree)"
                final_results.append(max_severity_result)
            else:
                final_results.append(group[0])
        
        # Add damage type classification (FR-2.2)
        if self.enable_damage_classification and self.damage_classifier and self.damage_classifier.is_fitted and data is not None:
            # Get original data for classification
            # Note: In real implementation, pass original data sample
            for result in final_results:
                # Classify damage type based on features
                # This is a simplified version - in production, use the original data sample
                damage_prediction = self._classify_damage_type(result, data)
                if damage_prediction:
                    result.damage_type = damage_prediction['damage_type']
                    result.damage_type_probability = damage_prediction['probability']
                    result.damage_type_confidence = damage_prediction['confidence']
        
        return final_results
    
    def _classify_damage_type(self, result: AnomalyResult, data: pd.DataFrame) -> Optional[Dict]:
        """Classify damage type for an anomaly result"""
        try:
            if self.damage_classifier and self.damage_classifier.is_fitted:
                # Extract features from the data point that caused the anomaly
                # In production, this should use the actual data sample, not just features
                sample_features = pd.DataFrame([result.features])
                
                # Use classifier
                damage_types, probabilities = self.damage_classifier.predict(sample_features)
                
                if damage_types and damage_types[0] is not None:
                    pred_idx = list(DamageType).index(damage_types[0])
                    prob = probabilities[0][pred_idx] if probabilities is not None else result.confidence
                    
                    return {
                        'damage_type': damage_types[0],
                        'probability': float(prob),
                        'confidence': float(prob)
                    }
        except Exception as e:
            self.logger.warning(f"Error classifying damage type: {e}")
        
        return None
    
    def train_damage_classifier(self, data: pd.DataFrame, labels: List[DamageType]) -> None:
        """Train the damage type classifier with labeled data"""
        if not self.enable_damage_classification or not self.damage_classifier:
            self.logger.warning("Damage classification not enabled")
            return
        
        try:
            # Extract features
            features = self.damage_classifier.extract_damage_features(data)
            
            # Train classifier
            self.damage_classifier.fit(features, labels)
            
            self.logger.info("Damage type classifier trained successfully")
        except Exception as e:
            self.logger.error(f"Error training damage classifier: {e}")
            raise

# Model persistence utilities
class ModelManager:
    """Manage model saving and loading"""
    
    @staticmethod
    def save_model(model, filepath: str) -> None:
        """Save model to disk"""
        try:
            joblib.dump(model, filepath)
            logging.info(f"Model saved to {filepath}")
        except Exception as e:
            logging.error(f"Error saving model: {e}")
            raise
    
    @staticmethod
    def load_model(filepath: str):
        """Load model from disk"""
        try:
            model = joblib.load(filepath)
            logging.info(f"Model loaded from {filepath}")
            return model
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            raise

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Generate sample data for testing
    np.random.seed(42)
    n_samples = 1000
    
    sample_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=n_samples, freq='1min'),
        'well_id': ['WELL_001'] * n_samples,
        'depth': np.linspace(1000, 2000, n_samples) + np.random.normal(0, 5, n_samples),
        'hook_load': 50000 + np.random.normal(0, 5000, n_samples),
        'weight_on_bit': 15000 + np.random.normal(0, 2000, n_samples),
        'torque': 8000 + np.random.normal(0, 1000, n_samples),
        'rpm': 120 + np.random.normal(0, 10, n_samples),
        'flow_rate': 400 + np.random.normal(0, 20, n_samples),
        'standpipe_pressure': 3000 + np.random.normal(0, 200, n_samples),
        'rop': 30 + np.random.normal(0, 5, n_samples)
    })
    
    # Add some anomalies
    anomaly_indices = np.random.choice(n_samples, 50, replace=False)
    sample_data.loc[anomaly_indices, 'weight_on_bit'] *= 2  # Simulate equipment issues
    
    print("Testing Isolation Forest Anomaly Detector...")
    if_detector = IsolationForestAnomalyDetector()
    if_detector.fit(sample_data)
    if_results = if_detector.predict(sample_data)
    print(f"Detected {len(if_results)} anomalies with Isolation Forest")
    
    print("\nTesting LSTM Anomaly Detector...")
    lstm_detector = LSTMAnomalyDetector()
    lstm_detector.fit(sample_data, epochs=10)  # Reduced epochs for testing
    lstm_results = lstm_detector.predict(sample_data)
    print(f"Detected {len(lstm_results)} anomalies with LSTM")
    
    print("\nTesting Ensemble Detector...")
    ensemble = EnsembleAnomalyDetector()
    ensemble.fit(sample_data)
    ensemble_results = ensemble.predict(sample_data)
    print(f"Detected {len(ensemble_results)} anomalies with Ensemble")