# Roadmap del proyecto

## Fase 0: Setup y documentación ✅
**Estado:** Completa

- [x] Research sobre blender-mcp y alternativas
- [x] Decisión de arquitectura (blender-mcp Python package + BlenderMCP addon)
- [x] Creación de CLAUDE.md y docs/
- [x] Estructura de directorios del proyecto

---

## Fase 1: Conexión básica Claude Code ↔ Blender ✅
**Estado:** Completa

- [x] Addon BlenderMCP instalado en Blender 5.1 (puerto 9876)
- [x] MPFB2 v2.0.14 instalado desde extensions.blender.org
- [x] blender-mcp Python package como servidor MCP (stdio)
- [x] `.mcp.json` configurado con blender + n8n-mcp servers
- [x] Conexión verificada: `get_scene_info` devuelve datos reales

---

## Fase 2: Scripts base ✅
**Estado:** Completa

- [x] `scripts/scene_setup.py` — Escena de estudio (plano, fondo infinito, cámara)
- [x] `scripts/lighting.py` — Setup 3 puntos (key 800W, fill 300W, rim 400W)
- [x] `scripts/materials.py` — Materiales de telas (algodón, denim, seda, piel)
- [x] `scripts/render.py` — PREVIEW (EEVEE) y PRODUCTION (Cycles 256 samples, denoising)
- [x] Escena guardada en `scenes/studio_base_v1.blend`

---

## Fase 3: Personajes y prendas ✅
**Estado:** Completa

- [x] `scripts/character.py` — Personaje MPFB2 con perfil talle grande (PERFIL_TALLEGR)
- [x] Shape keys de peso/proporciones via `TargetService.reapply_macro_details()`
- [x] `scripts/clothing.py` — Prendas procedurales (remera, vestido) con bmesh
- [x] Rig MPFB2 con pose parada natural (rotation_difference() geométrico)
- [x] Material de piel con subsurface scattering aplicado a todos los mesh del personaje
- [ ] Cloth simulation (bake físico) — ropa actual es procedural estática

---

## Fase 4: Pipeline automatizado con n8n ✅
**Estado:** Completa (core)

- [x] Bridge HTTP FastAPI (`blender-bridge`) en Docker puerto 9877
- [x] Docker Compose con red interna compartida n8n ↔ bridge
- [x] Workflow n8n "Blender - Render de Prenda" (ID: `KYMm3iZS5MM8Incf`)
- [x] Webhook `POST /webhook/render-prenda` activo y verificado
- [x] **Pipeline end-to-end funcionando**: webhook → n8n → bridge → Blender → PNG
- [ ] Google Drive upload automático post-render
- [ ] Trigger desde Google Sheets (nuevo producto → render automático)

---

## Fase 5: Producción y automatización completa
**Estado:** Próximo

### 5a — Calidad de renders
- [ ] Cloth simulation (bake 30 frames) para ropa con caída natural
- [ ] Más prendas: pantalón, campera, vestido largo
- [ ] Variaciones de pose (3/4, lateral, detalle)

### 5b — Integración Google
- [ ] Google Drive node en n8n — subir render post-producción
- [ ] Google Sheets trigger — leer producto nuevo → disparar render con parámetros
- [ ] Notificación WhatsApp (Evolution API) cuando el render está listo

### 5c — Batch y escala
- [ ] Batch render: misma prenda en múltiples colores en un solo workflow
- [ ] Templates de escenas por categoría (casual, formal, deportivo)
- [ ] Poses variadas (Mixamo o biblioteca propia)

---

## Backlog (ideas futuras)

- Usar renders como reference images para Imagen 4 Ultra / Veo 3
- Fondo de escena variable (outdoor, interior, neutro) por categoría
- Watermark automático con logo de El Guardarropa de Ana
- Preview rápido EEVEE para aprobación antes del render Cycles completo
