import math
import os

import bpy

# ═══════════════════ SETTINGS ════════════════════════════════════════════════
CAR_OBJECT    = "CAR_ROOT"
THUMB_RES_X   = 1100
THUMB_RES_Y   = 1100
THUMB_SAMPLES = 64
# ═════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR    = os.path.join(RESOURCES_DIR, "3d", "previews")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Render settings ──────────────────────────────────────────────────────────
scene = bpy.context.scene
scene.render.engine        = 'CYCLES'
scene.render.resolution_x  = THUMB_RES_X
scene.render.resolution_y  = THUMB_RES_Y
scene.cycles.samples       = THUMB_SAMPLES
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = 'OPTIX'
except Exception:
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'

scene.render.image_settings.file_format  = 'PNG'
scene.render.image_settings.color_mode   = 'RGBA'
scene.render.image_settings.compression  = 15

try:
    prefs  = bpy.context.preferences
    cprefs = prefs.addons['cycles'].preferences
    for device_type in ('OPTIX', 'CUDA'):
        try:
            cprefs.compute_device_type = device_type
            cprefs.refresh_devices()
            for dev in cprefs.devices:
                dev.use = True
            print(f"GPU compute: {device_type}")
            break
        except Exception:
            continue
except Exception:
    pass

scene.cycles.device = 'GPU'

# ── Estado original ───────────────────────────────────────────────────────────
car        = bpy.data.objects[CAR_OBJECT]
original_z = car.rotation_euler.z

# ── Escena_preview.png — coche a 36° (3/4 frontal derecho) ───────────────────
car.rotation_euler.z = original_z + math.radians(36)
bpy.context.view_layer.update()
scene.render.filepath = os.path.join(OUTPUT_DIR, "Escena_preview.png")
bpy.ops.render.render(write_still=True)
print("  Escena_preview.png")

# ── Suzuki_preview.png — coche frontal (0°) ───────────────────────────────────
car.rotation_euler.z = original_z
bpy.context.view_layer.update()
scene.render.filepath = os.path.join(OUTPUT_DIR, "Suzuki_preview.png")
bpy.ops.render.render(write_still=True)
print("  Suzuki_preview.png")

# ── Studio_preview.png — ciclorama vacío ──────────────────────────────────────
car.hide_render      = True
car.rotation_euler.z = original_z
bpy.context.view_layer.update()
scene.render.filepath = os.path.join(OUTPUT_DIR, "Studio_preview.png")
bpy.ops.render.render(write_still=True)
print("  Studio_preview.png")

# ── Restaurar ────────────────────────────────────────────────────────────────
car.hide_render      = False
car.rotation_euler.z = original_z

print(f"\nMiniaturas → {OUTPUT_DIR}")
