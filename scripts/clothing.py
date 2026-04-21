"""
clothing.py
Crear prendas procedurales sobre el personaje en Blender.

Prendas disponibles:
- create_top()    — top sin mangas (ajustado al torso real del personaje)
- create_skirt()  — falda acampanada
- create_dress()  — vestido completo (combinación de top + falda)

Las dimensiones están calibradas para el personaje MPFB2 con PERFIL_TALLEGR:
  Human bounds: X [-0.497, 0.497] | Y [-0.326, 0.110] | Z [-0.027, 1.667]
  Centro Y torso: -0.11 | Radios torso: X ~0.26-0.31, Y ~0.22-0.28

Cloth simulation (add_cloth_modifier + bake_cloth) está disponible pero
puede exceder el timeout de 180s del socket MCP. Usar con precaución.

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy
import bmesh
import math


# ============================================================
# PRESETS DE SIMULACIÓN
# ============================================================
CLOTH_PRESETS = {
    "algodon": {
        "quality": 8, "mass": 0.35,
        "tension_stiffness": 15.0, "compression_stiffness": 15.0,
        "shear_stiffness": 5.0, "bending_stiffness": 0.5,
    },
    "denim": {
        "quality": 10, "mass": 0.8,
        "tension_stiffness": 40.0, "compression_stiffness": 40.0,
        "shear_stiffness": 20.0, "bending_stiffness": 5.0,
    },
    "seda": {
        "quality": 12, "mass": 0.15,
        "tension_stiffness": 5.0, "compression_stiffness": 5.0,
        "shear_stiffness": 1.0, "bending_stiffness": 0.05,
    },
}

# Centro Y del torso del personaje MPFB2 talle grande
TORSO_CY = -0.11
# ============================================================


def _build_tube(sections, segs=20):
    """
    Construye un tubo con quads a partir de secciones (cx, cy, cz, rx, ry).
    Devuelve (mesh, bmesh_obj).
    """
    bm = bmesh.new()

    def ring(cx, cy, cz, rx, ry):
        return [bm.verts.new((cx + rx * math.cos(2 * math.pi * i / segs),
                              cy + ry * math.sin(2 * math.pi * i / segs), cz))
                for i in range(segs)]

    rings = [ring(*s) for s in sections]
    for i in range(len(rings) - 1):
        n = len(rings[i])
        for j in range(n):
            bm.faces.new([rings[i][j], rings[i][(j+1) % n],
                          rings[i+1][(j+1) % n], rings[i+1][j]])

    bm.normal_update()
    return bm


def create_top(color=(0.15, 0.25, 0.55), name="Top"):
    """
    Top sin mangas ajustado al torso del personaje talle grande.

    Secciones calibradas para no salirse de los brazos en T-pose:
    radios < 0.32 en X para quedarse en el torso.

    Args:
        color: RGB del material
        name:  nombre del objeto

    Returns:
        objeto Blender
    """
    cy = TORSO_CY
    sections = [
        (0, cy, 1.28, 0.22, 0.20),  # escote
        (0, cy, 1.10, 0.26, 0.23),
        (0, cy, 0.92, 0.29, 0.25),
        (0, cy, 0.75, 0.30, 0.26),
        (0, cy, 0.58, 0.29, 0.25),  # ruedo
    ]

    bm = _build_tube(sections, segs=20)
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.88
    bsdf.inputs["Specular IOR Level"].default_value = 0.05
    bsdf.inputs["Sheen Weight"].default_value = 0.3
    obj.data.materials.append(mat)

    print(f"{name} creado: dims={[round(d,3) for d in obj.dimensions]}")
    return obj


def create_skirt(color=(0.93, 0.92, 0.90), name="Skirt"):
    """
    Falda acampanada que empieza donde termina el top.

    Args:
        color: RGB del material
        name:  nombre del objeto

    Returns:
        objeto Blender
    """
    cy = TORSO_CY
    sections = [
        (0, cy, 0.58, 0.29, 0.25),  # cintura (coincide con ruedo del top)
        (0, cy, 0.42, 0.32, 0.28),
        (0, cy, 0.20, 0.35, 0.30),
        (0, cy, 0.02, 0.36, 0.31),  # ruedo
    ]

    bm = _build_tube(sections, segs=20)
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Sheen Weight"].default_value = 0.25
    obj.data.materials.append(mat)

    print(f"{name} creado: dims={[round(d,3) for d in obj.dimensions]}")
    return obj


def create_dress(color_top=(0.15, 0.25, 0.55), color_skirt=(0.15, 0.25, 0.55), name="Dress"):
    """
    Vestido completo: top + falda en una sola prenda, mismo color.

    Args:
        color_top:   RGB parte superior
        color_skirt: RGB parte inferior (por defecto igual al top)
        name:        nombre base del objeto

    Returns:
        objeto Blender
    """
    cy = TORSO_CY
    sections = [
        (0, cy, 1.28, 0.22, 0.20),  # escote
        (0, cy, 1.10, 0.26, 0.23),
        (0, cy, 0.92, 0.29, 0.25),
        (0, cy, 0.75, 0.30, 0.26),
        (0, cy, 0.58, 0.29, 0.25),  # cintura
        (0, cy, 0.42, 0.32, 0.28),
        (0, cy, 0.20, 0.35, 0.30),
        (0, cy, 0.02, 0.36, 0.31),  # ruedo
    ]

    bm = _build_tube(sections, segs=20)
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (*color_top, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.87
    bsdf.inputs["Sheen Weight"].default_value = 0.25
    obj.data.materials.append(mat)

    print(f"{name} creado: dims={[round(d,3) for d in obj.dimensions]}")
    return obj


def add_cloth_modifier(garment_obj, preset="algodon", collision_obj=None):
    """
    Agrega simulación de tela a la prenda.
    ADVERTENCIA: bake_cloth() puede exceder el timeout de 180s del socket MCP.

    Args:
        garment_obj:   objeto de la prenda
        preset:        "algodon", "denim" o "seda"
        collision_obj: objeto del personaje para colisión
    """
    cfg = CLOTH_PRESETS.get(preset, CLOTH_PRESETS["algodon"])

    bpy.context.view_layer.objects.active = garment_obj
    cloth = garment_obj.modifiers.new("Cloth", 'CLOTH')
    s = cloth.settings
    s.quality               = cfg["quality"]
    s.mass                  = cfg["mass"]
    s.tension_stiffness     = cfg["tension_stiffness"]
    s.compression_stiffness = cfg["compression_stiffness"]
    s.shear_stiffness       = cfg["shear_stiffness"]
    s.bending_stiffness     = cfg["bending_stiffness"]
    cloth.collision_settings.use_collision = True
    cloth.collision_settings.distance_min = 0.003

    if collision_obj and not collision_obj.modifiers.get("Collision"):
        bpy.context.view_layer.objects.active = collision_obj
        col_mod = collision_obj.modifiers.new("Collision", 'COLLISION')
        col_mod.settings.thickness_outer = 0.004
        bpy.context.view_layer.objects.active = garment_obj
        print(f"Collision en: {collision_obj.name}")

    print(f"Cloth '{preset}' en {garment_obj.name}")
    return cloth


def bake_cloth(frames=25):
    """
    Simula la tela avanzando frame a frame.
    ADVERTENCIA: puede timeout en el socket MCP con geometría alta.
    Usar con prenda de <= 3000 verts.
    Para geometría mayor usar bake_cloth_part1() + bake_cloth_part2().

    Args:
        frames: frames a simular (25 = resultado rápido suficiente)
    """
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = frames
    bpy.ops.ptcache.free_bake_all()

    for f in range(1, frames + 1):
        scene.frame_set(f)

    bpy.context.view_layer.update()
    print(f"Cloth simulado: {frames} frames")


def bake_cloth_part1(frames_end=15):
    """
    Primera mitad del bake de cloth (llamada 1 al bridge).
    Configura el rango de frames, limpia caché y simula frames 1..frames_end.

    Usar junto con bake_cloth_part2() para evitar el timeout de 120s:
      - Llamada bridge 1: bake_cloth_part1(15)
      - Llamada bridge 2: bake_cloth_part2(garment_obj, 16, 30)

    Args:
        frames_end: último frame de esta mitad (default 15)
    """
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 30  # rango total; la segunda llamada completará
    bpy.ops.ptcache.free_bake_all()

    for f in range(1, frames_end + 1):
        scene.frame_set(f)

    bpy.context.view_layer.update()
    print(f"Cloth parte 1 simulada: frames 1-{frames_end}")


def bake_cloth_part2(garment_obj, frames_start=16, frames_end=30):
    """
    Segunda mitad del bake de cloth (llamada 2 al bridge).
    Continúa la simulación y aplica el modifier para congelar la pose.

    Args:
        garment_obj:  objeto de la prenda con modifier Cloth activo
        frames_start: primer frame de esta mitad (default 16)
        frames_end:   último frame (default 30)
    """
    scene = bpy.context.scene

    for f in range(frames_start, frames_end + 1):
        scene.frame_set(f)

    bpy.context.view_layer.update()
    print(f"Cloth parte 2 simulada: frames {frames_start}-{frames_end}")

    # Aplicar modifier para congelar la geometría en el frame actual
    bpy.context.view_layer.objects.active = garment_obj
    garment_obj.select_set(True)
    try:
        bpy.ops.object.modifier_apply(modifier="Cloth")
        print("Modifier Cloth aplicado — geometría congelada")
    except Exception as e:
        print(f"No se pudo aplicar Cloth modifier: {e}")


if __name__ == "__main__":
    top   = create_top(color=(0.15, 0.25, 0.55))
    skirt = create_skirt(color=(0.93, 0.92, 0.90))
    print("Ropa creada:", top.name, skirt.name)
