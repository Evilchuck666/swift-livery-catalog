import bpy
import math
import os

# ═══════════════════ SETTINGS ════════════════════════════════════════════════
CAR_COLLECTION = "SUZUKI_CAR"
CAR_ROOT_NAME  = "CAR_ROOT"
CAR_LOCATION   = (0.0, 0.0, 0.1)
CAR_ROTATION_X = -0.25          # grados; ajustar si alguna rueda no toca el suelo
CAR_ROTATION_Z = 180.0          # grados; ajustar si el coche no mira hacia la cámara
# ═════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR  = os.path.dirname(SCRIPT_DIR)
SUZUKI_PATH  = os.path.join(PROJECT_DIR, "models", "Suzuki.blend")
OUTPUT_PATH  = os.path.join(PROJECT_DIR, "models", "Escena.blend")

# ── Importar colección desde Suzuki.blend ────────────────────────────────────
with bpy.data.libraries.load(SUZUKI_PATH, link=False) as (data_from, data_to):
    if CAR_COLLECTION not in data_from.collections:
        raise RuntimeError(f"Colección '{CAR_COLLECTION}' no encontrada en {SUZUKI_PATH}")
    data_to.collections = [CAR_COLLECTION]

suzuki_col = bpy.data.collections.get(CAR_COLLECTION)
if suzuki_col is None:
    raise RuntimeError(f"No se pudo cargar la colección '{CAR_COLLECTION}'")

bpy.context.scene.collection.children.link(suzuki_col)
print(f"Colección '{CAR_COLLECTION}' importada ({len(suzuki_col.objects)} objetos)")

# ── Posicionar CAR_ROOT ──────────────────────────────────────────────────────
car = bpy.data.objects.get(CAR_ROOT_NAME)
if car is None:
    raise RuntimeError(f"Objeto '{CAR_ROOT_NAME}' no encontrado tras la importación")

car.location       = CAR_LOCATION
car.rotation_euler = (math.radians(CAR_ROTATION_X), 0.0, math.radians(CAR_ROTATION_Z))
print(f"'{CAR_ROOT_NAME}' → location={CAR_LOCATION}  rotation_x={CAR_ROTATION_X}°")

# ── Guardar ──────────────────────────────────────────────────────────────────
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_PATH)
print(f"Escena guardada → {OUTPUT_PATH}")
