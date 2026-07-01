#!/usr/bin/env python3
"""
Genera miniaturas WebP 360x360 con fondo blanco para los PNG de resources/kanji/PNG/.

Uso:  python3 make-kanji-thumbs.py           # solo procesa los que faltan
      python3 make-kanji-thumbs.py --force   # regenera todos
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    raise SystemExit("✗ Pillow no instalado. Ejecuta: pip install Pillow")

SCRIPT_DIR   = Path(__file__).resolve().parent.parent.parent
PNG_DIR      = SCRIPT_DIR / "resources" / "kanji" / "PNG"
THUMBS_DIR   = SCRIPT_DIR / "resources" / "kanji" / "thumbnails"
THUMB_SIZE   = (360, 360)
WEBP_QUALITY = 85
WEBP_METHOD  = 6


def _flatten_on_white(img):
    if img.mode == "P":
        img = img.convert("RGBA")
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg.convert("RGB")
    return img.convert("RGB")


def main():
    force = "--force" in sys.argv

    if not PNG_DIR.is_dir():
        raise SystemExit(f"✗ No existe el directorio: {PNG_DIR}")

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    pngs = sorted(PNG_DIR.glob("*.png"))
    if not pngs:
        print(f"⚠  No se encontraron PNG en {PNG_DIR}")
        return

    for png in pngs:
        out = THUMBS_DIR / f"{png.stem}_preview.webp"
        if out.exists() and not force:
            print(f"  – {png.name} (ya existe, omitido)")
            continue
        with Image.open(png) as img:
            flat = _flatten_on_white(img)
            thumb = ImageOps.fit(flat, THUMB_SIZE, method=Image.LANCZOS)
            thumb.save(out, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
        print(f"  ✓ {png.name}")

    print(f"\n✓ Miniaturas en: {THUMBS_DIR.relative_to(SCRIPT_DIR)}")


if __name__ == "__main__":
    main()
