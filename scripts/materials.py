"""
materials.py
Materiales de telas y piel para renders de moda en Blender.

Incluye:
- Piel (skin) — base para personajes
- Algodón — opaco, rugosidad media
- Denim — azul, rugosidad alta, subsurface leve
- Seda — brillosa, anisotropía, baja rugosidad

Uso desde Claude Code:
  execute_blender_code con el contenido de este script
"""

import bpy


def _get_or_create_material(name):
    """Obtiene material existente o crea uno nuevo con nodos."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    return mat


def _get_bsdf(mat):
    """Devuelve el nodo Principled BSDF del material."""
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def create_skin_material():
    """
    Material de piel realista para personajes.
    Usa subsurface scattering para simular translucidez de la piel.
    """
    mat = _get_or_create_material("Skin_Base")
    bsdf = _get_bsdf(mat)

    bsdf.inputs["Base Color"].default_value = (0.78, 0.55, 0.42, 1.0)   # Tono piel medio
    bsdf.inputs["Roughness"].default_value = 0.6
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    # Subsurface para translucidez de piel
    bsdf.inputs["Subsurface Weight"].default_value = 0.15
    bsdf.inputs["Subsurface Radius"].default_value = (0.8, 0.3, 0.15)
    bsdf.inputs["Subsurface Scale"].default_value = 0.05

    return mat


def create_cotton_material(color=(0.8, 0.8, 0.8)):
    """
    Material de algodón — opaco, rugosidad media.
    Args:
        color: RGB tuple del color de la prenda
    """
    mat = _get_or_create_material(f"Cotton_{int(color[0]*255):02X}{int(color[1]*255):02X}{int(color[2]*255):02X}")
    bsdf = _get_bsdf(mat)

    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.85        # Algodón es muy rugoso
    bsdf.inputs["Specular IOR Level"].default_value = 0.05
    bsdf.inputs["Sheen Weight"].default_value = 0.3      # Pelusa característica del algodón
    bsdf.inputs["Sheen Roughness"].default_value = 0.5

    return mat


def create_denim_material(color=(0.08, 0.15, 0.35)):
    """
    Material de denim/jean — azul oscuro, rugosidad alta.
    Args:
        color: RGB tuple (por defecto azul jean clásico)
    """
    mat = _get_or_create_material("Denim_Blue")
    bsdf = _get_bsdf(mat)

    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.92
    bsdf.inputs["Specular IOR Level"].default_value = 0.02
    bsdf.inputs["Sheen Weight"].default_value = 0.5      # Textura de tela visible
    bsdf.inputs["Sheen Roughness"].default_value = 0.8

    return mat


def create_silk_material(color=(0.9, 0.85, 0.75)):
    """
    Material de seda — brillosa, anisotropía característica.
    Args:
        color: RGB tuple del color
    """
    mat = _get_or_create_material(f"Silk_{int(color[0]*255):02X}{int(color[1]*255):02X}{int(color[2]*255):02X}")
    bsdf = _get_bsdf(mat)

    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.08        # Seda es muy lisa
    bsdf.inputs["Specular IOR Level"].default_value = 0.8
    bsdf.inputs["Anisotropic"].default_value = 0.6       # Brillo anisotrópico de la seda
    bsdf.inputs["Anisotropic Rotation"].default_value = 0.0
    bsdf.inputs["Sheen Weight"].default_value = 0.1

    return mat


def apply_material(obj_name, material):
    """Aplica un material a un objeto por nombre."""
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        print(f"Objeto '{obj_name}' no encontrado")
        return False
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)
    print(f"Material '{material.name}' aplicado a '{obj_name}'")
    return True


# Crear todos los materiales
if __name__ == "__main__":
    skin = create_skin_material()
    cotton_white = create_cotton_material(color=(0.9, 0.9, 0.9))
    cotton_black = create_cotton_material(color=(0.05, 0.05, 0.05))
    denim = create_denim_material()
    silk_cream = create_silk_material()

    print("Materiales creados:")
    for mat in [skin, cotton_white, cotton_black, denim, silk_cream]:
        print(f"  - {mat.name}")
