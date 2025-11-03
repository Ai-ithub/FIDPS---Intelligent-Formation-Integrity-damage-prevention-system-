#!/usr/bin/env python3
"""
FIDPS Damage Type Classifier (FR-2.2)
This module classifies formation damage into one of 10 predefined damage types.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

from .anomaly_detector import DamageType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DamageTypeClassifier:
    """
    Multi-class classifier for formation damage types (FR-2.2)
    
    Classifies detected anomalies into one of 10 damage types:
    - DT-01: Clay/Iron Control
    - DT-02: Drilling-Induced
    - DT-03: Fluid Loss
    - DT-04: Scale/Sludge
    - DT-05: Near-Wellbore Emulsions
    - DT-06: Rock-Fluid Interaction
    - DT-07: Completion Damage
    - DT-08: Stress Corrosion
    - DT-09: Surface Filtration
    - DT-10: Ultra-Clean Fluids
    """
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize damage type classifier
        
        Args:
            model_type: 'random_forest' or 'gradient_boosting'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.logger = logging.getLogger(__name__)
        
        # Feature importance tracking
        self.feature_importance = None
        
        # Initialize model
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced'  # Handle class imbalance
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=10,
                learning_rate=0.05,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def extract_damage_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features relevant for damage type classification
        
        Features include:
        - Operational parameters (WOB, RPM, Flow, Mud Weight)
        - Formation evaluation (Gamma Ray, Resistivity, Porosity)
        - Pressure and temperature indicators
        - Drilling efficiency metrics
        - Anomaly characteristics
        """
        features = {}
        
        # Operational parameters
        if 'weight_on_bit' in data.columns:
            features['wob_mean'] = data['weight_on_bit'].mean()
            features['wob_std'] = data['weight_on_bit'].std()
            features['wob_max'] = data['weight_on_bit'].max()
        
        if 'rotary_speed' in data.columns or 'rpm' in data.columns:
            rpm_col = 'rotary_speed' if 'rotary_speed' in data.columns else 'rpm'
            features['rpm_mean'] = data[rpm_col].mean()
            features['rpm_std'] = data[rpm_col].std()
            features['rpm_max'] = data[rpm_col].max()
        
        if 'flow_rate' in data.columns:
            features['flow_mean'] = data['flow_rate'].mean()
            features['flow_std'] = data['flow_rate'].std()
            features['flow_max'] = data['flow_rate'].max()
        
        if 'mud_weight' in data.columns:
            features['mud_weight_mean'] = data['mud_weight'].mean()
            features['mud_weight_std'] = data['mud_weight'].std()
            features['mud_weight_max'] = data['mud_weight'].max()
        
        # Pressure indicators
        if 'standpipe_pressure' in data.columns:
            features['pressure_mean'] = data['standpipe_pressure'].mean()
            features['pressure_drop'] = data['standpipe_pressure'].max() - data['standpipe_pressure'].min()
        
        # Formation evaluation
        if 'gamma_ray' in data.columns:
            features['gamma_ray_mean'] = data['gamma_ray'].mean()
            features['gamma_ray_std'] = data['gamma_ray'].std()
        
        if 'resistivity' in data.columns:
            features['resistivity_mean'] = data['resistivity'].mean()
            features['resistivity_variation'] = data['resistivity'].std() / data['resistivity'].mean() if data['resistivity'].mean() > 0 else 0
        
        if 'porosity' in data.columns or 'neutron_porosity' in data.columns:
            por_col = 'porosity' if 'porosity' in data.columns else 'neutron_porosity'
            features['porosity_mean'] = data[por_col].mean()
            features['porosity_std'] = data[por_col].std()
        
        # Drilling efficiency
        if all(col in data.columns for col in ['weight_on_bit', 'torque', 'rpm', 'rop']):
            wob = data['weight_on_bit']
            torque = data['torque']
            rpm = data['rpm'] if 'rpm' in data.columns else data['rotary_speed']
            rop = data['rop']
            
            mse = (wob + (4 * np.pi * torque * rpm) / (rop * 1000)) / 1000
            features['mse_mean'] = mse.mean()
            features['mse_trend'] = np.polyfit(range(len(mse)), mse, 1)[0] if len(mse) > 1 else 0
        
        # Temperature (if available)
        if 'temperature' in data.columns or 'bottom_hole_temperature' in data.columns:
            temp_col = 'temperature' if 'temperature' in data.columns else 'bottom_hole_temperature'
            features['temperature_mean'] = data[temp_col].mean()
            features['temperature_trend'] = np.polyfit(range(len(data)), data[temp_col], 1)[0] if len(data) > 1 else 0
        
        # Fluid loss indicators
        if all(col in data.columns for col in ['flow_rate_in', 'flow_rate_out']):
            fluid_loss = (data['flow_rate_in'] - data['flow_rate_out']) / data['flow_rate_in']
            features['fluid_loss_ratio'] = fluid_loss.mean()
            features['fluid_loss_max'] = fluid_loss.max()
        elif 'pit_volume' in data.columns:
            features['pit_volume_change'] = data['pit_volume'].max() - data['pit_volume'].min()
        
        # Depth-based features
        if 'depth' in data.columns:
            features['depth_mean'] = data['depth'].mean()
            features['depth_range'] = data['depth'].max() - data['depth'].min()
        
        # Create DataFrame
        feature_df = pd.DataFrame([features])
        
        return feature_df
    
    def fit(self, X: pd.DataFrame, y: List[DamageType], validation_split: float = 0.2) -> None:
        """
        Train the damage type classifier
        
        Args:
            X: Feature DataFrame (from extract_damage_features)
            y: List of DamageType labels
            validation_split: Fraction of data for validation
        """
        try:
            # Convert labels to strings
            y_str = [dt.value if isinstance(dt, DamageType) else str(dt) for dt in y]
            
            # Handle missing values
            X = X.fillna(0)
            
            # Split data
            if validation_split > 0:
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y_str, test_size=validation_split, random_state=42, stratify=y_str
                )
            else:
                X_train, y_train = X, y_str
                X_val, y_val = None, None
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate on validation set if available
            if X_val is not None and len(X_val) > 0:
                X_val_scaled = self.scaler.transform(X_val)
                y_pred = self.model.predict(X_val_scaled)
                
                self.logger.info(f"Validation accuracy: {np.mean(y_pred == y_val):.3f}")
                self.logger.info(f"\n{classification_report(y_val, y_pred)}")
            
            # Store feature importance
            if hasattr(self.model, 'feature_importances_'):
                self.feature_importance = dict(zip(X.columns, self.model.feature_importances_))
                self.logger.info("Top 10 most important features:")
                for feat, imp in sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]:
                    self.logger.info(f"  {feat}: {imp:.4f}")
            
            self.is_fitted = True
            self.logger.info(f"Damage type classifier trained successfully with {len(X_train)} samples")
            
        except Exception as e:
            self.logger.error(f"Error training damage type classifier: {e}")
            raise
    
    def predict(
        self,
        X: pd.DataFrame,
        return_proba: bool = True
    ) -> Tuple[List[DamageType], Optional[np.ndarray]]:
        """
        Predict damage type for given features
        
        Args:
            X: Feature DataFrame
            return_proba: Whether to return probability distribution
            
        Returns:
            Tuple of (predicted_damage_types, probability_distributions)
        """
        if not self.is_fitted:
            raise ValueError("Classifier must be fitted before prediction")
        
        try:
            # Handle missing values
            X = X.fillna(0)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict
            predictions = self.model.predict(X_scaled)
            
            # Convert to DamageType enum
            damage_types = [DamageType(pred) if pred in [dt.value for dt in DamageType] else None for pred in predictions]
            
            # Get probabilities if requested
            probabilities = None
            if return_proba and hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(X_scaled)
            
            return damage_types, probabilities
            
        except Exception as e:
            self.logger.error(f"Error predicting damage type: {e}")
            raise
    
    def predict_single(
        self,
        data: pd.DataFrame,
        return_proba: bool = True
    ) -> Dict[str, any]:
        """
        Predict damage type for a single data sample
        
        Returns:
            Dictionary with:
            - damage_type: Predicted DamageType
            - probability: Confidence score
            - all_probabilities: Probability distribution for all types
        """
        # Extract features
        features = self.extract_damage_features(data)
        
        # Predict
        damage_types, probabilities = self.predict(features, return_proba=return_proba)
        
        result = {
            'damage_type': damage_types[0] if damage_types[0] is not None else DamageType.DRILLING_INDUCED,
            'probability': 0.0,
            'confidence': 0.0
        }
        
        if probabilities is not None and len(probabilities) > 0:
            # Get probability for predicted class
            pred_idx = list(DamageType).index(result['damage_type'])
            result['probability'] = float(probabilities[0][pred_idx])
            result['confidence'] = float(probabilities[0][pred_idx])
            
            # Get all probabilities
            result['all_probabilities'] = {
                dt.value: float(prob) for dt, prob in zip(DamageType, probabilities[0])
            }
        
        return result
    
    def save_model(self, filepath: str) -> None:
        """Save trained model to disk"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'model_type': self.model_type,
                'feature_importance': self.feature_importance
            }
            joblib.dump(model_data, filepath)
            self.logger.info(f"Model saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving model: {e}")
            raise
    
    def load_model(self, filepath: str) -> None:
        """Load trained model from disk"""
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.model_type = model_data['model_type']
            self.feature_importance = model_data.get('feature_importance')
            self.is_fitted = True
            self.logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            raise

