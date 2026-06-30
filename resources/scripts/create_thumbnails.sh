#!/usr/bin/env bash
set -euo pipefail

RESOURCES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RESOURCES_DIR"

for blend in 3d/*.blend; do
    echo "→ Rendering $(basename "$blend" .blend)..."
    blender --background "$blend" \
            --python scripts/create_thumbnails.py
done
