import math
import os
import sys

import bpy
import mathutils

# Ejecutar con:
#   ./scripts/render_shots.sh fast           # 1280×720,  128 samples, CUDA
#   ./scripts/render_shots.sh insane         # 7680×4320, 2048 samples, CUDA
#   ./scripts/render_shots.sh fast OPTIX     # ídem con OptiX
#   ./scripts/render_shots.sh                # insane + CUDA (por defecto)
#
# O directamente:
#   blender --background models/Escena.blend \
#           --python scripts/render_shots.py -- fast --cycles-device CUDA
#
# NOTA: -- (doble guión) es obligatorio antes de los argumentos del script.

# ═══════════════════ SETTINGS ════════════════════════════════════════════════
def _preset_from_argv():
    try:
        idx = sys.argv.index('--') + 1
        user_args = sys.argv[idx:]
    except ValueError:
        user_args = []
    for arg in user_args:
        if arg in ('fast', 'insane'):
            return arg
    return 'insane'

PRESET = _preset_from_argv()

PRESETS = {
    'fast':   {'res_x': 1280, 'res_y':  720, 'samples':  128},
    'insane': {'res_x': 7680, 'res_y': 4320, 'samples': 2048},
}

CAR_OBJECT   = "CAR_ROOT"
RESOLUTION_X = PRESETS[PRESET]['res_x']
RESOLUTION_Y = PRESETS[PRESET]['res_y']
SAMPLES      = PRESETS[PRESET]['samples']

# Tomas: (nombre_fichero, rotación_Z_en_grados)
# Convención: 0° = frontal del coche hacia la cámara
#             +90° = lado DERECHO del coche (piloto) hacia la cámara
#             -90° = lado IZQUIERDO del coche (piloto) hacia la cámara
SHOTS = [
    ("car_000_front.png",       0),
    ("car_036_front_right.png", 36),
    ("car_072_right_front.png", 72),
    ("car_108_right_rear.png",  108),
    ("car_144_rear_right.png",  144),
    ("car_180_rear.png",        180),
    ("car_216_rear_left.png",   216),
    ("car_252_left_rear.png",   252),
    ("car_288_left_front.png",  288),
    ("car_324_front_left.png",  324),
]

STAGE_CENTER   = (0.0, -0.1, 0.74)   # centro geométrico del coche
CAM_PICADO_LOC = (0.0, 12.75, 5.25)     # picado: más Y = más de frente, más Z = más cenital
CAM_PICADO_ROT = (-1.0, 0.0, 0.0)        # offset de rotación adicional en grados (X, Y, Z)
SHOTS_PICADO = [
    ("car_picado_front.png",  0),
    ("car_picado_rear.png", 180),
]

# SHOTS_DETALLE: (nombre, rot_Z_coche, (loc_x,loc_y,loc_z), (rot_x,rot_y,rot_z), dof, diorama_rot)
# Guía loc:
#   X positivo → lado derecho del coche; X negativo → lado izquierdo
#   Y → desliza a lo largo del coche (+Y = hacia el frontal, -Y = trasero)
#   Z → altura de la cámara (0.35–0.5 ≈ ras de suelo)
#   La rotación base es siempre perpendicular al lateral — Y y Z solo deslizan
# Guía rot: offset adicional sobre la perpendicular, en grados (X, Y, Z)
# dof: None = sin DoF  |  (focus_distance_metros, f_stop) = DoF activado
#      focus_distance: distancia cámara→punto de foco (ajustar hasta que la llanta quede nítida)
#      f_stop: apertura — menor valor = más desenfoque (1.4 = mucho bokeh, 2.8 = moderado)
# diorama_rot: None = sin cambio  |  grados = rotación Z absoluta del Cyclorama para esta toma
#              -90 = pared trasera → X=-10 (visible desde cámara en +X mirando -X)
#              +90 = pared trasera → X=+10 (visible desde cámara en -X mirando +X)
#              180 = pared trasera → Y=+10 (visible desde detrás del coche mirando +Y)
SHOTS_DETALLE = [
    ("car_detail_front_right.png",    0, ( 5.25, 1.125, 0.5), (0.0, 0.0,   0.0), None,        -90.0),
    ("car_detail_front_left.png",     0, (-5.25, 1.125, 0.5), (0.0, 0.0,   0.0), None,         90.0),
    ("car_detail_kanji_focused.png",  0, ( 1.3125, -1.5, 0.5), (-4.125, 0.0, -83.0), None,    180.0),
    ("car_detail_kanji_unfocused.png",0, ( 1.3125, -1.5, 0.5), (-4.125, 0.0, -83.0), (2.75, 2.5), 180.0),
]
# ═════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "renders")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Render settings ──────────────────────────────────────────────────────────
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.resolution_x = RESOLUTION_X
scene.render.resolution_y = RESOLUTION_Y
scene.cycles.samples      = SAMPLES
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = 'OPTIX'
except Exception:
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'

scene.render.image_settings.file_format  = 'PNG'
scene.render.image_settings.color_mode  = 'RGBA'
scene.render.image_settings.compression = 15

try:
    prefs  = bpy.context.preferences
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

# ── Render loop ──────────────────────────────────────────────────────────────
car = bpy.data.objects[CAR_OBJECT]
original_z = car.rotation_euler.z

print(f"\nPreset: {PRESET} — {RESOLUTION_X}×{RESOLUTION_Y}, {SAMPLES} samples")
print(f"Renderizando {len(SHOTS)} tomas → {OUTPUT_DIR}\n")

for i, (name, z_deg) in enumerate(SHOTS):
    car.rotation_euler.z = original_z + math.radians(z_deg)
    bpy.context.view_layer.update()

    scene.render.filepath = os.path.join(OUTPUT_DIR, name)
    bpy.ops.render.render(write_still=True)
    print(f"  [{i + 1}/{len(SHOTS)}] {name}.png")

car.rotation_euler.z = original_z

# ── Picados ──────────────────────────────────────────────────────────────────
if SHOTS_PICADO:
    cam = bpy.data.objects['Camera']
    orig_cam_loc = cam.location.copy()
    orig_cam_rot = cam.rotation_euler.copy()

    stage_v = mathutils.Vector(STAGE_CENTER)
    cam.location = mathutils.Vector(CAM_PICADO_LOC)
    direction = (stage_v - cam.location).normalized()
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.rotation_euler.x += math.radians(CAM_PICADO_ROT[0])
    cam.rotation_euler.y += math.radians(CAM_PICADO_ROT[1])
    cam.rotation_euler.z += math.radians(CAM_PICADO_ROT[2])
    bpy.context.view_layer.update()

    print(f"\nPicados: {len(SHOTS_PICADO)} tomas\n")
    for i, (name, z_deg) in enumerate(SHOTS_PICADO):
        car.rotation_euler.z = original_z + math.radians(z_deg)
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(OUTPUT_DIR, name)
        bpy.ops.render.render(write_still=True)
        print(f"  [picado {i + 1}/{len(SHOTS_PICADO)}] {name}")

    cam.location       = orig_cam_loc
    cam.rotation_euler = orig_cam_rot
    car.rotation_euler.z = original_z

# ── Detalle ───────────────────────────────────────────────────────────────────
if SHOTS_DETALLE:
    cam = bpy.data.objects['Camera']
    orig_cam_loc = cam.location.copy()
    orig_cam_rot = cam.rotation_euler.copy()

    stage_v = mathutils.Vector(STAGE_CENTER)

    print(f"\nDetalle: {len(SHOTS_DETALLE)} tomas\n")
    for i, (name, z_deg, det_loc, det_rot, dof, diorama_rot) in enumerate(SHOTS_DETALLE):
        ref_loc = mathutils.Vector((det_loc[0], STAGE_CENTER[1], STAGE_CENTER[2]))
        direction = (stage_v - ref_loc).normalized()
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cam.rotation_euler.x += math.radians(det_rot[0])
        cam.rotation_euler.y += math.radians(det_rot[1])
        cam.rotation_euler.z += math.radians(det_rot[2])
        cam.location = mathutils.Vector(det_loc)

        cyclorama    = bpy.data.objects.get('Cyclorama')
        orig_cyc_rot = cyclorama.rotation_euler.copy() if cyclorama else None
        if diorama_rot is not None and cyclorama:
            cyclorama.rotation_euler.z = math.radians(diorama_rot)

        orig_dof_use   = cam.data.dof.use_dof
        orig_dof_dist  = cam.data.dof.focus_distance
        orig_dof_fstop = cam.data.dof.aperture_fstop
        if dof is not None:
            cam.data.dof.use_dof        = True
            cam.data.dof.focus_distance = dof[0]
            cam.data.dof.aperture_fstop = dof[1]

        car.rotation_euler.z = original_z + math.radians(z_deg)
        bpy.context.view_layer.update()
        scene.render.filepath = os.path.join(OUTPUT_DIR, name)
        bpy.ops.render.render(write_still=True)
        print(f"  [detalle {i + 1}/{len(SHOTS_DETALLE)}] {name}")

        cam.data.dof.use_dof        = orig_dof_use
        cam.data.dof.focus_distance = orig_dof_dist
        cam.data.dof.aperture_fstop = orig_dof_fstop

        if orig_cyc_rot is not None and cyclorama:
            cyclorama.rotation_euler = orig_cyc_rot

    cam.location       = orig_cam_loc
    cam.rotation_euler = orig_cam_rot
    car.rotation_euler.z = original_z

print("\nListo.")
