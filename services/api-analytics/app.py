"""
911 AI Flow Demo - API Analytics Service
Stores incidents, calculates metrics, and generates mock predictions
"""

import os
import uuid
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Made with Bob
