# FIDPS WebSocket Routes
# Real-time data streaming for the dashboard

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Any
import json
import asyncio
import logging
from datetime import datetime

from ..app import connection_manager, db_manager
from ..models.api_models import DrillingSensorData, AnomalyAlert

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/dashboard/{client_id}")
async def websocket_dashboard(websocket: WebSocket, client_id: str):
    """Main dashboard WebSocket endpoint for real-time updates"""
    await connection_manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                await _handle_subscription(websocket, client_id, message)
            elif message.get("type") == "unsubscribe":
                await _handle_unsubscription(websocket, client_id, message)
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
            
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
        logger.info(f"Dashboard client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        connection_manager.disconnect(client_id)

@router.websocket("/ws/well/{well_id}/{client_id}")
async def websocket_well_data(websocket: WebSocket, well_id: str, client_id: str):
    """WebSocket endpoint for specific well real-time data"""
    full_client_id = f"well_{well_id}_{client_id}"
    await connection_manager.connect(websocket, full_client_id)
    
    try:
        # Send initial well data
        await _send_initial_well_data(websocket, well_id)
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_history":
                await _send_well_history(websocket, well_id, message.get("hours", 1))
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(full_client_id)
        logger.info(f"Well {well_id} client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for well {well_id} client {client_id}: {e}")
        connection_manager.disconnect(full_client_id)

@router.websocket("/ws/anomalies/{client_id}")
async def websocket_anomalies(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time anomaly alerts"""
    full_client_id = f"anomalies_{client_id}"
    await connection_manager.connect(websocket, full_client_id)
    
    try:
        # Send current active anomalies
        await _send_active_anomalies(websocket)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_active":
                await _send_active_anomalies(websocket)
            elif message.get("type") == "acknowledge":
                await _handle_anomaly_acknowledgment(websocket, message.get("anomaly_id"))
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(full_client_id)
        logger.info(f"Anomalies client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for anomalies client {client_id}: {e}")
        connection_manager.disconnect(full_client_id)

@router.websocket("/ws/system-status/{client_id}")
async def websocket_system_status(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for system status updates"""
    full_client_id = f"system_{client_id}"
    await connection_manager.connect(websocket, full_client_id)
    
    try:
        # Send initial system status
        await _send_system_status(websocket)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_status":
                await _send_system_status(websocket)
            elif message.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(full_client_id)
        logger.info(f"System status client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for system status client {client_id}: {e}")
        connection_manager.disconnect(full_client_id)

# Helper functions for WebSocket handlers

async def _handle_subscription(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """Handle client subscription to specific data streams"""
    subscription_type = message.get("subscription")
    
    if subscription_type == "all_wells":
        # Subscribe to all well data updates
        connection_manager.add_subscription(client_id, "all_wells")
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "subscription": "all_wells",
            "message": "Subscribed to all wells data"
        }))
    
    elif subscription_type == "anomalies":
        # Subscribe to anomaly alerts
        connection_manager.add_subscription(client_id, "anomalies")
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "subscription": "anomalies",
            "message": "Subscribed to anomaly alerts"
        }))
    
    elif subscription_type == "system_metrics":
        # Subscribe to system metrics
        connection_manager.add_subscription(client_id, "system_metrics")
        await websocket.send_text(json.dumps({
            "type": "subscription_confirmed",
            "subscription": "system_metrics",
            "message": "Subscribed to system metrics"
        }))

async def _handle_unsubscription(websocket: WebSocket, client_id: str, message: Dict[str, Any]):
    """Handle client unsubscription from data streams"""
    subscription_type = message.get("subscription")
    connection_manager.remove_subscription(client_id, subscription_type)
    
    await websocket.send_text(json.dumps({
        "type": "unsubscription_confirmed",
        "subscription": subscription_type,
        "message": f"Unsubscribed from {subscription_type}"
    }))

async def _send_initial_well_data(websocket: WebSocket, well_id: str):
    """Send initial data for a specific well"""
    try:
        # Get latest sensor data
        if db_manager.redis_client:
            cached_data = await db_manager.redis_client.get(f"latest_well_{well_id}")
            if cached_data:
                data = json.loads(cached_data)
                await websocket.send_text(json.dumps({
                    "type": "initial_data",
                    "well_id": well_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }))
                return
        
        # Fallback to database
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT * FROM sensor_data 
                WHERE well_id = $1 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            row = await conn.fetchrow(query, well_id)
            if row:
                await websocket.send_text(json.dumps({
                    "type": "initial_data",
                    "well_id": well_id,
                    "data": dict(row),
                    "timestamp": datetime.now().isoformat()
                }))
    
    except Exception as e:
        logger.error(f"Error sending initial well data: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to load initial data"
        }))

async def _send_well_history(websocket: WebSocket, well_id: str, hours: int = 1):
    """Send historical data for a well"""
    try:
        from datetime import timedelta
        start_time = datetime.now() - timedelta(hours=hours)
        
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT * FROM sensor_data 
                WHERE well_id = $1 AND timestamp >= $2
                ORDER BY timestamp ASC
                LIMIT 1000
            """
            rows = await conn.fetch(query, well_id, start_time)
            
            await websocket.send_text(json.dumps({
                "type": "history_data",
                "well_id": well_id,
                "hours": hours,
                "count": len(rows),
                "data": [dict(row) for row in rows],
                "timestamp": datetime.now().isoformat()
            }))
    
    except Exception as e:
        logger.error(f"Error sending well history: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to load historical data"
        }))

async def _send_active_anomalies(websocket: WebSocket):
    """Send current active anomalies"""
    try:
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT * FROM anomaly_alerts 
                WHERE status = 'active' 
                ORDER BY timestamp DESC 
                LIMIT 50
            """
            rows = await conn.fetch(query)
            
            await websocket.send_text(json.dumps({
                "type": "active_anomalies",
                "count": len(rows),
                "anomalies": [dict(row) for row in rows],
                "timestamp": datetime.now().isoformat()
            }))
    
    except Exception as e:
        logger.error(f"Error sending active anomalies: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to load anomalies"
        }))

async def _handle_anomaly_acknowledgment(websocket: WebSocket, anomaly_id: str):
    """Handle anomaly acknowledgment"""
    try:
        if not anomaly_id:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Anomaly ID required"
            }))
            return
        
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                UPDATE anomaly_alerts 
                SET status = 'acknowledged', 
                    acknowledged_at = $1,
                    acknowledged_by = $2
                WHERE id = $3
                RETURNING *
            """
            row = await conn.fetchrow(query, datetime.now(), "websocket_user", anomaly_id)
            
            if row:
                await websocket.send_text(json.dumps({
                    "type": "anomaly_acknowledged",
                    "anomaly_id": anomaly_id,
                    "anomaly": dict(row),
                    "timestamp": datetime.now().isoformat()
                }))
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Anomaly not found"
                }))
    
    except Exception as e:
        logger.error(f"Error acknowledging anomaly: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to acknowledge anomaly"
        }))

async def _send_system_status(websocket: WebSocket):
    """Send current system status"""
    try:
        # Get system status from MongoDB
        if db_manager.mongodb_db:
            cursor = db_manager.mongodb_db.system_status.find().sort("timestamp", -1).limit(1)
            status_doc = await cursor.to_list(length=1)
            
            if status_doc:
                status = status_doc[0]
                status['_id'] = str(status['_id'])  # Convert ObjectId to string
                
                await websocket.send_text(json.dumps({
                    "type": "system_status",
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }))
            else:
                await websocket.send_text(json.dumps({
                    "type": "system_status",
                    "status": {"service": "unknown", "status": "no_data"},
                    "timestamp": datetime.now().isoformat()
                }))
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "MongoDB not available"
            }))
    
    except Exception as e:
        logger.error(f"Error sending system status: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Failed to load system status"
        }))

# Broadcast functions (called from Kafka consumers)

async def broadcast_sensor_data(data: Dict[str, Any]):
    """Broadcast new sensor data to connected clients"""
    try:
        well_id = data.get('well_id')
        message = {
            "type": "sensor_data_update",
            "well_id": well_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to dashboard clients subscribed to all wells
        await connection_manager.broadcast_to_subscription("all_wells", json.dumps(message))
        
        # Broadcast to specific well clients
        well_clients = [client_id for client_id in connection_manager.active_connections.keys() 
                       if client_id.startswith(f"well_{well_id}_")]
        
        for client_id in well_clients:
            await connection_manager.send_personal_message(json.dumps(message), client_id)
    
    except Exception as e:
        logger.error(f"Error broadcasting sensor data: {e}")

async def broadcast_anomaly_alert(alert: Dict[str, Any]):
    """Broadcast new anomaly alert to connected clients"""
    try:
        message = {
            "type": "anomaly_alert",
            "alert": alert,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to all anomaly subscribers
        await connection_manager.broadcast_to_subscription("anomalies", json.dumps(message))
        
        # Also broadcast to dashboard clients
        await connection_manager.broadcast_to_subscription("all_wells", json.dumps(message))
        
        # Broadcast to anomaly-specific clients
        anomaly_clients = [client_id for client_id in connection_manager.active_connections.keys() 
                          if client_id.startswith("anomalies_")]
        
        for client_id in anomaly_clients:
            await connection_manager.send_personal_message(json.dumps(message), client_id)
    
    except Exception as e:
        logger.error(f"Error broadcasting anomaly alert: {e}")

async def broadcast_system_status(status: Dict[str, Any]):
    """Broadcast system status update to connected clients"""
    try:
        message = {
            "type": "system_status_update",
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Broadcast to system metrics subscribers
        await connection_manager.broadcast_to_subscription("system_metrics", json.dumps(message))
        
        # Broadcast to system status clients
        system_clients = [client_id for client_id in connection_manager.active_connections.keys() 
                         if client_id.startswith("system_")]
        
        for client_id in system_clients:
            await connection_manager.send_personal_message(json.dumps(message), client_id)
    
    except Exception as e:
        logger.error(f"Error broadcasting system status: {e}")