"""
character.py
Crear y configurar personaje femenino talle grande con MPFB2.

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy
import math
import sys
from mathutils import Vector


# ============================================================
# PERFILES
# ============================================================
PERFIL_TALLEGR = {
    "MPFB_HUM_GENDER":    1.0,
    "MPFB_HUM_WEIGHT":    0.85,
    "MPFB_HUM_MUSCLE":    0.3,
    "MPFB_HUM_AGE":       0.45,
    "MPFB_HUM_HEIGHT":    0.55,
    "MPFB_HUM_CUPSIZE":   0.75,
    "MPFB_HUM_CAUCASIAN": 0.5,
    "MPFB_HUM_AFRICAN":   0.3,
    "MPFB_HUM_ASIAN":     0.2,
}

PERFIL_BASE = {
    "MPFB_HUM_GENDER":    1.0,
    "MPFB_HUM_WEIGHT":    0.5,
    "MPFB_HUM_MUSCLE":    0.5,
    "MPFB_HUM_AGE":       0.5,
    "MPFB_HUM_HEIGHT":    0.5,
    "MPFB_HUM_CUPSIZE":   0.55,
    "MPFB_HUM_CAUCASIAN": 0.33,
    "MPFB_HUM_AFRICAN":   0.33,
    "MPFB_HUM_ASIAN":     0.33,
}
# ============================================================


def ensure_mpfb2():
    """Habilita MPFB2 si no está activo. Necesario en sesiones nuevas de Blender."""
    if sys.modules.get('bl_ext.blender_org.mpfb'):
        return True
    import addon_utils
    for mod in addon_utils.modules():
        if 'mpfb' in mod.__name__.lower():
            bpy.ops.preferences.addon_enable(module=mod.__name__)
            print("MPFB2 habilitado:", mod.__name__)
            return True
    print("MPFB2 no encontrado — instalar desde Extensions")
    return False


def create_character(perfil=None, name="Human"):
    """
    Crea un personaje MPFB2 con el perfil de proporciones dado.

    Args:
        perfil: dict con keys MPFB_HUM_*. Si None usa PERFIL_TALLEGR.
        name:   nombre del objeto en Blender

    Returns:
        El objeto Blender del personaje, o None si falló.
    """
    if perfil is None:
        perfil = PERFIL_TALLEGR

    ensure_mpfb2()

    result = bpy.ops.mpfb.create_human()
    if 'FINISHED' not in result:
        print("Error creando personaje:", result)
        return None

    human = bpy.context.active_object
    human.name = name

    for prop, val in perfil.items():
        if prop in human:
            human[prop] = val

    ts = sys.modules.get('bl_ext.blender_org.mpfb.services.targetservice')
    if ts:
        ts.TargetService.reapply_macro_details(human)
        print("  Shape keys aplicados")

    human.location = (0, 0, 0)
    print(f"Personaje '{name}' creado, dims: {[round(d,3) for d in human.dimensions]}")
    return human


def apply_skin(human, color=(0.82, 0.62, 0.50)):
    """
    Crea y aplica material de piel a todos los mesh del personaje.
    Omite objetos de ropa y fondo por nombre.

    Args:
        human: objeto Blender raíz del personaje
        color: RGB tuple del tono de piel
    """
    mat = bpy.data.materials.get("Skin_Base") or bpy.data.materials.new("Skin_Base")
    mat.use_nodes = True

    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.75
    bsdf.inputs["Specular IOR Level"].default_value = 0.15
    bsdf.inputs["Subsurface Weight"].default_value = 0.25
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.4, 0.2)
    bsdf.inputs["Subsurface Scale"].default_value = 0.08

    clothing_keywords = ('top', 'tshirt', 'shirt', 'skirt', 'dress', 'pants',
                         'jacket', 'coat', 'cloth')
    applied = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        if obj.name == 'Studio_Background':
            continue
        if any(k in obj.name.lower() for k in clothing_keywords):
            continue
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        applied.append(obj.name)

    print(f"Skin aplicada a: {applied}")
    return mat


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
    if rig:
        print(f"Rig: {rig.name} ({len(rig.data.bones)} huesos)")
    return rig


def apply_standing_pose(rig):
    """
    Aplica pose parada natural con brazos colgando al costado.
    Usa rotation_difference() geométrico para calcular la rotación correcta
    independientemente de los ejes locales del rig MPFB2.
    """
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.rot_clear()

    def arm_down(bone_name, side='L'):
        pb = rig.pose.bones.get(bone_name)
        if not pb:
            return
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
    human = create_character(perfil=PERFIL_TALLEGR)
    if human:
        apply_skin(human)
        rig = add_rig(human)
        if rig:
            apply_standing_pose(rig)
        print(f"Listo: {human.name}")
