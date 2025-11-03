# FIDPS API Routes
# REST API endpoints for the dashboard

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from ..app import db_manager, connection_manager
from ..models.api_models import (
    DrillingSensorData, AnomalyAlert, ValidationResult, 
    SystemStatus, DashboardMetrics
)
from ..utils.rate_limiter import check_rate_limit, Depends as RateLimitDepends
from fastapi import Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["API"])

# Dashboard Overview
@router.get("/dashboard/overview", response_model=DashboardMetrics)
async def get_dashboard_overview(request: Request, _: bool = RateLimitDepends(check_rate_limit)):
    """Get dashboard overview metrics"""
    try:
        # Get data from Redis cache and databases
        active_wells = await _get_active_wells_count()
        anomalies_today = await _get_anomalies_count_today()
        critical_alerts = await _get_critical_alerts_count()
        data_quality = await _get_average_data_quality()
        system_health = await _get_system_health_status()
        
        return DashboardMetrics(
            active_wells=active_wells,
            total_anomalies_today=anomalies_today,
            critical_alerts=critical_alerts,
            data_quality_score=data_quality,
            system_health=system_health,
            last_updated=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Real-time Data Endpoints
@router.get("/data/latest/{well_id}", response_model=DrillingSensorData)
async def get_latest_sensor_data(well_id: str):
    """Get latest sensor data for a specific well"""
    try:
        if not db_manager.redis_client:
            raise HTTPException(status_code=503, detail="Redis not available")
        
        # Try to get from cache first
        cached_data = await db_manager.redis_client.get(f"latest_well_{well_id}")
        if cached_data:
            data = json.loads(cached_data)
            return DrillingSensorData(**data)
        
        # Fallback to database
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT * FROM sensor_data 
                WHERE well_id = $1 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            row = await conn.fetchrow(query, well_id)
            if not row:
                raise HTTPException(status_code=404, detail="No data found for well")
            
            return DrillingSensorData(**dict(row))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest sensor data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/data/history/{well_id}")
async def get_sensor_data_history(
    well_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(1000, le=10000)
):
    """Get historical sensor data for a well"""
    try:
        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()
        
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT * FROM sensor_data 
                WHERE well_id = $1 
                AND timestamp BETWEEN $2 AND $3
                ORDER BY timestamp DESC 
                LIMIT $4
            """
            rows = await conn.fetch(query, well_id, start_time, end_time, limit)
            
            return {
                "well_id": well_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "count": len(rows),
                "data": [dict(row) for row in rows]
            }
    
    except Exception as e:
        logger.error(f"Error getting sensor data history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Anomaly Detection Endpoints
@router.get("/anomalies/active", response_model=List[AnomalyAlert])
async def get_active_anomalies(
    well_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get active anomaly alerts"""
    try:
        # Build query conditions
        conditions = ["status = 'active'"]
        params = []
        param_count = 0
        
        if well_id:
            param_count += 1
            conditions.append(f"well_id = ${param_count}")
            params.append(well_id)
        
        if severity:
            param_count += 1
            conditions.append(f"severity = ${param_count}")
            params.append(severity)
        
        param_count += 1
        params.append(limit)
        
        query = f"""
            SELECT * FROM anomaly_alerts 
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC 
            LIMIT ${param_count}
        """
        
        async with db_manager.postgres_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [AnomalyAlert(**dict(row)) for row in rows]
    
    except Exception as e:
        logger.error(f"Error getting active anomalies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/anomalies/history")
async def get_anomaly_history(
    well_id: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(1000, le=10000)
):
    """Get historical anomaly data"""
    try:
        if not start_time:
            start_time = datetime.now() - timedelta(days=7)
        if not end_time:
            end_time = datetime.now()
        
        conditions = ["timestamp BETWEEN $1 AND $2"]
        params = [start_time, end_time]
        param_count = 2
        
        if well_id:
            param_count += 1
            conditions.append(f"well_id = ${param_count}")
            params.append(well_id)
        
        param_count += 1
        params.append(limit)
        
        query = f"""
            SELECT * FROM anomaly_alerts 
            WHERE {' AND '.join(conditions)}
            ORDER BY timestamp DESC 
            LIMIT ${param_count}
        """
        
        async with db_manager.postgres_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            return {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "count": len(rows),
                "anomalies": [dict(row) for row in rows]
            }
    
    except Exception as e:
        logger.error(f"Error getting anomaly history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(anomaly_id: str):
    """Acknowledge an anomaly alert"""
    try:
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                UPDATE anomaly_alerts 
                SET status = 'acknowledged', 
                    acknowledged_at = $1,
                    acknowledged_by = $2
                WHERE id = $3
                RETURNING *
            """
            row = await conn.fetchrow(query, datetime.now(), "api_user", anomaly_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Anomaly not found")
            
            return {"message": "Anomaly acknowledged", "anomaly": dict(row)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging anomaly: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Data Validation Endpoints
@router.get("/validation/results", response_model=List[ValidationResult])
async def get_validation_results(
    well_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get data validation results"""
    try:
        # Try Redis cache first for recent results
        if db_manager.redis_client:
            cached_results = await db_manager.redis_client.lrange("recent_data-validation-results", 0, limit-1)
            if cached_results:
                results = []
                for result in cached_results:
                    data = json.loads(result)
                    if (not well_id or data.get('well_id') == well_id) and \
                       (not status or data.get('status') == status):
                        results.append(ValidationResult(**data))
                
                if results:
                    return results[:limit]
        
        # Fallback to database
        conditions = []
        params = []
        param_count = 0
        
        if well_id:
            param_count += 1
            conditions.append(f"well_id = ${param_count}")
            params.append(well_id)
        
        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status)
        
        param_count += 1
        params.append(limit)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT * FROM validation_results 
            {where_clause}
            ORDER BY timestamp DESC 
            LIMIT ${param_count}
        """
        
        async with db_manager.postgres_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [ValidationResult(**dict(row)) for row in rows]
    
    except Exception as e:
        logger.error(f"Error getting validation results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# System Status Endpoints
@router.get("/system/status", response_model=List[SystemStatus])
async def get_system_status():
    """Get system status for all services"""
    try:
        # Get from MongoDB
        if not db_manager.mongodb_db:
            raise HTTPException(status_code=503, detail="MongoDB not available")
        
        cursor = db_manager.mongodb_db.system_status.find().sort("timestamp", -1).limit(10)
        statuses = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
            statuses.append(SystemStatus(**doc))
        
        return statuses
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Wells Management
@router.get("/wells")
async def get_wells():
    """Get list of all wells"""
    try:
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT DISTINCT well_id, 
                       MAX(timestamp) as last_data_time,
                       COUNT(*) as data_points
                FROM sensor_data 
                GROUP BY well_id 
                ORDER BY last_data_time DESC
            """
            rows = await conn.fetch(query)
            
            wells = []
            for row in rows:
                well_data = dict(row)
                # Check if well is currently active (data within last hour)
                is_active = (datetime.now() - well_data['last_data_time']).total_seconds() < 3600
                well_data['is_active'] = is_active
                wells.append(well_data)
            
            return {"wells": wells, "count": len(wells)}
    
    except Exception as e:
        logger.error(f"Error getting wells: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/wells/{well_id}/summary")
async def get_well_summary(well_id: str):
    """Get summary information for a specific well"""
    try:
        async with db_manager.postgres_pool.acquire() as conn:
            # Get basic well info
            well_query = """
                SELECT well_id,
                       MIN(timestamp) as first_data_time,
                       MAX(timestamp) as last_data_time,
                       COUNT(*) as total_data_points,
                       AVG(depth) as avg_depth,
                       MAX(depth) as max_depth
                FROM sensor_data 
                WHERE well_id = $1
                GROUP BY well_id
            """
            well_info = await conn.fetchrow(well_query, well_id)
            
            if not well_info:
                raise HTTPException(status_code=404, detail="Well not found")
            
            # Get anomaly count
            anomaly_query = """
                SELECT COUNT(*) as anomaly_count,
                       COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_count
                FROM anomaly_alerts 
                WHERE well_id = $1
            """
            anomaly_info = await conn.fetchrow(anomaly_query, well_id)
            
            # Get latest validation status
            validation_query = """
                SELECT status, data_quality_score
                FROM validation_results 
                WHERE well_id = $1 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            validation_info = await conn.fetchrow(validation_query, well_id)
            
            return {
                "well_info": dict(well_info),
                "anomaly_stats": dict(anomaly_info) if anomaly_info else {},
                "validation_status": dict(validation_info) if validation_info else {},
                "is_active": (datetime.now() - well_info['last_data_time']).total_seconds() < 3600
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting well summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Helper functions
async def _get_active_wells_count() -> int:
    """Get count of active wells"""
    try:
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT COUNT(DISTINCT well_id) 
                FROM sensor_data 
                WHERE timestamp > $1
            """
            result = await conn.fetchval(query, datetime.now() - timedelta(hours=1))
            return result or 0
    except Exception:
        return 0

async def _get_anomalies_count_today() -> int:
    """Get count of anomalies detected today"""
    try:
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT COUNT(*) 
                FROM anomaly_alerts 
                WHERE timestamp >= $1
            """
            result = await conn.fetchval(query, datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
            return result or 0
    except Exception:
        return 0

async def _get_critical_alerts_count() -> int:
    """Get count of active critical alerts"""
    try:
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT COUNT(*) 
                FROM anomaly_alerts 
                WHERE status = 'active' AND severity = 'critical'
            """
            result = await conn.fetchval(query)
            return result or 0
    except Exception:
        return 0

async def _get_average_data_quality() -> float:
    """Get average data quality score"""
    try:
        async with db_manager.postgres_pool.acquire() as conn:
            query = """
                SELECT AVG(data_quality_score) 
                FROM validation_results 
                WHERE timestamp > $1
            """
            result = await conn.fetchval(query, datetime.now() - timedelta(hours=24))
            return float(result) if result else 0.0
    except Exception:
        return 0.0

async def _get_system_health_status() -> str:
    """Get overall system health status"""
    try:
        # Check if all services are responding
        services_ok = (
            db_manager.postgres_pool is not None and
            db_manager.mongodb_client is not None and
            db_manager.redis_client is not None
        )
        
        if services_ok:
            # Check for recent critical alerts
            critical_count = await _get_critical_alerts_count()
            if critical_count > 5:
                return "degraded"
            elif critical_count > 0:
                return "warning"
            else:
                return "healthy"
        else:
            return "unhealthy"
    except Exception:
        return "unknown"