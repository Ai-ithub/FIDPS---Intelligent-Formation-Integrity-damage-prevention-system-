#!/usr/bin/env python3
"""
FIDPS Digital Twin / Simulation Model
FR-401: Digital Twin Validation for RTO recommendations

This module implements a physics-based simulation model to validate
RTO recommendations before applying them to the actual drilling system.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

# Physics simulation libraries
from scipy.integrate import odeint
from scipy.optimize import fsolve

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of digital twin validation"""
    SAFE = "safe"  # Safe to implement
    UNSAFE = "unsafe"  # Unsafe - do not implement
    WARNING = "warning"  # Warning - implement with caution
    FAILED = "failed"  # Validation failed (simulation error)


@dataclass
class DigitalTwinState:
    """State of the digital twin model"""
    timestamp: datetime
    
    # Drilling parameters
    weight_on_bit: float
    rotary_speed: float
    flow_rate: float
    mud_weight: float
    depth: float
    
    # Formation properties
    formation_pressure: float
    formation_temperature: float
    formation_porosity: float
    formation_permeability: float
    
    # Wellbore state
    wellbore_pressure: float
    wellbore_temperature: float
    mud_cake_thickness: float
    
    # Damage indicators
    damage_risk_score: float = 0.0
    formation_damage_probability: float = 0.0
    integrity_status: str = "normal"


@dataclass
class ValidationResult:
    """Result of digital twin validation"""
    recommendation_id: str
    timestamp: datetime
    
    # Validation status
    status: ValidationStatus
    validation_confidence: float  # 0-1
    
    # Simulation results
    predicted_damage_risk: float
    predicted_formation_damage_probability: float
    predicted_operational_metrics: Dict[str, float]
    
    # Safety checks
    safety_checks_passed: bool
    safety_violations: List[str]
    constraint_violations: List[str]
    
    # Comparison with current state
    risk_change: float  # Percentage change
    efficiency_change: float  # Percentage change
    
    # Recommendations
    recommendation: str  # "approve", "reject", "modify"
    modification_suggestions: List[str] = None
    
    # Simulation metadata
    simulation_time_ms: float
    simulation_accuracy: float = 0.0


class DigitalTwinSimulator:
    """
    Physics-based drilling simulation model
    
    Implements:
    1. Drilling mechanics model
    2. Formation-fluid interaction
    3. Pressure-temperature dynamics
    4. Damage prediction model
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Model parameters
        self.model_params = self._initialize_model_parameters()
        
        # Current state
        self.current_state: Optional[DigitalTwinState] = None
        
        # Historical states for validation
        self.state_history: List[DigitalTwinState] = []
    
    def _initialize_model_parameters(self) -> Dict[str, float]:
        """Initialize physics model parameters"""
        return {
            # Drilling mechanics
            'drill_bit_efficiency': 0.85,
            'friction_coefficient': 0.3,
            'rock_strength': 50.0,  # MPa
            
            # Fluid dynamics
            'mud_density': 1200.0,  # kg/m³
            'mud_viscosity': 0.05,  # Pa·s
            'annular_flow_area': 0.1,  # m²
            
            # Formation properties (default)
            'formation_pressure_gradient': 0.01,  # MPa/m
            'formation_temperature_gradient': 0.03,  # °C/m
            'formation_porosity': 0.15,
            'formation_permeability': 100.0,  # mD
            
            # Damage thresholds
            'critical_differential_pressure': 5.0,  # MPa
            'critical_flow_velocity': 2.0,  # m/s
            'critical_temperature': 150.0,  # °C
        }
    
    def initialize_state(
        self,
        current_params: Dict[str, Any],
        formation_props: Optional[Dict[str, Any]] = None
    ) -> DigitalTwinState:
        """
        Initialize digital twin state from current drilling parameters
        
        Args:
            current_params: Current drilling parameters
            formation_props: Formation properties (optional)
        
        Returns:
            DigitalTwinState object
        """
        formation = formation_props or {}
        
        state = DigitalTwinState(
            timestamp=datetime.now(),
            weight_on_bit=current_params.get('weight_on_bit', 20.0),
            rotary_speed=current_params.get('rotary_speed', 100.0),
            flow_rate=current_params.get('flow_rate', 500.0),
            mud_weight=current_params.get('mud_weight', 10.0),
            depth=current_params.get('depth', 2000.0),
            formation_pressure=formation.get('formation_pressure', 
                                           current_params.get('depth', 2000) * 
                                           self.model_params['formation_pressure_gradient']),
            formation_temperature=formation.get('formation_temperature',
                                               current_params.get('depth', 2000) * 
                                               self.model_params['formation_temperature_gradient']),
            formation_porosity=formation.get('porosity', self.model_params['formation_porosity']),
            formation_permeability=formation.get('permeability', 
                                                self.model_params['formation_permeability']),
            wellbore_pressure=self._calculate_wellbore_pressure(current_params),
            wellbore_temperature=self._calculate_wellbore_temperature(current_params),
            mud_cake_thickness=0.001  # Initial mud cake thickness (m)
        )
        
        # Calculate initial damage indicators
        state.damage_risk_score = self._calculate_damage_risk(state)
        state.formation_damage_probability = self._calculate_damage_probability(state)
        
        self.current_state = state
        return state
    
    def _calculate_wellbore_pressure(self, params: Dict[str, Any]) -> float:
        """Calculate wellbore pressure"""
        depth = params.get('depth', 2000.0)
        mud_weight = params.get('mud_weight', 10.0)
        flow_rate = params.get('flow_rate', 500.0)
        
        # Hydrostatic pressure
        hydrostatic = depth * mud_weight * 0.052  # psi
        
        # Frictional pressure (simplified)
        frictional = flow_rate * 0.1  # Simplified model
        
        return hydrostatic + frictional
    
    def _calculate_wellbore_temperature(self, params: Dict[str, Any]) -> float:
        """Calculate wellbore temperature"""
        depth = params.get('depth', 2000.0)
        base_temp = 25.0  # Surface temperature °C
        
        # Geothermal gradient
        temp_gradient = self.model_params['formation_temperature_gradient']
        formation_temp = depth * temp_gradient
        
        # Frictional heating (simplified)
        rotary_speed = params.get('rotary_speed', 100.0)
        frictional_heating = rotary_speed * 0.05
        
        return formation_temp + base_temp + frictional_heating
    
    def _calculate_damage_risk(self, state: DigitalTwinState) -> float:
        """Calculate formation damage risk score (0-1)"""
        risk_factors = []
        
        # Differential pressure risk
        diff_pressure = state.wellbore_pressure - state.formation_pressure
        if diff_pressure > self.model_params['critical_differential_pressure']:
            risk_factors.append(0.4)
        elif diff_pressure > 0:
            risk_factors.append(0.2 * (diff_pressure / self.model_params['critical_differential_pressure']))
        
        # Flow velocity risk
        flow_velocity = state.flow_rate / (self.model_params['annular_flow_area'] * 60)
        if flow_velocity > self.model_params['critical_flow_velocity']:
            risk_factors.append(0.3)
        elif flow_velocity > 0:
            risk_factors.append(0.15 * (flow_velocity / self.model_params['critical_flow_velocity']))
        
        # Temperature risk
        if state.wellbore_temperature > self.model_params['critical_temperature']:
            risk_factors.append(0.2)
        elif state.wellbore_temperature > 100:
            risk_factors.append(0.1 * ((state.wellbore_temperature - 100) / 50))
        
        # WOB/RPM risk (mechanical damage)
        wob_risk = min(0.1, state.weight_on_bit / 100.0)
        rpm_risk = min(0.1, state.rotary_speed / 300.0)
        risk_factors.append(wob_risk + rpm_risk)
        
        # Combine risk factors
        total_risk = min(1.0, sum(risk_factors))
        return total_risk
    
    def _calculate_damage_probability(self, state: DigitalTwinState) -> float:
        """Calculate probability of formation damage (0-1)"""
        # Base probability from damage risk
        base_prob = state.damage_risk_score * 0.7
        
        # Adjust based on formation properties
        if state.formation_permeability > 500:  # High permeability
            base_prob += 0.1
        
        if state.formation_porosity > 0.25:  # High porosity
            base_prob += 0.1
        
        return min(1.0, base_prob)
    
    def simulate_parameters(
        self,
        recommended_params: Dict[str, Any],
        simulation_duration: float = 3600.0  # seconds (1 hour)
    ) -> DigitalTwinState:
        """
        Simulate drilling with recommended parameters
        
        Args:
            recommended_params: Recommended drilling parameters
            simulation_duration: Duration of simulation (seconds)
        
        Returns:
            Final DigitalTwinState after simulation
        """
        if not self.current_state:
            raise ValueError("Digital twin state not initialized")
        
        # Create new state with recommended parameters
        new_params = {
            'weight_on_bit': recommended_params.get('weight_on_bit', self.current_state.weight_on_bit),
            'rotary_speed': recommended_params.get('rotary_speed', self.current_state.rotary_speed),
            'flow_rate': recommended_params.get('flow_rate', self.current_state.flow_rate),
            'mud_weight': recommended_params.get('mud_weight', self.current_state.mud_weight),
            'depth': self.current_state.depth  # Depth doesn't change in short simulation
        }
        
        # Initialize simulation state
        sim_state = DigitalTwinState(
            timestamp=self.current_state.timestamp,
            weight_on_bit=new_params['weight_on_bit'],
            rotary_speed=new_params['rotary_speed'],
            flow_rate=new_params['flow_rate'],
            mud_weight=new_params['mud_weight'],
            depth=new_params['depth'],
            formation_pressure=self.current_state.formation_pressure,
            formation_temperature=self.current_state.formation_temperature,
            formation_porosity=self.current_state.formation_porosity,
            formation_permeability=self.current_state.formation_permeability,
            wellbore_pressure=self._calculate_wellbore_pressure(new_params),
            wellbore_temperature=self._calculate_wellbore_temperature(new_params),
            mud_cake_thickness=self.current_state.mud_cake_thickness
        )
        
        # Run simulation (simplified - single time step)
        # In production, this would be a time-series simulation
        sim_state.damage_risk_score = self._calculate_damage_risk(sim_state)
        sim_state.formation_damage_probability = self._calculate_damage_probability(sim_state)
        
        # Update mud cake (simplified model)
        sim_state.mud_cake_thickness = self._update_mud_cake(
            sim_state, simulation_duration
        )
        
        # Determine integrity status
        if sim_state.damage_risk_score > 0.7:
            sim_state.integrity_status = "critical"
        elif sim_state.damage_risk_score > 0.4:
            sim_state.integrity_status = "warning"
        else:
            sim_state.integrity_status = "normal"
        
        return sim_state
    
    def _update_mud_cake(
        self,
        state: DigitalTwinState,
        duration: float
    ) -> float:
        """Update mud cake thickness based on fluid loss"""
        # Simplified mud cake growth model
        diff_pressure = state.wellbore_pressure - state.formation_pressure
        
        if diff_pressure > 0:
            # Mud cake grows with time and pressure
            growth_rate = diff_pressure * 1e-6  # m/s per MPa
            new_thickness = state.mud_cake_thickness + growth_rate * duration
            return min(0.01, new_thickness)  # Max 1 cm
        
        return state.mud_cake_thickness
    
    def validate_recommendation(
        self,
        recommendation_id: str,
        recommended_params: Dict[str, Any],
        damage_type: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate RTO recommendation using digital twin simulation
        
        Args:
            recommendation_id: ID of the recommendation
            recommended_params: Recommended drilling parameters
            damage_type: Type of damage being mitigated
        
        Returns:
            ValidationResult object
        """
        start_time = datetime.now()
        
        try:
            if not self.current_state:
                raise ValueError("Digital twin state not initialized")
            
            # Simulate with recommended parameters
            simulated_state = self.simulate_parameters(recommended_params)
            
            # Compare with current state
            risk_change = ((simulated_state.damage_risk_score - 
                          self.current_state.damage_risk_score) / 
                         max(self.current_state.damage_risk_score, 0.01)) * 100
            
            # Calculate operational metrics
            current_rop = self._estimate_rop(self.current_state)
            simulated_rop = self._estimate_rop(simulated_state)
            efficiency_change = ((simulated_rop - current_rop) / 
                               max(current_rop, 1.0)) * 100
            
            # Safety checks
            safety_checks, safety_violations = self._perform_safety_checks(simulated_state)
            
            # Constraint checks
            constraint_checks, constraint_violations = self._perform_constraint_checks(
                simulated_state, recommended_params
            )
            
            # Determine validation status
            if safety_violations:
                status = ValidationStatus.UNSAFE
                recommendation = "reject"
            elif risk_change > 5:  # Risk increased by more than 5%
                status = ValidationStatus.WARNING
                recommendation = "modify"
            elif risk_change < -10:  # Risk decreased by more than 10%
                status = ValidationStatus.SAFE
                recommendation = "approve"
            else:
                status = ValidationStatus.SAFE
                recommendation = "approve"
            
            # Generate modification suggestions if needed
            modification_suggestions = []
            if status == ValidationStatus.WARNING:
                if risk_change > 0:
                    modification_suggestions.append(
                        "Consider further reducing operational parameters to lower risk"
                    )
                if safety_violations:
                    modification_suggestions.extend(safety_violations)
            
            # Calculate validation confidence
            confidence = self._calculate_validation_confidence(
                simulated_state, safety_violations, constraint_violations
            )
            
            simulation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = ValidationResult(
                recommendation_id=recommendation_id,
                timestamp=datetime.now(),
                status=status,
                validation_confidence=confidence,
                predicted_damage_risk=simulated_state.damage_risk_score,
                predicted_formation_damage_probability=simulated_state.formation_damage_probability,
                predicted_operational_metrics={
                    'rop': simulated_rop,
                    'efficiency': efficiency_change,
                    'torque': self._estimate_torque(simulated_state),
                    'pressure': simulated_state.wellbore_pressure
                },
                safety_checks_passed=safety_checks,
                safety_violations=safety_violations,
                constraint_violations=constraint_violations,
                risk_change=risk_change,
                efficiency_change=efficiency_change,
                recommendation=recommendation,
                modification_suggestions=modification_suggestions or [],
                simulation_time_ms=simulation_time,
                simulation_accuracy=0.85  # Model accuracy (would be calibrated)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in digital twin validation: {e}")
            return ValidationResult(
                recommendation_id=recommendation_id,
                timestamp=datetime.now(),
                status=ValidationStatus.FAILED,
                validation_confidence=0.0,
                predicted_damage_risk=1.0,
                predicted_formation_damage_probability=1.0,
                predicted_operational_metrics={},
                safety_checks_passed=False,
                safety_violations=[f"Simulation error: {str(e)}"],
                constraint_violations=[],
                risk_change=0.0,
                efficiency_change=0.0,
                recommendation="reject",
                simulation_time_ms=0.0
            )
    
    def _perform_safety_checks(
        self,
        state: DigitalTwinState
    ) -> Tuple[bool, List[str]]:
        """Perform safety checks on simulated state"""
        violations = []
        
        # Check pressure limits
        if state.wellbore_pressure > 5000:  # 5000 psi limit
            violations.append("Wellbore pressure exceeds safety limit (5000 psi)")
        
        # Check temperature limits
        if state.wellbore_temperature > 200:  # 200°C limit
            violations.append("Wellbore temperature exceeds safety limit (200°C)")
        
        # Check damage risk
        if state.damage_risk_score > 0.8:
            violations.append("Formation damage risk exceeds critical threshold (80%)")
        
        # Check integrity status
        if state.integrity_status == "critical":
            violations.append("Formation integrity is in critical state")
        
        return len(violations) == 0, violations
    
    def _perform_constraint_checks(
        self,
        state: DigitalTwinState,
        params: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Perform constraint checks on recommended parameters"""
        violations = []
        
        # Check operational limits
        if params.get('weight_on_bit', 0) > 50:
            violations.append("Weight on bit exceeds maximum (50 klbs)")
        
        if params.get('rotary_speed', 0) > 300:
            violations.append("Rotary speed exceeds maximum (300 RPM)")
        
        if params.get('flow_rate', 0) > 2000:
            violations.append("Flow rate exceeds maximum (2000 GPM)")
        
        if params.get('mud_weight', 0) < 8.0 or params.get('mud_weight', 0) > 15.0:
            violations.append("Mud weight outside acceptable range (8-15 ppg)")
        
        return len(violations) == 0, violations
    
    def _estimate_rop(self, state: DigitalTwinState) -> float:
        """Estimate Rate of Penetration"""
        # Simplified ROP model
        base_rop = 30.0  # ft/hr
        
        wob_factor = 1 + (state.weight_on_bit / 50) * 0.5
        rpm_factor = 1 + (state.rotary_speed / 200) * 0.3
        flow_factor = 1 + (state.flow_rate / 500) * 0.2
        
        depth_penalty = 1 - (state.depth / 5000) * 0.2
        
        rop = base_rop * wob_factor * rpm_factor * flow_factor * depth_penalty
        
        return max(10.0, min(100.0, rop))
    
    def _estimate_torque(self, state: DigitalTwinState) -> float:
        """Estimate drilling torque"""
        # Simplified torque model
        base_torque = 10000.0  # ft-lbs
        
        wob_factor = state.weight_on_bit / 20.0
        rpm_factor = state.rotary_speed / 100.0
        friction_factor = self.model_params['friction_coefficient']
        
        torque = base_torque * wob_factor * rpm_factor * friction_factor
        
        return max(1000.0, min(50000.0, torque))
    
    def _calculate_validation_confidence(
        self,
        state: DigitalTwinState,
        safety_violations: List[str],
        constraint_violations: List[str]
    ) -> float:
        """Calculate confidence in validation result"""
        confidence = 0.9  # Base confidence
        
        # Reduce confidence if there are violations
        if safety_violations:
            confidence -= 0.3
        
        if constraint_violations:
            confidence -= 0.2
        
        # Reduce confidence if risk is high
        if state.damage_risk_score > 0.6:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))

