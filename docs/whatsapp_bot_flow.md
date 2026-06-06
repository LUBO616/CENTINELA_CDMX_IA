# WhatsApp Bot Demo - 911 AI Flow

## Objetivo

Crear un flujo n8n que simule un bot tipo WhatsApp para recibir mensajes de emergencia, detectar palabras clave, categorizar el problema y enviarlo al flujo principal 911.

## Arquitectura

```
Usuario WhatsApp (simulado)
    ↓
POST /webhook/whatsapp-bot
    ↓
Normalize Message (hash phone, extract data)
    ↓
Keyword Categorizer (detect category, P0 signals, location)
    ↓
Build 911 Payload (format for main workflow)
    ↓
Call API Gateway /911-call
    ↓
Build Bot Response (user-friendly message)
    ↓
Respond JSON (return to user)
```

## Webhook Endpoint

**URL:** `http://localhost:5678/webhook/whatsapp-bot`

**Method:** POST

**Payload:**
```json
{
  "from": "+525512345678",
  "message": "Hay un incendio en mi edificio en colonia Centro",
  "timestamp": "2024-01-15T10:30:00Z",
  "profile_name": "Usuario Demo"
}
```

## Categorización por Palabras Clave

### Categorías Soportadas

#### 1. Security (Seguridad)
**Keywords:**
- robo, asalto, arma, disparos, violencia, secuestro
- amenaza, delincuente, ladrón, asaltante

**Ejemplo:** "Me están asaltando con un arma"

#### 2. Medical (Médico)
**Keywords:**
- herido, inconsciente, sangrado, ambulancia, infarto
- convulsiones, dolor, accidente, lesión, enfermo

**Ejemplo:** "Hay una persona inconsciente en la calle"

#### 3. Protection Civil (Protección Civil)
**Keywords:**
- incendio, fuga de gas, derrumbe, inundación, explosión
- fuego, humo, gas, temblor, sismo

**Ejemplo:** "Hay un incendio en mi edificio"

#### 4. Public Services (Servicios Públicos)
**Keywords:**
- bache, semáforo, alumbrado, árbol caído, fuga de agua
- basura, alcantarilla, poste, cable

**Ejemplo:** "Hay un árbol caído bloqueando la calle"

#### 5. Social Support (Apoyo Social)
**Keywords:**
- persona vulnerable, adulto mayor, extraviado, indigencia
- abandono, sin hogar, perdido

**Ejemplo:** "Hay un adulto mayor extraviado"

#### 6. Victim Attention (Atención a Víctimas)
**Keywords:**
- violencia familiar, abuso, agresión, víctima, maltrato
- violencia doméstica, golpes

**Ejemplo:** "Escucho gritos de violencia familiar"

### Señales P0 (Críticas)

**Keywords P0:**
- sangre, sangrado grave, inconsciente, arma de fuego
- incendio, explosión, bebé, niño, niña, secuestro
- amenaza de muerte, no respira

**Efecto:** Marca el caso como crítico y requiere revisión humana inmediata.

## Privacidad y Seguridad

### Protección de PII

1. **Número de teléfono:**
   - NO se guarda el número completo
   - Se hashea con SHA-256
   - Solo se almacenan primeros 16 caracteres del hash

2. **Mensaje:**
   - Se marca como "Reporte vía WhatsApp Bot"
   - No se loggea el mensaje crudo con PII
   - Se sanitiza antes de enviar al flujo principal

3. **Metadata:**
   - Se marca como `source: "whatsapp_bot_demo"`
   - Se incluye hash del remitente, no el número
   - Se marca como sintético para demo

### Ejemplo de Hash

```javascript
const crypto = require('crypto');
const hashedFrom = crypto.createHash('sha256')
  .update(from)
  .digest('hex')
  .substring(0, 16);
// Resultado: "a1b2c3d4e5f6g7h8"
```

## Respuestas del Bot

### Respuesta para Emergencia Crítica (P0)

```
⚠️ EMERGENCIA CRÍTICA DETECTADA

Tu reporte ha sido clasificado como PRIORIDAD MÁXIMA.

Categoría: protection_civil
Señales P0: incendio, bebé

Un operador humano revisará tu caso de inmediato.

Folio: 12345678
Incidente: abcd1234

Gracias por tu reporte. 🚨
```

### Respuesta para Prioridad Media/Alta

```
✅ Reporte recibido

Tu reporte ha sido clasificado como: medical
Nivel de prioridad: MEDIO

Un operador humano debe revisar el caso.

Folio: 87654321
Incidente: xyz98765

Gracias por tu reporte. 🚨
```

### Respuesta para Prioridad Baja

```
✅ Reporte recibido

Tu reporte ha sido registrado.
Categoría: public_services

Será procesado según prioridad.

Folio: 11223344
Incidente: def55667

Gracias por tu reporte. 🚨
```

### Respuesta de Error

```
❌ Lo sentimos, hubo un error al procesar tu reporte. 
Por favor intenta nuevamente o llama al 911.
```

## Flujo de Nodos n8n

### 1. Webhook WhatsApp Bot
- Recibe POST request
- Extrae payload
- Pasa a siguiente nodo

### 2. Normalize Message
- Hashea número de teléfono
- Convierte mensaje a lowercase
- Extrae metadata básica
- Protege PII

### 3. Keyword Categorizer
- Detecta categoría por keywords
- Identifica señales P0
- Extrae hint de ubicación
- Calcula nivel de riesgo sugerido
- Determina confianza de clasificación

### 4. Build 911 Payload
- Construye transcript sanitizado
- Agrega metadata completa
- Formatea para API Gateway
- Incluye solid_consent: true

### 5. Call API Gateway
- POST a http://api-gateway:8010/911-call
- Timeout: 15 segundos
- Maneja errores de red
- Retorna resultado del flujo principal

### 6. Build Bot Response
- Construye mensaje user-friendly
- Incluye folio e incident_id
- Adapta mensaje según prioridad
- Agrega emojis para claridad

### 7. Respond JSON
- Devuelve respuesta al usuario
- Incluye status, bot_reply, folios
- Formato JSON estructurado

### 8. Error Handler (fallback)
- Captura errores del flujo
- Construye mensaje de error amigable
- Loggea error para debugging
- Devuelve respuesta de error

## Testing

### Script de Prueba

Ver: `scripts/11_test_whatsapp_bot.sh`

### Casos de Prueba

1. **Incendio (Protection Civil + P0)**
   ```json
   {
     "from": "+525512345678",
     "message": "Hay un incendio en mi edificio en colonia Centro",
     "profile_name": "Usuario 1"
   }
   ```
   - Esperado: category=protection_civil, risk=critical, P0=true

2. **Bache (Public Services)**
   ```json
   {
     "from": "+525587654321",
     "message": "Hay un bache enorme en Reforma",
     "profile_name": "Usuario 2"
   }
   ```
   - Esperado: category=public_services, risk=low

3. **Herido (Medical)**
   ```json
   {
     "from": "+525511112222",
     "message": "Hay una persona herida en la calle",
     "profile_name": "Usuario 3"
   }
   ```
   - Esperado: category=medical, risk=mid

4. **Robo (Security)**
   ```json
   {
     "from": "+525533334444",
     "message": "Me están robando en Iztapalapa",
     "profile_name": "Usuario 4"
   }
   ```
   - Esperado: category=security, risk=mid

5. **Violencia Familiar (Victim Attention)**
   ```json
   {
     "from": "+525555556666",
     "message": "Escucho violencia familiar en el departamento de al lado",
     "profile_name": "Usuario 5"
   }
   ```
   - Esperado: category=victim_attention, risk=mid

## Integración con Flujo Principal

El bot envía el payload al mismo endpoint que el dashboard:
- **Endpoint:** `POST http://api-gateway:8010/911-call`
- **Flujo:** api-gateway → n8n main workflow → api-ingest → api-triage → api-analytics
- **Resultado:** Mismo procesamiento que llamadas normales

## Limitaciones Demo

1. **No WhatsApp Real:**
   - No se integra con WhatsApp Business API
   - Solo webhook HTTP para demo
   - Requiere credenciales de WhatsApp para producción

2. **Clasificación Básica:**
   - Basada en keywords simples
   - No usa NLP avanzado
   - Puede tener falsos positivos/negativos

3. **Sin Conversación:**
   - No mantiene contexto de conversación
   - No hace preguntas de seguimiento
   - Procesamiento one-shot

4. **Sin Multimedia:**
   - No procesa imágenes/videos
   - Solo texto
   - No geolocalización automática

## Mejoras Futuras

1. **WhatsApp Business API:**
   - Integración real con WhatsApp
   - Verificación de números
   - Mensajes de plantilla

2. **NLP Avanzado:**
   - Usar modelos de lenguaje
   - Mejor detección de intención
   - Análisis de sentimiento

3. **Conversación Interactiva:**
   - Preguntas de seguimiento
   - Confirmación de datos
   - Actualización de estado

4. **Multimedia:**
   - Procesamiento de imágenes
   - Análisis de video
   - Geolocalización automática

5. **Multi-idioma:**
   - Soporte para inglés
   - Lenguas indígenas
   - Traducción automática

## Seguridad

### Validaciones

- Longitud máxima de mensaje: 10,000 caracteres
- Rate limiting recomendado: 10 mensajes/minuto por número
- Validación de formato de número de teléfono
- Sanitización de input para prevenir injection

### Logging

- NO loggear números de teléfono completos
- NO loggear mensajes con PII
- SÍ loggear: hashes, categorías, timestamps
- SÍ loggear: errores y métricas

### Compliance

- GDPR: Derecho al olvido (eliminar hashes)
- LFPDPPP (México): Consentimiento explícito
- Retención de datos: Máximo 90 días
- Auditoría: Logs de acceso

## Monitoreo

### Métricas Clave

- Mensajes recibidos por hora
- Tasa de clasificación correcta
- Tiempo de respuesta promedio
- Tasa de error
- Distribución por categoría

### Alertas

- Spike de mensajes (posible ataque)
- Tasa de error > 5%
- Latencia > 5 segundos
- Caída de n8n o API Gateway

## Documentación Adicional

- [n8n Workflow Documentation](./n8n_workflow.md)
- [API Contract](./api_contract.md)
- [Privacy & Legal](./legal_privacy.md)
- [Architecture](./architecture.md)

---

**Nota:** Este es un demo para hackathon. Para producción, se requiere:
- Integración real con WhatsApp Business API
- Infraestructura escalable
- Monitoreo 24/7
- Equipo de soporte
- Compliance legal completo