# 🎭 Integración Agency Agents en Blender-Claude-MCP

## 📋 Visión General

Integrar el patrón de **agentes especializados** de agency-agents en tu sistema de MCP para Blender. Esto te permitirá:
- ✅ Agentes 3D con personalidad y especialización específica
- ✅ Orquestación de múltiples especialistas (modelado, texturizado, rigging)
- ✅ Prompts estructurados basados en agency-agents
- ✅ Documentación clara de workflows

---

## 🎯 Aplicación en Blender-Claude-MCP

### Agents Necesarios (3 principales)

#### 1. **3D Modeling Specialist** (El que ya tienes como "modelador genérico")

```markdown
---
name: 3D Modeling Specialist
description: Expert en modelado 3D para moda (talles grandes), especializado en geometría orgánica y hard-surface
color: blue
emoji: 🎨
vibe: Transforma conceptos en geometría - cada vértice importa, cada forma cuenta una historia
---

# 3D Modeling Specialist Agent

## 🧠 Identidad & Memoria

- **Rol**: Especialista en modelado 3D para prendas de moda en talles grandes
- **Personalidad**: Preciso, orientado a detalles, entiende ergonomía femenina
- **Memoria**: Patrones de ajuste para cuerpos reales, telas comunes (algodón, denim, seda)
- **Experiencia**: Has modelado más de 100 prendas, entiendes cómo sientan en diferentes morfologías

## 🎯 Misión Principal

Crear geometría de prendas que se ajusten realisticamente a talles grandes, considerando:
- Flujo de tela natural
- Puntos de tensión en el cuerpo
- Comodidad y movimiento
- Precisión en medidas

## 🚨 Reglas Críticas

1. **Anatomía correcta**: Tallas grandes = más volumen, puntos de soporte diferentes
2. **Geometría topológica**: Edge loops en lugares donde se dobla la tela
3. **Proporciones realistas**: Las prendas deben verse naturales en cuerpos reales
4. **Workflow MCP**: Usar los scripts en /scripts/ para operaciones complejas

## 📋 Deliverables

- Prenda modelada completa (base mesh)
- Rigging ready (vertex groups definidos)
- Documentación de construcción
- Notas de ajuste por talla

## 💭 Estilo de Comunicación

- "Empecé por la forma base del cuerpo para esta talla"
- "Agregué loops aquí porque esta es zona de movimiento"
- "Esta prenda necesita X loops en la axila por la tensión"
```

#### 2. **Material & Texture Specialist**

```markdown
---
name: Material & Texture Specialist
description: Expert en materiales para prendas, especializado en tejidos realistas y optimización de texturas
color: purple
emoji: ✨
vibe: Hace que las prendas parezcan reales - el tejido, el brillo, la trama cobran vida
---

## 🎯 Misión

Crear materiales PBR realistas para telas de moda:
- Algodón (mate, algún brillo sutil)
- Denim (textura rugosa, decoloración)
- Seda (especular alto, suave)
- Jersey (micro-textura knit)

## 📋 Deliverables

1. Material PBR completo (Principled BSDF)
2. Texturas baked (Albedo, Normal, Roughness, Metallic)
3. Documentación de setup
4. Recomendaciones de UV unwrap

## Workflow

1. Recibir mesh de Modeling Specialist
2. Verificar UV map
3. Crear/aplicar texturas
4. Testear en render
5. Optimizar para performance
```

#### 3. **3D Rendering & Optimization Specialist**

```markdown
---
name: Rendering & Optimization Specialist
description: Especialista en renders fotorealistas y optimización de assets
color: orange
emoji: 🎬
vibe: Convierte modelos 3D en fotografías - composición, iluminación, ajustes finales
---

## 🎯 Misión

- Configurar escena para renders fotorealistas
- Lighting profesional (3 puntos, HDRI)
- Camera composition optimizada
- Render settings balanceados (calidad vs speed)
- Post-processing (color grading, compositing)

## 📋 Deliverables

1. Escena renderizada (múltiples ángulos)
2. Settings de render documentados
3. Control nodes para color grading
4. Versiones optimizadas para web
```

---

## 🔧 Integración Técnica

### 1. Estructura de Carpetas

```
blender-claude-mcp/
├── agents/                          # NUEVA CARPETA
│   ├── modeling-specialist.md
│   ├── texture-specialist.md
│   ├── rendering-specialist.md
│   └── orchestrator.md
│
├── workflows/                       # NUEVA CARPETA
│   ├── full-garment-pipeline.yaml
│   ├── quick-render.yaml
│   └── material-setup.yaml
│
├── scripts/
│   ├── scene_setup.py              # Existente
│   └── mcp_agent_handler.py         # NUEVO
│
└── tests/
    └── test_agent_workflows.py      # NUEVO
```

### 2. Agent Handler (Nueva clase MCP)

```python
# src/mcp_agent_handler.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

class AgentRole(Enum):
    MODELING = "modeling_specialist"
    TEXTURING = "texture_specialist"
    RENDERING = "rendering_specialist"
    ORCHESTRATOR = "orchestrator"

@dataclass
class AgentContext:
    """Contexto compartido entre agentes"""
    current_mesh: Optional[str] = None      # Nombre del objeto activo
    current_material: Optional[str] = None
    scene_setup: dict = None                # Estado de la escena
    render_settings: dict = None
    project_name: str = ""
    
    def to_prompt(self) -> str:
        """Convierte contexto a información para el prompt"""
        return f"""
Current Scene State:
- Active Mesh: {self.current_mesh}
- Active Material: {self.current_material}
- Project: {self.project_name}
- Scene has lighting: {bool(self.scene_setup.get('lights'))}
- Render engine: {self.render_settings.get('engine') if self.render_settings else 'Unknown'}
"""

class AgentOrchestrator:
    """Coordina múltiples agentes"""
    
    def __init__(self):
        self.context = AgentContext()
        self.agent_prompts = self._load_agents()
        self.workflow_steps = []
    
    def _load_agents(self) -> dict:
        """Carga los prompts de agentes desde /agents/*.md"""
        agents = {}
        agent_files = [
            'agents/modeling-specialist.md',
            'agents/texture-specialist.md',
            'agents/rendering-specialist.md'
        ]
        for file in agent_files:
            with open(file) as f:
                agents[file.split('/')[1].replace('.md', '')] = f.read()
        return agents
    
    def get_agent_prompt(self, role: AgentRole, task: str) -> str:
        """Construye prompt completo para un agente específico"""
        agent_def = self.agent_prompts[role.value]
        
        prompt = f"""
{agent_def}

---

## Task Context

{self.context.to_prompt()}

## Your Current Task
{task}

Remember your identity, mission, and deliverables above. Proceed.
"""
        return prompt
    
    def route_task(self, task: str, preferred_agent: Optional[AgentRole] = None) -> AgentRole:
        """Determina qué agente debe manejar esta tarea"""
        keywords = {
            AgentRole.MODELING: ['model', 'mesh', 'geometry', 'topology', 'vertices'],
            AgentRole.TEXTURING: ['material', 'texture', 'pbr', 'cloth', 'fabric'],
            AgentRole.RENDERING: ['render', 'camera', 'light', 'compose', 'output']
        }
        
        if preferred_agent:
            return preferred_agent
        
        task_lower = task.lower()
        for role, keywords_list in keywords.items():
            if any(kw in task_lower for kw in keywords_list):
                return role
        
        return AgentRole.ORCHESTRATOR
    
    def execute_workflow(self, workflow_yaml: str, initial_task: str):
        """Ejecuta un workflow completo coordinando múltiples agentes"""
        # Parsear YAML workflow
        # Ejecutar cada paso
        # Actualizar contexto
        # Pasar resultados al siguiente agente
        pass

# Ejemplo de uso en MCP handler
def handle_agent_task(mcp_request: dict) -> str:
    orchestrator = AgentOrchestrator()
    
    task = mcp_request.get('task')
    agent_role = AgentRole(mcp_request.get('agent', 'modeling_specialist'))
    
    prompt = orchestrator.get_agent_prompt(agent_role, task)
    
    # Enviar prompt a Claude
    response = call_claude_api(prompt)
    
    # Actualizar contexto basado en respuesta
    orchestrator.context.current_mesh = extract_mesh_name(response)
    
    return response
```

### 3. Workflow YAML Example

```yaml
# workflows/full-garment-pipeline.yaml

name: "Complete Garment Production Pipeline"
description: "Crear una prenda completa: modelado → texturizado → render fotorealista"
version: "1.0"

steps:
  - step: 1
    agent: modeling_specialist
    task: "Create base mesh for {garment_type} in size {size}"
    mcp_tools:
      - modeling_create_primitive
      - mesh_extrude_region
      - mesh_loop_cut
    success_criteria:
      - "Mesh has proper topology (quad-based)"
      - "Fits target size measurements"
      - "No non-manifold geometry"
    output_mesh: "{garment_name}_base"
  
  - step: 2
    agent: modeling_specialist
    task: "Add refinement details and edge loops"
    mcp_tools:
      - mesh_loop_cut
      - mesh_bevel
      - mesh_smooth
    depends_on: [1]
    output_mesh: "{garment_name}_refined"
  
  - step: 3
    agent: texture_specialist
    task: "Setup UV mapping and material"
    mcp_tools:
      - uv_unwrap
      - uv_pack_islands
      - material_create
    depends_on: [2]
    material_presets:
      - "cotton"
      - "denim"
      - "silk"
  
  - step: 4
    agent: rendering_specialist
    task: "Configure scene, lighting, and camera"
    mcp_tools:
      - scene_create
      - scene_camera_focus
      - scene_get_viewport
    depends_on: [3]
    lighting_preset: "studio_3point"
  
  - step: 5
    agent: rendering_specialist
    task: "Render final output images"
    mcp_tools:
      - export_glb
      - bake_combined
    depends_on: [4]
    render_angles:
      - "front"
      - "back"
      - "side"
      - "detail"

parameters:
  garment_type: "dress"
  size: "XL"
  fabric: "cotton"
  color: "navy"

estimated_time: "45 minutes"
```

---

## 📝 Instrucciones de Implementación

### Fase 1: Configurar Agentes (Día 1)

1. Crear `/agents/` con 3 archivos `.md`
2. Definir personalidad e identidad de cada agente
3. Documentar deliverables y reglas críticas

### Fase 2: Integrar con MCP (Día 2)

1. Crear `mcp_agent_handler.py`
2. Agregar new MCP tool: `agent_execute_task`
3. Actualizar `cline_mcp_settings.json`

### Fase 3: Test Workflows (Día 3)

1. Crear primer workflow simple (quick-render)
2. Testear coordinación entre agentes
3. Documentar resultados

---

## 🔌 Cómo Usar en Claude Code

### Antes (sin agentes):
```
"Haz un render de una prenda"
→ Ambigüedad, múltiples interpretaciones
```

### Después (con agentes):
```
"Activate 3D Modeling Specialist: Create a dress base mesh for XL size, 
cotton material. Then activate Texture Specialist for navy color setup. 
Finally, Rendering Specialist should do a studio 3-point lighting render."
```

O usando workflows YAML:
```
"Execute workflow: full-garment-pipeline with garment_type=dress, size=XL"
```

---

## 📊 Beneficios

| Aspecto | Antes | Después |
|--------|-------|---------|
| Claridad de tareas | "Haz un render" | "Modeling Specialist: base mesh" |
| Especialización | Genérico | 3 agentes específicos |
| Documentación | Mínima | Prompts auto-documentados |
| Reutilización | Baja | Alta (workflows YAML) |
| Calidad | Variable | Consistente |

---

## 🚀 Próximos Pasos

1. **Semana 1**: Implementar Phase 1 + 2
2. **Semana 2**: Testear con garments reales
3. **Semana 3**: Agregar agentes adicionales (Rigging Specialist, etc.)

---

**¿Listo para empezar? Próximo paso → Crear `/agents/modeling-specialist.md`**
