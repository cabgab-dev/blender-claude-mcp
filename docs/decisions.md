# Log de decisiones técnicas

## DEC-001: blender-ai-mcp vs ahujasid/blender-mcp
**Fecha:** Marzo 2026
**Decisión:** Usar `patrykiti/blender-ai-mcp`

**Opciones consideradas:**
- ahujasid/blender-mcp (original, ~17.500 stars)
- patrykiti/blender-ai-mcp (fork mejorado)

**Razones:**
- blender-ai-mcp tiene imagen Docker lista (`ghcr.io/patrykiti/blender-ai-mcp:latest`)
- Variable `BLENDER_RPC_HOST` documentada para entornos Docker
- 50+ herramientas vs 22 del original
- Lista Claude Code como cliente soportado
- Arquitectura modular más mantenible

**Trade-offs:**
- Menor comunidad que el original
- Desarrollo "after-hours" (un solo mantenedor)
- Si el proyecto se abandona, migrar al original es sencillo (mismo addon de Blender)

**Fallback:** Si blender-ai-mcp falla, usar ahujasid/blender-mcp con wrapper `cmd /c`:
```json
{
  "mcpServers": {
    "blender": {
      "command": "cmd",
      "args": ["/c", "uvx", "blender-mcp"],
      "env": {"DISABLE_TELEMETRY": "true"}
    }
  }
}
```

---

## DEC-002: Docker vs instalación local para el servidor MCP
**Fecha:** Marzo 2026
**Decisión:** Usar Docker para el servidor MCP

**Razones:**
- Consistente con el stack existente (n8n, Evolution API ya en Docker)
- No contamina el entorno Python del sistema
- Fácil de actualizar/reemplazar
- Se alinea con la futura migración al VPS de DonWeb

**Nota:** Blender corre en Windows nativo (NO en Docker) porque necesita GPU/OpenGL
para EEVEE y acceso directo a la interfaz gráfica. Solo el servidor MCP va en Docker.

---

## DEC-003: MPFB2 para personajes (vs MB-Lab, Daz 3D)
**Fecha:** Marzo 2026
**Decisión:** MPFB2 (MakeHuman Plugin For Blender)

**Razones:**
- Activamente mantenido (vs MB-Lab abandonado)
- Instalable directamente desde Blender Extensions
- API Python documentada para automatización
- Shape keys paramétricos para proporciones corporales diversas
- Compatible con Blender 4.2+
- Licencia CC0

**Daz 3D:** Descartado porque no tiene integración MCP viable y requiere conocimiento previo.

---

## DEC-004: Cycles para renders de producción (vs EEVEE)
**Fecha:** Marzo 2026
**Decisión:** EEVEE para iteración, Cycles para renders finales

**Razones:**
- EEVEE es rápido (segundos) — ideal para verificar composición/iluminación
- Cycles es fotorrealista — necesario para renders de catálogo de moda
- EEVEE no funciona en Docker headless sin GPU passthrough
- Cycles CPU funciona en cualquier entorno, incluido Docker

**Para el futuro con n8n:** Los renders batch automatizados usarán Cycles CPU
o Cycles con CUDA si se configura GPU passthrough en el VPS.

---

## DEC-005: Scope del .mcp.json (project vs user)
**Fecha:** Marzo 2026
**Decisión:** Usar `.mcp.json` a nivel de proyecto (versionado)

**Razones:**
- El MCP de Blender es específico de este proyecto
- Permite que el proyecto sea reproducible desde cero
- Otros proyectos con Claude Code no se ven afectados
- La configuración es la misma para cualquier persona que clone el repo

**Nota sobre precedencia:** local > project > user.
Si hay conflictos, la config local de `~/.claude.json` tiene prioridad.
