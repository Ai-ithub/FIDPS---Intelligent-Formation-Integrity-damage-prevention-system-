#!/usr/bin/env python3
"""
FIDPS Image/Audio Processing Service (SSD)
Real-time processing of image and audio data for Damage Integrity detection

This service processes high-volume image and audio streams from sensors
to detect structural damage (cracks, fractures, etc.) that are part of
formation integrity.
"""

import json
import logging
import base64
import io
from typing import Dict, List, Optional, Any
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
import numpy as np
from PIL import Image
import cv2

# ML for image processing
try:
    import tensorflow as tf
    from tensorflow import keras
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logging.warning("TensorFlow not available, using simplified image processing")

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)


class ImageProcessingResult(BaseModel):
    """Result of image processing"""
    image_id: str
    well_id: str
    timestamp: datetime
    
    # Damage detection results
    damage_detected: bool
    damage_type: Optional[str] = None
    damage_severity: float = 0.0  # 0-1
    damage_location: Optional[Dict[str, float]] = None  # x, y, width, height
    
    # Integrity metrics
    integrity_score: float = 1.0  # 0-1, 1 = perfect integrity
    crack_density: float = 0.0
    fracture_count: int = 0
    
    # Processing metadata
    processing_time_ms: float
    model_confidence: float = 0.0
    processing_method: str = ""


class ImageProcessingService:
    """
    Service for processing image/audio data for damage integrity detection
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Kafka connections
        self.producer: Optional[KafkaProducer] = None
        self.consumer: Optional[KafkaConsumer] = None
        
        # ML models for damage detection
        self.damage_detection_model = None
        self.crack_detection_model = None
        
        # Initialize models
        self._initialize_models()
        
        # Metrics
        self.metrics = {
            'images_processed': 0,
            'damage_detected': 0,
            'processing_errors': 0
        }
    
    def _initialize_models(self):
        """Initialize ML models for damage detection"""
        try:
            # Load pre-trained models if available
            model_path = self.config.get('model_path', 'models/damage_detector.h5')
            
            if TF_AVAILABLE and os.path.exists(model_path):
                self.damage_detection_model = keras.models.load_model(model_path)
                self.logger.info("Loaded damage detection model")
            else:
                self.logger.info("Using simplified image processing (no ML model)")
                self.damage_detection_model = None
            
        except Exception as e:
            self.logger.error(f"Error initializing models: {e}")
            self.damage_detection_model = None
    
    def initialize(self):
        """Initialize service connections"""
        try:
            # Kafka producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.config['kafka']['bootstrap_servers'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            
            # Kafka consumer for image/audio data
            topics = self.config['kafka'].get('input_topics', ['image-data', 'audio-data', 'ssd-data'])
            self.consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.config['kafka']['bootstrap_servers'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                group_id='image-processing-service',
                auto_offset_reset='latest'
            )
            
            self.logger.info("Image Processing Service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing service: {e}")
            raise
    
    def process_image(
        self,
        image_data: bytes,
        image_id: str,
        well_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ImageProcessingResult:
        """
        Process image for damage detection
        
        Args:
            image_data: Image data as bytes
            image_id: Unique image identifier
            well_id: Well identifier
            metadata: Additional metadata
        
        Returns:
            ImageProcessingResult with damage detection results
        """
        start_time = datetime.now()
        
        try:
            # Decode image
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Convert to RGB if needed
            if len(image_array.shape) == 2:  # Grayscale
                image_array = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
            
            # Detect damage using ML model or computer vision
            if self.damage_detection_model and TF_AVAILABLE:
                damage_result = self._detect_damage_ml(image_array)
            else:
                damage_result = self._detect_damage_cv(image_array)
            
            # Calculate integrity metrics
            integrity_score = 1.0 - damage_result['severity']
            crack_density = damage_result.get('crack_density', 0.0)
            fracture_count = damage_result.get('fracture_count', 0)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            result = ImageProcessingResult(
                image_id=image_id,
                well_id=well_id,
                timestamp=datetime.now(),
                damage_detected=damage_result['detected'],
                damage_type=damage_result.get('damage_type'),
                damage_severity=damage_result['severity'],
                damage_location=damage_result.get('location'),
                integrity_score=integrity_score,
                crack_density=crack_density,
                fracture_count=fracture_count,
                processing_time_ms=processing_time,
                model_confidence=damage_result.get('confidence', 0.7),
                processing_method=damage_result.get('method', 'computer_vision')
            )
            
            # Update metrics
            self.metrics['images_processed'] += 1
            if damage_result['detected']:
                self.metrics['damage_detected'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing image {image_id}: {e}")
            self.metrics['processing_errors'] += 1
            raise
    
    def _detect_damage_ml(self, image_array: np.ndarray) -> Dict[str, Any]:
        """Detect damage using ML model"""
        try:
            # Preprocess image
            processed_image = self._preprocess_image(image_array)
            
            # Run inference
            predictions = self.damage_detection_model.predict(processed_image)
            
            # Extract results
            damage_probability = float(predictions[0][0])
            detected = damage_probability > 0.5
            
            return {
                'detected': detected,
                'severity': damage_probability,
                'confidence': damage_probability,
                'damage_type': 'structural_damage' if detected else None,
                'method': 'ml_model'
            }
            
        except Exception as e:
            self.logger.error(f"ML detection error: {e}")
            # Fallback to computer vision
            return self._detect_damage_cv(image_array)
    
    def _detect_damage_cv(self, image_array: np.ndarray) -> Dict[str, Any]:
        """Detect damage using computer vision techniques"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Edge detection for cracks
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours (potential cracks)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size (cracks are typically long and thin)
            crack_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 50:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = max(w, h) / max(min(w, h), 1)
                    if aspect_ratio > 3:  # Long and thin = crack
                        crack_contours.append(contour)
            
            # Calculate damage metrics
            fracture_count = len(crack_contours)
            
            # Calculate crack density (total crack area / image area)
            total_crack_area = sum(cv2.contourArea(c) for c in crack_contours)
            image_area = gray.shape[0] * gray.shape[1]
            crack_density = total_crack_area / max(image_area, 1)
            
            # Calculate severity (0-1)
            severity = min(1.0, crack_density * 10 + fracture_count * 0.1)
            
            # Determine damage location (centroid of largest crack)
            damage_location = None
            if crack_contours:
                largest_contour = max(crack_contours, key=cv2.contourArea)
                M = cv2.moments(largest_contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    damage_location = {
                        'x': float(cx),
                        'y': float(cy),
                        'width': float(w),
                        'height': float(h)
                    }
            
            detected = severity > 0.1  # Threshold for damage detection
            
            return {
                'detected': detected,
                'severity': severity,
                'confidence': 0.7,  # Medium confidence for CV method
                'damage_type': 'crack' if detected else None,
                'fracture_count': fracture_count,
                'crack_density': crack_density,
                'location': damage_location,
                'method': 'computer_vision'
            }
            
        except Exception as e:
            self.logger.error(f"Computer vision detection error: {e}")
            return {
                'detected': False,
                'severity': 0.0,
                'confidence': 0.0,
                'method': 'error'
            }
    
    def _preprocess_image(self, image_array: np.ndarray) -> np.ndarray:
        """Preprocess image for ML model"""
        # Resize to model input size (if model exists)
        if self.damage_detection_model:
            target_size = self.damage_detection_model.input_shape[1:3]
            resized = cv2.resize(image_array, target_size)
        else:
            resized = cv2.resize(image_array, (224, 224))
        
        # Normalize
        normalized = resized.astype(np.float32) / 255.0
        
        # Expand dimensions for batch
        return np.expand_dims(normalized, axis=0)
    
    def process_message(self, message: Dict[str, Any]) -> None:
        """Process Kafka message containing image/audio data"""
        try:
            # Extract image data
            if 'image_data' in message:
                # Base64 encoded image
                image_data = base64.b64decode(message['image_data'])
            elif 'image_url' in message:
                # URL to image (would need to fetch)
                self.logger.warning("Image URL not yet supported, skipping")
                return
            else:
                self.logger.warning("No image data in message")
                return
            
            image_id = message.get('image_id', f"img_{datetime.now().timestamp()}")
            well_id = message.get('well_id', 'unknown')
            metadata = message.get('metadata', {})
            
            # Process image
            result = self.process_image(image_data, image_id, well_id, metadata)
            
            # Publish results
            self._publish_results(result)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.metrics['processing_errors'] += 1
    
    def _publish_results(self, result: ImageProcessingResult):
        """Publish processing results to Kafka"""
        try:
            result_dict = {
                'image_id': result.image_id,
                'well_id': result.well_id,
                'timestamp': result.timestamp.isoformat(),
                'damage_detected': result.damage_detected,
                'damage_type': result.damage_type,
                'damage_severity': result.damage_severity,
                'damage_location': result.damage_location,
                'integrity_score': result.integrity_score,
                'crack_density': result.crack_density,
                'fracture_count': result.fracture_count,
                'processing_time_ms': result.processing_time_ms,
                'model_confidence': result.model_confidence,
                'processing_method': result.processing_method
            }
            
            # Publish to damage integrity topic
            self.producer.send('damage-integrity-results', value=result_dict)
            
            # If damage detected, publish to alerts
            if result.damage_detected:
                alert_dict = {
                    'alert_type': 'integrity_damage',
                    'severity': 'high' if result.damage_severity > 0.7 else 'medium',
                    'well_id': result.well_id,
                    'timestamp': result.timestamp.isoformat(),
                    'integrity_score': result.integrity_score,
                    'damage_details': result_dict
                }
                self.producer.send('integrity-alerts', value=alert_dict)
            
            self.producer.flush()
            
        except Exception as e:
            self.logger.error(f"Error publishing results: {e}")
    
    def start(self):
        """Start the service (process messages from Kafka)"""
        self.logger.info("Starting Image Processing Service...")
        
        if not self.consumer:
            self.initialize()
        
        try:
            for message in self.consumer:
                try:
                    self.process_message(message.value)
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
        except KeyboardInterrupt:
            self.logger.info("Stopping Image Processing Service...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the service"""
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()


# FastAPI app for HTTP API
app = FastAPI(
    title="FIDPS Image Processing Service",
    description="Real-time image/audio processing for damage integrity detection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
service: Optional[ImageProcessingService] = None


@app.on_event("startup")
async def startup():
    """Initialize service on startup"""
    global service
    
    config = {
        'kafka': {
            'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'input_topics': ['image-data', 'audio-data', 'ssd-data']
        },
        'model_path': os.getenv('MODEL_PATH', 'models/damage_detector.h5')
    }
    
    service = ImageProcessingService(config)
    service.initialize()


@app.post("/api/v1/process-image", response_model=ImageProcessingResult)
async def process_image_endpoint(
    image: UploadFile = File(...),
    well_id: str = None,
    image_id: str = None
):
    """Process uploaded image for damage detection"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Read image data
        image_data = await image.read()
        
        # Generate ID if not provided
        if not image_id:
            image_id = f"img_{datetime.now().timestamp()}"
        
        if not well_id:
            well_id = "unknown"
        
        # Process image
        result = service.process_image(image_data, image_id, well_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "image-processing-service",
        "metrics": service.metrics if service else {}
    }


if __name__ == "__main__":
    import uvicorn
    
    # For standalone service (Kafka consumer)
    if os.getenv('RUN_AS_KAFKA_CONSUMER', 'false') == 'true':
        config = {
            'kafka': {
                'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                'input_topics': ['image-data', 'audio-data', 'ssd-data']
            },
            'model_path': os.getenv('MODEL_PATH', 'models/damage_detector.h5')
        }
        service = ImageProcessingService(config)
        service.start()
    else:
        # Run as FastAPI server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=int(os.getenv('PORT', '8004')),
            reload=True
        )

