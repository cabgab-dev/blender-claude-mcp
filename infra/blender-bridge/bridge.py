"""
blender_bridge — HTTP → BlenderMCP socket bridge  v2.1.0
Permite que n8n (u otros servicios HTTP) controlen Blender via REST.

Cambios v2.1.0:
- SOCKET_TIMEOUT dinámico por mode (preview=120s, production=600s, ecommerce=900s)
- Fix: "Anisotropic" → "Anisotropy" para Blender 4.x/5.x (silk renderer)
- Fix: watermark reducido de 22% → 10% del ancho (más profesional)
- Fix: validación estricta del campo color (exactamente 3 floats, rango 0-1)
- Fix: detección RENDER_OK más robusta (busca en todos los campos del response)
- Migrado @app.on_event("startup") deprecado → lifespan context manager
"""

import json
import socket
import io
import base64
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional


BLENDER_HOST    = os.getenv("BLENDER_HOST",    "host.docker.internal")
BLENDER_PORT    = int(os.getenv("BLENDER_PORT",    "9876"))
RENDERS_DIR     = os.getenv("RENDERS_DIR",     "/renders")
ASSETS_DIR      = os.getenv("ASSETS_DIR",      "/assets")
# Rutas Windows del host (Blender corre en Windows, no en el contenedor)
RENDERS_DIR_WIN = os.getenv("RENDERS_DIR_WIN", "")
ASSETS_DIR_WIN  = os.getenv("ASSETS_DIR_WIN",  "")

# Timeouts por modo (segundos)
TIMEOUT_BY_MODE = {
    "preview":    int(os.getenv("SOCKET_TIMEOUT_PREVIEW",    "120")),
    "production": int(os.getenv("SOCKET_TIMEOUT_PRODUCTION", "600")),
    "ecommerce":  int(os.getenv("SOCKET_TIMEOUT_ECOMMERCE",  "900")),
}
DEFAULT_TIMEOUT = int(os.getenv("SOCKET_TIMEOUT", "120"))


# ── Startup helpers ───────────────────────────────────────────

def download_assets():
    """Descarga HDRI 4K y texturas de telas de Polyhaven si no están presentes."""
    import urllib.request
    os.makedirs(os.path.join(ASSETS_DIR, "hdri"), exist_ok=True)
    os.makedirs(os.path.join(ASSETS_DIR, "textures"), exist_ok=True)

    hdri_path = os.path.join(ASSETS_DIR, "hdri", "studio_small_08_4k.hdr")
    if not os.path.exists(hdri_path):
        try:
            url = "https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/studio_small_08_4k.hdr"
            print(f"Descargando HDRI 4K...")
            urllib.request.urlretrieve(url, hdri_path)
            print(f"HDRI 4K guardado: {hdri_path}")
        except Exception as e:
            print(f"No se pudo descargar HDRI 4K: {e}")

    FABRIC_TEXTURES = {
        "cotton": "cotton_jersey",
        "denim":  "denim_fabric",
        "silk":   "bi_stretch",
    }
    BASE_URL = "https://dl.polyhaven.org/file/ph-assets/Textures/png/1k"
    MAPS = {"col": "diff_1k.png", "nor_gl": "nor_gl_1k.png", "rough": "rough_1k.png"}

    for fabric, slug in FABRIC_TEXTURES.items():
        fabric_dir = os.path.join(ASSETS_DIR, "textures", fabric)
        os.makedirs(fabric_dir, exist_ok=True)
        for map_key, map_suffix in MAPS.items():
            dest = os.path.join(fabric_dir, f"{map_key}.png")
            if not os.path.exists(dest):
                try:
                    url = f"{BASE_URL}/{slug}/{slug}_{map_suffix}"
                    print(f"Descargando {fabric}/{map_key}...")
                    urllib.request.urlretrieve(url, dest)
                    print(f"OK: {dest}")
                except Exception as e:
                    print(f"No se pudo descargar {fabric}/{map_key}: {e}")


def ensure_placeholder_logo():
    logo_path = os.path.join(ASSETS_DIR, "egda_logo.png")
    if os.path.exists(logo_path):
        return
    os.makedirs(ASSETS_DIR, exist_ok=True)
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (260, 80), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 259, 79], fill=(30, 30, 30, 160))
        draw.text((12, 12), "EGDA", fill=(255, 255, 255, 220))
        draw.text((12, 42), "El Guardarropa de Ana", fill=(220, 220, 220, 180))
        img.save(logo_path, "PNG")
        print(f"Logo placeholder creado: {logo_path}")
    except Exception as e:
        print(f"No se pudo crear logo placeholder: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: descargar assets y asegurar logo."""
    download_assets()
    ensure_placeholder_logo()
    yield
    # Cleanup al shutdown (si necesario)


app = FastAPI(title="Blender Bridge", version="2.1.0", lifespan=lifespan)


# ── Watermark helper ──────────────────────────────────────────

def apply_watermark(image_bytes: bytes, background: str = "white") -> bytes:
    """
    Compone el render (transparente) sobre el fondo elegido y superpone el logo EGDA.
    background: "white" | "gradient"
    """
    logo_path = os.path.join(ASSETS_DIR, "egda_logo.png")
    if not os.path.exists(logo_path):
        return image_bytes
    try:
        from PIL import Image, ImageDraw
        render = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        w, h = render.size

        # Construir fondo
        if background == "gradient":
            bg = Image.new("RGBA", (w, h))
            draw = ImageDraw.Draw(bg)
            for y in range(h):
                t = y / h
                val = int(255 - t * 30)
                draw.line([(0, y), (w, y)], fill=(val, val, val, 255))
        else:
            bg = Image.new("RGBA", (w, h), (255, 255, 255, 255))

        bg.paste(render, mask=render.split()[3])
        render = bg.convert("RGBA")

        logo = Image.open(logo_path).convert("RGBA")

        # FIX v2.1: logo al 10% del ancho (era 22%, demasiado grande para ecommerce)
        target_w = max(80, int(render.width * 0.10))
        scale    = target_w / logo.width
        logo     = logo.resize(
            (target_w, int(logo.height * scale)), Image.LANCZOS
        )

        # Opacidad 40%
        r_ch, g_ch, b_ch, a_ch = logo.split()
        a_ch = a_ch.point(lambda p: int(p * 0.40))
        logo = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))

        margin = 24
        x = render.width  - logo.width  - margin
        y = render.height - logo.height - margin
        render.paste(logo, (x, y), logo)

        out = io.BytesIO()
        render.save(out, "PNG")
        return out.getvalue()
    except Exception as e:
        print(f"Watermark no aplicado: {e}")
        return image_bytes


# ── Modelos ──────────────────────────────────────────────────

class RenderRequest(BaseModel):
    garment: str = "dress"
    fabric: str = "cotton"
    color: list[float] = [0.9, 0.9, 0.9]
    output_name: str = "render_001"
    samples: int = 64
    pose: str = "standing"
    mode: str = "preview"           # "preview" | "production" | "ecommerce"
    watermark: bool = True
    background: str = "white"       # "white" | "gradient"

    @field_validator("garment")
    @classmethod
    def validate_garment(cls, v: str) -> str:
        allowed = {"dress", "tshirt", "pants"}
        if v not in allowed:
            raise ValueError(f"garment debe ser uno de {allowed}")
        return v

    @field_validator("fabric")
    @classmethod
    def validate_fabric(cls, v: str) -> str:
        allowed = {"cotton", "denim", "silk"}
        if v not in allowed:
            raise ValueError(f"fabric debe ser uno de {allowed}")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: list) -> list:
        if len(v) != 3:
            raise ValueError("color debe tener exactamente 3 valores [R, G, B]")
        for i, c in enumerate(v):
            if not (0.0 <= c <= 1.0):
                raise ValueError(f"color[{i}]={c} fuera de rango [0.0, 1.0]")
        return v

class ExecuteRequest(BaseModel):
    code: str

class CommandRequest(BaseModel):
    type: str
    params: dict = {}


# ── Socket helper ─────────────────────────────────────────────

def send_to_blender(command: dict, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Envía un comando JSON al socket de BlenderMCP y devuelve la respuesta."""
    payload = json.dumps(command).encode("utf-8")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((BLENDER_HOST, BLENDER_PORT))
            s.sendall(payload)

            chunks = []
            s.settimeout(timeout)
            while True:
                try:
                    chunk = s.recv(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    try:
                        json.loads(b"".join(chunks).decode("utf-8"))
                        break
                    except json.JSONDecodeError:
                        continue
                except socket.timeout:
                    break

            raw = b"".join(chunks)
            if not raw:
                raise ValueError("Blender no devolvió respuesta")
            return json.loads(raw.decode("utf-8"))

    except ConnectionRefusedError:
        raise HTTPException(503, "No se puede conectar a Blender. ¿Está corriendo con el addon activo?")
    except socket.timeout:
        raise HTTPException(504, f"Blender no respondió en {timeout}s. Para renders ecommerce usa mode='ecommerce' (timeout=900s).")
    except Exception as e:
        raise HTTPException(500, f"Error de comunicación: {str(e)}")


def render_ok_in_response(result: dict) -> bool:
    """
    FIX v2.1: Busca RENDER_OK en todos los campos del response de BlenderMCP,
    ya que distintas versiones del addon encapsulan el stdout de formas diferentes.
    """
    def search_recursive(obj) -> bool:
        if isinstance(obj, str):
            return "RENDER_OK:" in obj
        if isinstance(obj, dict):
            return any(search_recursive(v) for v in obj.values())
        if isinstance(obj, list):
            return any(search_recursive(item) for item in obj)
        return False
    return search_recursive(result)


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.1.0",
        "blender_host": BLENDER_HOST,
        "blender_port": BLENDER_PORT,
        "renders_dir": RENDERS_DIR,
        "assets_dir": ASSETS_DIR,
        "timeouts": TIMEOUT_BY_MODE,
    }


@app.get("/blender/ping")
def blender_ping():
    result = send_to_blender({"type": "get_scene_info"})
    return {"status": "ok", "blender_response": result}


@app.post("/execute")
def execute_code(req: ExecuteRequest):
    result = send_to_blender({"type": "execute_code", "params": {"code": req.code}})
    return result


@app.post("/render")
def render(req: RenderRequest):
    """
    Genera un render completo de una prenda sobre el personaje.
    Devuelve el PNG en base64 (con watermark si watermark=true).
    Timeout automático según mode: preview=120s, production=600s, ecommerce=900s.
    """
    # Timeout según mode
    render_timeout = TIMEOUT_BY_MODE.get(req.mode.lower(), DEFAULT_TIMEOUT)

    output_dir_win = RENDERS_DIR_WIN
    output_path_win = os.path.join(output_dir_win, f"{req.output_name}.png")
    output_path_container = os.path.join(RENDERS_DIR, f"{req.output_name}.png")

    r_val, g_val, b_val = req.color[0], req.color[1], req.color[2]

    assets_win = ASSETS_DIR_WIN
    hdri_path_win = os.path.join(assets_win, "hdri", "studio_small_08_4k.hdr")
    textures_win  = os.path.join(assets_win, "textures")
    fabric_tex_dir = os.path.join(textures_win, req.fabric)

    mode = req.mode.lower()
    if mode == "ecommerce":
        res_x, res_y, samples = 1920, 2560, 512
    elif mode == "production":
        res_x, res_y, samples = 800, 1100, 256
    else:
        res_x, res_y, samples = 800, 1100, req.samples

    # FIX v2.1: "Anisotropy" (Blender 4.x/5.x) en lugar de "Anisotropic" (Blender 3.x)
    code = f"""
import bpy, os, math, bmesh
from mathutils import Vector

os.makedirs(r"{output_dir_win}", exist_ok=True)

KEEP_TYPES = {{'CAMERA', 'LIGHT', 'LAMP'}}
for obj in list(bpy.data.objects):
    if obj.type not in KEEP_TYPES:
        bpy.data.objects.remove(obj, do_unlink=True)

mat_name = "Garment_Mat"
mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bsdf.inputs["Base Color"].default_value = ({r_val}, {g_val}, {b_val}, 1.0)

FABRIC_SETTINGS = {{
    "cotton": {{"Roughness": 0.85, "Specular IOR Level": 0.05, "Sheen Weight": 0.3}},
    "denim":  {{"Roughness": 0.92, "Specular IOR Level": 0.02, "Sheen Weight": 0.5}},
    "silk":   {{"Roughness": 0.15, "Specular IOR Level": 0.3,  "Anisotropy": 0.3}},
}}
for input_name, val in FABRIC_SETTINGS.get("{req.fabric}", FABRIC_SETTINGS["cotton"]).items():
    if input_name in bsdf.inputs:
        bsdf.inputs[input_name].default_value = val

segments = 48

def make_ring(bm, z, radio):
    ring = []
    for i in range(segments):
        a = 2 * 3.14159 * i / segments
        ring.append(bm.verts.new((math.cos(a)*radio, math.sin(a)*radio, z)))
    return ring

def connect_rings(bm, r1, r2):
    for i in range(segments):
        ni = (i+1) % segments
        bm.faces.new([r1[i], r1[ni], r2[ni], r2[i]])

garment_name = "{req.garment.capitalize()}"
mesh = bpy.data.meshes.new(garment_name + "_Mesh")
obj  = bpy.data.objects.new(garment_name, mesh)
bpy.context.collection.objects.link(obj)
bm = bmesh.new()

if "{req.garment}" == "dress":
    secs = [(0.05,0.30),(0.25,0.27),(0.55,0.22),(0.72,0.23),(0.88,0.23),(0.95,0.19)]
elif "{req.garment}" == "tshirt":
    secs = [(0.88,0.22),(0.92,0.21),(0.95,0.21),(1.00,0.22),(1.10,0.23),(1.45,0.24)]
else:
    secs = [(0.05,0.14),(0.30,0.15),(0.55,0.22),(0.75,0.24),(0.90,0.24),(0.95,0.23)]

rings = [make_ring(bm, z, r) for z,r in secs]
for i in range(len(rings)-1):
    connect_rings(bm, rings[i], rings[i+1])

bm.to_mesh(mesh); bm.free(); mesh.update()
bpy.context.view_layer.objects.active = obj
bpy.ops.object.shade_smooth()
obj.modifiers.new("Subd","SUBSURF").levels = 2

bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.cylinder_project(scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')

import os as _os
_tex_dir    = r"{fabric_tex_dir}"
_col_path   = _os.path.join(_tex_dir, "col.png")
_nor_path   = _os.path.join(_tex_dir, "nor_gl.png")
_rough_path = _os.path.join(_tex_dir, "rough.png")

if _os.path.exists(_col_path):
    nt = mat.node_tree
    nl = nt.links
    uv_n  = nt.nodes.new("ShaderNodeTexCoord")
    map_n = nt.nodes.new("ShaderNodeMapping")
    map_n.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
    nl.new(uv_n.outputs["UV"], map_n.inputs["Vector"])

    col_n = nt.nodes.new("ShaderNodeTexImage")
    col_n.image = bpy.data.images.load(_col_path, check_existing=True)
    nl.new(map_n.outputs["Vector"], col_n.inputs["Vector"])
    mix_n = nt.nodes.new("ShaderNodeMixRGB")
    mix_n.blend_type = "MULTIPLY"
    mix_n.inputs["Fac"].default_value = 0.75
    mix_n.inputs["Color2"].default_value = ({r_val}, {g_val}, {b_val}, 1.0)
    nl.new(col_n.outputs["Color"], mix_n.inputs["Color1"])
    nl.new(mix_n.outputs["Color"], bsdf.inputs["Base Color"])

    if _os.path.exists(_rough_path):
        rough_n = nt.nodes.new("ShaderNodeTexImage")
        rough_n.image = bpy.data.images.load(_rough_path, check_existing=True)
        rough_n.image.colorspace_settings.name = "Non-Color"
        nl.new(map_n.outputs["Vector"], rough_n.inputs["Vector"])
        nl.new(rough_n.outputs["Color"], bsdf.inputs["Roughness"])

    if _os.path.exists(_nor_path):
        nor_n  = nt.nodes.new("ShaderNodeTexImage")
        nor_n.image = bpy.data.images.load(_nor_path, check_existing=True)
        nor_n.image.colorspace_settings.name = "Non-Color"
        nor_map = nt.nodes.new("ShaderNodeNormalMap")
        nl.new(map_n.outputs["Vector"], nor_n.inputs["Vector"])
        nl.new(nor_n.outputs["Color"],  nor_map.inputs["Color"])
        nl.new(nor_map.outputs["Normal"], bsdf.inputs["Normal"])

obj.data.materials.append(mat)

cam_data = bpy.data.cameras.get("Camera") or bpy.data.cameras.new("Camera")
cam_obj  = bpy.data.objects.get("Camera")
if cam_obj is None:
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
cam_obj.location = (0.0, -4.5, 0.83)
cam_obj.rotation_euler = (math.radians(90), 0.0, 0.0)
cam_data.lens = 85.0
bpy.context.scene.camera = cam_obj

for o in list(bpy.data.objects):
    if o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)

def add_area(name, loc, energy, size=1.5):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.size   = size
    o = bpy.data.objects.new(name, d)
    o.location = loc
    bpy.context.collection.objects.link(o)
    return o

import mathutils
key  = add_area("KeyLight",  (-1.5, -3.0,  2.5), 150, 2.0)
fill = add_area("FillLight", ( 2.0, -2.0,  1.5),  60, 3.0)
back = add_area("BackLight", ( 0.0,  3.0,  3.0),  80, 1.5)
key.rotation_euler  = mathutils.Euler((math.radians(55), math.radians(-20), 0))
fill.rotation_euler = mathutils.Euler((math.radians(40), math.radians(30),  0))
back.rotation_euler = mathutils.Euler((math.radians(30), math.radians(170), 0))

world = bpy.data.worlds.get("StudioWorld") or bpy.data.worlds.new("StudioWorld")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes.clear()
world.node_tree.links.clear()
nt = world.node_tree

out       = nt.nodes.new("ShaderNodeOutputWorld")
lp        = nt.nodes.new("ShaderNodeLightPath")
mix_bg    = nt.nodes.new("ShaderNodeMixShader")
bg_hdri   = nt.nodes.new("ShaderNodeBackground")
bg_transp = nt.nodes.new("ShaderNodeBackground")

hdri_path = r"{hdri_path_win}"
if __import__('os').path.exists(hdri_path):
    env_tex = nt.nodes.new("ShaderNodeTexEnvironment")
    env_tex.image = __import__('bpy').data.images.load(hdri_path, check_existing=True)
    nt.links.new(env_tex.outputs["Color"], bg_hdri.inputs["Color"])
    bg_hdri.inputs["Strength"].default_value = 1.0
else:
    bg_hdri.inputs["Color"].default_value    = (0.9, 0.9, 1.0, 1.0)
    bg_hdri.inputs["Strength"].default_value = 0.8

bg_transp.inputs["Color"].default_value    = (0.0, 0.0, 0.0, 1.0)
bg_transp.inputs["Strength"].default_value = 0.0

# Is Camera Ray=1 → bg_transp (camara ve transparente, film_transparent lo resuelve)
# Is Camera Ray=0 → bg_hdri   (rayos indirectos iluminan con HDRI)
nt.links.new(lp.outputs["Is Camera Ray"], mix_bg.inputs["Fac"])
nt.links.new(bg_transp.outputs["Background"], mix_bg.inputs[1])
nt.links.new(bg_hdri.outputs["Background"],   mix_bg.inputs[2])
nt.links.new(mix_bg.outputs["Shader"], out.inputs["Surface"])

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.render.resolution_x = {res_x}
scene.render.resolution_y = {res_y}
scene.render.resolution_percentage = 100
scene.cycles.samples = {samples}
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.render.film_transparent = True
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "Standard"
scene.view_settings.exposure = 0.0
scene.render.filepath = r"{output_path_win}"
bpy.ops.render.render(write_still=True)
print("RENDER_OK:" + r"{output_path_win}")
"""

    result = send_to_blender(
        {"type": "execute_code", "params": {"code": code}},
        timeout=render_timeout
    )

    if not render_ok_in_response(result):
        # Extraer mensaje de error más informativo
        error_detail = str(result)[:400]
        raise HTTPException(500, f"Blender no confirmó el render (timeout={render_timeout}s). Respuesta: {error_detail}")

    image_base64 = None
    try:
        with open(output_path_container, "rb") as f:
            image_bytes = f.read()

        if req.watermark:
            image_bytes = apply_watermark(image_bytes, req.background)

        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    except Exception as e:
        print(f"Aviso: no se pudo procesar el PNG: {e}")

    return {
        "status": "ok",
        "version": "2.1.0",
        "output_path": output_path_win,
        "output_name": req.output_name,
        "garment": req.garment,
        "fabric": req.fabric,
        "color": req.color,
        "mode": req.mode,
        "render_timeout_used": render_timeout,
        "image_base64": image_base64,
        "image_mime_type": "image/png",
        "blender_result": result,
    }


@app.get("/scene")
def get_scene():
    return send_to_blender({"type": "get_scene_info"})


@app.get("/screenshot")
def get_screenshot():
    return send_to_blender({"type": "get_viewport_screenshot"})
