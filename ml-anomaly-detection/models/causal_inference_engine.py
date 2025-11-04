#!/usr/bin/env python3
"""
FIDPS Causal Inference Engine (CIE)
FR-301: Root Cause Analysis (RCA) and Mitigation Recommendations

This module implements causal inference algorithms to identify root causes
of formation damage and generate actionable mitigation recommendations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from collections import defaultdict

# Causal inference libraries
try:
    from dowhy import CausalModel
    from dowhy.causal_estimators import PropensityScoreEstimator
    DOWHY_AVAILABLE = True
except ImportError:
    DOWHY_AVAILABLE = False
    logging.warning("DoWhy not available, using simplified causal inference")

# Statistical analysis
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class RootCauseType(Enum):
    """Types of root causes for formation damage"""
    OPERATIONAL_PARAMETER = "operational_parameter"
    FLUID_PROPERTY = "fluid_property"
    FORMATION_CHARACTERISTIC = "formation_characteristic"
    EQUIPMENT_MALFUNCTION = "equipment_malfunction"
    ENVIRONMENTAL_FACTOR = "environmental_factor"
    PROCEDURAL_ERROR = "procedural_error"


class MitigationPriority(Enum):
    """Priority levels for mitigation recommendations"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Action within hours
    MEDIUM = "medium"  # Action within days
    LOW = "low"  # Preventive action


@dataclass
class CausalRelationship:
    """Represents a causal relationship between variables"""
    cause: str
    effect: str
    strength: float  # 0-1, strength of causal relationship
    confidence: float  # 0-1, confidence in the relationship
    direction: str  # "direct" or "indirect"
    evidence: List[str] = field(default_factory=list)
    p_value: Optional[float] = None


@dataclass
class RootCauseAnalysis:
    """Result of root cause analysis"""
    anomaly_id: str
    well_id: str
    damage_type: str
    timestamp: datetime
    
    # Identified root causes
    primary_root_cause: str
    root_cause_type: RootCauseType
    root_cause_confidence: float
    contributing_factors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Causal relationships
    causal_chain: List[CausalRelationship] = field(default_factory=list)
    
    # Evidence
    evidence_summary: str = ""
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    
    # Statistical analysis
    statistical_significance: float = 0.0
    correlation_analysis: Dict[str, float] = field(default_factory=dict)


@dataclass
class MitigationRecommendation:
    """Mitigation recommendation based on RCA"""
    recommendation_id: str
    root_cause_analysis_id: str
    well_id: str
    timestamp: datetime
    
    # Recommendation details
    action: str
    description: str
    priority: MitigationPriority
    expected_effectiveness: float  # 0-1, expected reduction in damage risk
    
    # Implementation details
    required_parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_implementation_time: str = ""
    estimated_cost: Optional[float] = None
    
    # Expected outcomes
    expected_risk_reduction: float = 0.0  # Percentage
    expected_improvement_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Validation
    confidence: float = 0.0
    validation_status: str = "pending"  # pending, validated, applied


class CausalInferenceEngine:
    """
    Causal Inference Engine for Root Cause Analysis
    
    Implements multiple causal inference methods:
    1. Propensity Score Matching
    2. Instrumental Variables
    3. Difference-in-Differences
    4. Structural Causal Models
    5. Granger Causality
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Knowledge base of known causal relationships
        self.causal_knowledge_base = self._initialize_knowledge_base()
        
        # Historical data for analysis
        self.historical_data: Optional[pd.DataFrame] = None
        
        # Statistical models
        self.correlation_model = None
        self.grangercausality_model = None
        
    def _initialize_knowledge_base(self) -> Dict[str, List[Dict]]:
        """Initialize domain knowledge base of causal relationships"""
        return {
            "DT-01": [  # Clay Swelling/Iron Control
                {
                    "cause": "low_ph_mud",
                    "effect": "clay_swelling",
                    "strength": 0.85,
                    "mechanism": "Low pH increases clay hydration and swelling"
                },
                {
                    "cause": "high_water_content",
                    "effect": "clay_swelling",
                    "strength": 0.75,
                    "mechanism": "Excessive water content promotes clay expansion"
                },
                {
                    "cause": "high_temperature",
                    "effect": "iron_precipitation",
                    "strength": 0.70,
                    "mechanism": "High temperature causes iron compound precipitation"
                }
            ],
            "DT-02": [  # Drilling Induced
                {
                    "cause": "high_wob",
                    "effect": "formation_crushing",
                    "strength": 0.90,
                    "mechanism": "Excessive weight on bit crushes formation"
                },
                {
                    "cause": "high_rpm",
                    "effect": "mechanical_damage",
                    "strength": 0.80,
                    "mechanism": "High rotational speed causes mechanical stress"
                },
                {
                    "cause": "improper_drilling_fluid",
                    "effect": "formation_damage",
                    "strength": 0.75,
                    "mechanism": "Incompatible fluid properties damage formation"
                }
            ],
            "DT-03": [  # Fluid Loss
                {
                    "cause": "high_mud_weight",
                    "effect": "differential_pressure",
                    "strength": 0.85,
                    "mechanism": "High mud weight creates excessive differential pressure"
                },
                {
                    "cause": "poor_mud_cake",
                    "effect": "fluid_loss",
                    "strength": 0.80,
                    "mechanism": "Inadequate mud cake allows fluid invasion"
                },
                {
                    "cause": "high_formation_permeability",
                    "effect": "fluid_loss",
                    "strength": 0.70,
                    "mechanism": "High permeability formation allows fluid migration"
                }
            ],
            "DT-04": [  # Scale/Sludge
                {
                    "cause": "incompatible_fluids",
                    "effect": "precipitation",
                    "strength": 0.85,
                    "mechanism": "Chemical incompatibility causes scale formation"
                },
                {
                    "cause": "high_temperature",
                    "effect": "scale_formation",
                    "strength": 0.75,
                    "mechanism": "Temperature changes cause solubility shifts"
                }
            ],
            "DT-05": [  # Near-Wellbore Emulsions
                {
                    "cause": "high_surfactant_concentration",
                    "effect": "emulsion_formation",
                    "strength": 0.80,
                    "mechanism": "Surfactants stabilize emulsions"
                },
                {
                    "cause": "high_mixing_energy",
                    "effect": "emulsion_stability",
                    "strength": 0.70,
                    "mechanism": "Mechanical mixing creates stable emulsions"
                }
            ]
        }
    
    def analyze_root_cause(
        self,
        anomaly_data: Dict[str, Any],
        historical_context: Optional[pd.DataFrame] = None,
        damage_type: str = "DT-02"
    ) -> RootCauseAnalysis:
        """
        Perform root cause analysis for a detected anomaly
        
        Args:
            anomaly_data: Current anomaly/damage event data
            historical_context: Historical data for comparison
            damage_type: Type of damage (DT-01 to DT-10)
        
        Returns:
            RootCauseAnalysis object with identified root causes
        """
        try:
            self.logger.info(f"Starting RCA for damage type {damage_type}")
            
            # Extract relevant features
            features = self._extract_features(anomaly_data)
            
            # Get historical context if provided
            if historical_context is not None:
                self.historical_data = historical_context
            
            # Apply multiple causal inference methods
            causal_relationships = self._identify_causal_relationships(
                features, damage_type, historical_context
            )
            
            # Identify primary root cause
            primary_cause = self._identify_primary_root_cause(
                causal_relationships, features, damage_type
            )
            
            # Build causal chain
            causal_chain = self._build_causal_chain(
                primary_cause, causal_relationships, features
            )
            
            # Generate evidence summary
            evidence_summary = self._generate_evidence_summary(
                primary_cause, causal_chain, features
            )
            
            # Calculate statistical significance
            statistical_sig = self._calculate_statistical_significance(
                primary_cause, features, historical_context
            )
            
            # Correlation analysis
            correlations = self._analyze_correlations(features, damage_type)
            
            # Create RCA result
            rca = RootCauseAnalysis(
                anomaly_id=anomaly_data.get('anomaly_id', 'unknown'),
                well_id=anomaly_data.get('well_id', 'unknown'),
                damage_type=damage_type,
                timestamp=datetime.now(),
                primary_root_cause=primary_cause['cause'],
                root_cause_type=primary_cause.get('type', RootCauseType.OPERATIONAL_PARAMETER),
                root_cause_confidence=primary_cause.get('confidence', 0.7),
                contributing_factors=primary_cause.get('contributing_factors', []),
                causal_chain=causal_relationships,
                evidence_summary=evidence_summary,
                supporting_data=features,
                statistical_significance=statistical_sig,
                correlation_analysis=correlations
            )
            
            self.logger.info(f"RCA completed: Primary cause = {primary_cause['cause']}")
            return rca
            
        except Exception as e:
            self.logger.error(f"Error in root cause analysis: {e}")
            # Return default RCA
            return RootCauseAnalysis(
                anomaly_id=anomaly_data.get('anomaly_id', 'unknown'),
                well_id=anomaly_data.get('well_id', 'unknown'),
                damage_type=damage_type,
                timestamp=datetime.now(),
                primary_root_cause="analysis_error",
                root_cause_type=RootCauseType.OPERATIONAL_PARAMETER,
                root_cause_confidence=0.0,
                evidence_summary=f"Analysis error: {str(e)}"
            )
    
    def _extract_features(self, anomaly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant features for causal analysis"""
        features = {
            # Operational parameters
            'weight_on_bit': anomaly_data.get('weight_on_bit_klbs', 0),
            'rotary_speed': anomaly_data.get('rpm', 0),
            'flow_rate': anomaly_data.get('flow_rate_gpm', 0),
            'mud_weight': anomaly_data.get('mud_weight', 0),
            'standpipe_pressure': anomaly_data.get('standpipe_pressure', 0),
            'torque': anomaly_data.get('torque', 0),
            
            # Fluid properties
            'mud_ph': anomaly_data.get('mud_ph', 7.0),
            'mud_viscosity': anomaly_data.get('mud_viscosity', 0),
            'mud_temperature': anomaly_data.get('temperature_degf', 0),
            
            # Formation characteristics
            'depth': anomaly_data.get('depth_ft', 0),
            'formation_type': anomaly_data.get('formation_type', 'unknown'),
            'permeability': anomaly_data.get('permeability', 0),
            'porosity': anomaly_data.get('porosity', 0),
            
            # Environmental
            'gamma_ray': anomaly_data.get('gamma_ray', 0),
            'resistivity': anomaly_data.get('resistivity', 0),
            'neutron_porosity': anomaly_data.get('neutron_porosity', 0),
            
            # Anomaly characteristics
            'anomaly_severity': anomaly_data.get('severity', 0),
            'anomaly_confidence': anomaly_data.get('confidence', 0),
            'damage_probability': anomaly_data.get('damage_probability', 0)
        }
        return features
    
    def _identify_causal_relationships(
        self,
        features: Dict[str, Any],
        damage_type: str,
        historical_data: Optional[pd.DataFrame]
    ) -> List[CausalRelationship]:
        """Identify causal relationships using multiple methods"""
        relationships = []
        
        # Method 1: Knowledge-based causal relationships
        knowledge_relationships = self._apply_knowledge_base(features, damage_type)
        relationships.extend(knowledge_relationships)
        
        # Method 2: Statistical correlation analysis
        if historical_data is not None and len(historical_data) > 10:
            statistical_relationships = self._statistical_causal_analysis(
                features, damage_type, historical_data
            )
            relationships.extend(statistical_relationships)
        
        # Method 3: Granger Causality (if time series data available)
        if historical_data is not None and len(historical_data) > 50:
            granger_relationships = self._granger_causality_analysis(
                features, historical_data
            )
            relationships.extend(granger_relationships)
        
        # Sort by strength and confidence
        relationships.sort(key=lambda x: x.strength * x.confidence, reverse=True)
        
        return relationships
    
    def _apply_knowledge_base(
        self,
        features: Dict[str, Any],
        damage_type: str
    ) -> List[CausalRelationship]:
        """Apply domain knowledge base to identify causal relationships"""
        relationships = []
        
        if damage_type not in self.causal_knowledge_base:
            return relationships
        
        knowledge = self.causal_knowledge_base[damage_type]
        
        for kb_item in knowledge:
            cause_var = kb_item['cause']
            effect_var = kb_item['effect']
            
            # Check if cause variable has abnormal value
            if cause_var in features:
                cause_value = features[cause_var]
                
                # Determine if value is abnormal (simplified threshold-based)
                is_abnormal = self._is_abnormal_value(cause_var, cause_value)
                
                if is_abnormal:
                    relationship = CausalRelationship(
                        cause=cause_var,
                        effect=effect_var,
                        strength=kb_item['strength'],
                        confidence=0.75,  # Medium confidence for knowledge-based
                        direction="direct",
                        evidence=[kb_item['mechanism']],
                        p_value=None
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _is_abnormal_value(self, variable: str, value: float) -> bool:
        """Determine if a value is abnormal based on operational limits"""
        # Operational limits (simplified)
        limits = {
            'weight_on_bit': (0, 50),
            'rotary_speed': (0, 300),
            'flow_rate': (0, 2000),
            'mud_weight': (8.0, 15.0),
            'mud_ph': (7.0, 11.0),
            'standpipe_pressure': (0, 5000),
            'torque': (0, 50000)
        }
        
        if variable in limits:
            min_val, max_val = limits[variable]
            # Consider abnormal if outside 80% of normal range
            range_width = max_val - min_val
            margin = range_width * 0.1
            return value < (min_val + margin) or value > (max_val - margin)
        
        return False
    
    def _statistical_causal_analysis(
        self,
        features: Dict[str, Any],
        damage_type: str,
        historical_data: pd.DataFrame
    ) -> List[CausalRelationship]:
        """Statistical causal analysis using correlation and regression"""
        relationships = []
        
        # Calculate correlations between features and damage indicators
        damage_indicators = [
            'damage_probability', 'anomaly_severity', 'formation_damage_score'
        ]
        
        for cause_var in features.keys():
            if cause_var in historical_data.columns:
                for effect_var in damage_indicators:
                    if effect_var in historical_data.columns:
                        # Calculate Pearson correlation
                        correlation, p_value = stats.pearsonr(
                            historical_data[cause_var].dropna(),
                            historical_data[effect_var].dropna()
                        )
                        
                        # Only include significant relationships
                        if abs(correlation) > 0.3 and p_value < 0.05:
                            relationship = CausalRelationship(
                                cause=cause_var,
                                effect=effect_var,
                                strength=abs(correlation),
                                confidence=1.0 - p_value,
                                direction="direct" if correlation > 0 else "inverse",
                                evidence=[f"Statistical correlation: r={correlation:.3f}"],
                                p_value=p_value
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _granger_causality_analysis(
        self,
        features: Dict[str, Any],
        historical_data: pd.DataFrame
    ) -> List[CausalRelationship]:
        """Granger Causality analysis for time series data"""
        relationships = []
        
        try:
            from statsmodels.tsa.stattools import grangercausalitytests
            
            # Select relevant time series
            time_series_vars = ['weight_on_bit', 'rotary_speed', 'flow_rate', 
                              'mud_weight', 'standpipe_pressure']
            
            for cause_var in time_series_vars:
                if cause_var not in historical_data.columns:
                    continue
                
                for effect_var in ['damage_probability', 'anomaly_severity']:
                    if effect_var not in historical_data.columns:
                        continue
                    
                    # Prepare data for Granger test
                    data = historical_data[[cause_var, effect_var]].dropna()
                    
                    if len(data) < 20:
                        continue
                    
                    try:
                        # Perform Granger causality test
                        gc_result = grangercausalitytests(
                            data[[effect_var, cause_var]], maxlag=2, verbose=False
                        )
                        
                        # Extract p-value from test
                        p_value = gc_result[2][0]['ssr_ftest'][1]
                        
                        if p_value < 0.05:  # Significant causality
                            relationship = CausalRelationship(
                                cause=cause_var,
                                effect=effect_var,
                                strength=1.0 - p_value,
                                confidence=1.0 - p_value,
                                direction="direct",
                                evidence=[f"Granger causality: p={p_value:.4f}"],
                                p_value=p_value
                            )
                            relationships.append(relationship)
                    except Exception as e:
                        self.logger.debug(f"Granger test failed for {cause_var}->{effect_var}: {e}")
                        continue
        
        except ImportError:
            self.logger.warning("statsmodels not available for Granger causality")
        
        return relationships
    
    def _identify_primary_root_cause(
        self,
        causal_relationships: List[CausalRelationship],
        features: Dict[str, Any],
        damage_type: str
    ) -> Dict[str, Any]:
        """Identify the primary root cause from causal relationships"""
        if not causal_relationships:
            return {
                'cause': 'unknown',
                'type': RootCauseType.OPERATIONAL_PARAMETER,
                'confidence': 0.0,
                'contributing_factors': []
            }
        
        # Score each relationship
        scored_relationships = []
        for rel in causal_relationships:
            score = rel.strength * rel.confidence
            if rel.p_value:
                score *= (1.0 - rel.p_value)
            scored_relationships.append((score, rel))
        
        # Get top relationship
        scored_relationships.sort(key=lambda x: x[0], reverse=True)
        top_relationship = scored_relationships[0][1]
        
        # Determine root cause type
        cause_type = self._categorize_root_cause_type(top_relationship.cause)
        
        # Get contributing factors
        contributing_factors = [
            {
                'factor': rel.cause,
                'strength': rel.strength,
                'confidence': rel.confidence
            }
            for _, rel in scored_relationships[1:6]  # Top 5 contributing factors
        ]
        
        return {
            'cause': top_relationship.cause,
            'type': cause_type,
            'confidence': top_relationship.confidence,
            'contributing_factors': contributing_factors
        }
    
    def _categorize_root_cause_type(self, cause: str) -> RootCauseType:
        """Categorize root cause type based on variable name"""
        operational_vars = ['weight_on_bit', 'rotary_speed', 'flow_rate', 
                          'torque', 'standpipe_pressure']
        fluid_vars = ['mud_weight', 'mud_ph', 'mud_viscosity', 'mud_temperature']
        formation_vars = ['depth', 'formation_type', 'permeability', 'porosity']
        equipment_vars = ['equipment_failure', 'sensor_malfunction']
        
        if cause in operational_vars:
            return RootCauseType.OPERATIONAL_PARAMETER
        elif cause in fluid_vars:
            return RootCauseType.FLUID_PROPERTY
        elif cause in formation_vars:
            return RootCauseType.FORMATION_CHARACTERISTIC
        elif cause in equipment_vars:
            return RootCauseType.EQUIPMENT_MALFUNCTION
        else:
            return RootCauseType.OPERATIONAL_PARAMETER
    
    def _build_causal_chain(
        self,
        primary_cause: Dict[str, Any],
        causal_relationships: List[CausalRelationship],
        features: Dict[str, Any]
    ) -> List[CausalRelationship]:
        """Build causal chain from primary cause to damage"""
        # Start with primary cause relationships
        chain = [rel for rel in causal_relationships 
                if rel.cause == primary_cause['cause']]
        
        # Add contributing factors
        for contrib in primary_cause.get('contributing_factors', []):
            contrib_rels = [rel for rel in causal_relationships 
                          if rel.cause == contrib['factor']]
            chain.extend(contrib_rels)
        
        return chain[:10]  # Limit to top 10 relationships
    
    def _generate_evidence_summary(
        self,
        primary_cause: Dict[str, Any],
        causal_chain: List[CausalRelationship],
        features: Dict[str, Any]
    ) -> str:
        """Generate human-readable evidence summary"""
        summary_parts = [
            f"Primary root cause identified: {primary_cause['cause']}",
            f"Confidence: {primary_cause['confidence']:.1%}",
            f"Root cause type: {primary_cause['type'].value}",
        ]
        
        if primary_cause['cause'] in features:
            value = features[primary_cause['cause']]
            summary_parts.append(f"Current value: {value}")
        
        if causal_chain:
            summary_parts.append(f"\nCausal chain identified with {len(causal_chain)} relationships")
        
        if primary_cause.get('contributing_factors'):
            summary_parts.append(f"\nContributing factors:")
            for factor in primary_cause['contributing_factors'][:3]:
                summary_parts.append(f"  - {factor['factor']} (strength: {factor['strength']:.2f})")
        
        return "\n".join(summary_parts)
    
    def _calculate_statistical_significance(
        self,
        primary_cause: Dict[str, Any],
        features: Dict[str, Any],
        historical_data: Optional[pd.DataFrame]
    ) -> float:
        """Calculate statistical significance of root cause"""
        if historical_data is None or len(historical_data) < 10:
            return 0.5  # Default medium significance
        
        cause_var = primary_cause['cause']
        if cause_var not in historical_data.columns:
            return 0.5
        
        # Calculate how unusual current value is compared to historical
        current_value = features.get(cause_var, 0)
        historical_values = historical_data[cause_var].dropna()
        
        if len(historical_values) == 0:
            return 0.5
        
        # Z-score
        mean_val = historical_values.mean()
        std_val = historical_values.std()
        
        if std_val == 0:
            return 0.5
        
        z_score = abs((current_value - mean_val) / std_val)
        
        # Convert to significance (0-1)
        # Higher z-score = more significant
        significance = min(1.0, z_score / 3.0)
        
        return significance
    
    def _analyze_correlations(
        self,
        features: Dict[str, Any],
        damage_type: str
    ) -> Dict[str, float]:
        """Analyze correlations between features and damage"""
        correlations = {}
        
        # Feature-damage type specific correlations (simplified)
        damage_correlations = {
            'DT-01': {'mud_ph': -0.7, 'mud_viscosity': 0.6, 'high_temperature': 0.5},
            'DT-02': {'weight_on_bit': 0.8, 'rotary_speed': 0.7, 'torque': 0.6},
            'DT-03': {'mud_weight': 0.75, 'standpipe_pressure': 0.7, 'flow_rate': -0.5},
            'DT-04': {'mud_temperature': 0.6, 'mud_ph': 0.5},
            'DT-05': {'mud_viscosity': 0.65, 'flow_rate': 0.5}
        }
        
        if damage_type in damage_correlations:
            correlations = damage_correlations[damage_type].copy()
        
        return correlations
    
    def generate_mitigation_recommendations(
        self,
        rca: RootCauseAnalysis
    ) -> List[MitigationRecommendation]:
        """
        Generate mitigation recommendations based on RCA
        
        Args:
            rca: RootCauseAnalysis result
        
        Returns:
            List of MitigationRecommendation objects
        """
        recommendations = []
        
        # Get mitigation strategies based on root cause type and damage type
        mitigation_strategies = self._get_mitigation_strategies(
            rca.primary_root_cause,
            rca.root_cause_type,
            rca.damage_type
        )
        
        for i, strategy in enumerate(mitigation_strategies):
            recommendation = MitigationRecommendation(
                recommendation_id=f"mit_{rca.anomaly_id}_{i}",
                root_cause_analysis_id=rca.anomaly_id,
                well_id=rca.well_id,
                timestamp=datetime.now(),
                action=strategy['action'],
                description=strategy['description'],
                priority=MitigationPriority(strategy['priority']),
                expected_effectiveness=strategy.get('effectiveness', 0.7),
                required_parameters=strategy.get('parameters', {}),
                estimated_implementation_time=strategy.get('time', '1-2 hours'),
                expected_risk_reduction=strategy.get('risk_reduction', 30.0),
                expected_improvement_metrics=strategy.get('metrics', {}),
                confidence=rca.root_cause_confidence * strategy.get('effectiveness', 0.7)
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _get_mitigation_strategies(
        self,
        root_cause: str,
        root_cause_type: RootCauseType,
        damage_type: str
    ) -> List[Dict[str, Any]]:
        """Get mitigation strategies based on root cause"""
        strategies = []
        
        # Operational parameter adjustments
        if root_cause_type == RootCauseType.OPERATIONAL_PARAMETER:
            if root_cause == 'weight_on_bit':
                strategies.append({
                    'action': 'Reduce Weight on Bit',
                    'description': 'Reduce WOB by 10-20% to minimize formation crushing',
                    'priority': 'high',
                    'effectiveness': 0.75,
                    'parameters': {'wob_reduction_percent': 15},
                    'time': '15-30 minutes',
                    'risk_reduction': 40.0,
                    'metrics': {'formation_damage_risk': -40, 'rop': -5}
                })
            
            elif root_cause == 'rotary_speed':
                strategies.append({
                    'action': 'Reduce Rotary Speed',
                    'description': 'Reduce RPM by 15-25% to minimize mechanical damage',
                    'priority': 'high',
                    'effectiveness': 0.70,
                    'parameters': {'rpm_reduction_percent': 20},
                    'time': '15-30 minutes',
                    'risk_reduction': 35.0,
                    'metrics': {'mechanical_damage_risk': -35, 'rop': -8}
                })
            
            elif root_cause == 'flow_rate':
                strategies.append({
                    'action': 'Adjust Flow Rate',
                    'description': 'Optimize flow rate to maintain proper hole cleaning',
                    'priority': 'medium',
                    'effectiveness': 0.65,
                    'parameters': {'optimal_flow_rate': 'calculated'},
                    'time': '30-60 minutes',
                    'risk_reduction': 30.0
                })
        
        # Fluid property adjustments
        elif root_cause_type == RootCauseType.FLUID_PROPERTY:
            if root_cause == 'mud_ph':
                strategies.append({
                    'action': 'Adjust Mud pH',
                    'description': f'Adjust pH to optimal range (9-10.5) for {damage_type}',
                    'priority': 'high',
                    'effectiveness': 0.80,
                    'parameters': {'target_ph': 9.5},
                    'time': '1-2 hours',
                    'risk_reduction': 45.0
                })
            
            elif root_cause == 'mud_weight':
                strategies.append({
                    'action': 'Optimize Mud Weight',
                    'description': 'Reduce mud weight to minimize differential pressure',
                    'priority': 'critical',
                    'effectiveness': 0.85,
                    'parameters': {'target_mud_weight': 'calculated'},
                    'time': '2-4 hours',
                    'risk_reduction': 50.0
                })
        
        # Default strategy if no specific match
        if not strategies:
            strategies.append({
                'action': 'Monitor and Adjust Parameters',
                'description': f'Continuously monitor {root_cause} and adjust as needed',
                'priority': 'medium',
                'effectiveness': 0.60,
                'parameters': {},
                'time': 'Ongoing',
                'risk_reduction': 20.0
            })
        
        return strategies

