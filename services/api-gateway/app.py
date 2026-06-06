"""
API Gateway - 911 AI Flow Demo
Propósito: Proxy con CORS para permitir que Lovable consuma el backend local
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import httpx
import logging
from datetime import datetime

# Configurar logging (sin imprimir PII)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="911 AI Flow Demo - API Gateway",
    description="Gateway con CORS y Private Network Access para integración con Lovable",
    version="1.0.2"
)

# Middleware único para CORS y Private Network Access
@app.middleware("http")
async def cors_private_network_middleware(request: Request, call_next):
    """
    Middleware único para manejar CORS y Private Network Access.
    
    Necesario para que Lovable (localhost:5173) pueda acceder al gateway (localhost:8010).
    Maneja preflight OPTIONS y agrega header Access-Control-Allow-Private-Network.
    
    IMPORTANTE: No usar CORSMiddleware de FastAPI al mismo tiempo, ya que intercepta
    el preflight OPTIONS antes de que este middleware pueda agregar el header PNA.
    """
    origin = request.headers.get("origin", "*")
    requested_headers = request.headers.get(
        "access-control-request-headers",
        "content-type, authorization"
    )

    # Manejar preflight OPTIONS (devolver 204 sin procesar)
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    # Agregar headers CORS y Private Network Access
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = requested_headers
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"
    response.headers["Vary"] = "Origin"

    return response

# URLs de servicios internos
N8N_WEBHOOK_URL = "http://n8n:5678/webhook/911-call"
N8N_AUTH = ("admin", "changeme")
ANALYTICS_BASE_URL = "http://api-analytics:8003"
TIMEOUT = 15.0  # 15 segundos

# Modelos Pydantic
class EmergencyCallPayload(BaseModel):
    transcript: str = Field(..., min_length=1, max_length=10000)
    location_hint: Optional[str] = Field(None, max_length=500)
    solid_consent: Optional[bool] = True
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "transcript": "Hay un incendio en mi edificio",
                "location_hint": "Colonia Centro",
                "solid_consent": True,
                "metadata": {
                    "source": "lovable_dashboard"
                }
            }
        }


# Health check
@app.get("/health")
async def health_check():
    """Health check del gateway"""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# Endpoint principal: POST /911-call
@app.post("/911-call")
async def submit_emergency_call(payload: EmergencyCallPayload):
    """
    Recibe llamada de emergencia desde Lovable y la reenvía a n8n webhook.
    
    NO guarda datos.
    NO loggea transcript (privacidad).
    """
    try:
        # Log sin PII
        logger.info(f"Received emergency call from Lovable (transcript length: {len(payload.transcript)} chars)")
        
        # Preparar payload para n8n
        n8n_payload = {
            "transcript": payload.transcript,
            "location_hint": payload.location_hint,
            "solid_consent": payload.solid_consent,
            "metadata": payload.metadata or {}
        }
        
        # Asegurar que metadata tenga source
        if "source" not in n8n_payload["metadata"]:
            n8n_payload["metadata"]["source"] = "lovable_dashboard"
        
        # Agregar timestamp si no existe
        if "timestamp" not in n8n_payload["metadata"]:
            n8n_payload["metadata"]["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Hacer request a n8n con timeout
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=n8n_payload,
                auth=N8N_AUTH
            )
            
            # Verificar respuesta
            if response.status_code != 200:
                logger.error(f"n8n webhook returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"n8n webhook error: {response.text}"
                )
            
            # Devolver respuesta de n8n
            result = response.json()
            logger.info(f"Emergency call processed successfully (call_id: {result.get('call_id', 'unknown')})")
            return result
            
    except httpx.TimeoutException:
        logger.error("Timeout calling n8n webhook")
        raise HTTPException(
            status_code=504,
            detail="Gateway timeout: n8n webhook did not respond in time"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error calling n8n: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Gateway error: Could not reach n8n webhook ({str(e)})"
        )
    except Exception as e:
        logger.error(f"Unexpected error in /911-call: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal gateway error: {str(e)}"
        )


# Endpoint: GET /analytics/summary
@app.get("/analytics/summary")
async def get_analytics_summary():
    """
    Proxy para obtener resumen de analytics.
    Reenvía a api-analytics:8003/analytics/summary
    """
    try:
        logger.info("Fetching analytics summary")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/analytics/summary")
            
            if response.status_code != 200:
                logger.error(f"api-analytics returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Analytics API error: {response.text}"
                )
            
            result = response.json()
            logger.info("Analytics summary fetched successfully")
            return result
            
    except httpx.TimeoutException:
        logger.error("Timeout calling api-analytics")
        raise HTTPException(
            status_code=504,
            detail="Gateway timeout: api-analytics did not respond in time"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error calling api-analytics: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Gateway error: Could not reach api-analytics ({str(e)})"
        )
    except Exception as e:
        logger.error(f"Unexpected error in /analytics/summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal gateway error: {str(e)}"
        )


# Endpoint: GET /analytics/predictions
@app.get("/analytics/predictions")
async def get_analytics_predictions():
    """
    Proxy para obtener predicciones de analytics.
    Reenvía a api-analytics:8003/analytics/predictions
    """
    try:
        logger.info("Fetching analytics predictions")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/analytics/predictions")
            
            if response.status_code != 200:
                logger.error(f"api-analytics returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Analytics API error: {response.text}"
                )
            
            result = response.json()
            logger.info("Analytics predictions fetched successfully")
            return result
            
    except httpx.TimeoutException:
        logger.error("Timeout calling api-analytics")
        raise HTTPException(
            status_code=504,
            detail="Gateway timeout: api-analytics did not respond in time"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error calling api-analytics: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Gateway error: Could not reach api-analytics ({str(e)})"
        )
    except Exception as e:
        logger.error(f"Unexpected error in /analytics/predictions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal gateway error: {str(e)}"
        )


# Endpoint: GET /judge/metrics/postgis
@app.get("/judge/metrics/postgis")
async def get_judge_metrics_postgis():
    """
    Proxy para obtener métricas PostGIS para jueces.
    Reenvía a api-analytics:8003/judge/metrics/postgis
    """
    try:
        logger.info("Fetching judge metrics (PostGIS)")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/judge/metrics/postgis")
            
            if response.status_code != 200:
                logger.error(f"api-analytics returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Analytics API error: {response.text}"
                )
            
            result = response.json()
            logger.info("Judge metrics fetched successfully")
            return result
            
    except httpx.TimeoutException:
        logger.error("Timeout calling api-analytics")
        raise HTTPException(
            status_code=504,
            detail="Gateway timeout: api-analytics did not respond in time"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error calling api-analytics: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Gateway error: Could not reach api-analytics ({str(e)})"
        )
    except Exception as e:
        logger.error(f"Unexpected error in /judge/metrics/postgis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal gateway error: {str(e)}"
        )


# Endpoint: GET /judge/geo/alcaldias
@app.get("/judge/geo/alcaldias")
async def get_alcaldias_geojson():
    """
    Proxy para obtener alcaldías como GeoJSON.
    Reenvía a api-analytics:8003/judge/geo/alcaldias
    """
    try:
        logger.info("Fetching alcaldías GeoJSON")
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/judge/geo/alcaldias")
            
            if response.status_code != 200:
                logger.error(f"api-analytics returned status {response.status_code}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Analytics API error: {response.text}"
                )
            
            result = response.json()
            logger.info(f"Alcaldías GeoJSON fetched successfully ({result.get('metadata', {}).get('feature_count', 0)} features)")
            return result
            
    except httpx.TimeoutException:
        logger.error("Timeout calling api-analytics")
        raise HTTPException(
            status_code=504,
            detail="Gateway timeout: api-analytics did not respond in time"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error calling api-analytics: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Gateway error: Could not reach api-analytics ({str(e)})"
        )
    except Exception as e:
        logger.error(f"Unexpected error in /judge/geo/alcaldias: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal gateway error: {str(e)}"
        )


# Predictive Analytics Endpoints
@app.get("/predictive/overview")
async def get_predictive_overview():
    """Proxy para obtener overview predictivo"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/predictive/overview")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except Exception as e:
        logger.error(f"Error in /predictive/overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/hourly")
async def get_predictive_hourly():
    """Proxy para obtener distribución horaria predictiva"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/predictive/hourly")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except Exception as e:
        logger.error(f"Error in /predictive/hourly: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/categories")
async def get_predictive_categories():
    """Proxy para obtener distribución por categorías predictivas"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/predictive/categories")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except Exception as e:
        logger.error(f"Error in /predictive/categories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/alcaldias")
async def get_predictive_alcaldias():
    """Proxy para obtener top alcaldías predictivas"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/predictive/alcaldias")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except Exception as e:
        logger.error(f"Error in /predictive/alcaldias: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/forecast")
async def get_predictive_forecast():
    """Proxy para obtener forecast predictivo"""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(f"{ANALYTICS_BASE_URL}/predictive/forecast")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    except Exception as e:
        logger.error(f"Error in /predictive/forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predictive/events")
async def predictive_events_sse():
    """
    Proxy SSE para eventos predictivos en tiempo real
    Nota: SSE streaming puede ser complejo en proxy. Si hay problemas,
    el frontend puede conectarse directamente a api-analytics:8003/predictive/events
    """
    from starlette.responses import StreamingResponse
    
    async def event_stream():
        """Stream events from analytics service"""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", f"{ANALYTICS_BASE_URL}/predictive/events") as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except Exception as e:
            logger.error(f"SSE proxy error: {str(e)}")
            yield f"event: error\ndata: {{'error': '{str(e)}'}}\n\n".encode()
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Manejo global de errores
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Manejo global de excepciones no capturadas"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

# Made with Bob
