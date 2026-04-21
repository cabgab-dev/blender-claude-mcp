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


def add_hair_basic(human, length=0.25, color=(0.15, 0.08, 0.05)):
    """
    Agrega cabello procedural básico al personaje usando sistema de partículas.
    No requiere MPFB2 ni addons externos.

    Args:
        human:  objeto Blender del personaje (mesh o raíz del rig)
        length: largo de las hebras en metros (default 0.25 = cabello medio)
        color:  RGB del color del cabello (default castaño oscuro)

    Returns:
        ParticleSystem o None si no se encontró mesh válido
    """
    # Buscar el mesh del personaje (puede ser el objeto directo o un hijo)
    mesh_obj = None
    if human.type == 'MESH':
        mesh_obj = human
    else:
        for child in human.children_recursive:
            if child.type == 'MESH' and 'body' in child.name.lower():
                mesh_obj = child
                break
        if not mesh_obj:
            for child in human.children_recursive:
                if child.type == 'MESH':
                    mesh_obj = child
                    break

    if not mesh_obj:
        print("add_hair_basic: no se encontró mesh del personaje")
        return None

    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.particle_system_add()

    psys = mesh_obj.particle_systems[-1]
    psys.name = "Hair_Basic"

    s = psys.settings
    s.type = 'HAIR'
    s.count = 800
    s.hair_length = length
    s.render_type = 'PATH'
    s.display_step = 3
    s.render_step = 5
    s.root_radius = 0.003
    s.tip_radius = 0.0005
    s.use_strand_primitive = True
    s.child_type = 'INTERPOLATED'
    s.child_nbr = 6
    s.rendered_child_count = 12
    s.clump_factor = 0.4
    s.roughness_1 = 0.015
    s.roughness_endpoint = 0.02

    # Material de cabello
    mat = bpy.data.materials.get("Hair_Mat") or bpy.data.materials.new("Hair_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()

    hair_bsdf = nodes.new('ShaderNodeBsdfHairPrincipled')
    hair_bsdf.parametrization = 'COLOR'
    hair_bsdf.inputs["Color"].default_value = (*color, 1.0)
    hair_bsdf.inputs["Roughness"].default_value = 0.35
    hair_bsdf.inputs["Radial Roughness"].default_value = 0.45

    output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(hair_bsdf.outputs["BSDF"], output.inputs["Surface"])

    mesh_obj.data.materials.append(mat)
    s.material = len(mesh_obj.data.materials)

    print(f"Cabello añadido: {s.count} hebras, largo={length}m, color={color}")
    return psys


def pose_tres_cuartos(rig):
    """
    Gira el cuerpo 30° en Z para una pose 3/4 más dinámica.
    Rota el bone raíz (hips/pelvis/root) del rig MPFB2.

    Args:
        rig: objeto Armature de Blender
    """
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')

    root_candidates = ["root", "Root", "hips", "Hips", "pelvis",
                       "Pelvis", "master", "Master", "spine_master"]
    rotated = False
    for name in root_candidates:
        pb = rig.pose.bones.get(name)
        if pb:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler.z = math.radians(30)
            print(f"Pose 3/4: '{name}' girado 30° en Z")
            rotated = True
            break

    if not rotated:
        # Fallback: rotar el armature completo en object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        rig.rotation_euler.z = math.radians(30)
        print("Pose 3/4: rotación aplicada al armature completo (fallback)")
        return

    bpy.ops.object.mode_set(mode='OBJECT')


def pose_detalle_superior():
    """
    Reposiciona la cámara a altura de cintura para mostrar detalle
    de la parte superior de la prenda (busto, escote, hombros).

    Posición: Y=-3.5, Z=1.1  apuntando al centro del torso.
    """
    cam = bpy.data.objects.get("Camera")
    if not cam:
        # Buscar cualquier cámara en la escena
        for obj in bpy.data.objects:
            if obj.type == 'CAMERA':
                cam = obj
                break

    if not cam:
        print("pose_detalle_superior: cámara no encontrada en la escena")
        return

    cam.location = (0.0, -3.5, 1.1)

    # Apuntar al torso (Z=1.05 ≈ nivel pecho del personaje)
    import mathutils
    target = mathutils.Vector((0.0, 0.0, 1.05))
    direction = target - mathutils.Vector(cam.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()

    print(f"Cámara reposicionada a nivel cintura: loc={cam.location[:]}, apunta a torso Z=1.05")


# Ejecutar al correr el script directamente
if __name__ == "__main__":
    human = create_character(perfil=PERFIL_TALLEGR)
    if human:
        apply_skin(human)
        rig = add_rig(human)
        if rig:
            apply_standing_pose(rig)
        print(f"Listo: {human.name}")
