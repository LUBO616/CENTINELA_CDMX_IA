# Ciberseguridad - 911 AI Flow Demo

## Aviso Importante

**Este es un MVP educativo con controles de seguridad básicos. NO está listo para producción.**

- ⚠️ No usar con datos reales
- ⚠️ No exponer a internet
- ⚠️ No usar en entorno de producción sin auditoría completa

---

## Tabla de Contenidos

1. [Threat Model](#threat-model)
2. [Activos Protegidos](#activos-protegidos)
3. [Superficie de Ataque](#superficie-de-ataque)
4. [Riesgos Principales](#riesgos-principales)
5. [Controles Implementados](#controles-implementados)
6. [Checklist Previo a Demo](#checklist-previo-a-demo)
7. [Limitaciones de Seguridad](#limitaciones-de-seguridad)
8. [Recomendaciones para Producción](#recomendaciones-para-producción)

---

## Threat Model

### Modelo de Amenazas Básico

```
┌─────────────────────────────────────────────────────────────┐
│                    Actores de Amenaza                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Atacante Externo (Internet)                              │
│    - Objetivo: Acceso no autorizado, exfiltración de datos  │
│    - Mitigación: Servicios en 127.0.0.1, no expuestos       │
│                                                              │
│ 2. Usuario Malicioso Local                                  │
│    - Objetivo: Inyección de código, DoS, acceso a DB        │
│    - Mitigación: Validación de inputs, rate limiting        │
│                                                              │
│ 3. Insider Threat (Acceso al Host)                          │
│    - Objetivo: Acceso a .env, DB, logs                      │
│    - Mitigación: .env fuera de git, permisos restrictivos   │
│                                                              │
│ 4. Fuga de Información                                      │
│    - Objetivo: Exposición de PII en logs, analytics         │
│    - Mitigación: Redacción automática, normalización        │
└─────────────────────────────────────────────────────────────┘
```

### Escenarios de Ataque

#### Escenario 1: Inyección SQL
**Amenaza:** Atacante envía payload malicioso en transcript
```json
{
  "transcript": "'; DROP TABLE raw.conversations; --"
}
```
**Mitigación:**
- ✅ Uso de prepared statements (psycopg2)
- ✅ Validación de inputs con Pydantic
- ✅ Sanitización de strings

#### Escenario 2: Exfiltración de PII
**Amenaza:** Atacante accede a logs o analytics para obtener PII
**Mitigación:**
- ✅ Redacción automática antes de almacenar
- ✅ Logs sin PII
- ✅ Normalización de ubicaciones
- ✅ No guardar transcript original

#### Escenario 3: Denegación de Servicio (DoS)
**Amenaza:** Atacante envía miles de requests para saturar sistema
**Mitigación:**
- ⚠️ Rate limiting básico (futuro)
- ✅ Timeouts configurados
- ✅ Recursos limitados por Docker

#### Escenario 4: Acceso No Autorizado a n8n
**Amenaza:** Atacante accede a n8n sin credenciales
**Mitigación:**
- ✅ Basic Auth habilitado
- ✅ Puerto en 127.0.0.1
- ⚠️ Credenciales por defecto (cambiar en producción)

---

## Activos Protegidos

### Clasificación de Activos

| Activo | Criticidad | Ubicación | Protección |
|--------|-----------|-----------|------------|
| **Transcripts redactados** | Alta | PostgreSQL raw.conversations | Redacción automática |
| **Resultados de triage** | Media | PostgreSQL core.triage_results | Separación de schemas |
| **Métricas agregadas** | Baja | PostgreSQL analytics.incidents | Normalización de ubicaciones |
| **Credenciales DB** | Crítica | .env (no en git) | .gitignore, permisos 600 |
| **Credenciales n8n** | Alta | .env (no en git) | .gitignore, Basic Auth |
| **Código fuente** | Media | Git repository | Público (sin secretos) |
| **Logs** | Media | Docker logs | Sin PII, rotación |

### Datos Sensibles

**PII que se redacta:**
- Teléfonos
- Emails
- Nombres propios
- Direcciones con número

**Datos que NO se almacenan:**
- ❌ Transcript original sin redactar
- ❌ Audio de llamadas
- ❌ Datos biométricos
- ❌ Identificadores oficiales (CURP, INE)

---

## Superficie de Ataque

### Puntos de Entrada

```
┌─────────────────────────────────────────────────────────────┐
│                    Superficie de Ataque                      │
├─────────────────────────────────────────────────────────────┤
│ 1. Webhook n8n                                              │
│    - URL: http://localhost:5678/webhook/911-call            │
│    - Método: POST                                            │
│    - Autenticación: Basic Auth                               │
│    - Validación: Payload JSON                                │
│                                                              │
│ 2. API Endpoints                                             │
│    - api-ingest:8001 (POST /raw-conversations)              │
│    - api-triage:8002 (POST /triage)                         │
│    - api-analytics:8003 (POST /incidents, GET /analytics/*) │
│    - Autenticación: Ninguna (localhost only)                 │
│    - Validación: Pydantic models                             │
│                                                              │
│ 3. PostgreSQL                                                │
│    - Puerto: 5432 (127.0.0.1)                               │
│    - Autenticación: Usuario/contraseña                       │
│    - Acceso: Solo desde Docker network                       │
│                                                              │
│ 4. Docker Host                                               │
│    - Acceso físico/SSH al servidor                           │
│    - Archivos: .env, docker-compose.yml                      │
│    - Comandos: docker exec, docker logs                      │
└─────────────────────────────────────────────────────────────┘
```

### Puertos Expuestos

| Puerto | Servicio | Bind | Acceso |
|--------|----------|------|--------|
| 5432 | PostgreSQL | 127.0.0.1 | Solo localhost |
| 5678 | n8n | 127.0.0.1 | Solo localhost |
| 8001 | api-ingest | 127.0.0.1 | Solo localhost |
| 8002 | api-triage | 127.0.0.1 | Solo localhost |
| 8003 | api-analytics | 127.0.0.1 | Solo localhost |

**Ventaja:** No hay exposición directa a internet.

---

## Riesgos Principales

### Matriz de Riesgos

| Riesgo | Probabilidad | Impacto | Severidad | Mitigación |
|--------|--------------|---------|-----------|------------|
| **Fuga de PII** | Media | Alto | Alto | Redacción automática, normalización |
| **Inyección SQL** | Baja | Alto | Medio | Prepared statements, validación |
| **DoS** | Media | Medio | Medio | Timeouts, rate limiting (futuro) |
| **Acceso no autorizado a n8n** | Baja | Medio | Bajo | Basic Auth, localhost only |
| **Exposición de credenciales** | Baja | Alto | Medio | .env fuera de git, .gitignore |
| **Logs con PII** | Baja | Alto | Medio | Logs sin PII, redacción |
| **Acceso físico al host** | Baja | Alto | Medio | Permisos de archivos, encriptación (futuro) |

### Riesgos Aceptados (MVP)

Por ser demo educativa, se aceptan los siguientes riesgos:

1. **No encriptación E2E**
   - Justificación: Demo local, no producción
   - Mitigación futura: TLS/SSL

2. **Credenciales por defecto**
   - Justificación: Demo, no datos reales
   - Mitigación futura: Credenciales fuertes, rotación

3. **No rate limiting avanzado**
   - Justificación: No expuesto a internet
   - Mitigación futura: Implementar rate limiting

4. **No WAF**
   - Justificación: No expuesto a internet
   - Mitigación futura: WAF en producción

---

## Controles Implementados

### 1. Controles de Red

#### Servicios en Localhost
```yaml
# docker-compose.yml
ports:
  - "127.0.0.1:5432:5432"  # PostgreSQL
  - "127.0.0.1:5678:5678"  # n8n
  - "127.0.0.1:8001:8001"  # api-ingest
  - "127.0.0.1:8002:8002"  # api-triage
  - "127.0.0.1:8003:8003"  # api-analytics
```

**Beneficio:** No hay exposición directa a internet.

#### Docker Network Interno
```yaml
networks:
  emergency-network:
    driver: bridge
```

**Beneficio:** Aislamiento de servicios.

### 2. Controles de Acceso

#### Autenticación n8n
```env
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=changeme
```

**Recomendación:** Cambiar credenciales en producción.

#### PostgreSQL
```env
POSTGRES_USER=emergency_user
POSTGRES_PASSWORD=changeme
```

**Recomendación:** Usar contraseñas fuertes en producción.

### 3. Controles de Datos

#### Redacción Automática de PII
```python
# api-ingest/app.py
def redact_pii(text: str) -> str:
    # Redactar teléfonos
    text = re.sub(r'\b\d{10}\b', '[PHONE_REDACTED]', text)
    # Redactar emails
    text = re.sub(r'\S+@\S+\.\S+', '[EMAIL_REDACTED]', text)
    # Redactar nombres
    text = redact_names(text)
    # Redactar direcciones
    text = redact_addresses(text)
    return text
```

#### Normalización de Ubicaciones
```python
# api-analytics/app.py
def normalize_location_hint(location: str) -> str:
    # "Calle Madero 45" → "Centro"
    # "Insurgentes 123" → "Zona simulada"
    if has_street_number(location):
        return "Zona simulada"
    return generalize_zone(location)
```

#### No Almacenar Transcript Original
```python
# api-ingest/app.py
original_transcript = '[NOT_STORED_PRIVACY_BY_DESIGN]'
```

### 4. Controles de Código

#### Validación de Inputs
```python
# Pydantic models
class TriageRequest(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=10000)
    call_id: str = Field(..., regex=r'^[0-9a-f-]{36}$')
    consent: bool = True
```

#### Prepared Statements
```python
# psycopg2
cursor.execute("""
    INSERT INTO raw.conversations (call_id, redacted_text)
    VALUES (%s, %s)
""", (call_id, redacted_text))
```

#### Sanitización de Logs
```python
# No loggear PII
logger.info(f"Processing call_id: {call_id}")  # ✓
logger.info(f"Processing call from {name}")    # ✗
```

### 5. Controles de Configuración

#### .gitignore
```gitignore
.env
*.log
__pycache__/
*.pyc
.DS_Store
```

#### .env.example (Sin Secretos)
```env
# Database
POSTGRES_PASSWORD=changeme_strong_password

# n8n
N8N_BASIC_AUTH_PASSWORD=changeme_n8n_password
```

#### Permisos de Archivos
```bash
chmod 600 .env
chmod 700 scripts/*.sh
```

### 6. Controles de Separación

#### Schemas en PostgreSQL
```sql
-- Separación lógica de datos
CREATE SCHEMA raw;      -- Datos redactados de entrada
CREATE SCHEMA core;     -- Resultados de clasificación
CREATE SCHEMA analytics; -- Métricas agregadas
```

**Beneficio:** Aislamiento de datos sensibles.

---

## Checklist Previo a Demo

### Antes de Iniciar Demo

- [ ] **Verificar que .env NO está en git**
  ```bash
  git status | grep .env
  # No debe aparecer
  ```

- [ ] **Cambiar credenciales por defecto**
  ```bash
  nano .env
  # Cambiar POSTGRES_PASSWORD
  # Cambiar N8N_BASIC_AUTH_PASSWORD
  ```

- [ ] **Verificar puertos en localhost**
  ```bash
  docker compose ps
  # Todos los puertos deben estar en 127.0.0.1
  ```

- [ ] **Verificar que servicios están corriendo**
  ```bash
  ./scripts/04_test_environment.sh all
  # Todos los tests deben pasar
  ```

- [ ] **Verificar logs sin PII**
  ```bash
  ./scripts/03_logs.sh api-ingest | grep -E '\d{10}|@'
  # No debe encontrar teléfonos ni emails
  ```

- [ ] **Verificar normalización de ubicaciones**
  ```bash
  curl http://localhost:8003/analytics/predictions | jq '.risk_zones'
  # No debe mostrar direcciones completas
  ```

- [ ] **Verificar que no hay secretos en código**
  ```bash
  grep -r "password.*=" services/ | grep -v "changeme"
  # No debe encontrar contraseñas hardcodeadas
  ```

- [ ] **Preparar disclaimer visible**
  ```
  ⚠️ DEMO EDUCATIVA - NO USAR PARA EMERGENCIAS REALES
  Datos 100% sintéticos - Sistema no conectado a C5 real
  ```

### Durante la Demo

- [ ] Mostrar disclaimer al inicio
- [ ] Usar solo datos sintéticos
- [ ] No compartir credenciales reales
- [ ] No exponer .env en pantalla
- [ ] Mencionar limitaciones de seguridad
- [ ] Enfatizar "humano en el loop"

### Después de la Demo

- [ ] Detener servicios
  ```bash
  ./scripts/02_stop.sh
  ```

- [ ] Revisar logs por anomalías
  ```bash
  ./scripts/03_logs.sh postgres | grep ERROR
  ```

- [ ] Limpiar datos de prueba (opcional)
  ```bash
  docker compose down -v
  ```

---

## Limitaciones de Seguridad

### Limitaciones del MVP

1. **No Encriptación End-to-End**
   - Datos en tránsito no encriptados (HTTP, no HTTPS)
   - Datos en reposo no encriptados en DB

2. **Autenticación Básica**
   - Basic Auth en n8n (no OAuth, no JWT)
   - No autenticación en APIs (solo localhost)

3. **No Rate Limiting Avanzado**
   - Sin protección contra DoS sofisticado
   - Sin throttling por IP

4. **No WAF**
   - Sin Web Application Firewall
   - Sin protección contra OWASP Top 10

5. **No SIEM**
   - Sin Security Information and Event Management
   - Sin alertas automáticas de seguridad

6. **No Auditoría Completa**
   - Sin logs de auditoría detallados
   - Sin trazabilidad completa de accesos

7. **Credenciales por Defecto**
   - Contraseñas débiles en .env.example
   - No rotación automática

8. **No Backup Encriptado**
   - Sin backups automáticos
   - Sin encriptación de backups

### Riesgos Residuales

**Riesgos que permanecen en el MVP:**

- ⚠️ Acceso físico al host compromete todo el sistema
- ⚠️ Credenciales débiles pueden ser adivinadas
- ⚠️ DoS puede saturar recursos locales
- ⚠️ Logs pueden contener información sensible si hay bugs

**Mitigación:** No usar en producción sin auditoría completa.

---

## Recomendaciones para Producción

### Controles Adicionales Requeridos

#### 1. Encriptación

**TLS/SSL:**
```yaml
# nginx.conf
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
}
```

**Encriptación en Reposo:**
```sql
-- PostgreSQL
CREATE EXTENSION pgcrypto;
ALTER TABLE raw.conversations 
  ALTER COLUMN redacted_text 
  TYPE bytea USING pgp_sym_encrypt(redacted_text, 'encryption_key');
```

#### 2. Autenticación Robusta

**OAuth 2.0 / JWT:**
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/raw-conversations")
async def create_conversation(token: str = Depends(oauth2_scheme)):
    # Validar token
    pass
```

**Multi-Factor Authentication (MFA):**
- Implementar 2FA para acceso a n8n
- Implementar 2FA para acceso a DB

#### 3. Rate Limiting

**Nginx:**
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20;
}
```

**FastAPI:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/raw-conversations")
@limiter.limit("10/minute")
async def create_conversation():
    pass
```

#### 4. WAF

**ModSecurity:**
```nginx
modsecurity on;
modsecurity_rules_file /etc/nginx/modsec/main.conf;
```

**Cloudflare:**
- Activar WAF rules
- Activar DDoS protection
- Activar Bot Management

#### 5. SIEM

**ELK Stack:**
```yaml
# docker-compose.yml
elasticsearch:
  image: elasticsearch:8.0
logstash:
  image: logstash:8.0
kibana:
  image: kibana:8.0
```

**Alertas:**
```yaml
# elastalert.yml
alert:
  - type: frequency
    num_events: 100
    timeframe:
      minutes: 5
    alert:
      - email
```

#### 6. Auditoría

**Logs de Auditoría:**
```python
audit_logger.info({
    "event": "data_access",
    "user": user_id,
    "resource": "raw.conversations",
    "action": "read",
    "timestamp": datetime.utcnow(),
    "ip": request.client.host
})
```

#### 7. Gestión de Secretos

**HashiCorp Vault:**
```python
import hvac

client = hvac.Client(url='http://vault:8200')
secret = client.secrets.kv.v2.read_secret_version(path='db/password')
```

**AWS Secrets Manager:**
```python
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='db-password')
```

#### 8. Pentesting

**Antes de Producción:**
- [ ] Pentesting por tercero certificado
- [ ] Revisión de código por expertos
- [ ] Análisis de vulnerabilidades (OWASP ZAP, Burp Suite)
- [ ] Pruebas de penetración (Metasploit)

#### 9. Compliance

**Certificaciones:**
- [ ] ISO 27001 (Gestión de Seguridad de la Información)
- [ ] SOC 2 (Controles de Seguridad)
- [ ] PCI DSS (si aplica)

**Auditorías:**
- [ ] Auditoría legal (LFPDPPP)
- [ ] Auditoría de seguridad
- [ ] Auditoría de privacidad

#### 10. Plan de Respuesta a Incidentes

**Procedimientos:**
1. Detección de incidente
2. Contención
3. Erradicación
4. Recuperación
5. Lecciones aprendidas

**Contactos:**
- Equipo de seguridad
- Legal
- Comunicación
- Autoridades (CERT-MX)

---

## Conclusión

Este MVP implementa **controles de seguridad básicos** suficientes para una demo educativa, pero **NO es seguro para producción**.

**Controles Implementados:**
- ✅ Servicios en localhost
- ✅ Redacción de PII
- ✅ Normalización de ubicaciones
- ✅ Separación de datos
- ✅ Logs sin PII
- ✅ .env fuera de git

**Controles Faltantes para Producción:**
- ❌ Encriptación E2E
- ❌ Autenticación robusta
- ❌ Rate limiting avanzado
- ❌ WAF
- ❌ SIEM
- ❌ Auditoría completa
- ❌ Pentesting
- ❌ Certificaciones

**Recordatorio:**
> No usar este sistema en producción sin auditoría completa de seguridad,  
> implementación de controles adicionales, y aprobación de autoridades competentes.

---

**Versión:** 1.0.0  
**Fecha:** 2026-06-06  
**Autor:** Bob  
**Propósito:** Demo educativa - Hackathon  
**Nivel de Seguridad:** Básico (MVP)