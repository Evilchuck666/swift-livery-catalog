# Livery Catalogue — Suzuki Swift Sport ZC33S

A static visual catalogue of vinyl livery designs for the Suzuki Swift Sport ZC33S. Displays renders by angle and view, colour specifications (HEX, RGB, HSV, CMYK, Pantone), kamon and kanji production resources, and 3D model assets.

No build system. No backend. No Node dependencies. Pure HTML, CSS and JavaScript.

---

## Project structure

```
.
├── index.html              # Main catalogue page
├── assets/
│   ├── main.js             # Catalogue logic (gallery, filters, resources, lightbox)
│   ├── styles.css          # Styles
│   ├── fonts.css           # Web font declarations
│   ├── favicon.svg
│   ├── favicon-32.png
│   ├── catalog-data.js     # Generated — not versioned
│   └── jszip.min.js        # ZIP download library — not versioned
└── resources/              # Local assets — not versioned (except scripts/ and about/)
    ├── scripts/            # Versioned
    │   └── build-site.py   # Generates thumbnails and catalog-data.js
    ├── about/              # Versioned — content for the About tab
    │   ├── project.md      # "About the project" section
    │   └── me.md           # "About me" section
    ├── liveries/
    │   └── <key>/
    │       ├── livery.json
    │       └── *.png       # 16 required shots
    ├── kamon/
    │   ├── *.png
    │   └── previews/
    ├── kanji/
    │   ├── *.png
    │   └── previews/
    ├── 3d/                 # 3D model renders (PNG with alpha)
    └── fonts/              # Web font files (.ttf)
```

---

## Requirements

- **Python 3 + Pillow** — required only to regenerate thumbnails and `catalog-data.js`.

```bash
pip install Pillow
```

No requirements to view the catalogue — any modern browser works.

---

## Adding a new livery

1. Create the folder `resources/liveries/<key>/` (`<key>` is the internal identifier — no spaces or accents, e.g. `rojo`).

2. Add `livery.json`:

```json
{
    "livery": "Visible name",
    "glyph": "漢",
    "hex": "#RRGGBB",
    "rgb": [R, G, B],
    "hsv": [H, S, V],
    "cmyk": [C, M, Y, K],
    "pantone": "XXXX C"
}
```

| Field | Description |
|-------|-------------|
| `livery` | Name shown in the UI |
| `glyph` | Decorative kanji identifying the livery |
| `hex` | Main colour in hexadecimal (`#RRGGBB`) |
| `rgb` | RGB values as integer array `[R, G, B]` |
| `hsv` | HSV values as float array `[H, S, V]` (H in degrees, S and V in %) |
| `cmyk` | CMYK values as float array `[C, M, Y, K]` (in %) |
| `pantone` | Pantone reference |

3. Add the **16 required PNGs** (see list below).

4. Regenerate the catalogue:

```bash
python3 resources/scripts/build-site.py
```

---

## Build script

`resources/scripts/build-site.py` consolidates all build steps. Run without arguments to execute everything in order.

| Flag | Description |
|------|-------------|
| _(none)_ | Run all steps: thumbnails + catalogue |
| `--thumbs` | All thumbnails (equivalent to all `--thumbs-*` flags combined) |
| `--thumbs-livery` | WebP 1600×900 + 640×360 thumbnail for each livery PNG |
| `--thumbs-3d` | 360×360 square thumbnails for 3D renders (preserves alpha) |
| `--thumbs-kamon` | 360×360 square thumbnails for kamon (white background) |
| `--thumbs-kanji` | 360×360 square thumbnails for kanji (white background) |
| `--catalog` | Generate `assets/catalog-data.js` |
| `--dry-run` | With `--catalog`: print output without writing the file |

Examples:

```bash
python3 resources/scripts/build-site.py                        # Everything
python3 resources/scripts/build-site.py --catalog              # Catalog only
python3 resources/scripts/build-site.py --catalog --dry-run    # Preview catalog
python3 resources/scripts/build-site.py --thumbs-livery        # Livery thumbnails only
python3 resources/scripts/build-site.py --thumbs --catalog     # Thumbnails + catalog
```

Thumbnail images always overwrite existing files. The `--dry-run` flag only applies to `--catalog`.

---

## Required shots

Each livery must have exactly these 16 PNG files in its folder:

```
car_000_front.png
car_216_rear_left.png
car_252_left_rear.png
car_288_left_front.png
car_324_front_left.png
car_036_front_right.png
car_072_right_front.png
car_108_right_rear.png
car_144_rear_right.png
car_180_rear.png
car_detail_front_left.png
car_detail_front_right.png
car_detail_kanji_unfocused.png
car_detail_kanji_focused.png
car_picado_front.png
car_picado_rear.png
```

The script validates all 16 are present before generating anything.

---

## Shared assets

Kamon, kanji and 3D renders are not tied to any specific livery — they are global resources:

- `resources/kamon/*.png` — side and tailgate emblems
- `resources/kamon/previews/*_preview.png` — contextual previews
- `resources/kanji/*.png` — Japanese lettering
- `resources/kanji/previews/*_preview.png`
- `resources/3d/*.png` — 3D model renders with alpha channel

The script scans these folders automatically. To add a new asset, place the PNG in the corresponding folder (and optionally a preview), then regenerate.

---

## About tab content

The **About** tab content is versioned and loaded at runtime via `fetch()`:

- `resources/about/project.md` — "About the project" section
- `resources/about/me.md` — "About me" section

Both files support a limited Markdown subset: headings (`##`, `###`), **bold**, *italic*, unordered lists (`-`), and links.

> **Note:** The About tab requires an HTTP server to load these files. It will not work when opening `index.html` directly via `file://`.

---

## Serving the catalogue

**Option A — HTTP server (recommended)**

Point Caddy, nginx, Apache or any static server at the project root. For quick local testing:

```bash
python3 -m http.server 8080
```

**Option B — Double-click**

Open `index.html` directly from the file manager (`file://`). The gallery and resources tabs work offline. The About tab and the catalogue ZIP download require HTTP and will not work over `file://`.

---

## Unversioned files

| Path | Reason |
|------|--------|
| `resources/liveries/` | Large image assets, environment-specific |
| `resources/kamon/` | Large image assets |
| `resources/kanji/` | Large image assets |
| `resources/3d/` | Large image assets |
| `resources/fonts/` | Font files referenced by `assets/fonts.css` |
| `assets/catalog-data.js` | Generated by the script; each environment regenerates it locally |
| `assets/jszip.min.js` | Third-party library for the ZIP download feature |

`resources/scripts/` and `resources/about/` **are versioned**.
