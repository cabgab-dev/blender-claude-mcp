# Prompt para nueva sesión de Claude Code

---

Estamos trabajando en el **pipeline automatizado de renders de moda para EGDA (El Guardarropa de Ana)**, marca de ropa en talles grandes.

## Directorio de trabajo
`C:\Users\cabga\Desktop\MI-AUTOMATIZACION\blender-pipeline`

El plan completo está en `docs/plan-egda-produccion.md`. Leelo antes de empezar.

---

## Estado actual — qué está COMPLETADO

### ✅ Fase A — Blockers (2026-04-03)
- Pipeline end-to-end funcional: n8n → blender-bridge (Docker :9877) → Blender 5.1 (:9876) → PNG
- Workflow n8n activo ID `0oDAI9xihMJn9OZR` — `POST http://localhost:5678/webhook/render-egda`

### ✅ Fase B — Calidad de imagen (2026-04-03)
- `render.py`: modo ECOMMERCE (1920×2560, 512 samples, OIDN)
- `bridge.py`: campo `mode` en RenderRequest ("preview" | "production" | "ecommerce")
- `clothing.py`: cloth simulation dividida en `bake_cloth_part1()` + `bake_cloth_part2()` sin timeout
- `character.py`: `add_hair_basic()` con partículas Hair + PrincipledHair shader
- `character.py`: `pose_tres_cuartos()` (30° en Z) + `pose_detalle_superior()` (cámara reposicionada)

### ✅ Fase C — Pipeline batch (2026-04-03)
- `bridge.py` devuelve `image_base64` del PNG + aplica watermark EGDA (Pillow, 30% opacity)
- `docker-compose.blender.yml`: volumes `/renders` + `/assets` montados en el container
- Workflow "Blender - Render EGDA" actualizado: Decodificar Imagen → Subir a Drive (pendiente credencial)
- Workflow "Blender - Batch EGDA" (ID: `UQmt2NgMCEzKdbNW`) creado (inactivo): Schedule → Google Sheets → render → marcar ✅

---

## Lo que falta configurar para activar Drive/Sheets

Estas son las 4 acciones manuales que quedan antes de que el pipeline sea 100% autónomo:

1. **Credencial Google Drive** en n8n → reemplazar placeholder `CONFIGURAR_CREDENCIAL_GOOGLE_DRIVE` en nodo "Subir a Drive" del workflow `0oDAI9xihMJn9OZR`
2. **ID carpeta EGDA en Drive** → reemplazar `CONFIGURAR_ID_CARPETA_EGDA_RENDERS` en el mismo nodo
3. **Credencial Google Sheets** + ID de planilla → configurar en workflow batch `UQmt2NgMCEzKdbNW`
4. **Logo real EGDA** → reemplazar `blender-pipeline/assets/egda_logo.png` (ahora hay un placeholder generado por Pillow)

---

## Próximo paso: Fase D — Calidad avanzada

**D1** — Texturas reales de telas desde Polyhaven (normal + roughness + color) via MCP
`mcp__blender__search_polyhaven_assets` + `mcp__blender__download_polyhaven_asset`

**D2** — Fondo blanco puro alternativo para fichas Mercado Libre / Amazon

**D3** — HDRI 4K (reemplazar `studio_small_08_1k.hdr` de 1K por versión 4K)
URL: `https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/studio_small_08_4k.hdr`

---

## Stack para levantar

```bash
# 1. Abrir Blender 5.1 → N → BlenderMCP → Connect (puerto 9876)

# 2. Levantar blender-bridge (rebuild obligatorio — bridge.py cambió)
cd C:/Users/cabga/Desktop/MI-AUTOMATIZACION/infra
docker compose -f docker-compose.blender.yml up -d --build

# 3. n8n ya corre como parte del stack alfred
cd C:/Users/cabga/Desktop/MI-AUTOMATIZACION/alfred/config
docker compose up -d

# Health check
curl http://localhost:9877/health
curl http://localhost:9877/blender/ping
```

## Render de prueba (modo ecommerce)

```bash
curl -X POST http://localhost:5678/webhook/render-egda \
  -H "Content-Type: application/json" \
  -d '{
    "garment": "dress",
    "fabric": "silk",
    "color": [0.8, 0.3, 0.5],
    "output_name": "egda_ecommerce_001",
    "mode": "ecommerce",
    "watermark": true
  }'
```
