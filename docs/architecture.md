# Arquitectura del proyecto

## Topología general

```
┌─────────────────────────────────────────────────────────┐
│  Windows Host                                           │
│                                                         │
│  ┌─────────────────┐        ┌──────────────────────┐   │
│  │  VS Code        │        │  Blender 4.2+        │   │
│  │  + Claude Code  │        │                      │   │
│  └────────┬────────┘        │  Addon BlenderMCP    │   │
│           │ stdio           │  TCP Server :9876    │   │
│  ┌────────▼────────┐        └──────────┬───────────┘   │
│  │  Docker Desktop │                   │               │
│  │                 │  host.docker.     │               │
│  │  blender-ai-mcp │◄──internal:9876───┘               │
│  │  (MCP Server)   │                                   │
│  └─────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

## Flujo de una operación

```
1. Usuario pide algo en Claude Code (VS Code)
      │
2. Claude Code llama herramienta MCP (ej: execute_blender_code)
      │
3. Petición JSON-RPC 2.0 → blender-ai-mcp container (stdio)
      │
4. Container reenvía comando JSON → Blender addon (TCP :9876)
      │
5. Addon ejecuta código Python en hilo principal de Blender
      │
6. Resultado JSON ← addon ← container ← Claude Code
      │
7. Claude Code devuelve respuesta al usuario
```

## Componentes y responsabilidades

### Claude Code (VS Code)
- Interfaz de usuario principal
- Interpreta pedidos en lenguaje natural
- Genera código Python para Blender cuando es necesario
- Lee CLAUDE.md al inicio para contexto completo del proyecto

### blender-ai-mcp (Docker)
- Servidor MCP que expone herramientas a Claude Code
- Se conecta al addon de Blender por TCP
- Sin estado propio: es solo un puente
- Se inicia automáticamente cuando Claude Code lo necesita

### Addon BlenderMCP (Blender)
- Se debe iniciar MANUALMENTE antes de trabajar
- Crea el servidor TCP en el puerto 9876
- Ejecuta código Python en el hilo principal de Blender (thread-safe con bpy)
- Compatible con Blender 3.0 - 4.x+

### Scripts Python (/scripts/)
- Biblioteca de operaciones reutilizables
- Se invocan desde Claude Code vía execute_blender_code
- Documentados con docstring y ejemplos de uso

---

## Estructura de directorios

```
blender-claude-mcp/
│
├── CLAUDE.md              ← Leído automáticamente por Claude Code
├── .mcp.json              ← Configuración MCP del proyecto (versionado)
├── .env.example           ← Template de variables de entorno
├── .env                   ← Variables reales (NO versionado)
├── .gitignore
│
├── docs/
│   ├── research.md        ← Todo lo investigado sobre blender-mcp
│   ├── architecture.md    ← Este archivo
│   ├── roadmap.md         ← Fases y tareas
│   └── decisions.md       ← Log de decisiones técnicas
│
├── scripts/
│   ├── README.md
│   ├── scene_setup.py     ← Setup de escena de estudio base
│   ├── character.py       ← Creación de personajes con MPFB2
│   ├── clothing.py        ← Importación y simulación de prendas
│   ├── materials.py       ← Materiales de textiles (Principled BSDF)
│   ├── lighting.py        ← Setups de iluminación de estudio
│   └── render.py          ← Configuración y ejecución de renders
│
├── scenes/                ← Archivos .blend (no versionados si son pesados)
│   └── studio_base.blend  ← Escena base de estudio
│
├── renders/               ← Output de renders (no versionado)
│   └── .gitkeep
│
└── assets/                ← Assets importados (no versionado)
    └── .gitkeep
```

---

## Configuración de red Docker

### Por qué host.docker.internal
Docker Desktop en Windows resuelve automáticamente `host.docker.internal` al IP del host.
El container (blender-ai-mcp) actúa como **cliente** que se conecta a Blender en el host,
no como servidor. Por eso no se necesita `-p` (publish ports).

### Firewall
Si la conexión falla, verificar que Windows Firewall permite conexiones entrantes en el
puerto 9876 desde el proceso de Blender. Normalmente Docker Desktop maneja esto, pero
en algunos entornos corporativos puede bloquearse.

### Puerto personalizado
Si el 9876 está ocupado, cambiar en el panel del addon de Blender Y en .env:
```
BLENDER_RPC_PORT=9877
```

---

## Arquitectura futura: integración n8n (Fase 4)

```
┌──────────────────────────────────────────────────────────────┐
│  Docker Compose                                              │
│                                                              │
│  ┌─────────┐     ┌──────────────────┐     ┌──────────────┐  │
│  │  n8n    │────▶│ blender-mcp-n8n  │────▶│  Blender     │  │
│  │ :5678   │     │ bridge :8008     │     │  (host)      │  │
│  └─────────┘     └──────────────────┘     │  addon :8888 │  │
│                                           └──────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

En esta fase, n8n puede disparar workflows de render automáticamente
(ej: nuevo producto en el sistema → render de ficha de catálogo).
