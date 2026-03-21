"""
clothing.py
Crear y simular prendas sobre el personaje en Blender.

Dos modos:
  - Procedural: genera mesh básico de vestido/remera directamente
  - MPFB2: carga prenda desde librería de MPFB2 (requiere assets instalados)

La prenda usa Cloth modifier para simulación de tela.

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy
import bmesh
import math


# ============================================================
# CONFIGURACIÓN
# ============================================================
CLOTH_PRESETS = {
    "algodon": {
        "quality":          8,
        "mass":             0.35,
        "tension_stiffness": 15.0,
        "compression_stiffness": 15.0,
        "shear_stiffness":  5.0,
        "bending_stiffness": 0.5,
    },
    "denim": {
        "quality":          10,
        "mass":             0.8,
        "tension_stiffness": 40.0,
        "compression_stiffness": 40.0,
        "shear_stiffness":  20.0,
        "bending_stiffness": 5.0,
    },
    "seda": {
        "quality":          12,
        "mass":             0.15,
        "tension_stiffness": 5.0,
        "compression_stiffness": 5.0,
        "shear_stiffness":  1.0,
        "bending_stiffness": 0.05,
    },
}
# ============================================================


def create_dress(location=(0, 0, 0), largo=1.1, radio_cintura=0.28,
                 radio_falda=0.42, radio_escote=0.16, segments=32):
    """
    Crea un vestido simple procedural (forma de campana).

    Args:
        location:      posición del centro de la cintura
        largo:         largo total del vestido en metros
        radio_cintura: radio en la cintura
        radio_falda:   radio en el ruedo (más amplio)
        radio_escote:  radio en el escote
        segments:      segmentos de la malla (más = más suave)

    Returns:
        objeto Blender de la prenda
    """
    mesh = bpy.data.meshes.new("Dress_Mesh")
    obj = bpy.data.objects.new("Dress", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    # Definir secciones del vestido: (altura_relativa, radio)
    # 0.0 = ruedo, 1.0 = escote
    secciones = [
        (0.00, radio_falda),        # Ruedo
        (0.25, radio_falda * 0.9),  # 1/4 inferior
        (0.55, radio_cintura),      # Cintura
        (0.75, radio_cintura * 1.1),# Torso
        (0.90, radio_cintura * 1.2),# Busto
        (1.00, radio_escote),       # Escote
    ]

    anillos = []
    for rel_h, radio in secciones:
        altura = location[2] + rel_h * largo
        anillo = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = location[0] + radio * math.cos(angle)
            y = location[1] + radio * math.sin(angle)
            v = bm.verts.new((x, y, altura))
            anillo.append(v)
        anillos.append(anillo)

    # Conectar anillos con quads
    for r in range(len(anillos) - 1):
        for i in range(segments):
            next_i = (i + 1) % segments
            bm.faces.new([
                anillos[r][i],
                anillos[r][next_i],
                anillos[r + 1][next_i],
                anillos[r + 1][i],
            ])

    # Cerrar ruedo (anillo inferior)
    centro_ruedo = bm.verts.new((location[0], location[1], location[2]))
    for i in range(segments):
        next_i = (i + 1) % segments
        bm.faces.new([centro_ruedo, anillos[0][i], anillos[0][next_i]])

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    # Suavizar normales
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

    # Subdivisión para mejor simulación de tela
    subdiv = obj.modifiers.new("Subdivision", 'SUBSURF')
    subdiv.levels = 2
    subdiv.render_levels = 2

    print(f"Vestido creado: {obj.name}")
    return obj


def create_tshirt(location=(0, 0, 0.9), largo=0.55,
                  radio_cuerpo=0.25, segments=32):
    """
    Crea una remera/camiseta básica (tubo con abertura de brazos).

    Args:
        location:     posición del hombro
        largo:        largo desde hombro hasta borde inferior
        radio_cuerpo: radio del cuerpo
        segments:     segmentos de la malla

    Returns:
        objeto Blender de la prenda
    """
    mesh = bpy.data.meshes.new("TShirt_Mesh")
    obj = bpy.data.objects.new("TShirt", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    secciones = [
        (0.00, radio_cuerpo * 1.05),  # Ruedo
        (0.40, radio_cuerpo * 1.0),   # Abdomen
        (0.70, radio_cuerpo * 0.95),  # Cintura
        (0.85, radio_cuerpo * 1.05),  # Torso
        (1.00, radio_cuerpo * 1.1),   # Hombros
    ]

    base_z = location[2] - largo
    anillos = []
    for rel_h, radio in secciones:
        altura = base_z + rel_h * largo
        anillo = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = location[0] + radio * math.cos(angle)
            y = location[1] + radio * math.sin(angle)
            v = bm.verts.new((x, y, altura))
            anillo.append(v)
        anillos.append(anillo)

    for r in range(len(anillos) - 1):
        for i in range(segments):
            next_i = (i + 1) % segments
            bm.faces.new([
                anillos[r][i],
                anillos[r][next_i],
                anillos[r + 1][next_i],
                anillos[r + 1][i],
            ])

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

    subdiv = obj.modifiers.new("Subdivision", 'SUBSURF')
    subdiv.levels = 2

    print(f"Remera creada: {obj.name}")
    return obj


def add_cloth_modifier(garment_obj, preset="algodon", collision_obj=None):
    """
    Agrega simulación de tela a la prenda.

    Args:
        garment_obj:   objeto de la prenda
        preset:        "algodon", "denim" o "seda"
        collision_obj: objeto con el que colisiona (el personaje)
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

    # Habilitar colisión con el personaje
    if collision_obj:
        if not collision_obj.modifiers.get("Collision"):
            collision_obj.modifiers.new("Collision", 'COLLISION')
        print(f"Colisión habilitada: {garment_obj.name} ↔ {collision_obj.name}")

    print(f"Cloth modifier '{preset}' aplicado a {garment_obj.name}")
    return cloth


def apply_material_to_garment(garment_obj, material):
    """Aplica un material a la prenda."""
    if garment_obj.data.materials:
        garment_obj.data.materials[0] = material
    else:
        garment_obj.data.materials.append(material)
    print(f"Material '{material.name}' → '{garment_obj.name}'")


def bake_cloth(frames=30):
    """
    Bake de la simulación de tela (frames limitados para no exceder timeout).

    Args:
        frames: cuántos frames simular (30 = resultado rápido, 80 = más natural)
    """
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = frames
    scene.frame_set(1)

    # Avanzar frame a frame para simular
    for f in range(1, frames + 1):
        scene.frame_set(f)

    print(f"Simulación completada ({frames} frames)")


# ============================================================
# Pipeline completo: vestido en escena de estudio
# ============================================================
if __name__ == "__main__":
    # Buscar personaje en escena
    character = next(
        (o for o in bpy.context.scene.objects
         if o.type == 'MESH' and o.name not in ('Studio_Background',)),
        None
    )

    # Crear vestido posicionado sobre el personaje
    dress = create_dress(
        location=(0, 0, 0),
        largo=1.05,
        radio_cintura=0.30,
        radio_falda=0.45,
        radio_escote=0.18,
    )

    # Cloth modifier
    add_cloth_modifier(dress, preset="algodon", collision_obj=character)

    # Material (algodón blanco)
    mat = bpy.data.materials.get("Cotton_E5E5E5")
    if mat:
        apply_material_to_garment(dress, mat)

    print("clothing.py ejecutado — listo para bake")
