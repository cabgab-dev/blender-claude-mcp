"""
character.py
Crear y configurar personaje femenino talle grande con MPFB2.

Crea un personaje base y ajusta proporciones para representar
diversidad corporal (talle grande), objetivo central del proyecto
El Guardarropa de Ana.

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy
import math
from mathutils import Vector


# ============================================================
# PERFILES — modificar para distintas proporciones
# ============================================================
PERFIL_TALLEGR = {
    "gender":    1.0,   # 0=masculino, 1=femenino
    "weight":    0.85,  # 0=delgado, 1=robusto
    "muscle":    0.3,   # 0=sin tono, 1=muy musculoso
    "age":       0.45,  # 0=joven, 1=mayor
    "height":    0.55,  # 0=bajo, 1=alto
    "cupsize":   0.75,  # 0=pequeño, 1=grande
    "caucasian": 0.5,
    "african":   0.3,
    "asian":     0.2,
}

PERFIL_BASE = {
    "gender":    1.0,
    "weight":    0.5,
    "muscle":    0.5,
    "age":       0.5,
    "height":    0.5,
    "cupsize":   0.55,
    "caucasian": 0.33,
    "african":   0.33,
    "asian":     0.33,
}
# ============================================================


def create_character(perfil=None, name="Character"):
    """
    Crea un personaje MPFB2 con el perfil de proporciones dado.

    Args:
        perfil: dict con keys gender, weight, muscle, age, height, cupsize,
                caucasian, african, asian. Si None usa PERFIL_TALLEGR.
        name: nombre del objeto en Blender

    Returns:
        El objeto Blender del personaje, o None si falló.
    """
    if perfil is None:
        perfil = PERFIL_TALLEGR

    # Crear humano base
    result = bpy.ops.mpfb.create_human()
    if 'FINISHED' not in result:
        print(f"Error creando personaje: {result}")
        return None

    # El objeto recién creado es el activo
    human = bpy.context.active_object
    human.name = name

    # Aplicar proporciones
    _apply_perfil(human, perfil)

    # Refit para aplicar los cambios al mesh
    bpy.ops.mpfb.refit_human()

    # Posicionar en origen
    human.location = (0, 0, 0)

    print(f"Personaje '{name}' creado")
    print(f"  Dimensiones: {human.dimensions}")
    return human


def _apply_perfil(human, perfil):
    """Aplica un dict de proporciones al objeto Human."""
    mapping = {
        "gender":    "MPFB_HUM_gender",
        "weight":    "MPFB_HUM_weight",
        "muscle":    "MPFB_HUM_muscle",
        "age":       "MPFB_HUM_age",
        "height":    "MPFB_HUM_height",
        "cupsize":   "MPFB_HUM_cupsize",
        "caucasian": "MPFB_HUM_caucasian",
        "african":   "MPFB_HUM_african",
        "asian":     "MPFB_HUM_asian",
    }
    for key, prop in mapping.items():
        if key in perfil:
            setattr(human, prop, perfil[key])


def apply_skin(human, color=(0.78, 0.55, 0.42)):
    """
    Crea y aplica material de piel al personaje.

    Args:
        human: objeto Blender del personaje
        color: RGB tuple del tono de piel
    """
    mat_name = "Skin_Base"
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    mat.use_nodes = True

    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    bsdf.inputs["Subsurface Weight"].default_value = 0.15
    bsdf.inputs["Subsurface Radius"].default_value = (0.8, 0.3, 0.15)
    bsdf.inputs["Subsurface Scale"].default_value = 0.05

    if human.data.materials:
        human.data.materials[0] = mat
    else:
        human.data.materials.append(mat)

    print(f"Skin '{mat_name}' aplicada a '{human.name}'")
    return mat


def setup_character_in_studio(perfil=None, skin_color=(0.78, 0.55, 0.42)):
    """
    Pipeline completo: crear personaje + skin en escena de estudio existente.
    Asume que ya se corrió scene_setup.py y lighting.py.

    Returns:
        objeto del personaje
    """
    # Eliminar personaje anterior si existe
    for obj in list(bpy.data.objects):
        if obj.type == 'MESH' and obj.name not in ('Studio_Background',):
            bpy.data.objects.remove(obj, do_unlink=True)

    human = create_character(perfil=perfil)
    if human:
        apply_skin(human, color=skin_color)

    return human


def add_rig(human):
    """Agrega rig estándar de MPFB2 al personaje."""
    bpy.context.view_layer.objects.active = human
    bpy.ops.object.select_all(action='DESELECT')
    human.select_set(True)
    result = bpy.ops.mpfb.add_standard_rig()
    if 'FINISHED' not in result:
        print("Error agregando rig:", result)
        return None
    rig = next((o for o in bpy.context.scene.objects if o.type == 'ARMATURE'), None)
    print(f"Rig agregado: {rig.name} ({len(rig.data.bones)} huesos)")
    return rig


def apply_standing_pose(rig):
    """
    Aplica pose parada natural con brazos colgando al costado.
    Calculada geométricamente a partir de los ejes locales del rig MPFB2.
    """
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()

    def arm_down(bone_name, side='L'):
        pb = rig.pose.bones[bone_name]
        mat_world = rig.matrix_world @ pb.bone.matrix_local
        current_dir = mat_world.col[1].xyz.normalized()
        sign = 1 if side == 'L' else -1
        target_dir = Vector((sign * 0.14, 0, -0.99)).normalized()
        rot = current_dir.rotation_difference(target_dir)
        bone_mat_inv = (rig.matrix_world @ pb.bone.matrix_local).inverted()
        rot_local = bone_mat_inv.to_3x3() @ rot.to_matrix() @ mat_world.to_3x3()
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = rot_local.to_quaternion()

    def rot_euler(name, x=0, y=0, z=0):
        pb = rig.pose.bones.get(name)
        if pb:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))

    arm_down("upperarm01.L", 'L')
    arm_down("upperarm01.R", 'R')
    rot_euler("lowerarm01.L", x=10)
    rot_euler("lowerarm01.R", x=10)
    rot_euler("spine01", x=2)
    rot_euler("spine02", x=2)

    bpy.ops.object.mode_set(mode='OBJECT')
    print("Pose parada aplicada")


# Ejecutar al correr el script directamente
if __name__ == "__main__":
    personaje = setup_character_in_studio(perfil=PERFIL_TALLEGR)
    if personaje:
        rig = add_rig(personaje)
        if rig:
            apply_standing_pose(rig)
        print(f"Listo: {personaje.name} en escena")
