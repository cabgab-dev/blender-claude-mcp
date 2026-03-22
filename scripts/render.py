"""
render.py
Configurar y ejecutar renders con Cycles en Blender.

Modos:
- PREVIEW    — Cycles 64 samples, rápido para verificar composición
- PRODUCTION — Cycles 256 samples, denoising, para render final

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
  (modificar OUTPUT_PATH y RENDER_MODE según necesidad)
"""

import bpy
import os
from datetime import datetime

# ============================================================
RENDER_MODE  = "PREVIEW"
OUTPUT_PATH  = r"C:\Users\cabga\OneDrive1\Escritorio\MI-AUTOMATIZACION\Blender\blender-claude-mcp\renders\auto\render_001.png"
RESOLUTION_X = 800
RESOLUTION_Y = 1100
# ============================================================


def configure_render(mode="PREVIEW", output_path=None, res_x=800, res_y=1100):
    """
    Configura el renderer de Blender.

    Args:
        mode:        "PREVIEW" o "PRODUCTION"
        output_path: ruta absoluta del PNG de salida
        res_x, res_y: resolución en píxeles
    """
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.compression = 15

    if mode == "PREVIEW":
        scene.cycles.samples = 64
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
        print(f"PREVIEW: Cycles 64 samples | {res_x}x{res_y}")

    elif mode == "PRODUCTION":
        scene.cycles.samples = 256
        scene.cycles.use_denoising = True

        # Detectar denoiser disponible
        try:
            scene.cycles.denoiser = 'OPTIX'
        except Exception:
            scene.cycles.denoiser = 'OPENIMAGEDENOISE'

        # GPU si está disponible
        try:
            prefs = bpy.context.preferences.addons['cycles'].preferences
            prefs.compute_device_type = 'CUDA'
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            scene.cycles.device = 'GPU'
            print("GPU habilitada (CUDA)")
        except Exception:
            scene.cycles.device = 'CPU'
            print("Usando CPU")

        print(f"PRODUCTION: Cycles 256 samples | denoiser={scene.cycles.denoiser} | {res_x}x{res_y}")

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        scene.render.filepath = output_path
        print(f"Output: {output_path}")


def execute_render():
    """Ejecuta el render y espera a que termine."""
    print("Iniciando render...")
    bpy.ops.render.render(write_still=True)
    print(f"Render completado: {bpy.context.scene.render.filepath}")


if __name__ == "__main__":
    configure_render(
        mode=RENDER_MODE,
        output_path=OUTPUT_PATH,
        res_x=RESOLUTION_X,
        res_y=RESOLUTION_Y,
    )
    execute_render()
