# Scripts Python para Blender

Esta carpeta contiene scripts reutilizables para ejecutar en Blender
a través de Claude Code usando la herramienta `execute_blender_code`.

## Cómo usar estos scripts desde Claude Code

```
"Ejecuta el script scripts/scene_setup.py en Blender"
```

O para combinar múltiples scripts:
```
"Configura una escena de estudio con iluminación de 3 puntos,
crea un personaje femenino de talle grande, y renderizá la escena
guardando el resultado en renders/YYYY-MM-DD/test_01.png"
```

## Scripts disponibles

| Script | Función |
|---|---|
| `scene_setup.py` | Escena de estudio base (plano, fondo infinito, cámara) |
| `lighting.py` | Setup de iluminación de estudio (3 puntos) |
| `materials.py` | Materiales de telas (algodón, denim, seda, jersey) |
| `character.py` | Personaje base con MPFB2 |
| `clothing.py` | Importar prenda + cloth simulation |
| `render.py` | Configurar y ejecutar render con Cycles |

## Convenciones

- Cada script puede correr de forma **independiente** o como parte de un pipeline
- Los objetos se nombran con prefijo: `Studio_`, `Character_`, `Cloth_`, `Light_`
- Los renders se guardan en `/renders/YYYY-MM-DD/`
- Siempre limpiar la escena al inicio si el script crea una escena nueva

## Notas técnicas

- Importar siempre `import bpy` al inicio
- Para operaciones largas (cloth bake), ejecutar en pasos separados
- Timeout del socket MCP: **180 segundos** — no exceder en una sola llamada
