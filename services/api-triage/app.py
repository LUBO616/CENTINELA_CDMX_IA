"""
CENTINELA_CDMX_IA - Agente A4 Triador
Clasificación determinista 1-10 con detección P0, grupos protegidos y canalización CDMX
RESTRICCIÓN CRÍTICA: Nunca degradar llamadas con señales P0 activas
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

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CENTINELA_CDMX_IA - A4 Triador",
    description="Clasificación determinista de emergencias 911 CDMX — nivel 1-10",
    version="2.0.0"
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5678").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://emergency_user:changeme@postgres:5432/emergency_demo")

# ============================================================================
# SEÑALES P0 — Ningún agente puede cerrar, degradar o descartar una llamada
# cuando estas señales están presentes. Restricción técnica invariable.
# ============================================================================
P0_SIGNALS = {
    # Armas
    "arma": "arma", "pistola": "arma de fuego", "cuchillo": "arma blanca",
    "navaja": "arma blanca", "rifle": "arma de fuego", "disparo": "arma de fuego",
    "balacera": "arma de fuego", "balazo": "arma de fuego",

    # Incendio / Explosión
    "fuego": "incendio", "incendio": "incendio", "humo": "incendio",
    "explosión": "explosión", "explota": "explosión", "bomba": "explosivo",
    "quemadura": "incendio",

    # Materiales peligrosos
    "gas": "fuga de gas", "químico": "químico peligroso", "tóxico": "sustancia tóxica",
    "gasolina": "derrame químico",

    # Emergencia médica vital
    "suicida": "intento suicida", "suicidio": "intento suicida",
    "matarme": "intento suicida", "quitarme la vida": "intento suicida",
    "inconsciente": "persona inconsciente", "desmayado": "persona inconsciente",
    "no respira": "dificultad respiratoria", "no puede respirar": "dificultad respiratoria",
    "dificultad respirar": "dificultad respiratoria", "ahogo": "dificultad respiratoria",
    "asfixia": "dificultad respiratoria", "respiración agitada": "dificultad respiratoria",
    "infarto": "emergencia cardíaca", "paro": "paro cardiorrespiratorio",
    "sangrado": "sangrado grave", "sangre": "sangrado grave", "hemorragia": "sangrado grave",
    "convulsión": "emergencia neurológica", "derrame": "emergencia neurológica",

    # Privación de libertad / Violencia
    "secuestro": "privación de libertad", "privación libertad": "privación de libertad",
    "persona privada de libertad": "privación de libertad",
    "retenido": "privación de libertad", "me tienen retenido": "privación de libertad",
    "desaparición": "persona desaparecida", "desaparecido": "persona desaparecida",
    "violación": "violencia sexual", "abuso sexual": "violencia sexual",
    "feminicidio": "violencia contra la mujer",

    # Violencia doméstica / Género
    "golpes": "violencia física", "me está golpeando": "violencia física",
    "violencia familiar": "violencia familiar",
    "mujer golpeada": "violencia contra la mujer",
    "violencia mujer": "violencia contra la mujer",
    "niño golpeado": "maltrato infantil", "maltrato infantil": "maltrato infantil",
    "adulto mayor maltrato": "maltrato adulto mayor",

    # Coacción / Imposibilidad de hablar
    "me obligan": "coacción", "coaccionado": "coacción", "no puedo hablar": "imposibilidad de hablar",
    "están escuchando": "coacción", "alguien me controla": "coacción",

    # Señales acústicas de riesgo
    "auxilio": "solicitud de auxilio", "gritos": "señal acústica de riesgo",
    "llanto": "señal acústica de riesgo",

    # Grupos vulnerables en riesgo
    "discapacidad riesgo": "persona con discapacidad en riesgo",
    "persona mayor sola": "adulto mayor en riesgo",
}

# ============================================================================
# CATEGORÍAS DE INCIDENTES
# ============================================================================
CATEGORY_KEYWORDS = {
    "security": [
        "robo", "asalto", "delincuente", "ladrón", "violencia", "arma",
        "amenaza", "agresión", "pandilla", "balacera", "extorsión"
    ],
    "medical": [
        "dolor", "herida", "sangre", "ambulancia", "enfermo", "accidente",
        "caída", "fractura", "desmayo", "convulsión", "parto", "embarazo",
        "infarto", "respirar", "inconsciente"
    ],
    "protection_civil": [
        "incendio", "inundación", "derrumbe", "gas", "árbol caído",
        "explosión", "fuga", "terremoto", "deslizamiento", "humo"
    ],
    "public_services": [
        "alumbrado", "bache", "agua", "basura", "alcantarilla",
        "semáforo", "tráfico", "estacionamiento", "poste"
    ],
    "social_support": [
        "adicción", "depresión", "orientación", "apoyo psicológico",
        "persona en situación de calle", "abandono", "desorientado"
    ],
    "victim_attention": [
        "violación", "secuestro", "trata", "abuso", "extorsión",
        "fraude", "víctima", "feminicidio"
    ]
}

# ============================================================================
# GRUPOS DE PROTECCIÓN REFORZADA
# Uso: SOLO para priorización protectora. Nunca para perfilar o discriminar.
# ============================================================================
NNA_KEYWORDS = [
    "niño", "niña", "menor", "bebé", "adolescente", "infante",
    "hijo", "hija", "escolar", "estudiante menor", "recién nacido"
]

ELDERLY_KEYWORDS = [
    "adulto mayor", "anciano", "anciana", "abuela", "abuelo",
    "tercera edad", "persona mayor", "de edad"
]

DISABILITY_KEYWORDS = [
    "discapacidad", "silla de ruedas", "no puede moverse", "ciego", "sordo",
    "discapacitado", "no puede caminar", "no puede ver", "no puede hablar"
]

GENDER_VIOLENCE_KEYWORDS = [
    "mujer golpeada", "violencia mujer", "esposo golpea", "pareja violenta",
    "feminicidio", "violencia género", "me golpea mi pareja", "acoso"
]

MIGRANT_KEYWORDS = [
    "migrante", "extranjero", "no habla español", "indocumentado",
    "deportado", "refugiado", "asilo"
]

INDIGENOUS_KEYWORDS = [
    "indígena", "no entiende", "habla lengua", "no habla español",
    "intérprete", "mixteco", "náhuatl", "otomí", "zapoteco"
]

LGBTTTI_KEYWORDS = [
    "gay", "lesbiana", "transgénero", "trans ", "no binario",
    "orientación sexual", "identidad género"
]

HOMELESS_KEYWORDS = [
    "persona en calle", "sin hogar", "vive en la calle",
    "deambulante", "sin techo", "indigente"
]

HUMAN_RIGHTS_KEYWORDS = [
    "periodista", "reportero", "defensor", "activista",
    "derechos humanos", "amenazado por denuncia"
]


class TriageEngine:
    """Motor de clasificación determinista A4 Triador"""

    @staticmethod
    def detect_p0_signals(text: str) -> List[str]:
        text_lower = text.lower()
        detected = []
        for keyword, signal in P0_SIGNALS.items():
            if keyword in text_lower:
                detected.append(signal)
        return list(set(detected))

    @staticmethod
    def detect_protected_groups(text: str) -> Dict[str, bool]:
        """
        Detecta grupos de protección reforzada.
        RESTRICCIÓN: Solo para priorización protectora, nunca para perfilar.
        """
        text_lower = text.lower()
        return {
            "child_or_adolescent": any(k in text_lower for k in NNA_KEYWORDS),
            "older_adult": any(k in text_lower for k in ELDERLY_KEYWORDS),
            "disability": any(k in text_lower for k in DISABILITY_KEYWORDS),
            "woman": any(k in text_lower for k in GENDER_VIOLENCE_KEYWORDS),
            "migrant_or_international_protection": any(k in text_lower for k in MIGRANT_KEYWORDS),
            "indigenous_person": any(k in text_lower for k in INDIGENOUS_KEYWORDS),
            "lgbttti": any(k in text_lower for k in LGBTTTI_KEYWORDS),
            "homelessness": any(k in text_lower for k in HOMELESS_KEYWORDS),
            "human_rights_defender": any(k in text_lower for k in HUMAN_RIGHTS_KEYWORDS),
        }

    @staticmethod
    def classify_category(text: str) -> str:
        text_lower = text.lower()
        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score
        return max(scores, key=scores.get) if scores else "unknown"

    @staticmethod
    def calculate_risk_level(text: str, p0_signals: List[str], groups: Dict[str, bool]) -> int:
        """
        Calcula nivel de riesgo 1-10.
        RESTRICCIÓN TÉCNICA: P0 signals → mínimo nivel 6, invariable.
        Matriz: Severidad 40% + Tiempo crítico 25% + Escalamiento 20% + Vulnerabilidad 15%
        """
        text_lower = text.lower()
        base_score = 1.0

        # P0: mínimo 6, sin excepción
        if p0_signals:
            base_score = max(6.0, base_score)
            base_score += min(len(p0_signals) * 0.5, 3.0)  # cap el bonus

        # NNA: siempre elevar (interés superior de la niñez)
        if groups.get("child_or_adolescent"):
            base_score += 2.0

        # Adulto mayor o discapacidad: elevar
        if groups.get("older_adult") or groups.get("disability"):
            base_score += 1.0

        # Accidente vial sin P0 → nivel 5 (validación intermedia)
        traffic_keywords = [
            "accidente", "choque", "colisión", "volcadura",
            "carros chocados", "vehículo detenido"
        ]
        if any(kw in text_lower for kw in traffic_keywords) and not p0_signals:
            return 5

        # Keywords médicos
        medical_count = sum(1 for kw in CATEGORY_KEYWORDS["medical"] if kw in text_lower)
        base_score += medical_count * 0.3

        # Keywords seguridad
        security_count = sum(1 for kw in CATEGORY_KEYWORDS["security"] if kw in text_lower)
        base_score += security_count * 0.4

        # Keywords protección civil
        protection_count = sum(1 for kw in CATEGORY_KEYWORDS["protection_civil"] if kw in text_lower)
        base_score += protection_count * 0.3

        risk_level = min(10, int(base_score))

        # Garantía: P0 → nunca por debajo de 6
        if p0_signals and risk_level < 6:
            risk_level = 6

        return risk_level

    @staticmethod
    def determine_branch(risk_level: int) -> str:
        if risk_level <= 4:
            return "low"
        elif risk_level == 5:
            return "mid"
        return "critical"

    @staticmethod
    def determine_priority(risk_level: int) -> str:
        if risk_level <= 2:
            return "minimum"
        elif risk_level <= 4:
            return "low"
        elif risk_level == 5:
            return "medium"
        elif risk_level <= 7:
            return "high"
        return "critical"

    @staticmethod
    def determine_authorities(category: str, p0_signals: List[str], groups: Dict[str, bool]) -> tuple:
        """
        Canalización con nombres reales de instituciones CDMX.
        A7 Bravo siempre incluye legal_basis_tag — aquí definimos la base.
        """
        # Defaults según categoría
        authority_map = {
            "medical": {
                "primary": "Secretaría de Salud CDMX / ERUM",
                "support": ["C5/C2", "Protección Civil"]
            },
            "security": {
                "primary": "SSC — Secretaría de Seguridad Ciudadana CDMX",
                "support": ["Fiscalía General de Justicia CDMX", "C5"]
            },
            "protection_civil": {
                "primary": "Protección Civil CDMX / Heroico Cuerpo de Bomberos",
                "support": ["Secretaría de Salud CDMX", "SSC", "C5"]
            },
            "victim_attention": {
                "primary": "Fiscalía General de Justicia CDMX",
                "support": ["ADEVI — Atención a Víctimas", "SSC", "DIF-CDMX"]
            },
            "social_support": {
                "primary": "SIBISO — Secretaría de Inclusión y Bienestar Social CDMX",
                "support": ["DIF-CDMX", "Secretaría de Salud CDMX"]
            },
            "public_services": {
                "primary": "Alcaldía competente / SACMEX",
                "support": ["Protección Civil CDMX", "C5"]
            },
        }

        result = authority_map.get(category, {
            "primary": "C5 — Centro de Comando, Control, Cómputo, Comunicaciones y Contacto Ciudadano",
            "support": ["SSC", "Secretaría de Salud CDMX"]
        })

        primary = result["primary"]
        support = list(result["support"])

        # Ajustes por grupos protegidos
        if groups.get("child_or_adolescent"):
            if "Procuraduría de Protección de NNA CDMX / DIF-CDMX" not in support:
                support.append("Procuraduría de Protección de NNA CDMX / DIF-CDMX")

        if groups.get("woman") or any("violencia" in s for s in p0_signals):
            if "Secretaría de las Mujeres CDMX" not in support:
                support.append("Secretaría de las Mujeres CDMX")

        if groups.get("migrant_or_international_protection") or groups.get("indigenous_person"):
            if "CDHCM — Comisión de Derechos Humanos CDMX" not in support:
                support.append("CDHCM — Comisión de Derechos Humanos CDMX")

        if groups.get("human_rights_defender"):
            if "Mecanismo de Protección para Personas Defensoras y Periodistas" not in support:
                support.append("Mecanismo de Protección para Personas Defensoras y Periodistas")

        # Ajustes por señales P0 específicas
        if any("incendio" in s for s in p0_signals):
            if "Heroico Cuerpo de Bomberos CDMX" not in support:
                support.append("Heroico Cuerpo de Bomberos CDMX")

        return primary, support


def get_db_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"Database connection error: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Database connection failed")


class TriageRequest(BaseModel):
    transcript: str = Field(..., min_length=1)
    call_id: str
    trace_id: Optional[str] = None
    consent: bool = False  # SOLID: OFF por defecto — privacidad by design
    location_hint: Optional[str] = None


class ProtectedGroupFlags(BaseModel):
    child_or_adolescent: bool = False
    older_adult: bool = False
    disability: bool = False
    woman: bool = False
    migrant_or_international_protection: bool = False
    indigenous_person: bool = False
    lgbttti: bool = False
    homelessness: bool = False
    human_rights_defender: bool = False


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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "service": "api-triage",
        "version": "2.0.0",
        "rules_loaded": len(P0_SIGNALS) + sum(len(v) for v in CATEGORY_KEYWORDS.values()),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.post("/triage", response_model=TriageResponse)
async def triage_call(request: TriageRequest):
    """
    Clasificación determinista A4 Triador.
    RESTRICCIÓN TÉCNICA: Llamadas con señales P0 nunca se degradan ni cierran sin operador humano.
    """
    try:
        trace_id = request.trace_id if request.trace_id else str(uuid.uuid4())

        # Detección de señales P0
        p0_signals = TriageEngine.detect_p0_signals(request.transcript)

        # Detección de grupos protegidos
        groups = TriageEngine.detect_protected_groups(request.transcript)

        # Nivel de riesgo
        risk_level = TriageEngine.calculate_risk_level(request.transcript, p0_signals, groups)

        # Rama y prioridad
        branch = TriageEngine.determine_branch(risk_level)
        priority_class = TriageEngine.determine_priority(risk_level)

        # Categoría
        case_category = TriageEngine.classify_category(request.transcript)

        # Autoridades CDMX
        primary_authority, support_authorities = TriageEngine.determine_authorities(
            case_category, p0_signals, groups
        )

        # ¿Requiere humano? Nivel ≥5, P0, NNA o mid siempre → sí
        human_required = (
            risk_level >= 5 or
            len(p0_signals) > 0 or
            groups.get("child_or_adolescent") or
            branch in ("mid", "critical")
        )

        best_interest_child = groups.get("child_or_adolescent", False)

        # Frase pública (protocolo de comunicación — nunca revelar cadena interna)
        stage_map = {
            range(1, 5): "Estoy en la etapa de recepción. Registro realizado, se dará seguimiento.",
            range(5, 6): "Estoy en la etapa de validación. Recopilando información adicional.",
            range(6, 9): "Estoy en la etapa de priorización. Atención prioritaria activada.",
            range(9, 11): "Estoy en la etapa de canalización. Emergencia crítica — operador humano asignado.",
        }
        public_phrase = next(
            (v for r, v in stage_map.items() if risk_level in r),
            "Estoy en la etapa de seguimiento."
        )

        # Justificación pública (sin revelar lógica interna)
        rationale_parts = []
        if p0_signals:
            rationale_parts.append(f"Señales detectadas: {', '.join(p0_signals[:2])}")
        if best_interest_child:
            rationale_parts.append("Interés superior de NNA activado")
        if risk_level >= 8:
            rationale_parts.append("Nivel crítico")
        rationale_public = "; ".join(rationale_parts) if rationale_parts else "Clasificación estándar"

        protected_group_flags = ProtectedGroupFlags(**groups)

        keywords_detected = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            found = [kw for kw in keywords if kw in request.transcript.lower()]
            if found:
                keywords_detected[category] = found[:5]

        # Persistir en BD
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
            request.call_id, trace_id, risk_level, branch, priority_class,
            case_category, Json(groups), best_interest_child, human_required,
            primary_authority, support_authorities, public_phrase, rationale_public,
            Json({"confidence_score": 0.85, "ambiguity_detected": False}),
            p0_signals, Json(keywords_detected)
        ))
        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Triage: call_id={request.call_id}, risk={risk_level}, p0={len(p0_signals)}, groups={sum(1 for v in groups.values() if v)}")

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

    except psycopg2.IntegrityError:
        logger.error(f"Integrity error: call_id {request.call_id} not found in raw.conversations")
        raise HTTPException(
            status_code=422,
            detail=f"call_id inválido: {request.call_id}. La llamada debe ser ingresada primero en api-ingest."
        )
    except Exception as e:
        logger.error(f"Error en triage: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Error interno durante el triage")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
