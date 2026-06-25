#!/usr/bin/env python3
"""
Genera assets/catalog-data.js desde cero escaneando resources/.

Uso:  python3 generate-catalog.py
      python3 generate-catalog.py --dry-run   (muestra el resultado sin escribir)
"""

import json
import os
import sys

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
CATALOG_JS   = os.path.join(SCRIPT_DIR, "assets", "catalog-data.js")
RESOURCES    = os.path.join(SCRIPT_DIR, "resources")
LIVERIES_DIR = os.path.join(SCRIPT_DIR, "resources", "liveries")

# ── Metadatos estáticos ───────────────────────────────────────────────────────

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
    "frontal_centrado":                  {"name": "Frontal centrado"},
    "tres_cuartos_delantero_izquierdo":  {"name": "3/4 Delantero izquierdo"},
    "tres_cuartos_delantero_derecho":    {"name": "3/4 Delantero derecho"},
    "perfil_completo_izquierdo":         {"name": "Perfil completo izquierdo"},
    "perfil_completo_izquierdo_ladeado": {"name": "Perfil completo izquierdo ladeado"},
    "perfil_completo_derecho":           {"name": "Perfil completo derecho"},
    "perfil_completo_derecho_ladeado":   {"name": "Perfil completo derecho ladeado"},
    "tres_cuartos_trasero_izquierdo":    {"name": "3/4 Trasero izquierdo"},
    "tres_cuartos_trasero_derecho":      {"name": "3/4 Trasero derecho"},
    "cola_centrada":                     {"name": "Cola centrada"},
    "cenital_delantero":                 {"name": "Cenital delantero"},
    "cenital_trasero":                   {"name": "Cenital trasero"},
    "detalle_kanji_desenfocado":         {"name": "Detalle kanji desenfocado"},
    "detalle_kanji_enfocado":            {"name": "Detalle kanji enfocado"},
    "detalle_llanta_delantera":          {"name": "Detalle llanta delantera"},
}
SHOT_ORDER = list(SHOT_META)

SHOT_VIEW = {
    "frontal_centrado":                  "frontal",
    "tres_cuartos_delantero_izquierdo":  "delantero",
    "tres_cuartos_delantero_derecho":    "delantero",
    "perfil_completo_izquierdo":         "lateral",
    "perfil_completo_izquierdo_ladeado": "lateral",
    "perfil_completo_derecho":           "lateral",
    "perfil_completo_derecho_ladeado":   "lateral",
    "tres_cuartos_trasero_izquierdo":    "trasero",
    "tres_cuartos_trasero_derecho":      "trasero",
    "cola_centrada":                     "cola",
    "cenital_delantero":                 "cenital",
    "cenital_trasero":                   "cenital",
    "detalle_kanji_desenfocado":         "detalle",
    "detalle_kanji_enfocado":            "detalle",
    "detalle_llanta_delantera":          "detalle",
}

KAMON_META = {
    "derecho.png":   {"name": "Aries Ferrus", "placement": "Lado derecho"},
    "izquierdo.png": {"name": "Aries Ferrus", "placement": "Lado izquierdo"},
    "tro.png":       {"name": "TRO",          "placement": "Maletero"},
}
KANJI_META = {
    "kin.png": {"name": "Kin (Oro, Metal)", "placement": "Ambos lados"},
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

# ── Helpers ───────────────────────────────────────────────────────────────────

def scan_livery_dirs(liveries_root):
    """Devuelve lista ordenada de (livery_key, livery_path)."""
    if not os.path.isdir(liveries_root):
        raise FileNotFoundError(f"✗ No existe el directorio: {liveries_root}")
    entries = sorted(e for e in os.listdir(liveries_root)
                     if os.path.isdir(os.path.join(liveries_root, e)))
    return [(e, os.path.join(liveries_root, e)) for e in entries]


def validate_livery(livery_key, livery_path):
    """Falla con mensaje claro si falta livery.json o algún PNG obligatorio."""
    if not os.path.isfile(os.path.join(livery_path, "livery.json")):
        raise FileNotFoundError(
            f"✗ Falta resources/liveries/{livery_key}/livery.json")
    missing = [s for s in SHOT_ORDER
               if not os.path.isfile(os.path.join(livery_path, f"{s}.png"))]
    if missing:
        raise FileNotFoundError(
            f"✗ Faltan imágenes en resources/liveries/{livery_key}/:\n" +
            "\n".join(f"  - {s}.png" for s in missing))


def read_livery_json(livery_path):
    with open(os.path.join(livery_path, "livery.json"), encoding="utf-8") as f:
        return json.load(f)


def scan_image_assets(asset_type, meta_map):
    """Escanea resources/{asset_type}/*.png usando meta_map para name/placement."""
    root = os.path.join(RESOURCES, asset_type)
    previews_dir = os.path.join(root, "previews")
    if not os.path.isdir(root):
        return []
    result = []
    for fname in sorted(os.listdir(root)):
        if not os.path.isfile(os.path.join(root, fname)) or not fname.lower().endswith(".png"):
            continue
        stem = os.path.splitext(fname)[0]
        m = meta_map.get(fname, {"name": f"TODO: {stem}", "placement": "TODO"})
        entry = {
            "name":      m["name"],
            "placement": m["placement"],
            "uri":       f"resources/{asset_type}/{fname}",
        }
        preview_path = os.path.join(previews_dir, f"{stem}_preview.png")
        if os.path.isfile(preview_path):
            entry["preview"] = f"resources/{asset_type}/previews/{stem}_preview.png"
        result.append(entry)
    return result


def colors_from_livery_json(lj):
    """Construye la lista de colores a partir de livery.json."""
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


def write_catalog_js(path, data, dry_run=False):
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    output   = f"window.CATALOG_DATA = {json_str};\n"
    if dry_run:
        print("\n── DRY RUN ── catalog-data.js resultante:\n")
        print(output)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(output)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv

    livery_dirs = scan_livery_dirs(LIVERIES_DIR)
    if not livery_dirs:
        print("⚠  No se encontraron liveries en resources/liveries/. Nada que hacer.")
        return

    # Validación temprana — falla antes de escribir nada
    for livery_key, livery_path in livery_dirs:
        validate_livery(livery_key, livery_path)

    items         = []
    liveries_meta = {}
    resources     = {}
    livery_order  = []

    for livery_key, livery_path in livery_dirs:
        lj = read_livery_json(livery_path)

        # Items
        for shot in SHOT_ORDER:
            items.append({
                "livery": livery_key,
                "view":   SHOT_VIEW[shot],
                "shot":   shot,
                "uri":    f"resources/liveries/{livery_key}/{shot}.png",
            })

        # meta.liveries
        lj_name = lj.get("livery", livery_key)
        liveries_meta[livery_key] = {
            "name":  lj_name,
            "glyph": lj.get("glyph", "◆"),
            "hex":   lj.get("hex", "#888888"),
        }

        # meta.resources
        resources[livery_key] = {
            "colors": colors_from_livery_json(lj),
        }

        livery_order.append(livery_key)
        print(f"✓ Livery: {livery_key} → {len(SHOT_ORDER)} shots")

    # Assets compartidos
    resources["kamon"] = scan_image_assets("kamon", KAMON_META)
    resources["kanji"] = scan_image_assets("kanji", KANJI_META)

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

    write_catalog_js(CATALOG_JS, data, dry_run=dry_run)

    if not dry_run:
        print(f"✓ catalog-data.js generado ({len(items)} items, {len(livery_order)} liveries)")


if __name__ == "__main__":
    main()
