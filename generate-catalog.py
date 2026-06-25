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
CATALOG_JS  = os.path.join(SCRIPT_DIR, "assets", "catalog-data.js")
RESOURCES   = os.path.join(SCRIPT_DIR, "resources")

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
        if os.path.isdir(os.path.join(resources_root, e))
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


def scan_image_assets(subdir_path, livery_key, asset_type, existing_meta):
    """
    Escanea resources/{livery}/{asset_type}/*.png (excluyendo previews/).
    Reutiliza name/placement del meta existente si el filename coincide.
    Retorna lista de dicts.
    """
    root = os.path.join(subdir_path, asset_type)
    previews_dir = os.path.join(root, "previews")
    if not os.path.isdir(root):
        return []

    # Mapa filename→{name,placement} del meta conocido
    known = {}
    for ref_livery, ref_data in existing_meta.get("resources", {}).items():
        for item in ref_data.get(asset_type, []):
            key = item.get("filename") or os.path.basename(item.get("uri", ""))
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

        uri     = f"resources/{livery_key}/{asset_type}/{fname}"
        preview_fname = f"{stem}_preview.png"
        preview_full  = os.path.join(previews_dir, preview_fname)
        preview = f"resources/{livery_key}/{asset_type}/previews/{preview_fname}" \
                  if os.path.isfile(preview_full) else None

        entry = {"name": name, "placement": placement, "uri": uri, "filename": fname}
        if preview:
            entry["preview"] = preview
        result.append(entry)

    return result


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

    livery_dirs = scan_livery_dirs(RESOURCES)
    if not livery_dirs:
        print("⚠  No se encontraron subdirectorios en resources/. Nada que hacer.")
        return

    new_items  = []
    new_livery_order = []
    warnings   = []

    for livery_key, livery_path in livery_dirs:
        shots = scan_shots(livery_path)
        kamon = scan_image_assets(livery_path, livery_key, "kamon", meta)
        kanji = scan_image_assets(livery_path, livery_key, "kanji", meta)

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
                "livery":   livery_key,
                "view":     view,
                "shot":     shot,
                "uri":      f"resources/{livery_key}/{fname}",
                "filename": fname,
                "route":    f"resources/{livery_key}/{fname}",
                "source":   f"resources/{livery_key}/{fname}",
            })

        # Ordenar por shot_order
        livery_items.sort(key=lambda x: sort_key_for_shot(x["shot"], shot_order))
        new_items.extend(livery_items)
        new_livery_order.append(livery_key)

        # Actualizar meta.liveries si es nuevo
        if "liveries" not in meta:
            meta["liveries"] = {}
        if livery_key not in meta["liveries"]:
            meta["liveries"][livery_key] = {
                "name":  f"TODO: nombre del livery '{livery_key}'",
                "short": "TODO",
                "glyph": "TODO",
                "hex":   "#TODO",
                "label": f"TODO: descripción del livery '{livery_key}'"
            }
            warnings.append(
                f"⚠  Livery nuevo '{livery_key}': rellena meta.liveries[\"{livery_key}\"] "
                f"y meta.resources[\"{livery_key}\"].colors en catalog-data.js"
            )

        # Actualizar meta.resources para este livery
        if "resources" not in meta:
            meta["resources"] = {}
        existing_res = meta["resources"].get(livery_key, {})
        meta["resources"][livery_key] = {
            "intro":  existing_res.get("intro") or f"TODO: descripción del livery '{livery_key}'",
            "colors": existing_res.get("colors") or [{"name": "TODO", "role": "TODO", "hex": "#TODO"}],
            "kamon":  kamon,
            "kanji":  kanji,
        }

        # Log
        status = "✓" if livery_key in [x for x, _ in livery_dirs if x in meta.get("liveries", {})] else "⚠"
        has_todo = livery_key in warnings or any("TODO" in str(v) for v in meta["liveries"].get(livery_key, {}).values())
        marker = "⚠" if has_todo else "✓"
        unknown_info = f" [⚠ shots sin view: {', '.join(unknown_shots)}]" if unknown_shots else ""
        print(f"{marker} Livery: {livery_key} → {len(livery_items)} shots, "
              f"{len(kamon)} kamon, {len(kanji)} kanji{unknown_info}")

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
    data["total"] = len(new_items)
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
