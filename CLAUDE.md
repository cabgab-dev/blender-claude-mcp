# Proyecto: Blender + Claude Code via MCP
## Pipeline de generación de contenido 3D para moda en talles grandes

---

## Objetivo del proyecto

Conectar Claude Code con Blender 4.2+ mediante el protocolo MCP para generar contenido visual 3D
(renders de prendas, personajes con proporciones corporales diversas, escenas de estudio).
El objetivo final es un pipeline semi-automatizado que produzca imágenes de producto para
la marca de ropa **El Guardarropa de Ana**, especializada en talles grandes.

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Editor | VS Code + Claude Code (extensión) |
| Blender | 4.2+ en Windows (host local) |
| MCP Server | blender-ai-mcp (imagen Docker) |
| Personajes | MPFB2 (MakeHuman Plugin For Blender) |
| Renders | Cycles (producción) / EEVEE (iteración) |
| Orquestación futura | n8n (self-hosted en Docker) |
| Storage | Google Drive (elguardarropadeana@gmail.com) |

---

## Arquitectura

```
Claude Code (VS Code)
    │  JSON-RPC 2.0 / stdio
    ▼
Docker Container: blender-ai-mcp
    │  TCP socket → host.docker.internal:9876
    ▼
Blender 4.2+ (Windows host)
    └─ Addon BlenderMCP activo en panel N
    └─ MPFB2 instalado
```

---

## Herramientas MCP disponibles

La tool más importante es `execute_blender_code` — ejecuta Python (`bpy`) arbitrario en Blender.
Usar esta herramienta para TODO lo relacionado con:
- Crear/modificar personajes con MPFB2
- Simulación de telas (cloth modifier)
- Configurar iluminación y materiales
- Ejecutar renders y guardar resultados

Las otras herramientas útiles:
- `get_scene_info` — inspeccionar estado de la escena
- `get_object_info(object_name)` — detalles de un objeto
- `get_viewport_screenshot` — captura del viewport para verificar visualmente
- `download_polyhaven_asset` — descargar HDRIs y texturas de estudio gratis

---

## Convenciones del proyecto

### Archivos
- Scripts Python reutilizables → `/scripts/`
- Renders de salida → `/renders/YYYY-MM-DD/`
- Escenas Blender → `/scenes/`
- Assets importados → `/assets/`

### Código Python para Blender
- Siempre importar `bpy` al inicio del script
- Limpiar escena antes de construirla: `bpy.ops.object.select_all(action='SELECT')` + delete
- Nombrar objetos con prefijo descriptivo: `Studio_Light_Key`, `Character_Base`, etc.
- Guardar el archivo .blend al final de cada sesión de trabajo

### Timeouts
El socket MCP tiene un timeout de 180 segundos.
Para operaciones largas (cloth bake, renders complejos), dividir en pasos separados.

---

## Variables de entorno necesarias

Ver `.env.example`. Las variables reales van en `.env` (no se versiona).

```
BLENDER_RPC_HOST=host.docker.internal
BLENDER_RPC_PORT=9876
DISABLE_TELEMETRY=true
```

---

## Cómo iniciar el entorno

### Antes de usar Claude Code:
1. Abrir Blender 4.2+ en Windows
2. Presionar `N` en el viewport 3D → pestaña **BlenderMCP**
3. Hacer clic en **"Connect to Claude"**
4. Verificar que el status muestre "Server running on port 9876"

### Verificar conexión desde Claude Code:
```
Pedirle a Claude Code: "Get scene info from Blender"
```
Si devuelve información de la escena, la conexión está activa.

---

## Estado del proyecto

- [x] Fase 0: Research y documentación
- [ ] Fase 1: Conexión básica Claude Code ↔ Blender
- [ ] Fase 2: Scripts base de personaje y escena de estudio
- [ ] Fase 3: Pipeline de render de prendas
- [ ] Fase 4: Integración con n8n

Ver `/docs/roadmap.md` para detalle completo.

---

## Limitaciones conocidas (importante)

1. **Sin herramientas de luces nativas** — usar `execute_blender_code` para todo lo relacionado con iluminación
2. **Timeout de 180s** — cloth bake puede excederlo; dividir en pasos
3. **Una sola instancia MCP a la vez** — no correr dos servidores simultáneos
4. **Blender debe estar abierto con el addon activo** antes de usar Claude Code
5. **EEVEE headless no funciona sin GPU** — para Docker headless usar Cycles CPU o configurar GPU passthrough

---

## Contacto del proyecto

Propietario: Gabo — El Guardarropa de Ana (Argentina)
Stack general: n8n + Docker + Evolution API + PostgreSQL + Redis
