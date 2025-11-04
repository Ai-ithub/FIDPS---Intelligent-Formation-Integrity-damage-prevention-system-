#!/usr/bin/env python3
"""
FIDPS MLflow Integration for MLOps
FR-301: Model versioning, A/B testing, and automatic retraining triggers

This module integrates MLflow for:
1. Model versioning and tracking
2. A/B testing between model versions
3. Automatic retraining triggers
4. Model performance monitoring
"""

import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json

try:
    import mlflow
    import mlflow.sklearn
    import mlflow.tensorflow
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logging.warning("MLflow not available, MLOps features disabled")

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MLflowManager:
    """
    MLflow Manager for model lifecycle management
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if not MLFLOW_AVAILABLE:
            self.logger.warning("MLflow not available, operating in limited mode")
            self.enabled = False
            return
        
        self.enabled = True
        
        # MLflow configuration
        self.tracking_uri = config.get('mlflow_tracking_uri', 'http://localhost:5000')
        self.experiment_name = config.get('mlflow_experiment', 'fidps-anomaly-detection')
        self.registry_name = config.get('mlflow_registry', 'fidps-models')
        
        # Initialize MLflow
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = MlflowClient(tracking_uri=self.tracking_uri)
        
        # Get or create experiment
        try:
            self.experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if self.experiment is None:
                self.experiment_id = mlflow.create_experiment(self.experiment_name)
                self.experiment = mlflow.get_experiment(self.experiment_id)
            else:
                self.experiment_id = self.experiment.experiment_id
            
            self.logger.info(f"MLflow experiment initialized: {self.experiment_name}")
        except Exception as e:
            self.logger.error(f"Error initializing MLflow experiment: {e}")
            self.enabled = False
    
    def log_model_training(
        self,
        model: Any,
        model_name: str,
        training_metrics: Dict[str, float],
        training_params: Dict[str, Any],
        feature_names: List[str],
        training_data_size: int
    ) -> str:
        """
        Log model training to MLflow
        
        Args:
            model: Trained model object
            model_name: Name of the model
            training_metrics: Training metrics (accuracy, precision, recall, etc.)
            training_params: Training hyperparameters
            feature_names: List of feature names used
            training_data_size: Size of training dataset
        
        Returns:
            Run ID
        """
        if not self.enabled:
            return None
        
        try:
            with mlflow.start_run(experiment_id=self.experiment_id) as run:
                run_id = run.info.run_id
                
                # Log parameters
                for param_name, param_value in training_params.items():
                    mlflow.log_param(param_name, param_value)
                
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("training_data_size", training_data_size)
                mlflow.log_param("num_features", len(feature_names))
                
                # Log metrics
                for metric_name, metric_value in training_metrics.items():
                    mlflow.log_metric(metric_name, metric_value)
                
                # Log feature list
                mlflow.log_param("features", json.dumps(feature_names))
                
                # Log model
                if hasattr(model, 'predict'):  # Scikit-learn model
                    mlflow.sklearn.log_model(model, "model")
                elif hasattr(model, '__call__'):  # TensorFlow/Keras model
                    mlflow.tensorflow.log_model(model, "model")
                else:
                    import joblib
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
                        joblib.dump(model, f.name)
                        mlflow.log_artifact(f.name, "model")
                
                # Add tags
                mlflow.set_tag("model_type", model_name)
                mlflow.set_tag("training_timestamp", datetime.now().isoformat())
                
                self.logger.info(f"Model training logged to MLflow: run_id={run_id}")
                return run_id
                
        except Exception as e:
            self.logger.error(f"Error logging model training: {e}")
            return None
    
    def log_model_prediction(
        self,
        model_version: str,
        predictions: List[Any],
        actuals: Optional[List[Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log model predictions for monitoring
        
        Args:
            model_version: Model version identifier
            predictions: Model predictions
            actuals: Actual values (if available)
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        try:
            # Create a run for predictions
            with mlflow.start_run(experiment_id=self.experiment_id, nested=True) as run:
                # Log prediction metrics
                mlflow.log_metric("predictions_count", len(predictions))
                
                if actuals:
                    # Calculate accuracy metrics
                    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
                    
                    accuracy = accuracy_score(actuals, predictions)
                    precision = precision_score(actuals, predictions, average='weighted', zero_division=0)
                    recall = recall_score(actuals, predictions, average='weighted', zero_division=0)
                    f1 = f1_score(actuals, predictions, average='weighted', zero_division=0)
                    
                    mlflow.log_metric("accuracy", accuracy)
                    mlflow.log_metric("precision", precision)
                    mlflow.log_metric("recall", recall)
                    mlflow.log_metric("f1_score", f1)
                
                # Log metadata
                if metadata:
                    for key, value in metadata.items():
                        mlflow.log_param(key, value)
                
                mlflow.set_tag("model_version", model_version)
                mlflow.set_tag("prediction_timestamp", datetime.now().isoformat())
                
        except Exception as e:
            self.logger.error(f"Error logging predictions: {e}")
    
    def register_model(
        self,
        run_id: str,
        model_name: str,
        stage: str = "Staging"
    ) -> str:
        """
        Register model in MLflow Model Registry
        
        Args:
            run_id: MLflow run ID
            model_name: Name for the model
            stage: Model stage (Staging, Production, Archived)
        
        Returns:
            Model version
        """
        if not self.enabled:
            return None
        
        try:
            model_uri = f"runs:/{run_id}/model"
            
            # Register model
            model_version = mlflow.register_model(
                model_uri=model_uri,
                name=model_name
            )
            
            # Transition to stage
            if stage != "None":
                self.client.transition_model_version_stage(
                    name=model_name,
                    version=model_version.version,
                    stage=stage
                )
            
            self.logger.info(f"Model registered: {model_name} v{model_version.version} ({stage})")
            return f"{model_name}/{model_version.version}"
            
        except Exception as e:
            self.logger.error(f"Error registering model: {e}")
            return None
    
    def load_model(self, model_name: str, version: Optional[str] = None, stage: Optional[str] = None) -> Any:
        """
        Load model from MLflow Model Registry
        
        Args:
            model_name: Name of the model
            version: Model version (if None, loads latest)
            stage: Model stage (Production, Staging, etc.)
        
        Returns:
            Loaded model
        """
        if not self.enabled:
            return None
        
        try:
            if stage:
                model_uri = f"models:/{model_name}/{stage}"
            elif version:
                model_uri = f"models:/{model_name}/{version}"
            else:
                model_uri = f"models:/{model_name}/latest"
            
            model = mlflow.pyfunc.load_model(model_uri)
            self.logger.info(f"Model loaded: {model_uri}")
            return model
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            return None
    
    def setup_ab_test(
        self,
        model_a_name: str,
        model_a_version: str,
        model_b_name: str,
        model_b_version: str,
        traffic_split: float = 0.5
    ) -> str:
        """
        Setup A/B test between two model versions
        
        Args:
            model_a_name: Name of model A
            model_a_version: Version of model A
            model_b_name: Name of model B
            model_b_version: Version of model B
            traffic_split: Percentage of traffic to model A (0-1)
        
        Returns:
            A/B test ID
        """
        if not self.enabled:
            return None
        
        try:
            ab_test_id = f"ab_test_{datetime.now().timestamp()}"
            
            # Store A/B test configuration
            ab_test_config = {
                'test_id': ab_test_id,
                'model_a': f"{model_a_name}/{model_a_version}",
                'model_b': f"{model_b_name}/{model_b_version}",
                'traffic_split': traffic_split,
                'start_time': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Store in MLflow as experiment tag
            with mlflow.start_run(experiment_id=self.experiment_id) as run:
                mlflow.set_tag("ab_test_id", ab_test_id)
                mlflow.set_tag("ab_test_config", json.dumps(ab_test_config))
            
            self.logger.info(f"A/B test setup: {ab_test_id}")
            return ab_test_id
            
        except Exception as e:
            self.logger.error(f"Error setting up A/B test: {e}")
            return None
    
    def evaluate_ab_test(
        self,
        ab_test_id: str,
        model_a_metrics: Dict[str, float],
        model_b_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluate A/B test results
        
        Args:
            ab_test_id: A/B test identifier
            model_a_metrics: Performance metrics for model A
            model_b_metrics: Performance metrics for model B
        
        Returns:
            Evaluation results
        """
        if not self.enabled:
            return {}
        
        try:
            evaluation = {
                'ab_test_id': ab_test_id,
                'model_a_metrics': model_a_metrics,
                'model_b_metrics': model_b_metrics,
                'evaluation_timestamp': datetime.now().isoformat()
            }
            
            # Compare metrics
            comparisons = {}
            for metric_name in set(model_a_metrics.keys()) & set(model_b_metrics.keys()):
                a_value = model_a_metrics[metric_name]
                b_value = model_b_metrics[metric_name]
                
                improvement = ((b_value - a_value) / max(abs(a_value), 0.001)) * 100
                
                comparisons[metric_name] = {
                    'model_a': a_value,
                    'model_b': b_value,
                    'improvement_percent': improvement,
                    'winner': 'model_b' if b_value > a_value else 'model_a'
                }
            
            evaluation['comparisons'] = comparisons
            
            # Determine overall winner
            winner_metrics = sum(1 for comp in comparisons.values() if comp['winner'] == 'model_b')
            total_metrics = len(comparisons)
            
            if winner_metrics > total_metrics * 0.5:
                evaluation['overall_winner'] = 'model_b'
                evaluation['recommendation'] = 'Promote model_b to production'
            else:
                evaluation['overall_winner'] = 'model_a'
                evaluation['recommendation'] = 'Keep model_a in production'
            
            # Log evaluation
            with mlflow.start_run(experiment_id=self.experiment_id) as run:
                mlflow.set_tag("ab_test_id", ab_test_id)
                mlflow.log_dict(evaluation, "ab_test_evaluation.json")
            
            self.logger.info(f"A/B test evaluated: {ab_test_id}, winner: {evaluation['overall_winner']}")
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error evaluating A/B test: {e}")
            return {}
    
    def check_retraining_trigger(
        self,
        model_version: str,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
        threshold_drop: float = 0.05
    ) -> Tuple[bool, str]:
        """
        Check if model needs retraining based on performance degradation
        
        Args:
            model_version: Current model version
            current_metrics: Current performance metrics
            baseline_metrics: Baseline performance metrics
            threshold_drop: Threshold for performance drop (e.g., 0.05 = 5%)
        
        Returns:
            Tuple of (needs_retraining, reason)
        """
        if not self.enabled:
            return False, "MLflow not available"
        
        try:
            # Compare metrics
            for metric_name in set(current_metrics.keys()) & set(baseline_metrics.keys()):
                current_value = current_metrics[metric_name]
                baseline_value = baseline_metrics[metric_name]
                
                if baseline_value == 0:
                    continue
                
                performance_drop = (baseline_value - current_value) / baseline_value
                
                if performance_drop > threshold_drop:
                    reason = f"{metric_name} dropped by {performance_drop*100:.1f}% " \
                            f"({current_value:.3f} vs {baseline_value:.3f})"
                    self.logger.warning(f"Retraining trigger: {reason}")
                    return True, reason
            
            return False, "Performance within acceptable range"
            
        except Exception as e:
            self.logger.error(f"Error checking retraining trigger: {e}")
            return False, f"Error: {str(e)}"
    
    def get_model_performance_history(
        self,
        model_name: str,
        days: int = 30
    ) -> pd.DataFrame:
        """
        Get model performance history
        
        Args:
            model_name: Name of the model
            days: Number of days to retrieve
        
        Returns:
            DataFrame with performance history
        """
        if not self.enabled:
            return pd.DataFrame()
        
        try:
            # Query MLflow for runs
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # Get runs for the model
            runs = self.client.search_runs(
                experiment_ids=[self.experiment_id],
                filter_string=f"tags.model_name='{model_name}'",
                max_results=1000
            )
            
            # Extract metrics
            history_data = []
            for run in runs:
                if run.info.start_time < start_time.timestamp() * 1000:
                    continue
                
                metrics = run.data.metrics
                params = run.data.params
                
                history_data.append({
                    'run_id': run.info.run_id,
                    'timestamp': datetime.fromtimestamp(run.info.start_time / 1000),
                    **metrics,
                    **params
                })
            
            if history_data:
                return pd.DataFrame(history_data)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"Error getting performance history: {e}")
            return pd.DataFrame()

