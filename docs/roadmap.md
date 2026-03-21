# Roadmap del proyecto

## Fase 0: Setup y documentación ✅
**Estado:** Completa

- [x] Research sobre blender-mcp y alternativas
- [x] Decisión de arquitectura (blender-ai-mcp + Docker)
- [x] Creación de CLAUDE.md y docs/
- [x] Estructura de directorios del proyecto

---

## Fase 1: Conexión básica Claude Code ↔ Blender
**Estado:** Pendiente
**Objetivo:** Que Claude Code pueda hablar con Blender y ejecutar una operación simple.

### Checklist de instalación

#### En Windows (Blender host)
- [ ] Instalar addon BlenderMCP en Blender 4.2+
  - Descargar: https://github.com/ahujasid/blender-mcp/blob/main/addon.py
  - Blender → Edit → Preferences → Add-ons → Install from Disk
  - Habilitar "Interface: Blender MCP"
- [ ] Instalar MPFB2 en Blender
  - Blender Extensions → buscar "MPFB" → Instalar
- [ ] Verificar que el addon corre en puerto 9876

#### En VS Code
- [ ] Confirmar que Docker Desktop está corriendo
- [ ] Abrir la carpeta del proyecto en VS Code
- [ ] Verificar que `.mcp.json` está en la raíz
- [ ] Pull de la imagen: `docker pull ghcr.io/patrykiti/blender-ai-mcp:latest`

#### Test de conexión
- [ ] Abrir Blender → Panel N → "Connect to Claude" → verificar "running on port 9876"
- [ ] Abrir Claude Code en VS Code
- [ ] Ejecutar: "Get scene info from Blender"
- [ ] Si devuelve info de la escena → ✅ conexión OK

### Troubleshooting esperado
Si falla la conexión:
1. Verificar que Blender tiene el addon activo y el servidor corriendo
2. Verificar que Docker Desktop está activo
3. Probar `docker pull ghcr.io/patrykiti/blender-ai-mcp:latest` manualmente
4. Revisar Windows Firewall para puerto 9876
5. Si sigue fallando, probar con la config alternativa de uvx (ver decisions.md)

---

## Fase 2: Scripts base
**Estado:** Pendiente
**Objetivo:** Tener los scripts Python fundamentales funcionando desde Claude Code.

- [ ] `scripts/scene_setup.py` — Escena de estudio base (plano, fondo infinito)
- [ ] `scripts/lighting.py` — Setup de 3 puntos (key, fill, rim)
- [ ] `scripts/materials.py` — Materiales de telas básicos (algodón, denim, seda)
- [ ] `scripts/render.py` — Render con Cycles, resolución y output path
- [ ] Hacer una escena de prueba completa end-to-end
- [ ] Documentar cada script con comentarios y ejemplos

---

## Fase 3: Personajes y prendas
**Estado:** Pendiente
**Objetivo:** Generar un personaje con proporciones de talle grande y vestirlo.

- [ ] `scripts/character.py` — Crear personaje base con MPFB2 API
- [ ] Explorar sliders de MPFB2 para proporciones corporales diversas
- [ ] `scripts/clothing.py` — Importar mesh de prenda simple
- [ ] Configurar cloth simulation básica (prenda sobre maniquí)
- [ ] Render completo: personaje + prenda + estudio + iluminación
- [ ] Documentar el workflow reproducible

---

## Fase 4: Pipeline automatizado con n8n
**Estado:** Futuro (post-Fase 3)
**Objetivo:** n8n puede disparar renders automáticamente.

- [ ] Evaluar blender-mcp-n8n (seehiong/blender-mcp-n8n)
- [ ] Diseñar trigger de workflow (ej: nuevo producto en Google Sheets)
- [ ] Implementar Docker Compose con n8n + bridge + Blender
- [ ] Primer workflow: "producto nuevo → render de ficha de catálogo"
- [ ] Guardar renders automáticamente en Google Drive

---

## Backlog (ideas para explorar)

- Integrar renders como reference images para Imagen 4 Ultra / Veo 3
- Batch renders con variaciones de color de la misma prenda
- Templates de escenas para diferentes categorías (casual, formal, deportivo)
- Poses variadas usando Mixamo + Blender
