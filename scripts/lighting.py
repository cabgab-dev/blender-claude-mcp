"""
lighting.py
Setup de iluminación de estudio fotográfico para moda.

Opciones:
- setup_hdri_lighting()       — HDRI de estudio (recomendado, más realista)
- setup_three_point_lighting() — 3 luces de área (fallback si no hay HDRI)
- setup_soft_lighting()        — 1 luz grande suave (editorial)

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy
import math
import os

# HDRI incluido en el proyecto
HDRI_PATH = r"C:\Users\cabga\OneDrive1\Escritorio\MI-AUTOMATIZACION\blender-pipeline\assets\hdri\studio_small_08_1k.hdr"


def setup_hdri_lighting(strength=1.5, hdri_path=None):
    """
    Iluminación via HDRI de estudio. Apaga las luces de área si existen.
    Produce el resultado más realista — usar como modo por defecto.

    Args:
        strength:  intensidad del HDRI (1.0-2.0)
        hdri_path: ruta al archivo .hdr/.exr (usa HDRI_PATH por defecto)
    """
    path = hdri_path or HDRI_PATH
    if not os.path.exists(path):
        print(f"HDRI no encontrado: {path}")
        print("Descargarlo con: curl -L 'https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/studio_small_08_1k.hdr' -o <path>")
        return False

    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    coord   = nt.nodes.new('ShaderNodeTexCoord');       coord.location   = (-800, 0)
    mapping = nt.nodes.new('ShaderNodeMapping');         mapping.location = (-600, 0)
    env     = nt.nodes.new('ShaderNodeTexEnvironment'); env.location     = (-300, 0)
    env.image = bpy.data.images.load(path)
    bg      = nt.nodes.new('ShaderNodeBackground');     bg.location      = (0, 0)
    bg.inputs['Strength'].default_value = strength
    out     = nt.nodes.new('ShaderNodeOutputWorld');    out.location     = (200, 0)

    nt.links.new(coord.outputs['Generated'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'],  env.inputs['Vector'])
    nt.links.new(env.outputs['Color'],       bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'],   out.inputs['Surface'])

    # Apagar luces de área
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT' and obj.name.startswith('Studio_'):
            obj.hide_render = True

    print(f"HDRI configurado: {os.path.basename(path)} | strength={strength}")
    return True


def create_area_light(name, location, rotation_euler, energy, size=2.0, color=(1,1,1)):
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.active_object
    light.name = name
    light.rotation_euler = rotation_euler
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    return light


def setup_three_point_lighting():
    """
    Iluminación de 3 puntos estándar.
    Fallback cuando no hay HDRI disponible.
    """
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    key = create_area_light(
        "Studio_Key_Light",
        location=(3.0, -2.0, 3.5),
        rotation_euler=(math.radians(45), 0, math.radians(45)),
        energy=800, size=1.5, color=(1.0, 0.97, 0.9)
    )
    fill = create_area_light(
        "Studio_Fill_Light",
        location=(-3.0, -1.5, 2.0),
        rotation_euler=(math.radians(30), 0, math.radians(-45)),
        energy=300, size=2.5, color=(0.9, 0.93, 1.0)
    )
    rim = create_area_light(
        "Studio_Rim_Light",
        location=(0.5, 3.0, 3.0),
        rotation_euler=(math.radians(-45), 0, math.radians(180)),
        energy=400, size=1.0, color=(1.0, 1.0, 1.0)
    )

    print(f"3-point lighting: key={key.data.energy}W fill={fill.data.energy}W rim={rim.data.energy}W")
    return {"key": key.name, "fill": fill.name, "rim": rim.name}


def setup_soft_lighting():
    """
    1 luz grande suave — estilo editorial.
    Buena para texturas delicadas.
    """
    for obj in list(bpy.data.objects):
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    main = create_area_light(
        "Studio_Main_Soft",
        location=(2.0, -2.0, 2.5),
        rotation_euler=(math.radians(45), 0, math.radians(35)),
        energy=600, size=4.0, color=(1.0, 0.98, 0.95)
    )
    fill = create_area_light(
        "Studio_Fill_Soft",
        location=(-2.5, 0, 1.5),
        rotation_euler=(math.radians(15), 0, math.radians(-90)),
        energy=150, size=5.0, color=(0.95, 0.97, 1.0)
    )

    print(f"Soft lighting: main={main.data.energy}W fill={fill.data.energy}W")
    return {"main": main.name, "fill": fill.name}


if __name__ == "__main__":
    # HDRI primero, 3-point como fallback
    if not setup_hdri_lighting():
        setup_three_point_lighting()
