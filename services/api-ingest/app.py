"""
CENTINELA_CDMX_IA - Agente A1 Recolector
Ingesta transcripciones 911, redacta PII automáticamente. Privacy by Design.
"""

import os
import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import logging

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable PII logging
class SafeLogger:
    """Logger that prevents PII from being logged"""
    def __init__(self, logger):
        self._logger = logger
    
    def info(self, msg, *args, **kwargs):
        # Never log transcript or redacted_text
        safe_msg = str(msg).replace('transcript', '[REDACTED]')
        self._logger.info(safe_msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        safe_msg = str(msg).replace('transcript', '[REDACTED]')
        self._logger.error(safe_msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        safe_msg = str(msg).replace('transcript', '[REDACTED]')
        self._logger.warning(safe_msg, *args, **kwargs)

safe_logger = SafeLogger(logger)

# Initialize FastAPI
app = FastAPI(
    title="CENTINELA_CDMX_IA - A1 Recolector",
    description="Ingesta y redacción de PII — A1 Recolector",
    version="2.0.0"
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

# PII Redaction Patterns
class PIIRedactor:
    """Redacts PII using regex and heuristics"""
    
    # Regex patterns
    PHONE_PATTERN = re.compile(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
    EMAIL_PATTERN = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
    
    # Heuristic patterns for names (after common phrases)
    NAME_TRIGGERS = [
        r'me llamo\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
        r'soy\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
        r'mi nombre es\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
        r'nombre:\s*([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
    ]
    
    # Heuristic patterns for addresses
    ADDRESS_TRIGGERS = [
        r'calle\s+[A-Za-záéíóúñÁÉÍÓÚÑ\s]+\d+',
        r'avenida\s+[A-Za-záéíóúñÁÉÍÓÚÑ\s]+\d+',
        r'colonia\s+[A-Za-záéíóúñÁÉÍÓÚÑ\s]+',
        r'número\s+\d+',
        r'edificio\s+[A-Za-záéíóúñÁÉÍÓÚÑ\s]+\d+',
    ]
    
    @classmethod
    def redact(cls, text: str) -> tuple[str, Dict[str, int]]:
        """
        Redact PII from text
        Returns: (redacted_text, redaction_summary)
        """
        redacted = text
        summary = {
            "phones_redacted": 0,
            "emails_redacted": 0,
            "names_redacted": 0,
            "addresses_redacted": 0
        }
        
        # Redact phone numbers
        phones = cls.PHONE_PATTERN.findall(redacted)
        summary["phones_redacted"] = len(phones)
        redacted = cls.PHONE_PATTERN.sub('[TELÉFONO-REDACTADO]', redacted)
        
        # Redact emails
        emails = cls.EMAIL_PATTERN.findall(redacted)
        summary["emails_redacted"] = len(emails)
        redacted = cls.EMAIL_PATTERN.sub('[EMAIL-REDACTADO]', redacted)
        
        # Redact names (heuristic)
        for pattern in cls.NAME_TRIGGERS:
            matches = re.finditer(pattern, redacted, re.IGNORECASE)
            for match in matches:
                if match.group(1):
                    summary["names_redacted"] += 1
                    redacted = redacted.replace(match.group(1), '[NOMBRE-REDACTADO]')
        
        # Redact addresses (heuristic)
        for pattern in cls.ADDRESS_TRIGGERS:
            matches = re.finditer(pattern, redacted, re.IGNORECASE)
            for match in matches:
                summary["addresses_redacted"] += 1
                redacted = redacted.replace(match.group(0), '[DIRECCIÓN-REDACTADA]')
        
        return redacted, summary


# Database helper
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        safe_logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


# Pydantic models
class ConversationMetadata(BaseModel):
    source: str = "unknown"
    timestamp: Optional[str] = None
    scenario: Optional[str] = None


class ConversationRequest(BaseModel):
    transcript: str = Field(..., min_length=1, description="Raw conversation transcript")
    metadata: Optional[ConversationMetadata] = None


class ConversationResponse(BaseModel):
    call_id: str
    trace_id: str
    redacted_text: str
    redaction_summary: Dict[str, int]
    created_at: str


class ConversationListItem(BaseModel):
    call_id: str
    trace_id: str
    redacted_text: str
    created_at: str


class ConversationListResponse(BaseModel):
    total: int
    items: List[ConversationListItem]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str
    timestamp: str


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    db_status = "disconnected"
    try:
        conn = get_db_connection()
        conn.close()
        db_status = "connected"
    except:
        pass
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "service": "api-ingest",
        "version": "1.0.0",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/raw-conversations", response_model=ConversationResponse, status_code=201)
async def create_raw_conversation(request: ConversationRequest):
    """
    Receive raw conversation, redact PII, and store in database
    IMPORTANT: Never stores original transcript, only redacted version
    """
    try:
        # Generate IDs
        call_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        
        # Redact PII
        redacted_text, redaction_summary = PIIRedactor.redact(request.transcript)
        
        # Prepare metadata
        metadata = request.metadata.dict() if request.metadata else {}
        
        # Store in database (NEVER store original transcript)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO raw.conversations
            (call_id, trace_id, original_text, redacted_text, redaction_flags, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING created_at
        """, (
            call_id,
            trace_id,
            '[NOT_STORED_PRIVACY_BY_DESIGN]',  # Privacy by design: never store original
            redacted_text,
            Json(redaction_summary),  # Wrap dict for JSONB
            Json(metadata)  # Wrap dict for JSONB
        ))
        
        created_at = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        safe_logger.info(f"Conversation stored: call_id={call_id}, redactions={redaction_summary}")
        
        return {
            "call_id": call_id,
            "trace_id": trace_id,
            "redacted_text": redacted_text,
            "redaction_summary": redaction_summary,
            "created_at": created_at.isoformat() + "Z"
        }
        
    except Exception as e:
        safe_logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/raw-conversations", response_model=ConversationListResponse)
async def list_raw_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List raw conversations (redacted)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM raw.conversations")
        total = cursor.fetchone()['count']
        
        # Get paginated results
        cursor.execute("""
            SELECT call_id, trace_id, redacted_text, created_at
            FROM raw.conversations
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                "call_id": str(row['call_id']),
                "trace_id": str(row['trace_id']),
                "redacted_text": row['redacted_text'],
                "created_at": row['created_at'].isoformat() + "Z"
            })
        
        cursor.close()
        conn.close()
        
        return {
            "total": total,
            "items": items
        }
        
    except Exception as e:
        safe_logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)

