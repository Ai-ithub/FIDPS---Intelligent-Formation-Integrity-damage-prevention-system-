"""
Async Kafka Consumer Utilities
Replaces threading-based Kafka consumers with async/await pattern
"""

import asyncio
import json
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError

logger = logging.getLogger(__name__)

class AsyncKafkaConsumer:
    """Async Kafka consumer that replaces threading-based consumer"""
    
    def __init__(
        self,
        topics: list[str],
        bootstrap_servers: str,
        group_id: str,
        message_handler: Callable[[Dict[str, Any]], None],
        error_handler: Optional[Callable[[Exception, Dict[str, Any]], None]] = None,
        dlq_topic: Optional[str] = None
    ):
        self.topics = topics
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.message_handler = message_handler
        self.error_handler = error_handler
        self.dlq_topic = dlq_topic
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.dlq_producer: Optional[AIOKafkaProducer] = None
        self.running = False
        self.max_retries = 3
        self.retry_counts: Dict[str, int] = {}
    
    async def start(self):
        """Start the async Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=False
            )
            
            await self.consumer.start()
            self.running = True
            
            # Create DLQ producer if needed
            if self.dlq_topic:
                self.dlq_producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await self.dlq_producer.start()
            
            logger.info(f"Async Kafka consumer started for topics: {self.topics}")
            
            # Start consuming loop
            asyncio.create_task(self._consume_loop())
            
        except Exception as e:
            logger.error(f"Failed to start async Kafka consumer: {e}")
            raise
    
    async def _consume_loop(self):
        """Main consumption loop"""
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                
                await self._process_message(message)
                
        except Exception as e:
            logger.error(f"Error in consume loop: {e}")
        finally:
            await self.stop()
    
    async def _process_message(self, message):
        """Process a single message with retry logic"""
        message_id = f"{message.topic}_{message.partition}_{message.offset}"
        
        try:
            data = message.value
            data['topic'] = message.topic
            data['timestamp'] = datetime.now().isoformat()
            
            # Call message handler
            if asyncio.iscoroutinefunction(self.message_handler):
                await self.message_handler(data)
            else:
                self.message_handler(data)
            
            # Commit on success
            await self.consumer.commit()
            
            # Reset retry count
            if message_id in self.retry_counts:
                del self.retry_counts[message_id]
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for message: {e}")
            # Send to DLQ immediately
            if self.dlq_topic:
                await self._send_to_dlq(self.dlq_topic, message, f"JSON decode error: {str(e)}")
            await self.consumer.commit()
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            # Retry logic
            current_retries = self.retry_counts.get(message_id, 0)
            if current_retries < self.max_retries:
                self.retry_counts[message_id] = current_retries + 1
                logger.info(f"Retrying message {message_id} (attempt {current_retries + 1}/{self.max_retries})")
                await asyncio.sleep(2 ** current_retries)  # Exponential backoff
                # Don't commit - will retry
            else:
                # Max retries reached - send to DLQ
                logger.error(f"Max retries reached for message {message_id}, sending to DLQ")
                if self.dlq_topic:
                    await self._send_to_dlq(
                        self.dlq_topic,
                        message,
                        f"Processing error after {self.max_retries} retries: {str(e)}"
                    )
                await self.consumer.commit()
                if message_id in self.retry_counts:
                    del self.retry_counts[message_id]
            
            # Call error handler if provided
            if self.error_handler:
                if asyncio.iscoroutinefunction(self.error_handler):
                    await self.error_handler(e, message.value if hasattr(message, 'value') else {})
                else:
                    self.error_handler(e, message.value if hasattr(message, 'value') else {})
    
    async def _send_to_dlq(self, dlq_topic: str, original_message, error_reason: str):
        """Send failed message to Dead Letter Queue"""
        if not self.dlq_producer:
            return
        
        try:
            dlq_message = {
                'original_topic': original_message.topic,
                'original_partition': original_message.partition,
                'original_offset': original_message.offset,
                'original_timestamp': original_message.timestamp,
                'error_reason': error_reason,
                'failed_at': datetime.now().isoformat(),
                'original_value': original_message.value if hasattr(original_message, 'value') else str(original_message.value)
            }
            
            await self.dlq_producer.send_and_wait(dlq_topic, value=dlq_message)
            logger.info(f"Message sent to DLQ: {dlq_topic}")
            
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {e}")
    
    async def stop(self):
        """Stop the consumer"""
        self.running = False
        
        if self.consumer:
            await self.consumer.stop()
        
        if self.dlq_producer:
            await self.dlq_producer.stop()
        
        logger.info("Async Kafka consumer stopped")

