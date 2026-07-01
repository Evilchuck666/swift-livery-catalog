#!/usr/bin/env python3
"""
Genera imágenes WebP 1600x900 para los PNG de cada livery en resources/liveries/.

Uso:  python3 make-livery-webp.py           # solo procesa los que faltan
      python3 make-livery-webp.py --force   # regenera todos
"""

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("✗ Pillow no instalado. Ejecuta: pip install Pillow")

SCRIPT_DIR   = Path(__file__).resolve().parent.parent.parent
LIVERIES_DIR = SCRIPT_DIR / "resources" / "liveries"
TARGET_SIZE  = (1600, 900)
WEBP_QUALITY = 90
WEBP_METHOD  = 6


def main():
    force = "--force" in sys.argv

    if not LIVERIES_DIR.is_dir():
        raise SystemExit(f"✗ No existe el directorio: {LIVERIES_DIR}")

    liveries = sorted(d for d in LIVERIES_DIR.iterdir() if d.is_dir())
    if not liveries:
        print(f"⚠  No se encontraron liveries en {LIVERIES_DIR}")
        return

    total = 0
    for livery_dir in liveries:
        png_dir = livery_dir / "PNG"
        if not png_dir.is_dir():
            continue
        webp_dir = livery_dir / "WebP"
        webp_dir.mkdir(exist_ok=True)

        pngs = sorted(png_dir.glob("*.png"))
        for png in pngs:
            out = webp_dir / f"{png.stem}.webp"
            if out.exists() and not force:
                print(f"  – {livery_dir.name}/{png.name} (ya existe, omitido)")
                continue
            with Image.open(png) as img:
                resized = img.convert("RGB").resize(TARGET_SIZE, Image.LANCZOS)
                resized.save(out, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
            print(f"  ✓ {livery_dir.name}/{png.name}")
            total += 1

    print(f"\n✓ {total} imágenes generadas en resources/liveries/*/WebP/")


if __name__ == "__main__":
    main()
