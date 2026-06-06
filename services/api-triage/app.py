"""
911 AI Flow Demo - API Triage Service
Deterministic AI classification using keyword matrix and P0 signal detection
CRITICAL: Never downgrade or close calls with P0 signals
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
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

# Initialize FastAPI
app = FastAPI(
    title="911 AI Flow Demo - API Triage",
    description="Deterministic AI triage classification",
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


# P0 Signals - CRITICAL: These MUST trigger human attention
P0_SIGNALS = {
    # Weapons
    "arma": "arma", "pistola": "arma de fuego", "cuchillo": "arma blanca",
    "navaja": "arma blanca", "rifle": "arma de fuego", "disparo": "arma de fuego",
    "disparos": "arma de fuego", "balazo": "arma de fuego",
    
    # Fire/Explosion
    "fuego": "incendio", "incendio": "incendio", "humo": "incendio",
    "explosion": "explosión", "explosión": "explosión", "bomba": "explosivo",
    
    # Hazmat
    "gas": "fuga de gas", "quimico": "químico peligroso", "químico": "químico peligroso",
    "toxico": "sustancia tóxica", "tóxico": "sustancia tóxica",
    
    # Life-threatening medical - CRITICAL
    "suicida": "intento suicida", "suicidio": "intento suicida", "matarme": "intento suicida",
    "inconsciente": "medical_critical", "desmayado": "medical_critical", "desmayada": "medical_critical",
    "no respira": "medical_critical", "dificultad respirar": "medical_critical",
    "ahogo": "medical_critical", "sangrado": "sangrado grave", "sangrando": "sangrado grave",
    "sangre": "sangrado grave", "hemorragia": "sangrado grave",
    "herido grave": "medical_critical", "herida grave": "medical_critical",
    
    # Kidnapping/Violence
    "secuestro": "privación de libertad", "privacion libertad": "privación de libertad",
    "privación libertad": "privación de libertad",
    "retenido": "privación de libertad", "desaparicion": "persona desaparecida",
    "desaparecido": "persona desaparecida", "violacion": "violencia sexual",
    "violación": "violencia sexual", "abuso sexual": "violencia sexual",
    
    # Domestic/Gender violence
    "golpes": "violencia física", "violencia familiar": "violencia familiar",
    "mujer golpeada": "violencia contra mujer", "violencia mujer": "violencia contra mujer",
    "niño golpeado": "maltrato infantil", "niña golpeada": "maltrato infantil",
    "maltrato infantil": "maltrato infantil", "adulto mayor maltrato": "maltrato adulto mayor",
    
    # Vulnerable populations
    "discapacidad riesgo": "persona con discapacidad en riesgo",
    
    # Communication issues (potential danger)
    "llamada silenciosa": "llamada silenciosa", "no puede hablar": "imposibilidad de hablar",
    "gritos": "gritos de auxilio", "llanto": "llanto de auxilio", "auxilio": "solicitud de auxilio"
}


# Category keywords - PRIORITY ORDER MATTERS
# victim_attention must be checked BEFORE security
CATEGORY_KEYWORDS = {
    "victim_attention": [
        "violencia familiar", "violencia domestica", "violencia doméstica",
        "golpes", "golpeando", "maltrato", "abuso", "agresion familiar",
        "agresión familiar", "victima", "víctima", "violación", "secuestro",
        "trata", "extorsión", "fraude", "amenaza familiar", "gritos casa"
    ],
    "medical": [
        "herido", "herida", "inconsciente", "desmayado", "desmayada",
        "ambulancia", "sangre", "sangrando", "sangrado", "no respira",
        "medico", "médico", "medica", "médica", "infarto", "convulsiones",
        "dolor", "enfermo", "accidente", "caída", "fractura", "desmayo",
        "convulsión", "parto", "embarazo"
    ],
    "protection_civil": [
        "incendio", "fuego", "humo", "inundación", "derrumbe", "gas",
        "árbol caído", "explosion", "explosión", "fuga", "terremoto",
        "deslizamiento", "derrumbe"
    ],
    "security": [
        "robo", "robando", "asalto", "asaltando", "delincuente", "ladrón",
        "arma", "pistola", "cuchillo", "disparo", "disparos", "balazo",
        "pandilla", "balacera", "amenaza"
    ],
    "public_services": [
        "alumbrado", "bache", "agua", "basura", "alcantarilla",
        "semáforo", "tráfico", "estacionamiento", "poste", "fuga agua",
        "coladera", "arbol caido"
    ],
    "social_support": [
        "adicción", "depresión", "orientación", "apoyo psicológico",
        "persona en situación de calle", "abandono", "persona vulnerable",
        "indigente", "indigencia", "extraviado", "perdido", "adulto mayor ayuda"
    ]
}


# NNA (Niñas, Niños, Adolescentes) keywords
NNA_KEYWORDS = [
    "niño", "niña", "menor", "bebé", "adolescente", "infante",
    "hijo", "hija", "escolar", "estudiante menor"
]


# Elderly keywords
ELDERLY_KEYWORDS = [
    "adulto mayor", "anciano", "anciana", "abuela", "abuelo",
    "tercera edad", "persona mayor"
]


# Gender violence keywords
GENDER_VIOLENCE_KEYWORDS = [
    "mujer golpeada", "violencia mujer", "esposo golpea",
    "pareja violenta", "feminicidio", "violencia género"
]


class TriageEngine:
    """Deterministic triage classification engine"""
    
    @staticmethod
    def detect_p0_signals(text: str) -> List[str]:
        """Detect P0 critical signals with accent normalization"""
        text_lower = text.lower()
        
        # Normalize accents for better detection
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
        }
        for a, b in replacements.items():
            text_lower = text_lower.replace(a, b)
        
        detected = []
        
        for keyword, signal in P0_SIGNALS.items():
            if keyword in text_lower:
                detected.append(signal)
        
        return list(set(detected))  # Remove duplicates
    
    @staticmethod
    def detect_nna(text: str) -> bool:
        """Detect if NNA (children/adolescents) are involved"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in NNA_KEYWORDS)
    
    @staticmethod
    def detect_elderly(text: str) -> bool:
        """Detect if elderly person is involved"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in ELDERLY_KEYWORDS)
    
    @staticmethod
    def detect_gender_violence(text: str) -> bool:
        """Detect gender violence indicators"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in GENDER_VIOLENCE_KEYWORDS)
    
    @staticmethod
    def classify_category(text: str) -> str:
        """
        Classify incident category based on keywords
        PRIORITY ORDER: victim_attention > medical > protection_civil > security > others
        """
        text_lower = text.lower()
        
        # Normalize accents for better detection
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
        }
        for a, b in replacements.items():
            text_lower = text_lower.replace(a, b)
        
        # Check categories in priority order
        priority_order = [
            "victim_attention",
            "medical",
            "protection_civil",
            "security",
            "public_services",
            "social_support"
        ]
        
        for category in priority_order:
            keywords = CATEGORY_KEYWORDS.get(category, [])
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "unknown"
    
    @staticmethod
    def calculate_risk_level(text: str, p0_signals: List[str], nna_involved: bool) -> int:
        """
        Calculate risk level 1-10
        CRITICAL RULE: P0 signals ALWAYS result in risk >= 6
        MEDICAL CRITICAL RULE: medical_critical P0 signal = risk >= 8
        MEDIUM RISK RULE: Traffic accidents without P0 signals = level 5
        """
        text_lower = text.lower()
        
        # Normalize accents
        replacements = {
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
        }
        for a, b in replacements.items():
            text_lower = text_lower.replace(a, b)
        
        base_score = 1.0
        
        # Check for medical_critical P0 signal (inconsciente, no respira, etc.)
        has_medical_critical = any("medical_critical" in sig for sig in p0_signals)
        
        # Medical critical: MINIMUM risk level 8
        if has_medical_critical:
            base_score = max(8.0, base_score)
        # Other P0 signals: MINIMUM risk level 6
        elif p0_signals:
            base_score = max(6.0, base_score)
            base_score += len(p0_signals) * 0.5
        
        # NNA involvement: ALWAYS elevate
        if nna_involved:
            base_score += 2.0
        
        # Medium risk traffic accidents (without P0 signals)
        traffic_keywords = [
            "accidente", "choque", "colision", "volcadura", "transito",
            "carros chocados", "vehiculo detenido", "bloqueo vial", "semaforo caido"
        ]
        has_traffic_incident = any(kw in text_lower for kw in traffic_keywords)
        
        # If traffic incident without P0 signals, set to level 5 (mid)
        if has_traffic_incident and not p0_signals:
            return 5
        
        # Count medical keywords
        medical_count = sum(1 for kw in CATEGORY_KEYWORDS["medical"] if kw in text_lower)
        base_score += medical_count * 0.3
        
        # Count security keywords
        security_count = sum(1 for kw in CATEGORY_KEYWORDS["security"] if kw in text_lower)
        base_score += security_count * 0.4
        
        # Count protection civil keywords
        protection_count = sum(1 for kw in CATEGORY_KEYWORDS["protection_civil"] if kw in text_lower)
        base_score += protection_count * 0.3
        
        # Cap at 10
        risk_level = min(10, int(base_score))
        
        # CRITICAL: Never below 8 if medical_critical P0 signal
        if has_medical_critical and risk_level < 8:
            risk_level = 8
        # CRITICAL: Never below 6 if other P0 signals present
        elif p0_signals and risk_level < 6:
            risk_level = 6
        
        return risk_level
    
    @staticmethod
    def determine_branch(risk_level: int) -> str:
        """Determine branch based on risk level"""
        if risk_level <= 4:
            return "low"
        elif risk_level == 5:
            return "mid"
        else:
            return "critical"
    
    @staticmethod
    def determine_priority(risk_level: int) -> str:
        """Determine priority class"""
        if risk_level <= 2:
            return "minimum"
        elif risk_level <= 4:
            return "low"
        elif risk_level == 5:
            return "medium"
        elif risk_level <= 7:
            return "high"
        else:
            return "critical"
    
    @staticmethod
    def determine_authorities(category: str, p0_signals: List[str]) -> tuple[str, List[str]]:
        """Determine primary and support authorities"""
        primary = "C5"
        support = []
        
        if category == "medical":
            primary = "ERUM"
            support = ["Cruz Roja", "Protección Civil"]
        elif category == "security":
            primary = "SSC"
            support = ["Fiscalía"]
        elif category == "protection_civil":
            primary = "Protección Civil"
            support = ["Bomberos", "ERUM"]
        elif category == "victim_attention":
            primary = "Fiscalía"
            support = ["ADEVI", "SSC"]
        
        # Add specialized support for P0 signals
        if any("incendio" in s for s in p0_signals):
            if "Bomberos" not in support:
                support.append("Bomberos")
        
        if any("violencia" in s or "maltrato" in s for s in p0_signals):
            if "ADEVI" not in support:
                support.append("ADEVI")
        
        return primary, support


# Database helper
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


# Pydantic models
class TriageRequest(BaseModel):
    transcript: str = Field(..., min_length=1)
    call_id: str
    trace_id: Optional[str] = None  # Optional: preserve from ingest or generate new
    consent: bool = True
    location_hint: Optional[str] = None


class ProtectedGroupFlags(BaseModel):
    nna_involved: bool = False
    elderly: bool = False
    disability: bool = False
    gender_violence: bool = False


class TrustFlags(BaseModel):
    confidence_score: float = 0.85
    ambiguity_detected: bool = False


class TriageResponse(BaseModel):
    call_id: str
    trace_id: str
    risk_level: int
    branch: str
    priority_class: str
    case_category: str
    medical_category: Optional[str] = None
    protected_group_flags: ProtectedGroupFlags
    best_interest_child: bool
    human_required: bool
    primary_authority: str
    support_authorities: List[str]
    public_stage_phrase: str
    rationale_public: str
    trust_flags: TrustFlags
    p0_signals: List[str]
    keywords_detected: Dict[str, List[str]]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    rules_loaded: int
    timestamp: str


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "api-triage",
        "version": "1.0.0",
        "rules_loaded": len(P0_SIGNALS) + sum(len(v) for v in CATEGORY_KEYWORDS.values()),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/triage", response_model=TriageResponse)
async def triage_call(request: TriageRequest):
    """
    Perform deterministic triage classification
    CRITICAL: Never downgrade calls with P0 signals
    """
    try:
        # Preserve trace_id from ingest or generate new one
        trace_id = request.trace_id if request.trace_id else str(uuid.uuid4())
        
        # Detect P0 signals
        p0_signals = TriageEngine.detect_p0_signals(request.transcript)
        
        # Detect protected groups
        nna_involved = TriageEngine.detect_nna(request.transcript)
        elderly_involved = TriageEngine.detect_elderly(request.transcript)
        gender_violence = TriageEngine.detect_gender_violence(request.transcript)
        
        # Calculate risk level
        risk_level = TriageEngine.calculate_risk_level(
            request.transcript, 
            p0_signals, 
            nna_involved
        )
        
        # Determine branch and priority
        branch = TriageEngine.determine_branch(risk_level)
        priority_class = TriageEngine.determine_priority(risk_level)
        
        # Classify category
        case_category = TriageEngine.classify_category(request.transcript)
        
        # Determine authorities
        primary_authority, support_authorities = TriageEngine.determine_authorities(
            case_category, 
            p0_signals
        )
        
        # Determine if human required
        human_required = (
            risk_level >= 6 or 
            len(p0_signals) > 0 or 
            nna_involved or 
            branch == "mid"
        )
        
        # Best interest of child
        best_interest_child = nna_involved
        
        # Generate public communication
        if risk_level >= 8:
            public_phrase = "Unidad de emergencia en camino"
        elif risk_level >= 6:
            public_phrase = "Atención prioritaria, unidad asignada"
        elif risk_level == 5:
            public_phrase = "Validando información, manténgase en línea"
        else:
            public_phrase = "Registro realizado, se dará seguimiento"
        
        # Rationale
        rationale_parts = []
        if p0_signals:
            rationale_parts.append(f"Señales P0 detectadas: {', '.join(p0_signals[:2])}")
        if nna_involved:
            rationale_parts.append("Menor de edad involucrado")
        if risk_level >= 8:
            rationale_parts.append("Riesgo crítico")
        
        rationale_public = "; ".join(rationale_parts) if rationale_parts else "Clasificación estándar"
        
        # Protected group flags
        protected_group_flags = ProtectedGroupFlags(
            nna_involved=nna_involved,
            elderly=elderly_involved,
            disability=False,  # Would need more sophisticated detection
            gender_violence=gender_violence
        )
        
        # Keywords detected (for transparency)
        keywords_detected = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            found = [kw for kw in keywords if kw in request.transcript.lower()]
            if found:
                keywords_detected[category] = found[:5]  # Limit to 5
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO core.triage_results
            (call_id, trace_id, risk_level, branch, priority_class, case_category,
             protected_group_flags, best_interest_child, human_required,
             primary_authority, support_authorities, public_stage_phrase,
             rationale_public, trust_flags, p0_signals, keywords_detected)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            request.call_id,
            trace_id,
            risk_level,
            branch,
            priority_class,
            case_category,
            Json(protected_group_flags.dict()),  # Wrap dict for JSONB
            best_interest_child,
            human_required,
            primary_authority,
            support_authorities,  # TEXT[] - no need to wrap
            public_phrase,
            rationale_public,
            Json({"confidence_score": 0.85, "ambiguity_detected": False}),  # Wrap dict for JSONB
            p0_signals,  # TEXT[] - no need to wrap
            Json(keywords_detected)  # Wrap dict for JSONB
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Triage completed: call_id={request.call_id}, risk={risk_level}, p0={len(p0_signals)}")
        
        return TriageResponse(
            call_id=request.call_id,
            trace_id=trace_id,
            risk_level=risk_level,
            branch=branch,
            priority_class=priority_class,
            case_category=case_category,
            medical_category=None,
            protected_group_flags=protected_group_flags,
            best_interest_child=best_interest_child,
            human_required=human_required,
            primary_authority=primary_authority,
            support_authorities=support_authorities,
            public_stage_phrase=public_phrase,
            rationale_public=rationale_public,
            trust_flags=TrustFlags(confidence_score=0.85, ambiguity_detected=False),
            p0_signals=p0_signals,
            keywords_detected=keywords_detected
        )
        
    except psycopg2.IntegrityError as e:
        # Foreign key violation - call_id doesn't exist
        logger.error(f"Integrity error in triage: call_id may not exist")
        raise HTTPException(
            status_code=422,
            detail=f"Invalid call_id: {request.call_id}. Call must be ingested first."
        )
    except Exception as e:
        logger.error(f"Error in triage: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Internal server error during triage")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)

# Made with Bob
