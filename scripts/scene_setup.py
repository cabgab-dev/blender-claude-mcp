"""
scene_setup.py
Setup de escena de estudio fotográfico base en Blender.

Crea:
- Plano de fondo infinito (cyc)
- Cámara en posición frontal estándar para moda
- Limpia la escena antes de construir

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy
import math

def setup_studio_scene():
    """Configura una escena de estudio fotográfico base."""

    # 1. Limpiar escena completamente
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # 2. Crear plano de fondo (cyclorama)
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
    background = bpy.context.active_object
    background.name = "Studio_Background"

    # 3. Crear material blanco para el fondo
    mat = bpy.data.materials.new(name="Studio_Background_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    background.data.materials.append(mat)

    # 4. Configurar cámara
    bpy.ops.object.camera_add(location=(0, -4, 1.7))
    camera = bpy.context.active_object
    camera.name = "Studio_Camera"
    camera.rotation_euler = (math.radians(88), 0, 0)

    # Configurar cámara como activa
    bpy.context.scene.camera = camera

    # Parámetros de cámara para moda (50mm equivalente)
    camera.data.lens = 50
    camera.data.clip_end = 100

    # 5. Configurar renderer
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128  # Bajo para iteración, subir a 512+ para producción
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1350  # Formato vertical (Instagram/catálogo)
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False

    print("✅ Escena de estudio configurada correctamente")
    print(f"   - Resolución: {scene.render.resolution_x}x{scene.render.resolution_y}")
    print(f"   - Engine: {scene.render.engine}")
    print(f"   - Cámara: {camera.name} en {camera.location}")

    return {
        "background": background.name,
        "camera": camera.name,
        "resolution": f"{scene.render.resolution_x}x{scene.render.resolution_y}"
    }

# Ejecutar al correr el script
result = setup_studio_scene()
print(result)
