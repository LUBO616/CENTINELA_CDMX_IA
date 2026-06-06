"""
911 AI Flow Demo - API Analytics Service
Stores incidents, calculates metrics, and generates mock predictions
"""

import os
import uuid
import random
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

def num(value, default=0.0):
    """Convert DB numeric/Decimal/None values to native float."""
    if value is None:
        return default
    try:
        return float(value)
    except Exception:
        return default



# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="911 AI Flow Demo - API Analytics",
    description="Analytics, metrics, and predictions",
    version="1.0.0"
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5678").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://emergency_user:changeme@postgres:5432/emergency_demo")


# Database helper
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


# Privacy helper
def normalize_location_hint(location_hint: Optional[str]) -> str:
    """
    Normalize location to generalized zone, never expose full addresses
    Privacy by design: no street numbers or specific addresses
    """
    if not location_hint:
        return "Zona simulada"
    
    location_lower = location_hint.lower()
    
    # Known colonias/zones in CDMX
    known_zones = {
        "centro": "Centro",
        "colonia centro": "Centro",
        "cuauhtémoc": "Cuauhtémoc",
        "iztapalapa": "Iztapalapa",
        "benito juárez": "Benito Juárez",
        "benito juarez": "Benito Juárez",
        "coyoacán": "Coyoacán",
        "coyoacan": "Coyoacán",
        "tlalpan": "Tlalpan",
        "xochimilco": "Xochimilco",
        "miguel hidalgo": "Miguel Hidalgo",
        "álvaro obregón": "Álvaro Obregón",
        "alvaro obregon": "Álvaro Obregón",
        "azcapotzalco": "Azcapotzalco",
        "gustavo a. madero": "Gustavo A. Madero",
        "venustiano carranza": "Venustiano Carranza",
        "magdalena contreras": "Magdalena Contreras",
        "milpa alta": "Milpa Alta"
    }
    
    # Check if any known zone is mentioned
    for key, zone in known_zones.items():
        if key in location_lower:
            return zone
    
    # If contains street number pattern (e.g., "45", "123"), generalize
    import re
    if re.search(r'\b\d{1,4}\b', location_hint):
        # Has numbers, likely an address - return generic zone
        return "Zona simulada"
    
    # If it's a major street/avenue without number, keep it generalized
    major_streets = ["reforma", "insurgentes", "revolución", "constituyentes", "periférico"]
    for street in major_streets:
        if street in location_lower:
            return f"Zona {street.capitalize()}"
    
    # Default: return as generic zone if can't determine
    return "Zona simulada"


# Pydantic models
class IncidentRequest(BaseModel):
    call_id: str
    trace_id: str
    risk_level: int = Field(..., ge=1, le=10)
    branch: str
    case_category: str
    human_required: bool = False
    p0_signals: List[str] = []
    location_hint: Optional[str] = None


class IncidentResponse(BaseModel):
    incident_id: str
    stored_at: str
    status: str = "stored"


class IncidentListItem(BaseModel):
    incident_id: str
    call_id: str
    risk_level: int
    branch: str
    case_category: str
    human_required: bool
    timestamp: str


class IncidentListResponse(BaseModel):
    total: int
    items: List[IncidentListItem]


class SummaryResponse(BaseModel):
    total_incidents: int
    by_risk_level: Dict[str, int]
    by_branch: Dict[str, int]
    by_category: Dict[str, int]
    human_required_count: int
    p0_signals_count: int
    nna_involved_count: int
    last_updated: str


class HourlyPattern(BaseModel):
    hour: int
    avg_calls: int


class VolumeForecast(BaseModel):
    predicted_calls: int
    confidence: float
    trend: str
    hourly_pattern: List[HourlyPattern]


class CategoryDistribution(BaseModel):
    security: float
    medical: float
    protection_civil: float
    public_services: float
    social_support: float
    victim_attention: float


class RiskZone(BaseModel):
    zone: str
    risk_score: float
    incident_count: int
    primary_category: str


class PredictionsResponse(BaseModel):
    volume_forecast: VolumeForecast
    category_distribution: CategoryDistribution
    risk_zones: List[RiskZone]
    generated_at: str
    ai_model_version: str = "mock-v1.0"  # Renamed to avoid Pydantic reserved word


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    total_incidents: int
    timestamp: str


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_status = "disconnected"
    total_incidents = 0
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM analytics.incidents")
        total_incidents = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        db_status = "connected"
    except:
        pass
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "service": "api-analytics",
        "version": "1.0.0",
        "database": db_status,
        "total_incidents": total_incidents,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(request: IncidentRequest):
    """Store incident in analytics database"""
    try:
        incident_id = str(uuid.uuid4())
        has_p0_signals = len(request.p0_signals) > 0
        
        # Normalize location to prevent storing full addresses (privacy by design)
        normalized_location = normalize_location_hint(request.location_hint)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO analytics.incidents
            (incident_id, call_id, trace_id, risk_level, branch, case_category,
             human_required, has_p0_signals, location_hint)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING processed_at
        """, (
            incident_id,
            request.call_id,
            request.trace_id,
            request.risk_level,
            request.branch,
            request.case_category,
            request.human_required,
            has_p0_signals,
            normalized_location  # Use normalized location instead of raw
        ))
        
        processed_at = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Incident stored: incident_id={incident_id}, risk={request.risk_level}")
        
        return {
            "incident_id": incident_id,
            "stored_at": processed_at.isoformat() + "Z",
            "status": "stored"
        }
        
    except Exception as e:
        logger.error(f"Error storing incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    risk_level: Optional[int] = Query(None, ge=1, le=10),
    category: Optional[str] = None
):
    """List incidents with optional filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query with filters
        where_clauses = []
        params = []
        
        if risk_level is not None:
            where_clauses.append("risk_level = %s")
            params.append(risk_level)
        
        if category:
            where_clauses.append("case_category = %s")
            params.append(category)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM analytics.incidents{where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['count']
        
        # Get paginated results
        list_query = f"""
            SELECT incident_id, call_id, risk_level, branch, case_category,
                   human_required, timestamp
            FROM analytics.incidents
            {where_sql}
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_query, params + [limit, offset])
        
        items = []
        for row in cursor.fetchall():
            items.append({
                "incident_id": str(row['incident_id']),
                "call_id": str(row['call_id']),
                "risk_level": row['risk_level'],
                "branch": row['branch'],
                "case_category": row['case_category'],
                "human_required": row['human_required'],
                "timestamp": row['timestamp'].isoformat() + "Z"
            })
        
        cursor.close()
        conn.close()
        
        return {
            "total": total,
            "items": items
        }
        
    except Exception as e:
        logger.error(f"Error listing incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/summary", response_model=SummaryResponse)
async def get_summary():
    """Get summary analytics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total incidents
        cursor.execute("SELECT COUNT(*) as count FROM analytics.incidents")
        total_incidents = cursor.fetchone()['count']
        
        # By risk level
        cursor.execute("""
            SELECT risk_level, COUNT(*) as count
            FROM analytics.incidents
            GROUP BY risk_level
            ORDER BY risk_level
        """)
        by_risk_level = {str(row['risk_level']): row['count'] for row in cursor.fetchall()}
        
        # By branch
        cursor.execute("""
            SELECT branch, COUNT(*) as count
            FROM analytics.incidents
            GROUP BY branch
        """)
        by_branch = {row['branch']: row['count'] for row in cursor.fetchall()}
        
        # By category
        cursor.execute("""
            SELECT case_category, COUNT(*) as count
            FROM analytics.incidents
            WHERE case_category IS NOT NULL
            GROUP BY case_category
        """)
        by_category = {row['case_category']: row['count'] for row in cursor.fetchall()}
        
        # Human required count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM analytics.incidents
            WHERE human_required = TRUE
        """)
        human_required_count = cursor.fetchone()['count']
        
        # P0 signals count
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM analytics.incidents
            WHERE has_p0_signals = TRUE
        """)
        p0_signals_count = cursor.fetchone()['count']
        
        # NNA involved (would need to join with triage_results)
        nna_involved_count = 0  # Simplified for MVP
        
        cursor.close()
        conn.close()
        
        return {
            "total_incidents": total_incidents,
            "by_risk_level": by_risk_level,
            "by_branch": by_branch,
            "by_category": by_category,
            "human_required_count": human_required_count,
            "p0_signals_count": p0_signals_count,
            "nna_involved_count": nna_involved_count,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/predictions", response_model=PredictionsResponse)
async def get_predictions():
    """
    Get mock predictions based on historical data
    This is a simplified mock for MVP - production would use real ML models
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get recent incidents for pattern analysis
        cursor.execute("""
            SELECT 
                EXTRACT(HOUR FROM timestamp) as hour,
                COUNT(*) as count
            FROM analytics.incidents
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY EXTRACT(HOUR FROM timestamp)
            ORDER BY hour
        """)
        hourly_data = cursor.fetchall()
        
        # Calculate hourly pattern (mock)
        hourly_pattern = []
        for hour in range(24):
            # Find actual data or use average
            actual = next((row['count'] for row in hourly_data if int(row['hour']) == hour), None)
            if actual:
                avg_calls = int(actual)
            else:
                # Mock pattern: higher during day, lower at night
                if 6 <= hour <= 22:
                    avg_calls = random.randint(15, 35)
                else:
                    avg_calls = random.randint(5, 15)
            
            hourly_pattern.append({
                "hour": hour,
                "avg_calls": avg_calls
            })
        
        # Volume forecast (mock)
        current_hour = datetime.now().hour
        current_avg = next((p['avg_calls'] for p in hourly_pattern if p['hour'] == current_hour), 20)
        predicted_calls = int(current_avg * random.uniform(0.9, 1.1))
        
        # Determine trend
        if current_hour > 0:
            prev_avg = next((p['avg_calls'] for p in hourly_pattern if p['hour'] == current_hour - 1), 20)
            trend = "increasing" if predicted_calls > prev_avg else "decreasing"
        else:
            trend = "stable"
        
        volume_forecast = {
            "predicted_calls": predicted_calls,
            "confidence": 0.75,
            "trend": trend,
            "hourly_pattern": hourly_pattern
        }
        
        # Category distribution (based on recent data)
        cursor.execute("""
            SELECT case_category, COUNT(*) as count
            FROM analytics.incidents
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
            AND case_category IS NOT NULL
            GROUP BY case_category
        """)
        category_data = cursor.fetchall()
        
        total_recent = sum(row['count'] for row in category_data)
        
        if total_recent > 0:
            category_dist = {
                "security": 0.0,
                "medical": 0.0,
                "protection_civil": 0.0,
                "public_services": 0.0,
                "social_support": 0.0,
                "victim_attention": 0.0
            }
            
            for row in category_data:
                cat = row['case_category']
                if cat in category_dist:
                    category_dist[cat] = round(row['count'] / total_recent, 2)
        else:
            # Mock distribution if no recent data
            category_dist = {
                "security": 0.30,
                "medical": 0.25,
                "protection_civil": 0.15,
                "public_services": 0.20,
                "social_support": 0.05,
                "victim_attention": 0.05
            }
        
        # Risk zones (based on location_hint aggregation)
        cursor.execute("""
            SELECT 
                location_hint as zone,
                AVG(risk_level) as avg_risk,
                COUNT(*) as count,
                case_category
            FROM analytics.incidents
            WHERE location_hint IS NOT NULL
            AND timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY location_hint, case_category
            ORDER BY count DESC
            LIMIT 5
        """)
        zone_data = cursor.fetchall()
        
        risk_zones = []
        for row in zone_data:
            # Normalize location to prevent exposing full addresses
            normalized_zone = normalize_location_hint(row['zone'])
            risk_zones.append({
                "zone": normalized_zone,
                "risk_score": round(float(row['avg_risk']), 1),
                "incident_count": row['count'],
                "primary_category": row['case_category'] or "unknown"
            })
        
        # Add mock zones if not enough data
        if len(risk_zones) < 3:
            mock_zones = [
                {"zone": "Centro", "risk_score": 7.5, "incident_count": 45, "primary_category": "security"},
                {"zone": "Iztapalapa", "risk_score": 6.8, "incident_count": 38, "primary_category": "medical"},
                {"zone": "Cuauhtémoc", "risk_score": 6.2, "incident_count": 32, "primary_category": "public_services"}
            ]
            risk_zones.extend(mock_zones[:3 - len(risk_zones)])
        
        cursor.close()
        conn.close()
        
        return {
            "volume_forecast": volume_forecast,
            "category_distribution": category_dist,
            "risk_zones": risk_zones,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "model_version": "mock-v1.0"
        }
        
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/overview")
async def get_predictive_overview():
    """
    Get overview statistics from massive predictive dataset
    Returns aggregated metrics for predictive dashboard
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total incidents
        cursor.execute("SELECT COUNT(*) as count FROM analytics.predictive_incidents")
        total_incidents = cursor.fetchone()['count']
        
        # Last 24h
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM analytics.predictive_incidents
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        last_24h = cursor.fetchone()['count']
        
        # Last 7d
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM analytics.predictive_incidents
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        last_7d = cursor.fetchone()['count']
        
        # By branch
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE branch = 'critical') as critical_count,
                COUNT(*) FILTER (WHERE branch = 'mid') as mid_count,
                COUNT(*) FILTER (WHERE branch = 'low') as low_count
            FROM analytics.predictive_incidents
        """)
        branch_counts = cursor.fetchone()
        
        # Human required
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM analytics.predictive_incidents
            WHERE human_required = TRUE
        """)
        human_required_count = cursor.fetchone()['count']
        
        # P0 signals
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM analytics.predictive_incidents
            WHERE p0_signals IS NOT NULL AND array_length(p0_signals, 1) > 0
        """)
        p0_count = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return {
            "total_incidents": total_incidents,
            "last_24h": last_24h,
            "last_7d": last_7d,
            "critical_count": branch_counts['critical_count'],
            "mid_count": branch_counts['mid_count'],
            "low_count": branch_counts['low_count'],
            "human_required_count": human_required_count,
            "p0_count": p0_count,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting predictive overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/hourly")
async def get_predictive_hourly():
    """
    Get hourly distribution of predictive incidents
    Returns incident count and average risk by hour of day
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT
                EXTRACT(HOUR FROM created_at)::INTEGER as hour,
                COUNT(*) as incident_count,
                ROUND(AVG(risk_level)::NUMERIC, 2) as avg_risk
            FROM analytics.predictive_incidents
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY hour
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Fill in missing hours with 0
        hourly_data = {i: {"hour": i, "incident_count": 0, "avg_risk": 0.0} for i in range(24)}
        for row in rows:
            hourly_data[row['hour']] = {
                "hour": row['hour'],
                "incident_count": row['incident_count'],
                "avg_risk": float(row['avg_risk'])
            }
        
        return {
            "hourly_distribution": list(hourly_data.values()),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting predictive hourly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/categories")
async def get_predictive_categories():
    """
    Get distribution by category from predictive dataset
    Returns incident count and metrics per category
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT
                case_category,
                COUNT(*) as incident_count,
                ROUND(AVG(risk_level)::NUMERIC, 2) as avg_risk,
                COUNT(*) FILTER (WHERE branch = 'critical') as critical_count,
                COUNT(*) FILTER (WHERE human_required = TRUE) as human_required_count,
                COUNT(*) FILTER (WHERE p0_signals IS NOT NULL AND array_length(p0_signals, 1) > 0) as p0_count
            FROM analytics.predictive_incidents
            GROUP BY case_category
            ORDER BY incident_count DESC
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        categories = []
        for row in rows:
            categories.append({
                "category": row['case_category'],
                "incident_count": row['incident_count'],
                "avg_risk": float(row['avg_risk']),
                "critical_count": row['critical_count'],
                "human_required_count": row['human_required_count'],
                "p0_count": row['p0_count']
            })
        
        return {
            "categories": categories,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting predictive categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/alcaldias")
async def get_predictive_alcaldias():
    """
    Get top alcaldías by incident metrics from predictive dataset
    Returns alcaldía statistics sorted by incident count
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT
                alcaldia_norm,
                COUNT(*) as incident_count,
                ROUND(AVG(risk_level)::NUMERIC, 2) as avg_risk,
                COUNT(*) FILTER (WHERE branch = 'critical') as critical_count,
                COUNT(*) FILTER (WHERE p0_signals IS NOT NULL AND array_length(p0_signals, 1) > 0) as p0_count
            FROM analytics.predictive_incidents
            WHERE alcaldia_norm IS NOT NULL
            GROUP BY alcaldia_norm
            ORDER BY incident_count DESC
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        alcaldias = []
        for row in rows:
            alcaldias.append({
                "alcaldia": row['alcaldia_norm'],
                "incident_count": row['incident_count'],
                "avg_risk": float(row['avg_risk']),
                "critical_count": row['critical_count'],
                "p0_count": row['p0_count']
            })
        
        return {
            "alcaldias": alcaldias,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting predictive alcaldias: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/forecast")
async def get_predictive_forecast():
    """
    Get predictive forecast based on historical patterns
    Returns next hour/24h predictions and risk hotspots
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get hourly average for current hour
        current_hour = datetime.now().hour
        cursor.execute("""
            SELECT
                ROUND(AVG(hourly_count)::NUMERIC, 0) as avg_hourly
            FROM (
                SELECT
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as hourly_count
                FROM analytics.predictive_incidents
                WHERE EXTRACT(HOUR FROM created_at) = %s
                GROUP BY DATE_TRUNC('day', created_at), EXTRACT(HOUR FROM created_at)
            ) hourly_stats
        """, (current_hour,))
        
        result = cursor.fetchone()
        avg_hourly = int(result['avg_hourly']) if result['avg_hourly'] else 20
        
        # Calculate next hour prediction (with some variance)
        next_hour_expected = int(avg_hourly * random.uniform(0.9, 1.1))
        
        # Calculate 24h prediction
        cursor.execute("""
            SELECT ROUND(AVG(daily_count)::NUMERIC, 0) as avg_daily
            FROM (
                SELECT
                    DATE_TRUNC('day', created_at) as day,
                    COUNT(*) as daily_count
                FROM analytics.predictive_incidents
                GROUP BY DATE_TRUNC('day', created_at)
            ) daily_stats
        """)
        
        result = cursor.fetchone()
        avg_daily = int(result['avg_daily']) if result['avg_daily'] else 500
        next_24h_expected = int(avg_daily * random.uniform(0.95, 1.05))
        
        # Determine trend (compare last 24h vs last 7d average)
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') / 7.0 as avg_daily_7d
            FROM analytics.predictive_incidents
        """)
        
        trend_data = cursor.fetchone()
        last_24h = int(trend_data['last_24h'] or 0)
        avg_daily_7d = num(trend_data['avg_daily_7d'], 0.0)

        if last_24h > avg_daily_7d:
            trend = "increasing"
        elif last_24h < avg_daily_7d * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Get risk hotspots (top alcaldías by risk)
        cursor.execute("""
            SELECT
                alcaldia_norm,
                ROUND(AVG(risk_level)::NUMERIC, 2) as avg_risk,
                COUNT(*) as incident_count
            FROM analytics.predictive_incidents
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            AND alcaldia_norm IS NOT NULL
            GROUP BY alcaldia_norm
            HAVING AVG(risk_level) >= 6
            ORDER BY avg_risk DESC
            LIMIT 5
        """)
        
        hotspot_rows = cursor.fetchall()
        risk_hotspots = []
        for row in hotspot_rows:
            risk_hotspots.append({
                "alcaldia": row['alcaldia_norm'],
                "avg_risk": float(row['avg_risk']),
                "incident_count": row['incident_count']
            })
        
        # Calculate recommended staffing level
        if next_hour_expected > 30:
            staffing_level = "high"
        elif next_hour_expected > 15:
            staffing_level = "medium"
        else:
            staffing_level = "low"
        
        # Calculate confidence based on data volume
        cursor.execute("SELECT COUNT(*) as count FROM analytics.predictive_incidents")
        total_count = cursor.fetchone()['count']
        confidence = min(0.95, 0.5 + (total_count / 10000) * 0.45)
        
        cursor.close()
        conn.close()
        
        return {
            "next_hour_expected_calls": next_hour_expected,
            "next_24h_expected_calls": next_24h_expected,
            "trend": trend,
            "confidence": round(confidence, 2),
            "risk_hotspots": risk_hotspots,
            "recommended_staffing_level": staffing_level,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting predictive forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/events")
async def predictive_events_sse():
    """
    Server-Sent Events endpoint for real-time predictive updates
    Listens to PostgreSQL NOTIFY channel and streams events to clients
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    import select
    
    async def event_generator():
        """Generate SSE events from PostgreSQL NOTIFY"""
        conn = None
        try:
            # Connect to database
            conn = get_db_connection()
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Listen to predictive_updates channel
            cursor.execute("LISTEN predictive_updates;")
            logger.info("SSE: Listening to predictive_updates channel")
            
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
            
            # Heartbeat counter
            heartbeat_counter = 0
            
            while True:
                # Check for notifications with timeout
                if select.select([conn], [], [], 15.0) == ([], [], []):
                    # Timeout - send heartbeat
                    heartbeat_counter += 1
                    yield f"event: heartbeat\ndata: {json.dumps({'count': heartbeat_counter, 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
                else:
                    # Process notifications
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        payload = json.loads(notify.payload)
                        
                        logger.info(f"SSE: Received notification - {payload.get('operation')} on {payload.get('incident_id')}")
                        
                        # Send event to client
                        yield f"event: predictive_update\ndata: {json.dumps(payload)}\n\n"
                
                # Small async sleep to prevent blocking
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        finally:
            if conn:
                try:
                    cursor.execute("UNLISTEN predictive_updates;")
                    cursor.close()
                    conn.close()
                    logger.info("SSE: Connection closed")
                except:
                    pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/judge/metrics/postgis")
async def get_judge_metrics_postgis():
    """
    Get judge metrics calculated from PostGIS data
    Returns metrics for hackathon judges demonstrating territorial equity
    """
    try:
        metrics_file = Path("evidence/judge_metrics/judge_metrics_postgis.json")
        
        if not metrics_file.exists():
            return {
                "status": "not_generated",
                "message": "Run scripts/08_setup_postgis_demo.sh first",
                "hint": "PostGIS metrics need to be generated before they can be retrieved"
            }
        
        with open(metrics_file, "r") as f:
            metrics = json.load(f)
        
        logger.info("Judge metrics retrieved successfully")
        return metrics
        
    except Exception as e:
        logger.error(f"Error retrieving judge metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/judge/geo/alcaldias")
async def get_alcaldias_geojson():
    """
    Get alcaldías as GeoJSON FeatureCollection with incident statistics
    Returns synthetic geographic boundaries with metrics for visualization
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get alcaldías with geometry and statistics
        cursor.execute("""
            SELECT 
                a.alcaldia,
                a.alcaldia_norm,
                ST_AsGeoJSON(a.geom) as geometry,
                a.synthetic,
                COUNT(p.id) AS incident_count,
                COALESCE(AVG(p.risk_level), 0) AS avg_risk,
                COUNT(CASE WHEN p.p0_signals IS NOT NULL AND p.p0_signals != '' THEN 1 END) AS p0_count,
                d.digital_access_index,
                d.percentile
            FROM geo.alcaldias_geom a
            LEFT JOIN geo.synthetic_incident_points p ON p.alcaldia_joined = a.alcaldia_norm
            LEFT JOIN economia.digital_access_alcaldia d ON d.alcaldia_norm = a.alcaldia_norm
            GROUP BY a.id, a.alcaldia, a.alcaldia_norm, a.geom, a.synthetic, d.digital_access_index, d.percentile
            ORDER BY a.alcaldia_norm
        """)
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Build GeoJSON FeatureCollection
        features = []
        for row in rows:
            geometry = json.loads(row['geometry'])
            
            feature = {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "alcaldia": row['alcaldia'],
                    "alcaldia_norm": row['alcaldia_norm'],
                    "synthetic": row['synthetic'],
                    "incident_count": int(row['incident_count']),
                    "avg_risk": round(float(row['avg_risk']), 2),
                    "p0_count": int(row['p0_count']),
                    "digital_access_index": float(row['digital_access_index']) if row['digital_access_index'] else 0.0,
                    "percentile": int(row['percentile']) if row['percentile'] else 0
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "disclaimer": "Datos geoespaciales sintéticos para demo. No representan límites oficiales.",
                "synthetic_data": True,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "feature_count": len(features)
            }
        }
        
        logger.info(f"GeoJSON retrieved: {len(features)} alcaldías")
        return geojson
        
    except Exception as e:
        logger.error(f"Error retrieving GeoJSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Made with Bob
