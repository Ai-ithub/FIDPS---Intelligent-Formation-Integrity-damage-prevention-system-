#!/usr/bin/env python3
"""
FIDPS Real-Time Optimization (RTO) Service
FR-4: Multi-objective optimization for drilling parameters
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio
from enum import Enum

# Optimization libraries
import numpy as np
from scipy.optimize import minimize
import cvxpy as cp

# Data processing
import pandas as pd

# Kafka integration
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
rto_recommendations = Counter('rto_recommendations_total', 'Total RTO recommendations generated')
rto_optimization_time = Histogram('rto_optimization_seconds', 'Time taken for optimization')
rto_approved = Counter('rto_approved_total', 'Total approved RTO recommendations')
rto_rejected = Counter('rto_rejected_total', 'Total rejected RTO recommendations')

# Damage Types (FR-2.2)
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
class DrillingParameters(BaseModel):
    """Current drilling parameters"""
    weight_on_bit: float = Field(..., ge=0, description="Weight on bit in klbs")
    rotary_speed: float = Field(..., ge=0, le=300, description="Rotary speed in RPM")
    flow_rate: float = Field(..., ge=0, description="Flow rate in gpm")
    mud_weight: float = Field(..., ge=0, le=20, description="Mud weight in ppg")
    torque: Optional[float] = Field(None, ge=0, description="Torque in ft-lbs")
    standpipe_pressure: Optional[float] = Field(None, ge=0, description="Standpipe pressure in psi")
    rate_of_penetration: Optional[float] = Field(None, ge=0, description="ROP in ft/hr")
    depth: float = Field(..., ge=0, description="Current depth in meters")

class RTORecovery(BaseModel):
    """RTO Recommendation"""
    id: str
    timestamp: datetime
    well_id: str
    damage_type: DamageType
    damage_probability: float = Field(..., ge=0, le=1)
    
    # Current parameters
    current_values: DrillingParameters
    
    # Recommended parameters
    recommended_values: DrillingParameters
    
    # Optimization results
    expected_improvement: float = Field(..., description="Expected efficiency improvement (%)")
    risk_reduction: float = Field(..., description="Formation damage risk reduction (%)")
    confidence: float = Field(..., ge=0, le=1, description="Optimization confidence")
    
    # Constraints
    constraints_satisfied: bool
    constraint_violations: List[str] = Field(default_factory=list)
    
    # Status
    status: str = Field("pending", description="pending, approved, rejected, applied")
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Metadata
    optimization_method: str
    computation_time_ms: float

class RTOOptimizer:
    """Multi-objective optimization engine for drilling parameters"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def optimize(
        self,
        current_params: DrillingParameters,
        damage_type: DamageType,
        damage_probability: float,
        well_id: str
    ) -> Dict[str, Any]:
        """
        Execute multi-objective optimization (FR-4.1)
        
        Objective function:
        - Minimize formation damage risk for the predicted damage type
        - Maximize drilling efficiency (ROP)
        - Minimize drilling costs (torque, WOB)
        """
        start_time = datetime.now()
        
        # Extract current values as numpy array
        x0 = np.array([
            current_params.weight_on_bit,
            current_params.rotary_speed,
            current_params.flow_rate,
            current_params.mud_weight
        ])
        
        # Bounds for optimization (FR-4.3: safe operating limits)
        bounds = [
            (max(0, x0[0] - 10), min(x0[0] + 10, 50)),  # WOB: ±10 klbs, max 50
            (max(0, x0[1] - 30), min(x0[1] + 30, 200)),  # RPM: ±30, max 200
            (max(0, x0[2] - 50), min(x0[2] + 50, 500)),  # Flow: ±50 gpm, max 500
            (max(8.0, x0[3] - 1.0), min(x0[3] + 1.0, 15.0))  # Mud: ±1 ppg, 8-15 range
        ]
        
        # Multi-objective optimization (FR-4.1)
        def objective_function(x):
            wob, rpm, flow, mud = x
            
            # Objective 1: Minimize damage risk (based on damage type)
            risk_score = self._calculate_damage_risk(
                wob, rpm, flow, mud, damage_type, damage_probability
            )
            
            # Objective 2: Maximize efficiency (estimated ROP)
            efficiency = self._estimate_rop(wob, rpm, flow, mud, current_params.depth)
            
            # Objective 3: Minimize operational costs (weighted)
            cost = (wob * 0.1) + (rpm * 0.05) + (flow * 0.02)
            
            # Combined objective (risk is most important)
            return risk_score * 0.6 - efficiency * 0.3 + cost * 0.1
        
        # Constraints
        constraints = []
        
        # Constraint 1: Maintain safe pressure margins
        if current_params.standpipe_pressure:
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: 3000 - (x[2] * 2.5 + x[0] * 10)  # Simplified pressure model
            })
        
        # Constraint 2: Maintain minimum ROP
        constraints.append({
            'type': 'ineq',
            'fun': lambda x: self._estimate_rop(x[0], x[1], x[2], x[3], current_params.depth) - 20  # Min 20 ft/hr
        })
        
        # Constraint 3: Damage-specific constraints
        damage_constraints = self._get_damage_specific_constraints(damage_type)
        constraints.extend(damage_constraints)
        
        # Run optimization
        try:
            result = minimize(
                objective_function,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 100, 'ftol': 1e-6}
            )
            
            if not result.success:
                logger.warning(f"Optimization did not converge: {result.message}")
            
            # Extract results
            optimal_wob = max(bounds[0][0], min(bounds[0][1], result.x[0]))
            optimal_rpm = max(bounds[1][0], min(bounds[1][1], result.x[1]))
            optimal_flow = max(bounds[2][0], min(bounds[2][1], result.x[2]))
            optimal_mud = max(bounds[3][0], min(bounds[3][1], result.x[3]))
            
            # Calculate improvements
            current_risk = self._calculate_damage_risk(
                current_params.weight_on_bit,
                current_params.rotary_speed,
                current_params.flow_rate,
                current_params.mud_weight,
                damage_type,
                damage_probability
            )
            
            optimal_risk = self._calculate_damage_risk(
                optimal_wob, optimal_rpm, optimal_flow, optimal_mud,
                damage_type, damage_probability
            )
            
            risk_reduction = max(0, (current_risk - optimal_risk) / current_risk * 100) if current_risk > 0 else 0
            
            current_rop = self._estimate_rop(
                current_params.weight_on_bit,
                current_params.rotary_speed,
                current_params.flow_rate,
                current_params.mud_weight,
                current_params.depth
            )
            
            optimal_rop = self._estimate_rop(
                optimal_wob, optimal_rpm, optimal_flow, optimal_mud, current_params.depth
            )
            
            efficiency_improvement = max(0, (optimal_rop - current_rop) / current_rop * 100) if current_rop > 0 else 0
            
            computation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                'recommended_values': {
                    'weight_on_bit': round(optimal_wob, 2),
                    'rotary_speed': round(optimal_rpm, 2),
                    'flow_rate': round(optimal_flow, 2),
                    'mud_weight': round(optimal_mud, 2),
                },
                'expected_improvement': round(efficiency_improvement, 2),
                'risk_reduction': round(risk_reduction, 2),
                'confidence': min(1.0, 1.0 - (risk_reduction / 100)),
                'constraints_satisfied': result.success,
                'constraint_violations': [] if result.success else [result.message],
                'optimization_method': 'SLSQP',
                'computation_time_ms': round(computation_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")
    
    def _calculate_damage_risk(
        self,
        wob: float,
        rpm: float,
        flow: float,
        mud: float,
        damage_type: DamageType,
        base_probability: float
    ) -> float:
        """Calculate formation damage risk based on parameters and damage type"""
        
        # Base risk from ML prediction
        risk = base_probability
        
        # Damage-specific risk adjustments
        if damage_type == DamageType.DRILLING_INDUCED:
            # High WOB and RPM increase risk
            risk += (wob / 50) * 0.2 + (rpm / 200) * 0.15
        
        elif damage_type == DamageType.FLUID_LOSS:
            # High mud weight and pressure increase risk
            risk += (mud / 15) * 0.25 + (flow / 500) * 0.1
        
        elif damage_type == DamageType.SCALE_SLUDGE:
            # Temperature and flow rate related
            risk += (flow / 500) * 0.15
        
        elif damage_type == DamageType.CLAY_IRON_CONTROL:
            # Mud weight and chemistry related
            risk += (mud / 15) * 0.2
        
        # Normalize risk to [0, 1]
        return min(1.0, max(0.0, risk))
    
    def _estimate_rop(self, wob: float, rpm: float, flow: float, mud: float, depth: float) -> float:
        """Estimate Rate of Penetration based on drilling parameters"""
        # Simplified ROP model
        # ROP = f(WOB, RPM, Flow, Mud, Depth)
        base_rop = 30.0  # Base ROP in ft/hr
        
        # WOB contribution (diminishing returns)
        wob_factor = 1 + (wob / 50) * 0.5
        
        # RPM contribution
        rpm_factor = 1 + (rpm / 200) * 0.3
        
        # Flow contribution (cleaning effect)
        flow_factor = 1 + (flow / 500) * 0.2
        
        # Depth penalty (deeper = slower)
        depth_penalty = 1 - (depth / 5000) * 0.2
        
        estimated_rop = base_rop * wob_factor * rpm_factor * flow_factor * depth_penalty
        
        return max(10.0, min(100.0, estimated_rop))  # Clamp between 10-100 ft/hr
    
    def _get_damage_specific_constraints(self, damage_type: DamageType) -> List[Dict]:
        """Get damage-specific optimization constraints"""
        constraints = []
        
        if damage_type == DamageType.DRILLING_INDUCED:
            # Reduce WOB and RPM to minimize drilling damage
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: 30 - x[0]  # WOB should be less than 30 klbs
            })
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: 150 - x[1]  # RPM should be less than 150
            })
        
        elif damage_type == DamageType.FLUID_LOSS:
            # Reduce mud weight and flow to minimize fluid loss
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: 11.0 - x[3]  # Mud weight should be less than 11 ppg
            })
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: 350 - x[2]  # Flow should be less than 350 gpm
            })
        
        elif damage_type == DamageType.SCALE_SLUDGE:
            # Maintain higher flow for cleaning
            constraints.append({
                'type': 'ineq',
                'fun': lambda x: x[2] - 300  # Flow should be at least 300 gpm
            })
        
        return constraints

# FastAPI app
app = FastAPI(
    title="FIDPS RTO Service",
    description="Real-Time Optimization Service for Drilling Parameters",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global optimizer instance
optimizer = RTOOptimizer()

# In-memory storage for recommendations (should be in DB in production)
recommendations_store: Dict[str, RTORecovery] = {}

# Kafka consumer for damage predictions
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
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id='rto-service',
            auto_offset_reset='latest'
        )
        
        kafka_producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        logger.info("Kafka connections established")
    except Exception as e:
        logger.error(f"Failed to setup Kafka: {e}")

async def process_damage_predictions():
    """Background task to process damage predictions and generate RTO recommendations"""
    if not kafka_consumer:
        return
    
    for message in kafka_consumer:
        try:
            prediction = message.value
            
            if prediction.get('damage_type') and prediction.get('well_id'):
                # Generate RTO recommendation
                await generate_rto_recommendation(
                    well_id=prediction['well_id'],
                    damage_type=DamageType(prediction['damage_type']),
                    damage_probability=prediction.get('probability', 0.5),
                    current_params=DrillingParameters(**prediction.get('current_params', {}))
                )
        except Exception as e:
            logger.error(f"Error processing damage prediction: {e}")

async def generate_rto_recommendation(
    well_id: str,
    damage_type: DamageType,
    damage_probability: float,
    current_params: DrillingParameters
):
    """Generate RTO recommendation for a well"""
    try:
        optimization_result = optimizer.optimize(
            current_params,
            damage_type,
            damage_probability,
            well_id
        )
        
        recommendation = RTORecovery(
            id=f"rto_{well_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            well_id=well_id,
            damage_type=damage_type,
            damage_probability=damage_probability,
            current_values=current_params,
            recommended_values=DrillingParameters(**optimization_result['recommended_values']),
            expected_improvement=optimization_result['expected_improvement'],
            risk_reduction=optimization_result['risk_reduction'],
            confidence=optimization_result['confidence'],
            constraints_satisfied=optimization_result['constraints_satisfied'],
            constraint_violations=optimization_result.get('constraint_violations', []),
            optimization_method=optimization_result['optimization_method'],
            computation_time_ms=optimization_result['computation_time_ms']
        )
        
        # Store recommendation
        recommendations_store[recommendation.id] = recommendation
        
        # Publish to Kafka
        if kafka_producer:
            kafka_producer.send('rto-recommendations', value=recommendation.dict())
        
        rto_recommendations.inc()
        logger.info(f"Generated RTO recommendation {recommendation.id} for {well_id}")
        
    except Exception as e:
        logger.error(f"Error generating RTO recommendation: {e}")

@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    await setup_kafka()
    # Start background task for processing predictions
    asyncio.create_task(process_damage_predictions())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "rto-service",
        "timestamp": datetime.now().isoformat(),
        "kafka_connected": kafka_consumer is not None
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

@app.post("/api/v1/rto/optimize", response_model=RTORecovery)
async def optimize_parameters(
    current_params: DrillingParameters,
    damage_type: DamageType,
    damage_probability: float = Field(..., ge=0, le=1),
    well_id: str = Field(..., description="Well identifier")
):
    """
    Generate RTO recommendation (FR-4.1, FR-4.3)
    
    This endpoint generates optimal drilling parameters to minimize
    formation damage risk for the specified damage type.
    """
    start_time = datetime.now()
    
    try:
        optimization_result = optimizer.optimize(
            current_params,
            damage_type,
            damage_probability,
            well_id
        )
        
        recommendation = RTORecovery(
            id=f"rto_{well_id}_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            well_id=well_id,
            damage_type=damage_type,
            damage_probability=damage_probability,
            current_values=current_params,
            recommended_values=DrillingParameters(**optimization_result['recommended_values']),
            expected_improvement=optimization_result['expected_improvement'],
            risk_reduction=optimization_result['risk_reduction'],
            confidence=optimization_result['confidence'],
            constraints_satisfied=optimization_result['constraints_satisfied'],
            constraint_violations=optimization_result.get('constraint_violations', []),
            optimization_method=optimization_result['optimization_method'],
            computation_time_ms=optimization_result['computation_time_ms']
        )
        
        # Store recommendation
        recommendations_store[recommendation.id] = recommendation
        
        # Publish to Kafka
        if kafka_producer:
            kafka_producer.send('rto-recommendations', value=recommendation.dict())
        
        rto_recommendations.inc()
        optimization_time = (datetime.now() - start_time).total_seconds()
        rto_optimization_time.observe(optimization_time)
        
        logger.info(f"RTO optimization completed in {optimization_time:.2f}s for {well_id}")
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/rto/recommendations/{recommendation_id}", response_model=RTORecovery)
async def get_recommendation(recommendation_id: str):
    """Get a specific RTO recommendation"""
    if recommendation_id not in recommendations_store:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return recommendations_store[recommendation_id]

@app.get("/api/v1/rto/recommendations", response_model=List[RTORecovery])
async def list_recommendations(
    well_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List RTO recommendations"""
    recommendations = list(recommendations_store.values())
    
    if well_id:
        recommendations = [r for r in recommendations if r.well_id == well_id]
    
    if status:
        recommendations = [r for r in recommendations if r.status == status]
    
    # Sort by timestamp descending
    recommendations.sort(key=lambda x: x.timestamp, reverse=True)
    
    return recommendations[:limit]

@app.post("/api/v1/rto/recommendations/{recommendation_id}/approve", response_model=RTORecovery)
async def approve_recommendation(
    recommendation_id: str,
    approved_by: str = Field(..., description="User who approved the recommendation")
):
    """
    Approve RTO recommendation (FR-4.4)
    
    User approval is required before applying RTO recommendations.
    """
    if recommendation_id not in recommendations_store:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    recommendation = recommendations_store[recommendation_id]
    
    if recommendation.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation already {recommendation.status}")
    
    recommendation.status = "approved"
    recommendation.approved_by = approved_by
    recommendation.approved_at = datetime.now()
    
    # Publish approval event
    if kafka_producer:
        kafka_producer.send('rto-approvals', value={
            'recommendation_id': recommendation_id,
            'status': 'approved',
            'approved_by': approved_by,
            'timestamp': datetime.now().isoformat()
        })
    
    rto_approved.inc()
    logger.info(f"RTO recommendation {recommendation_id} approved by {approved_by}")
    
    return recommendation

@app.post("/api/v1/rto/recommendations/{recommendation_id}/reject", response_model=RTORecovery)
async def reject_recommendation(
    recommendation_id: str,
    reason: Optional[str] = None
):
    """Reject RTO recommendation"""
    if recommendation_id not in recommendations_store:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    recommendation = recommendations_store[recommendation_id]
    
    if recommendation.status != "pending":
        raise HTTPException(status_code=400, detail=f"Recommendation already {recommendation.status}")
    
    recommendation.status = "rejected"
    
    # Publish rejection event
    if kafka_producer:
        kafka_producer.send('rto-approvals', value={
            'recommendation_id': recommendation_id,
            'status': 'rejected',
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
    
    rto_rejected.inc()
    logger.info(f"RTO recommendation {recommendation_id} rejected")
    
    return recommendation

@app.post("/api/v1/rto/recommendations/{recommendation_id}/apply")
async def apply_recommendation(recommendation_id: str):
    """Apply approved RTO recommendation to drilling system"""
    if recommendation_id not in recommendations_store:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    recommendation = recommendations_store[recommendation_id]
    
    if recommendation.status != "approved":
        raise HTTPException(status_code=400, detail="Recommendation must be approved before applying")
    
    # Update status
    recommendation.status = "applied"
    
    # Publish to control system (via Kafka)
    if kafka_producer:
        kafka_producer.send('rto-setpoints', value={
            'well_id': recommendation.well_id,
            'setpoints': recommendation.recommended_values.dict(),
            'recommendation_id': recommendation_id,
            'timestamp': datetime.now().isoformat()
        })
    
    logger.info(f"RTO recommendation {recommendation_id} applied to {recommendation.well_id}")
    
    return {
        "message": "Recommendation applied successfully",
        "recommendation_id": recommendation_id,
        "setpoints": recommendation.recommended_values.dict()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )

