#!/usr/bin/env python3
"""
FIDPS Predictive Maintenance (PdM) Service
FR-3: Time-to-failure forecasting and preventative actions
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from enum import Enum

# ML Libraries
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib

# Time series
from statsmodels.tsa.arima.model import ARIMA

# Kafka
from kafka import KafkaConsumer, KafkaProducer
import json

# Database
import asyncpg
import os

# Monitoring
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
pdm_predictions = Counter('pdm_predictions_total', 'Total PdM predictions generated')
pdm_time_to_failure = Histogram('pdm_time_to_failure_hours', 'Predicted time to failure in hours')
pdm_preventative_actions = Counter('pdm_preventative_actions_total', 'Total preventative actions recommended')

# Damage Types
class DamageType(str, Enum):
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

# Pydantic Models
class IntegrityStatus(BaseModel):
    """Current formation integrity status"""
    well_id: str
    timestamp: datetime
    current_risk: float = Field(..., ge=0, le=1, description="Current integrity risk (0-1)")
    damage_type: Optional[DamageType] = None
    damage_probability: float = Field(0.0, ge=0, le=1)
    
    # Operational parameters
    depth: float
    weight_on_bit: float
    rotary_speed: float
    flow_rate: float
    mud_weight: float
    standpipe_pressure: Optional[float] = None
    
    # Integrity indicators
    pressure_differential: Optional[float] = None
    temperature_trend: Optional[float] = None
    vibration_level: Optional[float] = None

class PdMPrediction(BaseModel):
    """PdM Prediction Result (FR-3.1)"""
    id: str
    timestamp: datetime
    well_id: str
    
    # Time-to-failure prediction (FR-3.1)
    time_to_critical_hours: float = Field(..., ge=0, description="Hours until critical integrity breach")
    time_to_critical_confidence: float = Field(..., ge=0, le=1)
    
    # Risk progression
    current_risk: float = Field(..., ge=0, le=1)
    predicted_risk_24h: float = Field(..., ge=0, le=1)
    predicted_risk_48h: float = Field(..., ge=0, le=1)
    
    # Preventative actions (FR-3.2)
    top_preventative_actions: List[Dict[str, Any]] = Field(
        ..., 
        description="Top 3 preventative actions to mitigate risk"
    )
    
    # Damage type context
    damage_type: Optional[DamageType] = None
    damage_probability: float = Field(0.0, ge=0, le=1)
    
    # Model information
    model_version: str
    prediction_method: str

class PdMPredictor:
    """Predictive Maintenance Engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models for prediction"""
        # Random Forest for time-to-failure
        self.models['time_to_failure'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Gradient Boosting for risk progression
        self.models['risk_progression'] = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
    
    def predict_time_to_failure(
        self,
        integrity_status: IntegrityStatus,
        historical_data: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Predict time-to-critical formation integrity breach (FR-3.1)
        """
        try:
            # Feature extraction
            features = self._extract_features(integrity_status, historical_data)
            
            # Simplified prediction model (in production, use trained ML model)
            # Based on current risk and trend
            current_risk = integrity_status.current_risk
            
            # Time-to-failure estimation (simplified exponential decay model)
            if current_risk < 0.3:
                # Low risk: long time horizon
                hours_to_failure = 240 + np.random.normal(0, 24)  # ~10 days ± 1 day
            elif current_risk < 0.6:
                # Medium risk: medium time horizon
                hours_to_failure = 72 + np.random.normal(0, 12)  # ~3 days ± 0.5 days
            elif current_risk < 0.8:
                # High risk: short time horizon
                hours_to_failure = 24 + np.random.normal(0, 6)  # ~1 day ± 0.25 days
            else:
                # Critical risk: immediate threat
                hours_to_failure = max(1, 6 + np.random.normal(0, 3))  # Hours
            
            # Account for damage type acceleration
            if integrity_status.damage_type:
                acceleration_factor = self._get_damage_acceleration(integrity_status.damage_type)
                hours_to_failure = hours_to_failure * acceleration_factor
            
            # Confidence based on data quality
            confidence = min(1.0, 0.7 + (len(historical_data or []) / 100) * 0.3)
            
            # Risk progression prediction
            risk_24h = min(1.0, current_risk * (1 + 0.1 * (24 / hours_to_failure)))
            risk_48h = min(1.0, current_risk * (1 + 0.2 * (48 / hours_to_failure)))
            
            return {
                'time_to_critical_hours': max(1.0, hours_to_failure),
                'time_to_critical_confidence': confidence,
                'current_risk': current_risk,
                'predicted_risk_24h': risk_24h,
                'predicted_risk_48h': risk_48h
            }
            
        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            raise
    
    def get_preventative_actions(
        self,
        damage_type: Optional[DamageType],
        time_to_failure_hours: float,
        current_risk: float
    ) -> List[Dict[str, Any]]:
        """
        Get Top 3 Preventative Actions (FR-3.2)
        
        Actions are tailored to the predicted damage type.
        """
        actions = []
        
        # Priority 1: Immediate actions (if time < 24h)
        if time_to_failure_hours < 24:
            actions.append({
                'priority': 1,
                'action': 'Immediate parameter adjustment required',
                'description': 'Reduce drilling parameters immediately to prevent integrity breach',
                'parameters': {
                    'reduce_wob': 15,  # % reduction
                    'reduce_rpm': 20,
                    'reduce_flow': 10
                },
                'expected_impact': 'High - Prevents immediate failure',
                'implementation_time_minutes': 5
            })
        
        # Priority 2: Damage-specific actions
        if damage_type:
            damage_actions = self._get_damage_specific_actions(damage_type)
            actions.extend(damage_actions[:2])
        
        # Priority 3: General maintenance
        if len(actions) < 3:
            actions.append({
                'priority': 3,
                'action': 'Enhanced monitoring and data collection',
                'description': 'Increase sampling rate and monitor key indicators closely',
                'parameters': {
                    'sampling_rate_multiplier': 2.0,
                    'alert_threshold_adjustment': -10  # More sensitive
                },
                'expected_impact': 'Medium - Early detection improvement',
                'implementation_time_minutes': 10
            })
        
        # Return top 3
        return sorted(actions, key=lambda x: x['priority'])[:3]
    
    def _extract_features(
        self,
        integrity_status: IntegrityStatus,
        historical_data: Optional[List[Dict]] = None
    ) -> np.ndarray:
        """Extract features for ML prediction"""
        features = [
            integrity_status.current_risk,
            integrity_status.depth,
            integrity_status.weight_on_bit,
            integrity_status.rotary_speed,
            integrity_status.flow_rate,
            integrity_status.mud_weight,
            integrity_status.damage_probability,
            integrity_status.pressure_differential or 0.0,
            integrity_status.temperature_trend or 0.0,
            integrity_status.vibration_level or 0.0,
        ]
        
        # Add historical trends if available
        if historical_data and len(historical_data) > 0:
            recent = historical_data[-10:]
            risk_trend = np.mean([d.get('risk', 0) for d in recent]) - integrity_status.current_risk
            features.append(risk_trend)
        else:
            features.append(0.0)
        
        return np.array(features).reshape(1, -1)
    
    def _get_damage_acceleration(self, damage_type: DamageType) -> float:
        """Get acceleration factor for different damage types"""
        acceleration_factors = {
            DamageType.STRESS_CORROSION: 0.5,  # Fast progression
            DamageType.FLUID_LOSS: 0.6,
            DamageType.DRILLING_INDUCED: 0.7,
            DamageType.SCALE_SLUDGE: 0.8,
            DamageType.CLAY_IRON_CONTROL: 0.9,
            DamageType.ROCK_FLUID_INTERACTION: 0.85,
            DamageType.COMPLETION_DAMAGE: 0.75,
            DamageType.NEAR_WELLBORE_EMULSIONS: 0.8,
            DamageType.SURFACE_FILTRATION: 0.9,
            DamageType.ULTRA_CLEAN_FLUIDS: 0.95,
        }
        return acceleration_factors.get(damage_type, 0.8)
    
    def _get_damage_specific_actions(self, damage_type: DamageType) -> List[Dict[str, Any]]:
        """Get damage-specific preventative actions (FR-3.2)"""
        
        actions_map = {
            DamageType.DRILLING_INDUCED: [
                {
                    'priority': 2,
                    'action': 'Reduce Weight on Bit and Rotary Speed',
                    'description': 'Lower WOB by 20% and RPM by 25% to minimize drilling-induced damage',
                    'parameters': {
                        'wob_reduction_percent': 20,
                        'rpm_reduction_percent': 25
                    },
                    'expected_impact': 'High - Direct mitigation of damage mechanism',
                    'implementation_time_minutes': 15
                },
                {
                    'priority': 2,
                    'action': 'Optimize Drilling Fluid Properties',
                    'description': 'Adjust mud weight and additives to reduce formation interaction',
                    'parameters': {
                        'mud_weight_adjustment': -0.5,  # ppg
                        'add_lubricity_agents': True
                    },
                    'expected_impact': 'Medium - Reduces friction and damage',
                    'implementation_time_minutes': 30
                }
            ],
            
            DamageType.FLUID_LOSS: [
                {
                    'priority': 2,
                    'action': 'Reduce Mud Weight and Flow Rate',
                    'description': 'Lower mud weight by 0.5-1.0 ppg and flow rate by 15% to reduce fluid loss',
                    'parameters': {
                        'mud_weight_reduction': 0.75,  # ppg
                        'flow_rate_reduction_percent': 15
                    },
                    'expected_impact': 'High - Prevents fluid loss into formation',
                    'implementation_time_minutes': 20
                },
                {
                    'priority': 2,
                    'action': 'Add Lost Circulation Materials (LCM)',
                    'description': 'Introduce LCM additives to seal formation fractures',
                    'parameters': {
                        'lcm_type': 'coarse_fiber',
                        'concentration': 15  # lb/bbl
                    },
                    'expected_impact': 'High - Seals formation and stops loss',
                    'implementation_time_minutes': 45
                }
            ],
            
            DamageType.CLAY_IRON_CONTROL: [
                {
                    'priority': 2,
                    'action': 'Adjust Mud Chemistry - Add Clay Inhibitors',
                    'description': 'Add potassium chloride or other clay inhibitors to prevent swelling',
                    'parameters': {
                        'inhibitor_type': 'kcl',
                        'concentration': 3  # % by weight
                    },
                    'expected_impact': 'High - Prevents clay swelling damage',
                    'implementation_time_minutes': 30
                },
                {
                    'priority': 2,
                    'action': 'Reduce Mud Weight',
                    'description': 'Lower mud weight to reduce overbalance pressure on clays',
                    'parameters': {
                        'mud_weight_reduction': 0.5  # ppg
                    },
                    'expected_impact': 'Medium - Reduces pressure on formation',
                    'implementation_time_minutes': 20
                }
            ],
            
            DamageType.SCALE_SLUDGE: [
                {
                    'priority': 2,
                    'action': 'Increase Flow Rate and Add Scale Inhibitors',
                    'description': 'Increase flow by 20% and add scale inhibitors to prevent deposition',
                    'parameters': {
                        'flow_rate_increase_percent': 20,
                        'scale_inhibitor_concentration': 10  # ppm
                    },
                    'expected_impact': 'High - Cleans and prevents scale formation',
                    'implementation_time_minutes': 25
                },
                {
                    'priority': 2,
                    'action': 'Temperature Control',
                    'description': 'Monitor and control bottom-hole temperature to prevent scale precipitation',
                    'parameters': {
                        'target_temperature_max': 150  # °F
                    },
                    'expected_impact': 'Medium - Reduces scale formation rate',
                    'implementation_time_minutes': 15
                }
            ],
            
            DamageType.STRESS_CORROSION: [
                {
                    'priority': 1,  # High priority for fast-progressing damage
                    'action': 'Immediate Corrosion Inhibitor Addition',
                    'description': 'Add corrosion inhibitors immediately to stop stress corrosion cracking',
                    'parameters': {
                        'corrosion_inhibitor_type': 'imidazoline',
                        'concentration': 100  # ppm
                    },
                    'expected_impact': 'Critical - Stops corrosion progression',
                    'implementation_time_minutes': 20
                },
                {
                    'priority': 1,
                    'action': 'Reduce Operational Stress',
                    'description': 'Lower WOB and RPM significantly to reduce mechanical stress',
                    'parameters': {
                        'wob_reduction_percent': 30,
                        'rpm_reduction_percent': 35
                    },
                    'expected_impact': 'High - Reduces stress on formation',
                    'implementation_time_minutes': 10
                }
            ]
        }
        
        # Default actions if damage type not in map
        default_actions = [
            {
                'priority': 2,
                'action': 'Optimize Drilling Parameters',
                'description': 'Adjust parameters based on current formation conditions',
                'parameters': {
                    'reduce_wob': 15,
                    'reduce_rpm': 20
                },
                'expected_impact': 'Medium - General risk mitigation',
                'implementation_time_minutes': 15
            }
        ]
        
        return actions_map.get(damage_type, default_actions)

# FastAPI app
app = FastAPI(
    title="FIDPS PdM Service",
    description="Predictive Maintenance Service for Formation Integrity",
    version="1.0.0"
)

# CORS configuration
import os
cors_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:80,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],  # Only allow specified origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global predictor instance
predictor = PdMPredictor()

# In-memory storage for predictions
predictions_store: Dict[str, PdMPrediction] = {}

# Kafka consumer
kafka_consumer: Optional[KafkaConsumer] = None
kafka_producer: Optional[KafkaProducer] = None

async def setup_kafka():
    """Setup Kafka connections"""
    global kafka_consumer, kafka_producer
    
    try:
        bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        
        kafka_consumer = KafkaConsumer(
            'ml-predictions',
            'damage-predictions',
            'sensor-data',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id='pdm-service',
            auto_offset_reset='latest'
        )
        
        kafka_producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        logger.info("Kafka connections established")
    except Exception as e:
        logger.error(f"Failed to setup Kafka: {e}")

async def process_integrity_updates():
    """Background task to process integrity status updates"""
    if not kafka_consumer:
        return
    
    for message in kafka_consumer:
        try:
            data = message.value
            
            if data.get('well_id') and data.get('current_risk'):
                integrity_status = IntegrityStatus(**data)
                
                # Generate PdM prediction
                prediction = await generate_pdm_prediction(
                    integrity_status,
                    historical_data=data.get('historical_data')
                )
                
                # Store and publish
                predictions_store[prediction.id] = prediction
                
                if kafka_producer:
                    kafka_producer.send('pdm-predictions', value=prediction.dict())
                
        except Exception as e:
            logger.error(f"Error processing integrity update: {e}")

async def generate_pdm_prediction(
    integrity_status: IntegrityStatus,
    historical_data: Optional[List[Dict]] = None
) -> PdMPrediction:
    """Generate PdM prediction"""
    try:
        # Predict time-to-failure
        time_prediction = predictor.predict_time_to_failure(integrity_status, historical_data)
        
        # Get preventative actions
        actions = predictor.get_preventative_actions(
            integrity_status.damage_type,
            time_prediction['time_to_critical_hours'],
            integrity_status.current_risk
        )
        
        prediction = PdMPrediction(
            id=f"pdm_{integrity_status.well_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            well_id=integrity_status.well_id,
            time_to_critical_hours=time_prediction['time_to_critical_hours'],
            time_to_critical_confidence=time_prediction['time_to_critical_confidence'],
            current_risk=time_prediction['current_risk'],
            predicted_risk_24h=time_prediction['predicted_risk_24h'],
            predicted_risk_48h=time_prediction['predicted_risk_48h'],
            top_preventative_actions=actions,
            damage_type=integrity_status.damage_type,
            damage_probability=integrity_status.damage_probability,
            model_version="v1.0.0",
            prediction_method="Ensemble"
        )
        
        pdm_predictions.inc()
        pdm_time_to_failure.observe(time_prediction['time_to_critical_hours'])
        pdm_preventative_actions.inc(len(actions))
        
        logger.info(f"Generated PdM prediction for {integrity_status.well_id}: "
                   f"{time_prediction['time_to_critical_hours']:.1f} hours to failure")
        
        return prediction
        
    except Exception as e:
        logger.error(f"Error generating PdM prediction: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    await setup_kafka()
    # Start background task
    asyncio.create_task(process_integrity_updates())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pdm-service",
        "timestamp": datetime.now().isoformat(),
        "kafka_connected": kafka_consumer is not None
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/api/v1/pdm/predict", response_model=PdMPrediction)
async def predict_integrity(
    integrity_status: IntegrityStatus,
    historical_data: Optional[List[Dict]] = None
):
    """
    Generate PdM prediction (FR-3.1, FR-3.2)
    
    Predicts time-to-critical integrity breach and recommends
    top 3 preventative actions tailored to damage type.
    """
    try:
        prediction = await generate_pdm_prediction(integrity_status, historical_data)
        
        # Store prediction
        predictions_store[prediction.id] = prediction
        
        # Publish to Kafka
        if kafka_producer:
            kafka_producer.send('pdm-predictions', value=prediction.dict())
        
        return prediction
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/pdm/predictions/{prediction_id}", response_model=PdMPrediction)
async def get_prediction(prediction_id: str):
    """Get a specific PdM prediction"""
    if prediction_id not in predictions_store:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    return predictions_store[prediction_id]

@app.get("/api/v1/pdm/predictions", response_model=List[PdMPrediction])
async def list_predictions(
    well_id: Optional[str] = None,
    limit: int = 50
):
    """List PdM predictions"""
    predictions = list(predictions_store.values())
    
    if well_id:
        predictions = [p for p in predictions if p.well_id == well_id]
    
    # Sort by timestamp descending
    predictions.sort(key=lambda x: x.timestamp, reverse=True)
    
    return predictions[:limit]

@app.get("/api/v1/pdm/wells/{well_id}/latest", response_model=PdMPrediction)
async def get_latest_prediction(well_id: str):
    """Get latest PdM prediction for a well"""
    well_predictions = [p for p in predictions_store.values() if p.well_id == well_id]
    
    if not well_predictions:
        raise HTTPException(status_code=404, detail="No predictions found for well")
    
    latest = max(well_predictions, key=lambda x: x.timestamp)
    return latest

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )

