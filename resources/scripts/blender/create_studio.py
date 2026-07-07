import bpy
import math
import os
import mathutils

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(PROJECT_DIR, "models", "Studio.blend")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

DIORAMA_COLOR = (0.325, 0.325, 0.625, 1.0)  # Gris claro
WIDTH = 16.0
FLOOR_FRONT = 10.0
ARC_CENTER_Y = 0.0
ARC_CENTER_Z = 16.0
ARC_RADIUS = 16.0
ARC_SEGMENTS = 64
WALL_Y = ARC_CENTER_Y - ARC_RADIUS   # = -10.0
WALL_HEIGHT = 6.0

# ── Limpiar escena por defecto ───────────────────────────────────────────────
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(mesh)
for light in list(bpy.data.lights):
    bpy.data.lights.remove(light)
for cam in list(bpy.data.cameras):
    bpy.data.cameras.remove(cam)
for mat in list(bpy.data.materials):
    bpy.data.materials.remove(mat)

# ── Ciclorama (pared trasera curva + suelo) ──────────────────────────────────
def make_cyclorama():

    # Perfil 2D (y, z) desde frente del suelo hasta la parte alta de la pared trasera
    profile = [(FLOOR_FRONT, 0.0)]
    for i in range(ARC_SEGMENTS + 1):
        angle_rad = math.radians(270.0 - i * 90.0 / ARC_SEGMENTS)
        py = ARC_CENTER_Y + math.cos(angle_rad) * ARC_RADIUS
        pz = ARC_CENTER_Z + math.sin(angle_rad) * ARC_RADIUS
        profile.append((py, pz))
    profile.append((WALL_Y, WALL_HEIGHT))

    # Vértices: extruir perfil a lo largo del eje X
    verts = []
    for (py, pz) in profile:
        verts.append((-WIDTH / 2, py, pz))   # lado izquierdo
        verts.append(( WIDTH / 2, py, pz))   # lado derecho

    # Caras (quads con enrollado CCW para normales hacia el interior del estudio)
    faces = []
    for i in range(len(profile) - 1):
        bl = i * 2
        br = i * 2 + 1
        tr = (i + 1) * 2 + 1
        tl = (i + 1) * 2
        faces.append((bl, tl, tr, br))

    mesh = bpy.data.meshes.new("Cyclorama")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("Cyclorama", mesh)
    bpy.context.collection.objects.link(obj)
    return obj

cyclorama = make_cyclorama()

mat = bpy.data.materials.new("Cyclorama_White")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = DIORAMA_COLOR
    bsdf.inputs["Roughness"].default_value = 0.8
    for spec_name in ("Specular IOR Level", "Specular"):
        if spec_name in bsdf.inputs:
            bsdf.inputs[spec_name].default_value = 0.0
            break
cyclorama.data.materials.append(mat)

# ── Luces de área (softboxes) ────────────────────────────────────────────────
STAGE_CENTER = mathutils.Vector((0.0, -0.1, 0.74))

def add_area_light(name, location, energy, size_x, size_y):
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.energy = energy
    light_data.size = size_x
    light_data.size_y = size_y
    light_obj = bpy.data.objects.new(name, light_data)
    light_obj.location = mathutils.Vector(location)
    direction = (STAGE_CENTER - mathutils.Vector(location)).normalized()
    light_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.collection.objects.link(light_obj)
    return light_obj

add_area_light("Key_Light",  (-5.0,  6.0, 5.0), 2500, 2.0, 1.0)
add_area_light("Fill_Light", ( 5.0,  6.0, 3.0),  800, 1.5, 0.75)
add_area_light("Rim_Light",  ( 0.0, -5.0, 5.0), 1500, 1.0, 0.5)

# ── Cámara 85 mm ────────────────────────────────────────────────────────────
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 85

cam_loc = mathutils.Vector((0.0, 10.5, 1.5))
cam_obj = bpy.data.objects.new("Camera", cam_data)
cam_obj.location = cam_loc
direction = (STAGE_CENTER - cam_loc).normalized()
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

bpy.context.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# ── Configuración de render ─────────────────────────────────────────────────
scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

scene.render.engine = 'CYCLES'

try:
    prefs = bpy.context.preferences
    cprefs = prefs.addons['cycles'].preferences
    for device_type in ('OPTIX', 'CUDA'):
        try:
            cprefs.compute_device_type = device_type
            cprefs.refresh_devices()
            gpu_devs = [d for d in cprefs.devices if d.type != 'CPU']
            print(f"  Dispositivos {device_type} encontrados: {len(gpu_devs)}")
            for d in cprefs.devices:
                print(f"    {d.name}  type={d.type}  use={d.use}")
            for dev in cprefs.devices:
                dev.use = True
            print(f"GPU compute: {device_type}")
            break
        except Exception:
            continue
except Exception:
    pass

scene.cycles.device = 'GPU'

scene.cycles.samples = 128
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = 'OPTIX'
except Exception:
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'

# Fondo del mundo: negro
world = bpy.data.worlds.new("Studio_World")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bg.inputs["Strength"].default_value = 0.0
scene.world = world

# ── Guardar ─────────────────────────────────────────────────────────────────
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_PATH)
print(f"Estudio guardado → {OUTPUT_PATH}")
