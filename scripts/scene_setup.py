"""
scene_setup.py
Setup de escena de estudio fotográfico base en Blender.

Crea:
- Fondo en L (piso + pared trasera — cyclorama)
- Cámara frontal estándar para moda (85mm, cuerpo completo)
- Limpia la escena antes de construir

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy
import bmesh
import math


def setup_studio_scene():
    """Configura una escena de estudio fotográfico base."""

    # 1. Limpiar escena
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # 2. Fondo en L: piso 4x4 + pared trasera 4x3
    bm = bmesh.new()

    # Piso
    v0 = bm.verts.new((-2, -2, 0))
    v1 = bm.verts.new(( 2, -2, 0))
    v2 = bm.verts.new(( 2,  2, 0))
    v3 = bm.verts.new((-2,  2, 0))
    bm.faces.new([v0, v1, v2, v3])

    # Pared trasera (sube desde y=2)
    v4 = bm.verts.new((-2, 2, 0))
    v5 = bm.verts.new(( 2, 2, 0))
    v6 = bm.verts.new(( 2, 2, 3))
    v7 = bm.verts.new((-2, 2, 3))
    bm.faces.new([v4, v5, v6, v7])

    bm.normal_update()
    mesh = bpy.data.meshes.new("BG_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    background = bpy.data.objects.new("Studio_Background", mesh)
    bpy.context.scene.collection.objects.link(background)

    mat = bpy.data.materials.new("Studio_BG_Mat")
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.95
    background.data.materials.append(mat)

    # 3. Cámara — 85mm, encuadre cuerpo completo (personaje ~1.67m centrado en origen)
    bpy.ops.object.camera_add(location=(0, -4.5, 0.83))
    camera = bpy.context.active_object
    camera.name = "Studio_Camera"
    camera.rotation_euler = (math.radians(90), 0, 0)
    camera.data.lens = 85
    camera.data.clip_end = 100
    bpy.context.scene.camera = camera

    # 4. Render settings base
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'

    print("Escena de estudio lista")
    print(f"  Camara: {camera.name} | lens: {camera.data.lens}mm")
    print(f"  Resolucion: {scene.render.resolution_x}x{scene.render.resolution_y}")
    return {"background": background.name, "camera": camera.name}


if __name__ == "__main__":
    result = setup_studio_scene()
    print(result)
