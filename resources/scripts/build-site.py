#!/usr/bin/env python3
"""
Script de build para el catálogo de livery del Suzuki Swift Sport ZC33S.

Genera miniaturas WebP y el archivo catalog-data.js necesarios para el sitio.
Los pasos de miniaturas siempre sobreescriben los archivos existentes.

Sin argumentos ejecuta todos los pasos en orden.
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    raise SystemExit(
        "✗ Pillow no instalado.\n"
        "  Ejecuta: pip install Pillow"
    )

# ── Rutas ─────────────────────────────────────────────────────────────────────

ROOT       = Path(__file__).resolve().parent.parent.parent
RESOURCES  = ROOT / "resources"
CATALOG_JS = ROOT / "assets" / "catalog-data.js"

# ── Constantes de calidad WebP ────────────────────────────────────────────────

_QUALITY_HI = 90   # WebP de livery 1600×900
_METHOD_HI  = 6
_QUALITY_TH = 85   # todas las miniaturas
_METHOD_TH  = 6

_SIZE_LIVERY_WEBP  = (1600, 900)
_SIZE_LIVERY_THUMB = (640,  360)
_SIZE_SQUARE_THUMB = (360,  360)

# ── Metadatos del catálogo ────────────────────────────────────────────────────

VIEWS_META = {
    "frontal":   {"name": "Frontal",       "glyph": "正", "sub": "Vista frontal centrada"},
    "delantero": {"name": "3/4 Delantero", "glyph": "前", "sub": "Ángulos delanteros"},
    "lateral":   {"name": "Lateral",       "glyph": "側", "sub": "Perfiles completos"},
    "trasero":   {"name": "3/4 Trasero",   "glyph": "後", "sub": "Ángulos traseros"},
    "cola":      {"name": "Cola",          "glyph": "尾", "sub": "Trasera centrada"},
    "cenital":   {"name": "Cenital",       "glyph": "上", "sub": "Vistas superiores"},
    "detalle":   {"name": "Detalle",       "glyph": "細", "sub": "Detalles de vinilos y llantas"},
}
VIEW_ORDER = list(VIEWS_META)

SHOT_META = {
    "car_000_front":              {"name": "Frontal centrado"},
    "car_216_rear_left":          {"name": "3/4 Trasero izquierdo"},
    "car_252_left_rear":          {"name": "Perfil izquierdo (trasero)"},
    "car_288_left_front":         {"name": "Perfil izquierdo (delantero)"},
    "car_324_front_left":         {"name": "3/4 Delantero izquierdo"},
    "car_036_front_right":        {"name": "3/4 Delantero derecho"},
    "car_072_right_front":        {"name": "Perfil derecho (delantero)"},
    "car_108_right_rear":         {"name": "Perfil derecho (trasero)"},
    "car_144_rear_right":         {"name": "3/4 Trasero derecho"},
    "car_180_rear":               {"name": "Cola centrada"},
    "car_detail_front_left":      {"name": "Detalle frontal izquierdo"},
    "car_detail_front_right":     {"name": "Detalle frontal derecho"},
    "car_detail_kanji_unfocused": {"name": "Detalle kanji desenfocado"},
    "car_detail_kanji_focused":   {"name": "Detalle kanji enfocado"},
    "car_picado_front":           {"name": "Cenital delantero"},
    "car_picado_rear":            {"name": "Cenital trasero"},
}
SHOT_ORDER = list(SHOT_META)

SHOT_VIEW = {
    "car_000_front":              "frontal",
    "car_216_rear_left":          "trasero",
    "car_252_left_rear":          "lateral",
    "car_288_left_front":         "lateral",
    "car_324_front_left":         "delantero",
    "car_036_front_right":        "delantero",
    "car_072_right_front":        "lateral",
    "car_108_right_rear":         "lateral",
    "car_144_rear_right":         "trasero",
    "car_180_rear":               "cola",
    "car_detail_front_left":      "detalle",
    "car_detail_front_right":     "detalle",
    "car_detail_kanji_unfocused": "detalle",
    "car_detail_kanji_focused":   "detalle",
    "car_picado_front":           "cenital",
    "car_picado_rear":            "cenital",
}

KAMON_META = {
    "derecho.png":   {"name": "Aries Ferrus", "placement": "Lado derecho"},
    "izquierdo.png": {"name": "Aries Ferrus", "placement": "Lado izquierdo"},
    "tro.png":       {"name": "TRO",          "placement": "Maletero"},
}
KANJI_META = {
    "san.png":   {"name": "San (Tres)",        "placement": "Ambos lados"},
    "gatsu.png": {"name": "Gatsu (Luna, Mes)", "placement": "Ambos lados"},
}
MODELS_3D_META = {
    "Suzuki.blend": {"name": "Suzuki Swift Sport ZC33S", "role": "Modelo del vehículo"},
    "Escena.blend": {"name": "Escena completa",          "role": "Vehículo con escenario"},
    "Studio.blend": {"name": "Estudio de iluminación",   "role": "Entorno de render"},
}

_BLACK_COLOR = {
    "hex":        "#101820",
    "rgb":        "16, 24, 32",
    "hsv":        {"hue": 210.0, "saturation": 50.0, "value": 12.55},
    "cmyk":       "50.00%, 25.00%, 0.00%, 87.45%",
    "pantone":    "Black 6 C",
    "matte":      "Acabado mate",
    "matteLevel": "none",
}

_IMAGE_EXTS = (".png", ".jpg", ".jpeg")
_MODEL_EXTS = (".blend",)

# ── Helper de imagen ──────────────────────────────────────────────────────────

def _prepare_image(img, preserve_alpha=False):
    """
    Normaliza el modo de color de una imagen antes de procesar.

    preserve_alpha=False (por defecto):
        Aplana canales de transparencia sobre fondo blanco y devuelve RGB.
        Usar para kamon y kanji, cuyos PNG tienen fondo transparente que
        debe mostrarse sobre blanco.

    preserve_alpha=True:
        Convierte a RGBA conservando el canal alpha.
        Usar para renders 3D que tienen fondo transparente intencionado.
    """
    if img.mode == "P":
        img = img.convert("RGBA")

    if img.mode in ("RGBA", "LA"):
        if preserve_alpha:
            return img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg.convert("RGB")

    return img.convert("RGB")

# ── Pasos de build ────────────────────────────────────────────────────────────

def step_thumbs_livery():
    """
    Para cada livery en resources/liveries/:
      - Genera WebP 1600×900 en <livery>/WebP/
      - Genera miniatura 640×360 en <livery>/thumbnails/
    Siempre sobreescribe los archivos existentes.
    """
    liveries_dir = RESOURCES / "liveries"
    if not liveries_dir.is_dir():
        raise SystemExit(
            f"✗ No existe el directorio de liveries: {liveries_dir}\n"
            "  Comprueba que 'resources/liveries/' existe en el proyecto."
        )

    liveries = sorted(d for d in liveries_dir.iterdir() if d.is_dir())
    if not liveries:
        print("⚠  No se encontraron liveries en resources/liveries/")
        return

    total = 0
    for livery_dir in liveries:
        png_dir   = livery_dir / "PNG"
        webp_dir  = livery_dir / "WebP"
        thumb_dir = livery_dir / "thumbnails"

        if not png_dir.is_dir():
            print(f"  ⚠  {livery_dir.name}: sin directorio PNG/, omitido")
            continue

        webp_dir.mkdir(exist_ok=True)
        thumb_dir.mkdir(exist_ok=True)

        for png in sorted(png_dir.glob("*.png")):
            with Image.open(png) as img:
                rgb = img.convert("RGB")
                rgb.resize(_SIZE_LIVERY_WEBP, Image.LANCZOS).save(
                    webp_dir  / f"{png.stem}.webp",
                    "WEBP", quality=_QUALITY_HI, method=_METHOD_HI,
                )
                rgb.resize(_SIZE_LIVERY_THUMB, Image.LANCZOS).save(
                    thumb_dir / f"{png.stem}_preview.webp",
                    "WEBP", quality=_QUALITY_TH, method=_METHOD_TH,
                )
            print(f"  ✓ {livery_dir.name}/{png.name}")
            total += 1

    print(f"\n✓ {total} imágenes procesadas en resources/liveries/*/")


def step_thumbs_square(asset_type, preserve_alpha=False):
    """
    Genera miniaturas cuadradas 360×360 WebP para resources/{asset_type}/PNG/*.png
    y las guarda en resources/{asset_type}/thumbnails/.
    Siempre sobreescribe los archivos existentes.

    preserve_alpha: véase _prepare_image().
    """
    png_dir   = RESOURCES / asset_type / "PNG"
    thumb_dir = RESOURCES / asset_type / "thumbnails"

    if not png_dir.is_dir():
        raise SystemExit(
            f"✗ No existe el directorio: {png_dir}\n"
            f"  Comprueba que 'resources/{asset_type}/PNG/' existe en el proyecto."
        )

    thumb_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted(png_dir.glob("*.png"))
    if not pngs:
        print(f"  ⚠  No se encontraron PNG en {png_dir.relative_to(ROOT)}")
        return

    for png in pngs:
        with Image.open(png) as img:
            prepared = _prepare_image(img, preserve_alpha=preserve_alpha)
            thumb    = ImageOps.fit(prepared, _SIZE_SQUARE_THUMB, method=Image.LANCZOS)
            thumb.save(
                thumb_dir / f"{png.stem}_preview.webp",
                "WEBP", quality=_QUALITY_TH, method=_METHOD_TH,
            )
        print(f"  ✓ {png.name}")

    print(f"\n✓ Miniaturas en: {thumb_dir.relative_to(ROOT)}")


# ── Catálogo ──────────────────────────────────────────────────────────────────

def _find_image(directory, stem):
    for ext in _IMAGE_EXTS:
        candidate = directory / f"{stem}{ext}"
        if candidate.is_file():
            return candidate.name
    return None


def _colors_from_livery_json(lj):
    hex_   = lj.get("hex", "#888888")
    rgb_v  = lj.get("rgb", [])
    hsv_v  = lj.get("hsv", [0, 0, 0])
    cmyk_v = lj.get("cmyk", [0, 0, 0, 0])

    rgb_str  = ", ".join(str(v) for v in rgb_v) if rgb_v else "—"
    cmyk_str = ", ".join(f"{x:.2f}%" for x in cmyk_v) if cmyk_v else "—"

    stripe = {
        "hex":  hex_,
        "rgb":  rgb_str,
        "hsv":  {
            "hue":        round(float(hsv_v[0]), 2),
            "saturation": round(float(hsv_v[1]), 2),
            "value":      round(float(hsv_v[2]), 2),
        } if len(hsv_v) == 3 else {},
        "cmyk":       cmyk_str,
        "pantone":    lj.get("pantone", "—"),
        "matte":      "Acabado satinado",
        "matteLevel": "medium",
    }

    return [
        {"name": "Racing stripe central", "role": "Franja longitudinal principal", **stripe},
        {"name": "Racing stripe lateral", "role": "Franja lateral",               **stripe},
        {"name": "Kanji", "role": "Grafía japonesa",               **_BLACK_COLOR},
        {"name": "Kamon", "role": "Emblemas laterales y maletero", **_BLACK_COLOR},
    ]


def _scan_image_assets(asset_type, meta_map):
    png_dir   = RESOURCES / asset_type / "PNG"
    thumb_dir = RESOURCES / asset_type / "thumbnails"
    if not png_dir.is_dir():
        return []
    result = []
    for fname in sorted(f for f in os.listdir(png_dir)
                        if (png_dir / f).is_file() and f.lower().endswith(_IMAGE_EXTS)):
        stem = Path(fname).stem
        m    = meta_map.get(fname, {"name": f"TODO: {stem}", "placement": "TODO"})
        entry = {
            "name":      m["name"],
            "placement": m["placement"],
            "uri":       f"resources/{asset_type}/PNG/{fname}",
        }
        preview = thumb_dir / f"{stem}_preview.webp"
        if preview.is_file():
            entry["preview"] = f"resources/{asset_type}/thumbnails/{stem}_preview.webp"
        result.append(entry)
    return result


def _scan_3d_assets(asset_type, meta_map):
    root      = RESOURCES / asset_type
    thumb_dir = root / "thumbnails"
    if not root.is_dir():
        return []
    result = []
    for fname in sorted(f for f in os.listdir(root)
                        if (root / f).is_file() and f.lower().endswith(_MODEL_EXTS)):
        stem = Path(fname).stem
        m    = meta_map.get(fname, {"name": stem, "role": "Modelo 3D"})
        entry = {
            "name": m["name"],
            "role": m["role"],
            "uri":  f"resources/{asset_type}/{fname}",
        }
        preview = thumb_dir / f"{stem}_preview.webp"
        if preview.is_file():
            entry["preview"] = f"resources/{asset_type}/thumbnails/{stem}_preview.webp"
        result.append(entry)
    return result


def step_catalog(dry_run=False):
    """
    Escanea todos los recursos y genera assets/catalog-data.js.
    Si dry_run=True, imprime el resultado sin escribir el archivo.
    """
    liveries_dir = RESOURCES / "liveries"
    if not liveries_dir.is_dir():
        raise SystemExit(
            f"✗ No existe el directorio de liveries: {liveries_dir}\n"
            "  El catálogo no puede generarse sin liveries."
        )

    livery_dirs = sorted(
        (e.name, e)
        for e in liveries_dir.iterdir()
        if e.is_dir()
    )
    if not livery_dirs:
        raise SystemExit(
            "✗ No se encontraron liveries en resources/liveries/.\n"
            "  Añade al menos un directorio de livery antes de generar el catálogo."
        )

    # Validación temprana — falla antes de escribir nada
    for livery_key, livery_path in livery_dirs:
        json_path = livery_path / "livery.json"
        if not json_path.is_file():
            raise SystemExit(
                f"✗ Falta el archivo de metadatos:\n"
                f"  resources/liveries/{livery_key}/livery.json\n"
                "  Crea el archivo con los datos del livery antes de continuar."
            )
        png_dir = livery_path / "PNG"
        missing = [s for s in SHOT_ORDER if not _find_image(png_dir, s)]
        if missing:
            raise SystemExit(
                f"✗ Faltan imágenes en resources/liveries/{livery_key}/PNG/:\n"
                + "\n".join(f"  - {s}.png" for s in missing)
            )

    items         = []
    liveries_meta = {}
    resources     = {}
    livery_order  = []

    for livery_key, livery_path in livery_dirs:
        with open(livery_path / "livery.json", encoding="utf-8") as f:
            lj = json.load(f)

        png_dir   = livery_path / "PNG"
        webp_dir  = livery_path / "WebP"
        thumb_dir = livery_path / "thumbnails"

        for shot in SHOT_ORDER:
            fname = _find_image(png_dir, shot)
            stem  = Path(fname).stem
            item  = {
                "livery": livery_key,
                "view":   SHOT_VIEW[shot],
                "shot":   shot,
                "uri":    f"resources/liveries/{livery_key}/PNG/{fname}",
            }
            if (webp_dir / f"{stem}.webp").is_file():
                item["webp"] = f"resources/liveries/{livery_key}/WebP/{stem}.webp"
            if (thumb_dir / f"{stem}_preview.webp").is_file():
                item["preview"] = f"resources/liveries/{livery_key}/thumbnails/{stem}_preview.webp"
            items.append(item)

        lj_name = lj.get("livery", livery_key)
        liveries_meta[livery_key] = {
            "name":  lj_name,
            "glyph": lj.get("glyph", "◆"),
            "hex":   lj.get("hex", "#888888"),
        }
        resources[livery_key] = {"colors": _colors_from_livery_json(lj)}
        livery_order.append(livery_key)
        print(f"  ✓ Livery: {livery_key} → {len(SHOT_ORDER)} shots")

    resources["kamon"]     = _scan_image_assets("kamon", KAMON_META)
    resources["kanji"]     = _scan_image_assets("kanji", KANJI_META)
    resources["models_3d"] = _scan_3d_assets("3d", MODELS_3D_META)

    data = {
        "items": items,
        "meta": {
            "liveries": liveries_meta,
            "views":    VIEWS_META,
            "shots":    SHOT_META,
            "order": {
                "liveries": livery_order,
                "views":    VIEW_ORDER,
                "shots":    SHOT_ORDER,
            },
            "resources": resources,
        },
    }

    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    output   = f"window.CATALOG_DATA = {json_str};\n"

    if dry_run:
        print("\n── DRY RUN ── catalog-data.js resultante:\n")
        print(output)
    else:
        with open(CATALOG_JS, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\n✓ catalog-data.js generado ({len(items)} items, {len(livery_order)} liveries)")


# ── CLI ───────────────────────────────────────────────────────────────────────

def _build_parser():
    parser = argparse.ArgumentParser(
        prog="build-site.py",
        description=(
            "Genera miniaturas WebP y el catálogo catalog-data.js\n"
            "para el sitio de livery del Suzuki Swift Sport ZC33S.\n\n"
            "Sin argumentos ejecuta todos los pasos en orden."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Ejemplos:
  python3 build-site.py                        Genera todo en orden
  python3 build-site.py --thumbs               Todas las miniaturas
  python3 build-site.py --thumbs-livery        Solo WebP + miniaturas de liveries
  python3 build-site.py --thumbs-3d            Solo miniaturas de modelos 3D
  python3 build-site.py --thumbs-kamon         Solo miniaturas de kamon
  python3 build-site.py --thumbs-kanji         Solo miniaturas de kanji
  python3 build-site.py --catalog              Solo el catálogo
  python3 build-site.py --thumbs --catalog     Miniaturas y catálogo
  python3 build-site.py --catalog --dry-run    Vista previa del catálogo sin escribirlo
""",
    )

    pasos = parser.add_argument_group("pasos")
    pasos.add_argument(
        "--thumbs", action="store_true",
        help="Todas las miniaturas (equivale a --thumbs-livery --thumbs-3d --thumbs-kamon --thumbs-kanji)",
    )
    pasos.add_argument(
        "--thumbs-livery", action="store_true", dest="thumbs_livery",
        help="WebP 1600×900 + miniaturas 640×360 para los PNG de cada livery",
    )
    pasos.add_argument(
        "--thumbs-3d", action="store_true", dest="thumbs_3d",
        help="Miniaturas 360×360 para los PNG de modelos 3D (preserva canal alpha)",
    )
    pasos.add_argument(
        "--thumbs-kamon", action="store_true", dest="thumbs_kamon",
        help="Miniaturas 360×360 para los PNG de kamon (fondo blanco)",
    )
    pasos.add_argument(
        "--thumbs-kanji", action="store_true", dest="thumbs_kanji",
        help="Miniaturas 360×360 para los PNG de kanji (fondo blanco)",
    )
    pasos.add_argument(
        "--catalog", action="store_true",
        help="Genera assets/catalog-data.js escaneando todos los recursos",
    )

    opciones = parser.add_argument_group("opciones")
    opciones.add_argument(
        "--dry-run", action="store_true", dest="dry_run",
        help="Con --catalog: muestra el resultado por pantalla sin escribir el archivo",
    )

    return parser


def main():
    parser = _build_parser()
    args   = parser.parse_args()

    # --thumbs expande a todos los pasos de miniaturas
    if args.thumbs:
        args.thumbs_livery = args.thumbs_3d = args.thumbs_kamon = args.thumbs_kanji = True

    # Sin pasos seleccionados → ejecutar todo
    any_step = any([
        args.thumbs_livery, args.thumbs_3d,
        args.thumbs_kamon,  args.thumbs_kanji,
        args.catalog,
    ])
    if not any_step:
        args.thumbs_livery = args.thumbs_3d = args.thumbs_kamon = args.thumbs_kanji = args.catalog = True

    # --dry-run sin --catalog no tiene efecto útil
    if args.dry_run and not args.catalog:
        print("⚠  --dry-run solo tiene efecto con --catalog. Ignorado para otros pasos.", file=sys.stderr)

    # ── Ejecutar en orden ─────────────────────────────────────────────────────

    if args.thumbs_livery:
        print("\n── Livery · WebP + miniaturas ────────────────────────────")
        step_thumbs_livery()

    if args.thumbs_3d:
        print("\n── 3D · Miniaturas ───────────────────────────────────────")
        step_thumbs_square("3d", preserve_alpha=True)

    if args.thumbs_kamon:
        print("\n── Kamon · Miniaturas ────────────────────────────────────")
        step_thumbs_square("kamon")

    if args.thumbs_kanji:
        print("\n── Kanji · Miniaturas ────────────────────────────────────")
        step_thumbs_square("kanji")

    if args.catalog:
        print("\n── Catálogo ──────────────────────────────────────────────")
        step_catalog(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
