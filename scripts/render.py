"""
render.py
Configurar y ejecutar renders con Cycles en Blender.

Permite:
- Cambiar entre EEVEE (rápido) y Cycles (calidad)
- Configurar resolución y samples
- Definir path de salida
- Ejecutar el render

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
  (modificar OUTPUT_PATH y RENDER_MODE según necesidad)
"""

import bpy
import os
from datetime import datetime

# ============================================================
# CONFIGURACIÓN — modificar estos valores según necesidad
# ============================================================
RENDER_MODE = "PREVIEW"  # "PREVIEW" (EEVEE rápido) o "PRODUCTION" (Cycles calidad)
OUTPUT_PATH = f"//renders/{datetime.now().strftime('%Y-%m-%d')}/render_001.png"
RESOLUTION_X = 1080
RESOLUTION_Y = 1350  # Formato vertical Instagram/catálogo
# ============================================================

def configure_render(mode="PREVIEW", output_path=None, res_x=1080, res_y=1350):
    """
    Configura el renderer de Blender.

    Args:
        mode: "PREVIEW" para EEVEE rápido, "PRODUCTION" para Cycles
        output_path: Ruta de salida del render (relativa a .blend o absoluta)
        res_x, res_y: Resolución en píxeles
    """
    scene = bpy.context.scene

    if mode == "PREVIEW":
        # EEVEE — rápido, para verificar composición
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
        print("🔵 Motor: EEVEE (preview rápido)")

    elif mode == "PRODUCTION":
        # Cycles — fotorrealista, para render final
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 256
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'

        # Usar GPU si está disponible, sino CPU
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'  # Cambiar a 'NONE' si no hay GPU
        scene.cycles.device = 'GPU'
        print("🟠 Motor: Cycles (producción)")
        print(f"   - Samples: {scene.cycles.samples}")

    # Resolución
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100

    # Formato de salida
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.compression = 15

    # Path de salida
    if output_path:
        # Crear directorio si no existe (solo para paths absolutos)
        abs_path = bpy.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        scene.render.filepath = output_path
        print(f"   - Output: {output_path}")

    print(f"   - Resolución: {res_x}x{res_y}px")

def execute_render():
    """Ejecuta el render y espera a que termine."""
    print("🎬 Iniciando render...")
    bpy.ops.render.render(write_still=True)
    print(f"✅ Render completado: {bpy.context.scene.render.filepath}")

# Ejecutar configuración y render
configure_render(
    mode=RENDER_MODE,
    output_path=OUTPUT_PATH,
    res_x=RESOLUTION_X,
    res_y=RESOLUTION_Y
)

execute_render()
