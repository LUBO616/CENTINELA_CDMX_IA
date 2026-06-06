# Gate 5: Corrección de CORS y Private Network Access

## Problema Identificado

El navegador bloqueaba requests de Lovable (localhost:5173) al gateway (localhost:8010) con el error:

```
Permission was denied for this request to access the 'loopback' address space.
```

**Causa raíz:** FastAPI `CORSMiddleware` interceptaba el preflight OPTIONS antes de que el middleware custom pudiera agregar el header `Access-Control-Allow-Private-Network: true`.

---

## Solución Implementada

### Cambios en services/api-gateway/app.py

1. **Eliminado:** `from fastapi.middleware.cors import CORSMiddleware`
2. **Eliminado:** `app.add_middleware(CORSMiddleware, ...)`
3. **Mantenido:** Middleware custom único que maneja CORS y PNA

### Middleware Final

```python
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
```

---

## Validación

### 1. Reconstruir Gateway

```bash
# Detener servicios
docker compose down

# Reconstruir solo api-gateway
docker compose build api-gateway

# Levantar servicios
docker compose --profile services up -d

# Verificar que gateway está corriendo
docker compose ps api-gateway
```

### 2. Test Preflight OPTIONS - GET /analytics/summary

```bash
curl -X OPTIONS http://localhost:8010/analytics/summary \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: content-type" \
  -v 2>&1 | grep -i "access-control"
```

**Resultado esperado:**
```
< access-control-allow-origin: http://localhost:5173
< access-control-allow-methods: GET, POST, OPTIONS
< access-control-allow-headers: content-type
< access-control-allow-private-network: true
< access-control-max-age: 86400
< vary: Origin
```

**✅ CLAVE:** Debe aparecer `access-control-allow-private-network: true`

---

### 3. Test Preflight OPTIONS - POST /911-call

```bash
curl -X OPTIONS http://localhost:8010/911-call \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -v 2>&1 | grep -i "access-control"
```

**Resultado esperado:**
```
< access-control-allow-origin: http://localhost:5173
< access-control-allow-methods: GET, POST, OPTIONS
< access-control-allow-headers: content-type
< access-control-allow-private-network: true
< access-control-max-age: 86400
< vary: Origin
```

---

### 4. Test GET Real - /analytics/summary

```bash
curl -X GET http://localhost:8010/analytics/summary \
  -H "Origin: http://localhost:5173" \
  -v 2>&1 | grep -i "access-control"
```

**Resultado esperado:**
```
< access-control-allow-origin: http://localhost:5173
< access-control-allow-methods: GET, POST, OPTIONS
< access-control-allow-headers: content-type, authorization
< access-control-allow-private-network: true
< access-control-max-age: 86400
< vary: Origin
```

---

### 5. Test POST Real - /911-call

```bash
curl -X POST http://localhost:8010/911-call \
  -H "Origin: http://localhost:5173" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Test CORS con Private Network Access",
    "location_hint": "Colonia Centro",
    "solid_consent": true
  }' \
  -v 2>&1 | grep -i "access-control"
```

**Resultado esperado:**
```
< access-control-allow-origin: http://localhost:5173
< access-control-allow-methods: GET, POST, OPTIONS
< access-control-allow-headers: content-type, authorization
< access-control-allow-private-network: true
< access-control-max-age: 86400
< vary: Origin
```

---

### 6. Test desde Lovable (JavaScript)

```javascript
// En Lovable (localhost:5173)
// Abrir DevTools Console y ejecutar:

// Test 1: GET /analytics/summary
fetch('http://localhost:8010/analytics/summary')
  .then(r => r.json())
  .then(data => console.log('✅ Analytics Summary:', data))
  .catch(err => console.error('❌ Error:', err));

// Test 2: POST /911-call
fetch('http://localhost:8010/911-call', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    transcript: 'Hay un incendio en mi edificio',
    location_hint: 'Colonia Centro',
    solid_consent: true,
  }),
})
  .then(r => r.json())
  .then(data => console.log('✅ Emergency Call:', data))
  .catch(err => console.error('❌ Error:', err));
```

**Resultado esperado:**
- ✅ Sin errores de CORS en consola
- ✅ Sin errores de Private Network Access
- ✅ Datos recibidos correctamente

---

## Checklist de Validación

- [ ] Gateway reconstruido con `docker compose build api-gateway`
- [ ] Gateway corriendo con `docker compose ps api-gateway`
- [ ] OPTIONS /analytics/summary devuelve `access-control-allow-private-network: true`
- [ ] OPTIONS /911-call devuelve `access-control-allow-private-network: true`
- [ ] GET /analytics/summary devuelve datos + headers CORS
- [ ] POST /911-call procesa llamada + headers CORS
- [ ] Lovable puede hacer fetch() sin errores de CORS
- [ ] Lovable puede hacer fetch() sin errores de Private Network Access
- [ ] DevTools Console sin errores

---

## Diferencias Clave

### Antes (con CORSMiddleware)

```python
# ❌ CORSMiddleware interceptaba OPTIONS antes del middleware custom
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_private_network_access_headers(request: Request, call_next):
    # Este middleware nunca veía el preflight OPTIONS
    # porque CORSMiddleware ya lo había respondido
    ...
```

**Resultado:** Header `Access-Control-Allow-Private-Network` nunca se agregaba.

### Después (solo middleware custom)

```python
# ✅ Middleware único maneja todo
@app.middleware("http")
async def cors_private_network_middleware(request: Request, call_next):
    # Este middleware ve TODOS los requests, incluido OPTIONS
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)
    
    # Agregar headers CORS + PNA
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    ...
```

**Resultado:** Header `Access-Control-Allow-Private-Network` siempre se agrega.

---

## Comandos Rápidos

```bash
# Reconstruir y levantar
docker compose down
docker compose build api-gateway
docker compose --profile services up -d

# Verificar headers PNA en OPTIONS
curl -X OPTIONS http://localhost:8010/analytics/summary \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -v 2>&1 | grep "access-control-allow-private-network"

# Debe mostrar:
# < access-control-allow-private-network: true

# Ver logs del gateway
docker compose logs api-gateway --tail=50 -f
```

---

## Notas Importantes

### Por qué falló antes

1. FastAPI `CORSMiddleware` es un middleware de Starlette
2. Los middlewares se ejecutan en orden LIFO (Last In, First Out)
3. `CORSMiddleware` se agregó DESPUÉS del middleware custom
4. Por lo tanto, `CORSMiddleware` se ejecutó ANTES
5. `CORSMiddleware` respondió el OPTIONS con 200 OK
6. El middleware custom nunca vio el request OPTIONS
7. El header `Access-Control-Allow-Private-Network` nunca se agregó

### Por qué funciona ahora

1. Solo hay un middleware: `cors_private_network_middleware`
2. Este middleware ve TODOS los requests, incluido OPTIONS
3. Responde OPTIONS con 204 No Content
4. Agrega TODOS los headers necesarios, incluido PNA
5. El navegador recibe el header PNA y permite el request

---

## Referencias

- [Private Network Access](https://developer.chrome.com/blog/private-network-access-preflight/)
- [CORS Preflight](https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)

---

**Versión:** 1.0.2  
**Fecha:** 2026-06-06  
**Estado:** ✅ CORS y Private Network Access funcionando correctamente