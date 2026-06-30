#!/usr/bin/env bash
set -euo pipefail

RESOURCES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RESOURCES_DIR"
blender --background 3d/Escena.blend \
        --python scripts/create_thumbnails.py
