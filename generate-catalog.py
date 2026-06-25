#!/usr/bin/env python3
"""
Regenera assets/catalog-data.js escaneando resources/<livery>/*.png.

Uso:  python3 generate-catalog.py
      python3 generate-catalog.py --dry-run   (muestra el resultado sin escribir)
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_JS   = os.path.join(SCRIPT_DIR, "assets", "catalog-data.js")
RESOURCES    = os.path.join(SCRIPT_DIR, "resources")
LIVERIES_DIR = os.path.join(SCRIPT_DIR, "resources", "liveries")

# Subdirectorios de resources/ que son assets compartidos, no liveries
SHARED_DIRS = {"kamon", "kanji"}

# ── Helpers ──────────────────────────────────────────────────────────────────

def read_catalog_js(path):
    """Devuelve (header, data_dict, iife_tail) del catalog-data.js."""
    with open(path, encoding="utf-8") as f:
        src = f.read()

    # Separar cabecera (comentarios antes de window.CATALOG_DATA)
    match_start = re.search(r'window\.CATALOG_DATA\s*=\s*', src)
    if not match_start:
        raise ValueError("No se encontró 'window.CATALOG_DATA = ' en el fichero.")

    header = src[:match_start.start()]
    after_assign = src[match_start.end():]

    # Extraer el objeto JSON usando un contador de llaves
    depth = 0
    json_end = 0
    in_string = False
    escape = False
    for i, ch in enumerate(after_assign):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                json_end = i + 1
                break

    json_str  = after_assign[:json_end]
    iife_tail = after_assign[json_end:].lstrip(';').lstrip('\n')

    data = json.loads(json_str)
    return header, data, iife_tail


def write_catalog_js(path, header, data, iife_tail, dry_run=False):
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    output   = f"{header}window.CATALOG_DATA = {json_str};\n{iife_tail}"
    if dry_run:
        print("\n── DRY RUN ── catalog-data.js resultante:\n")
        print(output)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(output)


def scan_livery_dirs(resources_root):
    """Devuelve lista ordenada de (livery_key, livery_path)."""
    if not os.path.isdir(resources_root):
        raise FileNotFoundError(f"No existe el directorio: {resources_root}")
    entries = sorted(
        e for e in os.listdir(resources_root)
        if os.path.isdir(os.path.join(resources_root, e)) and e not in SHARED_DIRS
    )
    return [(e, os.path.join(resources_root, e)) for e in entries]


def scan_shots(livery_path):
    """PNGs en la raíz del directorio de livery (excluye subdirectorios)."""
    shots = []
    for fname in sorted(os.listdir(livery_path)):
        full = os.path.join(livery_path, fname)
        if os.path.isfile(full) and fname.lower().endswith(".png"):
            shots.append(os.path.splitext(fname)[0])
    return shots


def scan_image_assets(shared_root, asset_type, existing_meta):
    """
    Escanea resources/{asset_type}/*.png (nivel compartido, excluyendo previews/).
    Reutiliza name/placement del meta existente si el filename coincide.
    Retorna lista de dicts con URIs sin prefijo de livery.
    """
    root = os.path.join(shared_root, asset_type)
    previews_dir = os.path.join(root, "previews")
    if not os.path.isdir(root):
        return []

    # Mapa filename→{name,placement} del meta conocido (kamon/kanji en nivel compartido)
    known = {}
    for item in existing_meta.get("resources", {}).get(asset_type, []):
        key = os.path.basename(item.get("uri", ""))
        if key:
            known[key] = {"name": item.get("name", ""), "placement": item.get("placement", "")}

    result = []
    for fname in sorted(os.listdir(root)):
        full = os.path.join(root, fname)
        if not os.path.isfile(full) or not fname.lower().endswith(".png"):
            continue
        stem = os.path.splitext(fname)[0]
        meta_entry = known.get(fname, {})
        name      = meta_entry.get("name") or f"TODO: nombre de {stem}"
        placement = meta_entry.get("placement") or "TODO: ubicación"

        uri           = f"resources/{asset_type}/{fname}"
        preview_fname = f"{stem}_preview.png"
        preview_full  = os.path.join(previews_dir, preview_fname)
        preview       = f"resources/{asset_type}/previews/{preview_fname}" \
                        if os.path.isfile(preview_full) else None

        entry = {"name": name, "placement": placement, "uri": uri}
        if preview:
            entry["preview"] = preview
        result.append(entry)

    return result


_BLACK_COLOR = {
    "hex":        "#101820",
    "rgb":        "16, 24, 32",
    "hsv":        {"hue": 210, "saturation": 50, "value": 12.55},
    "cmyk":       "50.00%, 25.00%, 0.00%, 87.45%",
    "pantone":    "Black 6 C",
    "matte":      "Acabado mate",
    "matteLevel": "none",
}


def read_livery_json(livery_path):
    """Lee livery.json de la carpeta del livery. Devuelve dict o None si no existe."""
    path = os.path.join(livery_path, "livery.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def colors_from_livery_json(lj):
    """Construye meta.resources[key].colors a partir de livery.json."""
    hex_   = lj.get("hex", "#888888")
    rgb_v  = lj.get("rgb", [])
    hsv_v  = lj.get("hsv", [0, 0, 0])
    cmyk_v = lj.get("cmyk", [0, 0, 0, 0])

    rgb_str  = ", ".join(str(v) for v in rgb_v) if rgb_v else "—"
    cmyk_str = ", ".join(f"{x:.2f}%" for x in cmyk_v) if cmyk_v else "—"

    stripe = {
        "hex":        hex_,
        "rgb":        rgb_str,
        "hsv":        {"hue": hsv_v[0], "saturation": hsv_v[1], "value": hsv_v[2]} if len(hsv_v) == 3 else {},
        "cmyk":       cmyk_str,
        "pantone":    lj.get("pantone", "—"),
        "matte":      "Acabado satinado",
        "matteLevel": "medium",
    }

    return [
        {"name": "Racing stripe central", "role": "Franja longitudinal principal", **stripe},
        {"name": "Racing stripe lateral", "role": "Franja lateral",               **stripe},
        {"name": "Kanji", "role": "Grafía japonesa",                **_BLACK_COLOR},
        {"name": "Kamon", "role": "Emblemas laterales y maletero",  **_BLACK_COLOR},
    ]


def build_shot_view_map(items):
    """Extrae {shot: view} de los items existentes."""
    return {item["shot"]: item["view"] for item in items if "shot" in item and "view" in item}


def sort_key_for_shot(shot, shot_order):
    try:
        return shot_order.index(shot)
    except ValueError:
        return 10000


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    dry_run = "--dry-run" in sys.argv

    header, data, iife_tail = read_catalog_js(CATALOG_JS)

    meta       = data.get("meta", {})
    order      = meta.get("order", {})
    shot_order = order.get("shots", [])
    livery_order_existing = order.get("liveries", [])

    shot_view_map = build_shot_view_map(data.get("items", []))

    livery_dirs = scan_livery_dirs(LIVERIES_DIR)
    if not livery_dirs:
        print("⚠  No se encontraron subdirectorios en resources/. Nada que hacer.")
        return

    # Kamon y kanji son compartidos — se escanean una sola vez desde resources/
    kamon_shared = scan_image_assets(RESOURCES, "kamon", meta)
    kanji_shared = scan_image_assets(RESOURCES, "kanji", meta)

    new_items  = []
    new_livery_order = []
    warnings   = []

    for livery_key, livery_path in livery_dirs:
        shots      = scan_shots(livery_path)
        livery_json = read_livery_json(livery_path)

        # Construir items de este livery
        livery_items = []
        unknown_shots = []
        for shot in shots:
            view = shot_view_map.get(shot)
            if view is None:
                view = "desconocido"
                unknown_shots.append(shot)
            fname = f"{shot}.png"
            livery_items.append({
                "livery": livery_key,
                "view":   view,
                "shot":   shot,
                "uri":    f"resources/liveries/{livery_key}/{fname}",
            })

        # Ordenar por shot_order
        livery_items.sort(key=lambda x: sort_key_for_shot(x["shot"], shot_order))
        new_items.extend(livery_items)
        new_livery_order.append(livery_key)

        # ── meta.liveries ────────────────────────────────────────────────────
        if "liveries" not in meta:
            meta["liveries"] = {}
        existing_lm = meta["liveries"].get(livery_key, {})

        if livery_json:
            # livery.json es fuente de verdad para lo que define;
            # campos ausentes en el JSON caen back al valor existente en catalog-data.js
            lj_name = livery_json.get("livery", existing_lm.get("name", livery_key))
            meta["liveries"][livery_key] = {
                "name":  lj_name,
                "short": livery_json.get("short", existing_lm.get("short", lj_name)),
                "glyph": livery_json.get("glyph", existing_lm.get("glyph", "◆")),
                "hex":   livery_json.get("hex",   existing_lm.get("hex", "#888888")),
            }
        elif not existing_lm:
            # Nuevo livery sin livery.json → placeholder TODO
            meta["liveries"][livery_key] = {
                "name":  f"TODO: nombre del livery '{livery_key}'",
                "short": "TODO",
                "glyph": "TODO",
                "hex":   "#TODO",
            }
            warnings.append(
                f"⚠  Livery nuevo '{livery_key}' sin livery.json: "
                f"crea resources/{livery_key}/livery.json o rellena manualmente catalog-data.js"
            )

        # ── meta.resources ───────────────────────────────────────────────────
        if "resources" not in meta:
            meta["resources"] = {}
        existing_res    = meta["resources"].get(livery_key, {})
        existing_colors = existing_res.get("colors")

        if existing_colors:
            colors = existing_colors           # preservar colores ya definidos manualmente
        elif livery_json:
            colors = colors_from_livery_json(livery_json)
        else:
            colors = [{"name": "TODO", "role": "TODO", "hex": "#TODO"}]

        meta["resources"][livery_key] = {
            "intro":  existing_res.get("intro") or
                      (livery_json.get("intro", "") if livery_json else "") or
                      f"TODO: descripción del livery '{livery_key}'",
            "colors": colors,
        }

        # ── Log ──────────────────────────────────────────────────────────────
        has_todo = any("TODO" in str(v) for v in meta["liveries"].get(livery_key, {}).values())
        marker   = "⚠" if has_todo else "✓"
        unknown_info = f" [⚠ shots sin view: {', '.join(unknown_shots)}]" if unknown_shots else ""
        json_info    = "" if livery_json else " [sin livery.json]"
        print(f"{marker} Livery: {livery_key} → {len(livery_items)} shots, "
              f"{len(kamon_shared)} kamon, {len(kanji_shared)} kanji{json_info}{unknown_info}")

    # Assets compartidos — nivel raíz de resources, no por livery
    meta["resources"]["kamon"] = kamon_shared
    meta["resources"]["kanji"] = kanji_shared

    # Actualizar order.liveries preservando orden existente + nuevos al final
    seen = set()
    merged_order = []
    for k in livery_order_existing + new_livery_order:
        if k in [lk for lk, _ in livery_dirs] and k not in seen:
            merged_order.append(k)
            seen.add(k)
    order["liveries"] = merged_order
    meta["order"]     = order

    # Actualizar datos
    data["items"] = new_items
    data["meta"]  = meta

    # Warnings
    for w in warnings:
        print(w)

    write_catalog_js(CATALOG_JS, header, data, iife_tail, dry_run=dry_run)

    if not dry_run:
        print(f"✓ catalog-data.js actualizado ({len(new_items)} items, "
              f"{len(merged_order)} liveries)")


if __name__ == "__main__":
    main()
