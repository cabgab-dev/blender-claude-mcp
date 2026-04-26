# Test Fase A — Verificación end-to-end

## Prerequisitos (hacer en orden)

### 1. Levantar Blender
- Abrir Blender 4.2+
- Presionar `N` → pestaña **BlenderMCP**
- Click en **Connect to Claude** → verificar "Server running on port 9876"

### 2. Levantar blender-bridge (Docker)
```bash
cd C:\Users\cabga\Desktop\MI-AUTOMATIZACION\infra
docker compose -f docker-compose.blender.yml up -d --build
```
Verificar: `curl http://localhost:9877/health` → debe devolver `{"status":"ok"}`

### 3. Levantar n8n
```bash
cd C:\Users\cabga\Desktop\MI-AUTOMATIZACION\alfred\config
docker compose up -d
```

### 4. Importar workflow en n8n
- Ir a `http://localhost:5678`
- Menú → **Workflows → Import from file**
- Seleccionar: `alfred/n8n-workflows/blender-render-egda.json`
- Activar el workflow (toggle ON)

---

## Tests en orden

### Test 1 — Bridge alive
```bash
curl http://localhost:9877/health
```
Respuesta esperada:
```json
{"status": "ok", "blender_host": "host.docker.internal", "blender_port": 9876}
```

### Test 2 — Blender conectado
```bash
curl http://localhost:9877/blender/ping
```
Respuesta esperada: JSON con info de la escena de Blender.

### Test 3 — Render directo al bridge (sin n8n)
```bash
curl -X POST http://localhost:9877/render \
  -H "Content-Type: application/json" \
  -d "{\"garment\": \"dress\", \"fabric\": \"cotton\", \"color\": [0.8, 0.3, 0.5], \"output_name\": \"test_fase_a\", \"samples\": 32}"
```
Respuesta esperada:
```json
{"status": "ok", "output_path": "C:\\...\\blender-pipeline\\renders\\auto\\test_fase_a.png", ...}
```
Verificar que existe el archivo: `blender-pipeline/renders/auto/test_fase_a.png`

### Test 4 — Render via n8n webhook (pipeline completo)
```bash
curl -X POST http://localhost:5678/webhook/render-egda \
  -H "Content-Type: application/json" \
  -d "{\"garment\": \"dress\", \"fabric\": \"silk\", \"color\": [0.9, 0.8, 0.7], \"output_name\": \"egda_test_001\", \"samples\": 64}"
```
Respuesta esperada:
```json
{"status": "ok", "output_path": "...egda_test_001.png", "garment": "dress", "fabric": "silk"}
```
Verificar que existe el archivo: `blender-pipeline/renders/auto/egda_test_001.png`

---

## Errores comunes

| Error | Causa | Solución |
|---|---|---|
| `503 No se puede conectar a Blender` | Blender no está corriendo o addon inactivo | Abrir Blender → activar addon |
| `504 timeout` | Render demoró más de 120s | Bajar `samples` o usar modo CPU |
| `500 Blender no confirmó el render` | Error en el script Python | Ver logs del addon en Blender (Info > Toggle System Console) |
| Bridge no responde en :9877 | Docker no está corriendo | `docker compose up -d --build` |
| n8n no recibe webhook | Workflow no activo | Activar toggle en n8n UI |
