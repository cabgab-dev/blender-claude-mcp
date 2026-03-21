"""
lighting.py
Setup de iluminación de estudio fotográfico para moda.

Crea iluminación de 3 puntos estándar:
- Key light (luz principal, lateral)
- Fill light (luz de relleno, suave)
- Rim light (luz de contorno, posterior)
+ HDRI de estudio desde PolyHaven (opcional)

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy
import math

def create_area_light(name, location, rotation_euler, energy, size=2.0, color=(1,1,1)):
    """Crea una luz de área con los parámetros dados."""
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
    Setup de iluminación de 3 puntos para moda.
    Elimina luces existentes antes de crear las nuevas.
    """

    # Eliminar luces existentes
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    lights = {}

    # KEY LIGHT — luz principal lateral derecha
    # Posición: derecha del sujeto, 45° arriba, 45° lateral
    key = create_area_light(
        name="Studio_Key_Light",
        location=(3.0, -2.0, 3.5),
        rotation_euler=(math.radians(45), 0, math.radians(45)),
        energy=800,
        size=1.5,
        color=(1.0, 0.97, 0.9)  # Blanco cálido
    )
    lights["key"] = key.name

    # FILL LIGHT — relleno lateral izquierdo, más suave
    fill = create_area_light(
        name="Studio_Fill_Light",
        location=(-3.0, -1.5, 2.0),
        rotation_euler=(math.radians(30), 0, math.radians(-45)),
        energy=300,
        size=2.5,
        color=(0.9, 0.93, 1.0)  # Blanco frío suave
    )
    lights["fill"] = fill.name

    # RIM LIGHT — contorno posterior, separar sujeto del fondo
    rim = create_area_light(
        name="Studio_Rim_Light",
        location=(0.5, 3.0, 3.0),
        rotation_euler=(math.radians(-45), 0, math.radians(180)),
        energy=400,
        size=1.0,
        color=(1.0, 1.0, 1.0)
    )
    lights["rim"] = rim.name

    print("✅ Iluminación de 3 puntos configurada")
    print(f"   - Key: {key.name} | {key.data.energy}W")
    print(f"   - Fill: {fill.name} | {fill.data.energy}W")
    print(f"   - Rim: {rim.name} | {rim.data.energy}W")

    return lights

def setup_soft_lighting():
    """
    Setup de iluminación suave (estilo editorial).
    Una sola luz grande + relleno ambiental.
    Ideal para prendas con texturas delicadas.
    """

    # Eliminar luces existentes
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    # Luz principal grande y suave (simula ventana grande)
    main = create_area_light(
        name="Studio_Main_Soft",
        location=(2.0, -2.0, 2.5),
        rotation_euler=(math.radians(45), 0, math.radians(35)),
        energy=600,
        size=4.0,
        color=(1.0, 0.98, 0.95)
    )

    # Relleno ambiental (simula rebote en pared blanca)
    fill = create_area_light(
        name="Studio_Fill_Soft",
        location=(-2.5, 0, 1.5),
        rotation_euler=(math.radians(15), 0, math.radians(-90)),
        energy=150,
        size=5.0,
        color=(0.95, 0.97, 1.0)
    )

    print("✅ Iluminación suave configurada")

    return {"main": main.name, "fill": fill.name}

# Por defecto usar 3 puntos
result = setup_three_point_lighting()
print(result)
