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


# ============================================================================
# WHATSAPP LAB ENDPOINTS
# ============================================================================

class WhatsAppLabMessageRequest(BaseModel):
    """Request model for WhatsApp Lab message"""
    from_number: Optional[str] = Field(None, description="Phone number (will be hashed, auto-generated if not provided)")
    profile_name: Optional[str] = Field(None, description="User profile name")
    message: str = Field(..., description="Message text")
    location_hint: Optional[str] = Field(None, description="Location hint from user")
    incident_time: Optional[str] = Field(None, description="Incident time (ISO format)")

class WhatsAppLabMessageResponse(BaseModel):
    """Response model for WhatsApp Lab message"""
    message_id: str
    message_text: Optional[str] = None
    message_text_redacted: Optional[str] = None
    profile_name: Optional[str] = None
    category: Optional[str]
    branch: Optional[str]
    risk_level: Optional[int]
    human_required: bool
    p0_signals: List[str]
    bot_reply: str
    from_number_redacted: Optional[str] = None
    location_hint: Optional[str] = None
    location_source: Optional[str] = None
    incident_time: Optional[str] = None
    alcaldia_norm: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: str
@app.post("/whatsapp-lab/messages", response_model=WhatsAppLabMessageResponse)
async def create_whatsapp_lab_message(request: WhatsAppLabMessageRequest):
    """
    Process a WhatsApp-style message, classify it, and store in database.
    Auto-enriches missing data: phone, location, time, alcaldía, coordinates.
    """
    try:
        import hashlib
        import re
        import random
        
        # Auto-enrich: Generate or use provided phone number
        from_number = request.from_number or "+525512345678"
        from_hash = hashlib.sha256(from_number.encode()).hexdigest()[:16]
        from_number_redacted = f"***{from_number[-4:]}"
        
        # Auto-enrich: Profile name
        profile_name = request.profile_name or "Usuario Demo"
        
        # Auto-enrich: Incident time
        if request.incident_time:
            try:
                incident_time = datetime.fromisoformat(request.incident_time.replace('Z', '+00:00'))
            except:
                incident_time = datetime.utcnow()
        else:
            incident_time = datetime.utcnow()
        
        # Generate message ID
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        
        # Redact PII from message
        message_text = request.message
        message_redacted = message_text
        
        # Simple PII redaction patterns
        message_redacted = re.sub(r'\b\d{10,}\b', '[PHONE]', message_redacted)
        message_redacted = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', message_redacted)
        message_redacted = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]', message_redacted)
        
        # Auto-enrich: Detect location from text or generate synthetic
        location_hint = None
        location_source = "synthetic_911_geolocation"
        alcaldia_norm = None
        latitude = None
        longitude = None
        
        # Alcaldías de CDMX para detección
        alcaldias_cdmx = [
            "alvaro obregon", "azcapotzalco", "benito juarez", "coyoacan",
            "cuajimalpa", "cuauhtemoc", "gustavo a madero", "iztacalco",
            "iztapalapa", "magdalena contreras", "miguel hidalgo", "milpa alta",
            "tlahuac", "tlalpan", "venustiano carranza", "xochimilco"
        ]
        
        message_lower = message_text.lower()
        
        # Normalizar acentos para detección
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
        }
        for a, b in replacements.items():
            message_lower = message_lower.replace(a, b)
        
        # Detectar alcaldía en el texto
        for alc in alcaldias_cdmx:
            if alc in message_lower:
                alcaldia_norm = alc.replace(" ", "_")
                location_hint = alc.title()
                location_source = "user_text"
                break
        
        # Detectar colonias comunes (ejemplos)
        colonias = {
            "centro": ("cuauhtemoc", "Centro Histórico"),
            "condesa": ("cuauhtemoc", "Condesa"),
            "roma": ("cuauhtemoc", "Roma"),
            "polanco": ("miguel_hidalgo", "Polanco"),
            "santa fe": ("cuajimalpa", "Santa Fe"),
            "coyoacan": ("coyoacan", "Coyoacán Centro"),
        }
        
        for colonia_key, (alc, colonia_name) in colonias.items():
            if colonia_key in message_lower:
                alcaldia_norm = alc
                location_hint = colonia_name
                location_source = "user_text"
                break
        
        # Si no se detectó ubicación, generar sintética
        if not location_hint:
            # Generar alcaldía aleatoria
            alcaldia_norm = random.choice(alcaldias_cdmx).replace(" ", "_")
            location_hint = f"Zona {alcaldia_norm.replace('_', ' ').title()}"
            location_source = "synthetic_911_geolocation"
        
        # Generar coordenadas sintéticas para CDMX (aprox)
        # CDMX: lat 19.2-19.6, lon -99.3 a -98.9
        latitude = round(random.uniform(19.2, 19.6), 6)
        longitude = round(random.uniform(-99.3, -98.9), 6)
        
        # Keyword-based categorization
        message_lower = message_text.lower()

        # Normalizar acentos para que "explosión", "semáforo", "agresión", etc. funcionen
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
        }
        for a, b in replacements.items():
            message_lower = message_lower.replace(a, b)

        category = "unknown"
        branch = "low"
        risk_level = 1
        human_required = False
        p0_signals = []

        # PRIORITY 0) Self-harm / Crisis emocional crítica - MÁXIMA PRIORIDAD
        if any(kw in message_lower for kw in [
            "me quiero suicidar", "quiero suicidarme", "me voy a matar", "quiero matarme",
            "ya no quiero vivir", "me quiero hacer dano", "voy a hacerme dano",
            "autolesion", "quiero morir", "voy a morir", "me quiero ir",
            "no aguanto mas", "no puedo mas", "quiero acabar con todo"
        ]):
            category = "victim_attention"  # Crisis emocional es atención a víctimas
            branch = "critical"
            risk_level = 9
            human_required = True
            p0_signals.append("self_harm_risk")

        # 1) Protección Civil / señales P0
        elif any(kw in message_lower for kw in [
            "incendio", "fuego", "humo", "explosion", "explota", "gas", "derrumbe", "inundacion"
        ]):
            category = "protection_civil"
            branch = "critical"
            risk_level = 9
            human_required = True

            if any(kw in message_lower for kw in ["incendio", "fuego", "humo"]):
                p0_signals.append("incendio")
            if any(kw in message_lower for kw in ["explosion", "explota"]):
                p0_signals.append("explosion")
            if "gas" in message_lower:
                p0_signals.append("gas")

        # 2) Atención a víctimas ANTES que seguridad
        elif any(kw in message_lower for kw in [
            "violencia familiar", "violencia domestica", "violencia",
            "golpes", "golpeando", "amenaza", "amenazando",
            "gritos", "abuso", "maltrato", "agresion familiar", "victima"
        ]):
            category = "victim_attention"
            branch = "mid"
            risk_level = 5
            human_required = True

        # 3) Médico
        elif any(kw in message_lower for kw in [
            "herido", "herida", "inconsciente", "desmayado", "desmayada",
            "ambulancia", "sangre", "sangrando", "sangrado", "no respira",
            "medico", "medica", "infarto", "convulsiones", "dolor"
        ]):
            category = "medical"
            human_required = True

            # Caso médico crítico / P0
            if any(kw in message_lower for kw in [
                "inconsciente", "no respira", "desmayado", "desmayada",
                "sangrando", "sangrado grave", "sangre", "herido grave", "herida grave"
            ]):
                branch = "critical"
                risk_level = 8
                p0_signals.append("medical_critical")
            else:
                branch = "mid"
                risk_level = 4

        # 4) Seguridad
        elif any(kw in message_lower for kw in [
            "robo", "robando", "asalto", "asaltando", "arma", "pistola",
            "cuchillo", "disparo", "disparos", "balazo", "secuestro"
        ]):
            category = "security"
            human_required = True

            if any(kw in message_lower for kw in ["arma", "pistola", "disparo", "disparos", "balazo", "cuchillo"]):
                branch = "critical"
                risk_level = 7
            else:
                branch = "mid"
                risk_level = 5

        # 5) Servicios públicos
        elif any(kw in message_lower for kw in [
            "bache", "alumbrado", "poste", "fuga", "agua", "basura",
            "coladera", "semaforo", "arbol caido"
        ]):
            category = "public_services"
            branch = "low"
            risk_level = 2
            human_required = False

        # 6) Apoyo social
        elif any(kw in message_lower for kw in [
            "persona vulnerable", "persona en calle", "indigente", "indigencia",
            "extraviado", "perdido", "adulto mayor", "ayuda"
        ]):
            category = "social_support"
            branch = "mid"
            risk_level = 4
            human_required = True

        # Generate bot reply
        category_names = {
            'security': 'Seguridad',
            'medical': 'Médico',
            'protection_civil': 'Protección Civil',
            'public_services': 'Servicios Públicos',
            'social_support': 'Apoyo Social',
            'victim_attention': 'Atención a Víctimas',
            'unknown': 'General'
        }
        
        branch_names = {
            'critical': 'crítica',
            'mid': 'media',
            'low': 'baja'
        }
        
        # Generate bot reply with special handling for self-harm
        if "self_harm_risk" in p0_signals:
            bot_reply = f"🆘 ATENCIÓN PRIORITARIA: Detectamos una situación de crisis emocional. Un operador humano especializado te contactará de inmediato. No estás solo/a. Folio: {message_id}"
        else:
            bot_reply = f"✅ Recibimos tu reporte. Se clasificó como {category_names.get(category, 'General')} con prioridad {branch_names.get(branch, 'baja')}."
            
            if human_required:
                bot_reply += " Un operador humano debe revisar el caso."
            
            if p0_signals:
                bot_reply += " ⚠️ Señales críticas detectadas. Prioridad máxima."
            
            bot_reply += f" Folio: {message_id}"
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO analytics.whatsapp_lab_messages
            (message_id, from_hash, from_number_redacted, profile_name,
             message_text, message_text_redacted,
             location_hint, location_source, incident_time,
             alcaldia_norm, latitude, longitude,
             category, branch, risk_level, human_required, p0_signals, bot_reply,
             source, synthetic, created_at, processed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            message_id, from_hash, from_number_redacted, profile_name,
            message_text, message_redacted,
            location_hint, location_source, incident_time,
            alcaldia_norm, latitude, longitude,
            category, branch, risk_level, human_required, p0_signals, bot_reply,
            'webchat', True
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"WhatsApp Lab message created: {message_id}, category: {category}, branch: {branch}")
        
        return WhatsAppLabMessageResponse(
            message_id=message_id,
            message_text=message_text,
            message_text_redacted=message_redacted,
            profile_name=profile_name,
            category=category,
            branch=branch,
            risk_level=risk_level,
            human_required=human_required,
            p0_signals=p0_signals,
            bot_reply=bot_reply,

            # Enriched demo fields
            from_number_redacted=from_number_redacted,
            location_hint=location_hint,
            location_source=location_source,
            incident_time=incident_time.isoformat() + "Z",
            alcaldia_norm=alcaldia_norm,
            latitude=latitude,
            longitude=longitude,

            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Error creating WhatsApp Lab message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/whatsapp-lab/messages/recent")
async def get_recent_whatsapp_lab_messages(limit: int = Query(50, ge=1, le=200)):
    """
    Get recent WhatsApp Lab messages with enriched data
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT
                message_id,
                from_hash,
                from_number_redacted,
                profile_name,
                message_text_redacted as message_text,
                location_hint,
                location_source,
                incident_time,
                alcaldia_norm,
                latitude,
                longitude,
                category,
                branch,
                risk_level,
                human_required,
                p0_signals,
                bot_reply,
                source,
                created_at
            FROM analytics.whatsapp_lab_messages
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert to list of dicts
        result = []
        for msg in messages:
            result.append({
                "message_id": msg['message_id'],
                "from_hash": msg['from_hash'],
                "from_number_redacted": msg['from_number_redacted'],
                "profile_name": msg['profile_name'],
                "message_text": msg['message_text'],
                "location_hint": msg['location_hint'],
                "location_source": msg['location_source'],
                "incident_time": msg['incident_time'].isoformat() + "Z" if msg['incident_time'] else None,
                "alcaldia_norm": msg['alcaldia_norm'],
                "latitude": msg['latitude'],
                "longitude": msg['longitude'],
                "category": msg['category'],
                "branch": msg['branch'],
                "risk_level": msg['risk_level'],
                "human_required": msg['human_required'],
                "p0_signals": msg['p0_signals'] or [],
                "bot_reply": msg['bot_reply'],
                "source": msg['source'],
                "created_at": msg['created_at'].isoformat() + "Z" if msg['created_at'] else None
            })
        
        logger.info(f"Retrieved {len(result)} recent WhatsApp Lab messages")
        return {"messages": result, "count": len(result)}
        
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/whatsapp-lab/summary")
async def get_whatsapp_lab_summary():
    """
    Get summary statistics for WhatsApp Lab
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Total messages
        cursor.execute("SELECT COUNT(*) as count FROM analytics.whatsapp_lab_messages")
        total_messages = cursor.fetchone()['count']
        
        # Last 24h
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM analytics.whatsapp_lab_messages
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        last_24h = cursor.fetchone()['count']
        
        # By branch
        cursor.execute("""
            SELECT branch, COUNT(*) as count
            FROM analytics.whatsapp_lab_messages
            WHERE branch IS NOT NULL
            GROUP BY branch
        """)
        by_branch = {row['branch']: row['count'] for row in cursor.fetchall()}
        
        # By category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM analytics.whatsapp_lab_messages
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)
        by_category = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # Human required
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM analytics.whatsapp_lab_messages
            WHERE human_required = TRUE
        """)
        human_required_count = cursor.fetchone()['count']
        
        # P0 signals
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM analytics.whatsapp_lab_messages
            WHERE p0_signals IS NOT NULL AND array_length(p0_signals, 1) > 0
        """)
        p0_count = cursor.fetchone()['count']
        
        cursor.close()
        conn.close()
        
        return {
            "total_messages": total_messages,
            "last_24h": last_24h,
            "by_branch": by_branch,
            "by_category": by_category,
            "human_required_count": human_required_count,
            "p0_count": p0_count,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting WhatsApp Lab summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/whatsapp-lab/events")
async def whatsapp_lab_events_sse():
    """
    Server-Sent Events endpoint for real-time WhatsApp Lab updates
    """
    from fastapi.responses import StreamingResponse
    import select
    
    async def event_generator():
        conn = get_db_connection()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        try:
            # Listen to the notification channel
            cursor.execute("LISTEN whatsapp_lab_updates;")
            logger.info("SSE client connected to whatsapp_lab_updates channel")
            
            # Send initial connection message
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
            
            while True:
                # Wait for notification with timeout
                if select.select([conn], [], [], 15.0) == ([], [], []):
                    # Timeout - send heartbeat
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
                else:
                    # Check for notifications
                    conn.poll()
                    while conn.notifies:
                        notify = conn.notifies.pop(0)
                        logger.info(f"SSE notification: {notify.payload}")
                        yield f"event: whatsapp_lab_update\ndata: {notify.payload}\n\n"
        
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        finally:
            cursor.close()
            conn.close()
            logger.info("SSE client disconnected from whatsapp_lab_updates")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/activity/recent")
async def get_recent_activity(limit: int = Query(10, ge=1, le=50)):
    """
    Get recent activity: both 911 calls and WhatsApp Lab messages
    Consolidated endpoint for main dashboard
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get recent 911 calls from analytics.incidents
        cursor.execute("""
            SELECT 
                i.incident_id,
                i.call_id,
                i.risk_level,
                i.branch,
                i.case_category,
                i.human_required,
                i.has_p0_signals,
                i.location_hint,
                i.timestamp,
                c.redacted_text as transcript,
                t.p0_signals
            FROM analytics.incidents i
            LEFT JOIN raw.conversations c ON i.call_id = c.call_id
            LEFT JOIN core.triage_results t ON i.call_id = t.call_id
            ORDER BY i.timestamp DESC
            LIMIT %s
        """, (limit,))
        
        calls = []
        for row in cursor.fetchall():
            calls.append({
                "type": "911_call",
                "incident_id": str(row['incident_id']) if row['incident_id'] else None,
                "call_id": str(row['call_id']) if row['call_id'] else None,
                "transcript": row['transcript'],
                "category": row['case_category'],
                "branch": row['branch'],
                "risk_level": row['risk_level'],
                "human_required": row['human_required'],
                "p0_signals": row['p0_signals'] or [],
                "location_hint": row['location_hint'],
                "timestamp": row['timestamp'].isoformat() + "Z" if row['timestamp'] else None
            })
        
        # Get recent WhatsApp Lab messages
        cursor.execute("""
            SELECT 
                message_id,
                from_number_redacted,
                profile_name,
                message_text_redacted as message_text,
                location_hint,
                location_source,
                incident_time,
                alcaldia_norm,
                category,
                branch,
                risk_level,
                human_required,
                p0_signals,
                created_at
            FROM analytics.whatsapp_lab_messages
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "type": "whatsapp_message",
                "message_id": row['message_id'],
                "from_number_redacted": row['from_number_redacted'],
                "profile_name": row['profile_name'],
                "message_text": row['message_text'],
                "location_hint": row['location_hint'],
                "location_source": row['location_source'],
                "incident_time": row['incident_time'].isoformat() + "Z" if row['incident_time'] else None,
                "alcaldia_norm": row['alcaldia_norm'],
                "category": row['category'],
                "branch": row['branch'],
                "risk_level": row['risk_level'],
                "human_required": row['human_required'],
                "p0_signals": row['p0_signals'] or [],
                "timestamp": row['created_at'].isoformat() + "Z" if row['created_at'] else None
            })
        
        # Get summary stats for last 24h
        cursor.execute("""
            SELECT 
                COUNT(*) as total_calls,
                COUNT(*) FILTER (WHERE branch = 'critical') as critical_calls,
                COUNT(*) FILTER (WHERE human_required = TRUE) as human_required_calls,
                COUNT(*) FILTER (WHERE has_p0_signals = TRUE) as p0_calls
            FROM analytics.incidents
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """)
        calls_summary = cursor.fetchone()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_messages,
                COUNT(*) FILTER (WHERE branch = 'critical') as critical_messages,
                COUNT(*) FILTER (WHERE human_required = TRUE) as human_required_messages,
                COUNT(*) FILTER (WHERE p0_signals IS NOT NULL AND array_length(p0_signals, 1) > 0) as p0_messages
            FROM analytics.whatsapp_lab_messages
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        messages_summary = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Calculate totals
        total_recent = (calls_summary['total_calls'] or 0) + (messages_summary['total_messages'] or 0)
        critical_recent = (calls_summary['critical_calls'] or 0) + (messages_summary['critical_messages'] or 0)
        human_required_recent = (calls_summary['human_required_calls'] or 0) + (messages_summary['human_required_messages'] or 0)
        p0_recent = (calls_summary['p0_calls'] or 0) + (messages_summary['p0_messages'] or 0)
        
        logger.info(f"Retrieved recent activity: {len(calls)} calls, {len(messages)} messages")
        
        return {
            "calls": calls,
            "messages": messages,
            "summary": {
                "total_recent": total_recent,
                "critical_recent": critical_recent,
                "human_required_recent": human_required_recent,
                "p0_recent": p0_recent,
                "calls_24h": calls_summary['total_calls'] or 0,
                "messages_24h": messages_summary['total_messages'] or 0
            },
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))




if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Made with Bob
