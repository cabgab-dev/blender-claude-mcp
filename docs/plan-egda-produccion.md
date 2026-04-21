# Plan de producción EGDA — Pipeline Blender automatizado

**Objetivo:** Pipeline semi-automatizado que genere imágenes de producto para El Guardarropa de Ana
(moda en talles grandes) usando Blender + n8n + bridge HTTP.

**Última actualización:** 2026-04-03

---

## Estado del pipeline

```
n8n  →  POST /webhook/render-egda
         ↓
     blender-bridge :9877  (Docker, infra/docker-compose.blender.yml)
         ↓ TCP socket
     Blender 5.1 :9876  (addon BlenderMCP activo)
         ↓ bpy Python
     PNG → blender-pipeline/renders/auto/
```

---

## ✅ Fase A — Blockers (completada 2026-04-03)

- [x] Rutas hardcodeadas corregidas en `lighting.py`, `render.py`, `bridge.py`
- [x] Validación de render en bridge.py reparada (detecta `RENDER_OK:` en respuesta)
- [x] `infra/docker-compose.blender.yml` limpiado (solo blender-bridge)
- [x] Workflow n8n "Blender - Render EGDA" creado y activo (ID: `0oDAI9xihMJn9OZR`)
- [x] 4/4 tests pasados — pipeline end-to-end funcional

**Cómo disparar un render hoy:**
```bash
curl -X POST http://localhost:5678/webhook/render-egda \
  -H "Content-Type: application/json" \
  -d '{
    "garment": "dress",
    "fabric": "cotton",
    "color": [0.8, 0.3, 0.5],
    "output_name": "egda_vestido_001",
    "samples": 64
  }'
```
Valores válidos: `garment` = dress | tshirt | pants | `fabric` = cotton | denim | silk

---

## 🔜 Fase B — Calidad de imagen

**Objetivo:** subir calidad al nivel de e-commerce real.

### B1 — Resolución y samples de producción
**Archivo:** `scripts/render.py`
- Agregar modo `ECOMMERCE`: 1920×2560 px, 512 samples, OIDN denoising
- Actualizar `bridge.py` para aceptar parámetro `mode` (preview | production | ecommerce)
- Actualizar `RenderRequest` en bridge.py con campo `mode: str = "preview"`

### B2 — Cloth simulation sin timeout
**Archivo:** `scripts/clothing.py`
- Dividir `bake_cloth()` en dos llamadas separadas al bridge (evita timeout de 120s)
- Llamada 1: setup cloth modifier + bake frames 1–15
- Llamada 2: bake frames 16–30 + apply_as_shape_key para congelar pose

### B3 — Cabello procedural básico
**Archivo:** `scripts/character.py`
- Agregar función `add_hair_basic(human, length=0.25, color=(0.15, 0.08, 0.05))`
- Usar sistema de partículas de Blender (Hair type), no requiere MPFB2
- Resultado suficiente para silueta de moda

### B4 — Poses adicionales
**Archivo:** `scripts/character.py`
- `pose_tres_cuartos()` — cuerpo girado 30° en Z, más dinámico
- `pose_detalle_superior()` — reposiciona cámara a altura de cintura (location Y=-3.5, Z=1.1)

---

## ✅ Fase C — Pipeline batch automatizado (completada 2026-04-03)

### C1 — Google Drive auto-upload
**Archivo:** workflow n8n `blender-render-egda.json`
- Agregar nodo Google Drive después del `Responder OK`
- Sube PNG a carpeta `EGDA/renders/YYYY-MM-DD/` en Drive de elguardarropadeana@gmail.com
- Requiere credencial OAuth Google Drive en n8n

### C2 — Trigger desde Google Sheets
**Workflow nuevo:** `blender-batch-egda.json`
- Trigger: Google Sheets (polling cada 30min o webhook)
- Lee columnas: prenda | tela | color_hex | nombre_archivo | estado
- Por cada fila con estado vacío: convierte hex→RGB, dispara render, sube a Drive, marca "✅"

### C3 — Watermark EGDA
- Post-proceso en n8n con nodo Edit Image
- Logo en esquina inferior derecha, 30% opacity
- Archivo de logo: `blender-pipeline/assets/egda_logo.png` (agregar)

---

## 🔜 Fase D — Calidad avanzada (después de C)

### D1 — Texturas reales de telas
- Descargar desde Polyhaven via MCP: `fabric_cotton_002`, `fabric_denim`, `fabric_silk`
- Mapas: color + normal + roughness
- Reemplaza materiales procedurales en `materials.py`

### D2 — Fondos alternativos
- Fondo blanco puro (RGB 1,1,1) para fichas Mercado Libre / Amazon
- Fondo degradado suave gris→blanco

### D3 — HDRI 4K
- Reemplazar `studio_small_08_1k.hdr` (1K) por versión 4K
- Elimina banding en zonas especulares (seda, cuero)
- Descargar: `https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/studio_small_08_4k.hdr`

---

## Referencia rápida — comandos del stack

```bash
# Levantar blender-bridge
cd MI-AUTOMATIZACION/infra
docker compose -f docker-compose.blender.yml up -d --build

# Levantar n8n + postgres + redis + evolution + ngrok
cd MI-AUTOMATIZACION/alfred/config
docker compose up -d

# Ver containers activos
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Health checks
curl http://localhost:9877/health       # bridge
curl http://localhost:9877/blender/ping # bridge → blender
curl http://localhost:5678/healthz      # n8n
```

---

## Archivos clave del pipeline

| Archivo | Propósito |
|---|---|
| `infra/blender-bridge/bridge.py` | API REST → Blender socket |
| `infra/docker-compose.blender.yml` | Solo blender-bridge |
| `alfred/config/docker-compose.yml` | Stack completo (n8n, postgres, redis, evolution, ngrok) |
| `alfred/n8n-workflows/blender-render-egda.json` | Workflow n8n activo |
| `scripts/character.py` | Personaje talle grande MPFB2 |
| `scripts/clothing.py` | Prendas procedurales + cloth sim |
| `scripts/lighting.py` | HDRI + 3-point lighting |
| `scripts/materials.py` | Materiales textiles |
| `scripts/render.py` | Configuración y ejecución Cycles |
| `scripts/scene_setup.py` | Escena de estudio base |
| `assets/hdri/studio_small_08_1k.hdr` | HDRI de iluminación |
| `renders/auto/` | Output de renders automáticos |
