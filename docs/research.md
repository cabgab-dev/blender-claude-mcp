# Research: Blender MCP ecosystem
**Fecha:** Marzo 2026
**Objetivo:** Evaluar opciones de conexión Claude Code ↔ Blender para pipeline de moda

---

## Proyecto principal: ahujasid/blender-mcp

- **Versión actual:** 1.5.5 (enero 2026)
- **Stars:** ~17.500 en GitHub
- **Licencia:** MIT
- **Distribución:** PyPI + descarga manual del addon

### Arquitectura interna
- Addon Blender (`addon.py`) → servidor TCP en `localhost:9876`
- Servidor MCP (`server.py`, 1186 líneas) → proceso separado vía `uvx blender-mcp`
- Comunicación: JSON plano sobre TCP, buffer 8192 bytes, timeout 180 segundos
- Mensajes: `{"type": "command", "params": {...}}` → `{"status": "success", "result": ...}`

### 22 herramientas expuestas
**Core (siempre disponibles):**
- `get_scene_info`
- `get_object_info(object_name)`
- `get_viewport_screenshot(max_size)`
- `execute_blender_code(code)` ← **la más importante**

**PolyHaven (sin API key):**
- `search_polyhaven_assets`, `download_polyhaven_asset`, `set_texture`, etc.

**Sketchfab (requiere API key):**
- `search_sketchfab_models`, `download_sketchfab_model`

**Generación IA (Hyper3D Rodin / Hunyuan3D):**
- `generate_hyper3d_model_via_text`, `generate_hyper3d_model_via_images`

### Limitaciones críticas
- Sin herramientas nativas para luces, modificadores, animación
- `execute_blender_code` sin sandboxing (riesgo de seguridad, pero necesario)
- Issues de conectividad frecuentes en Windows (ProactorEventLoop, Issue #52)
- Issue #13: Claude Code específicamente reportado como problemático (sin resolución oficial)
- Timeout de 180s puede ser insuficiente para cloth bake complejos
- Un solo servidor MCP a la vez

---

## Alternativa elegida: patrykiti/blender-ai-mcp

**¿Por qué es mejor para nuestro caso?**
- Imagen Docker lista en `ghcr.io/patrykiti/blender-ai-mcp:latest`
- 50+ herramientas (vs 22 del original)
- Variable `BLENDER_RPC_HOST` documentada para Docker
- Architecture modular con namespaces (scene, material, UV, collection)
- Testing en Blender 5.0
- Lista Claude Code como cliente soportado

**Configuración Docker:**
```json
{
  "mcpServers": {
    "blender": {
      "command": "docker",
      "args": ["run", "--rm", "-i",
               "-e", "BLENDER_RPC_HOST=host.docker.internal",
               "ghcr.io/patrykiti/blender-ai-mcp:latest"]
    }
  }
}
```

---

## Addon de Blender a instalar

El addon es compatible con los **dos servidores** (ahujasid y blender-ai-mcp usan el mismo addon).

1. Descargar `addon.py` desde: https://github.com/ahujasid/blender-mcp/blob/main/addon.py
2. Blender → Edit → Preferences → Add-ons → Install from Disk → seleccionar `addon.py`
3. Habilitar "Interface: Blender MCP"
4. Viewport 3D → tecla N → pestaña BlenderMCP → "Connect to Claude"

**Puerto por defecto:** 9876 (configurable en el panel del addon)

---

## Herramienta estrella: execute_blender_code

Todo lo que no está como herramienta nativa se hace con Python vía esta tool.
Permite ejecutar cualquier operación de la API `bpy`:

```python
# Ejemplo: crear escena de estudio básica
import bpy

# Limpiar escena
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Agregar plano de fondo
bpy.ops.mesh.primitive_plane_add(size=10)
plane = bpy.context.active_object
plane.name = "Studio_Background"

# Agregar luz de área
bpy.ops.object.light_add(type='AREA', location=(3, -3, 5))
key_light = bpy.context.active_object
key_light.name = "Studio_Key_Light"
key_light.data.energy = 500
```

---

## Personajes para moda en talles grandes: MPFB2

**MPFB** (MakeHuman Plugin For Blender) es la mejor opción free para personajes parametrizados.

- **Compatibilidad:** Blender 4.2+ ✓
- **Instalación:** Blender Extensions (sin descargar manualmente)
- **Licencia:** CC0

**API programática clave:**
```python
from mpfb.services.humanservice import HumanService

# Crear personaje con proporciones específicas
human = HumanService.create_human()
# Ajustar masa corporal (relevante para talles grandes)
obj.data.shape_keys.key_blocks['muscle'].value = 0.3
obj.data.shape_keys.key_blocks['overweight'].value = 0.7
```

**Alternativas evaluadas:**
- MB-Lab: abandonado, no recomendado
- MakeHuman standalone: menos integración con Blender 4.x
- Daz 3D: sin integración MCP viable

---

## Rendering: EEVEE vs Cycles

| | EEVEE | Cycles |
|---|---|---|
| Velocidad | Segundos | Minutos |
| Calidad | Media-alta | Fotorrealista |
| Uso recomendado | Iteración, pruebas | Renders finales |
| Headless Docker | ❌ (requiere OpenGL) | ✅ (con CPU) |
| GPU Docker | ❌ | ✅ (CUDA) |

**Estrategia:** EEVEE para iterar, Cycles para renders de catálogo final.

---

## Integración n8n (Fase 4)

Existe `seehiong/blender-mcp-n8n` que implementa un bridge ASGI en puerto 8008:
```
n8n AI Agent → MCP Client (HTTP) → Bridge Server (8008) → Blender Addon (8888)
```

Configuración Docker Compose disponible en `/docs/architecture.md`.

---

## Fuentes consultadas
- https://github.com/ahujasid/blender-mcp
- https://github.com/patrykiti/blender-ai-mcp
- https://github.com/seehiong/blender-mcp-n8n
- https://static.makehumancommunity.org/mpfb.html
- https://deepwiki.com/ahujasid/blender-mcp
- Issues GitHub: #13, #52, #51, #73, #102
