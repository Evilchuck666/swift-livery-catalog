#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cat <<EOF
Uso: $(basename "$0") [PRESET] [CYCLES_DEVICE]

  PRESET         fast    → 1280×720,  128 samples  (preview rápido)
                 insane  → 7680×4320, 2048 samples (calidad máxima)
                 (por defecto: insane)

  CYCLES_DEVICE  CUDA    → GPU vía CUDA
                 OPTIX   → GPU vía OptiX  (más rápido en RTX)
                 (por defecto: CUDA)

Ejemplos:
  $(basename "$0") fast
  $(basename "$0") insane OPTIX
  $(basename "$0")                   # insane + CUDA

Salida: renders/ (PNG, uno por toma)
EOF
    exit 0
fi

PRESET="${1:-insane}"            # fast | insane  (default: insane)
CYCLES_DEVICE="${2:-CUDA}"       # CUDA | OPTIX   (default: CUDA)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
blender --background models/Escena.blend \
        --python scripts/render_shots.py \
        -- "$PRESET" --cycles-device "$CYCLES_DEVICE"
