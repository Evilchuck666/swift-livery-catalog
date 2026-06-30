import math
import os
import bpy

# ═══════════════════ SETTINGS ════════════════════════════════════════════════
THUMB_RES_X   = 1100
THUMB_RES_Y   = 1100
THUMB_SAMPLES = 64

# ── Camera overrides (edit these to adjust thumbnail framing) ────────────────
# location: (X, Y, Z) metres  |  rotation_deg: (X, Y, Z) Euler degrees
# Omit a stem to use the scene's default camera unchanged.
CAM_OVERRIDES = {
    "Studio": {
        "location":     (17.5, 52.5, 5.0),
        "rotation_deg": (90.0, 0.0, 160.625),
    },
}
# ═════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR    = os.path.join(RESOURCES_DIR, "3d", "previews")

os.makedirs(OUTPUT_DIR, exist_ok=True)

stem = os.path.splitext(os.path.basename(bpy.data.filepath))[0]

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

# ── Camera override ───────────────────────────────────────────────────────────
override = CAM_OVERRIDES.get(stem)
if override and scene.camera:
    cam = scene.camera
    cam.location = override["location"]
    cam.rotation_euler = [math.radians(d) for d in override["rotation_deg"]]
    bpy.context.view_layer.update()

# ── Render ───────────────────────────────────────────────────────────────────
output_path = os.path.join(OUTPUT_DIR, f"{stem}_preview.png")
scene.render.filepath = output_path
bpy.ops.render.render(write_still=True)
print(f"\n  {stem}_preview.png → {output_path}")
