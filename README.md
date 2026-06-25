# Catálogo de livery — Suzuki Swift Sport ZC33S

Catálogo visual estático de los diseños de vinilo (liveries) del Suzuki Swift Sport ZC33S. Muestra fotografías por vista y ángulo, especificaciones de color (HEX, RGB, HSV, CMYK, Pantone) y recursos de kamon y kanji.

Sin build system, sin backend, sin dependencias de Node. Solo HTML, CSS y JavaScript.

---

## Estructura del proyecto

```
.
├── index.html              # Página principal del catálogo
├── generate-catalog.py     # Script que genera assets/catalog-data.js
├── assets/
│   ├── main.js             # Lógica del catálogo (filtros, galería, recursos)
│   ├── styles.css          # Estilos
│   ├── favicon.svg
│   ├── favicon-32.png
│   └── catalog-data.js     # Generado — no se versiona (.gitignore)
└── resources/              # Assets locales — no se versionan (.gitignore)
    ├── liveries/
    │   └── <key>/          # Una carpeta por livery
    │       ├── livery.json
    │       └── *.png       # 15 shots obligatorios
    ├── kamon/
    │   ├── *.png
    │   └── previews/
    └── kanji/
        ├── *.png
        └── previews/
```

---

## Requisitos

- **Python 3** — solo para regenerar `catalog-data.js` al añadir o modificar liveries.
- Ningún requisito para visualizar el catálogo (cualquier navegador moderno).

---

## Añadir una nueva livery

1. Crear la carpeta `resources/liveries/<key>/` (el `<key>` es el identificador interno, sin espacios ni acentos, ej. `rojo`).

2. Añadir `livery.json` con esta estructura:

```json
{
    "livery": "Nombre visible",
    "glyph": "漢",
    "hex": "#RRGGBB",
    "rgb": [R, G, B],
    "hsv": [H, S, V],
    "cmyk": [C, M, Y, K],
    "pantone": "XXXX C"
}
```

| Campo | Descripción |
|-------|-------------|
| `livery` | Nombre que aparece en la UI |
| `glyph` | Kanji decorativo que identifica la livery |
| `hex` | Color principal en hexadecimal (`#RRGGBB`) |
| `rgb` | Valores RGB como array de enteros `[R, G, B]` |
| `hsv` | Valores HSV como array de floats `[H, S, V]` (H en grados, S y V en %) |
| `cmyk` | Valores CMYK como array de floats `[C, M, Y, K]` (en %) |
| `pantone` | Referencia Pantone |

3. Añadir los **15 PNGs obligatorios** (ver lista abajo).

4. Regenerar el catálogo:

```bash
python3 generate-catalog.py
```

Para previsualizar sin escribir el archivo:

```bash
python3 generate-catalog.py --dry-run
```

---

## Shots requeridos

Cada livery debe tener exactamente estos 15 archivos PNG en su carpeta:

```
frontal_centrado.png
tres_cuartos_delantero_izquierdo.png
tres_cuartos_delantero_derecho.png
perfil_completo_izquierdo.png
perfil_completo_izquierdo_ladeado.png
perfil_completo_derecho.png
perfil_completo_derecho_ladeado.png
tres_cuartos_trasero_izquierdo.png
tres_cuartos_trasero_derecho.png
cola_centrada.png
cenital_delantero.png
cenital_trasero.png
detalle_kanji_desenfocado.png
detalle_kanji_enfocado.png
detalle_llanta_delantera.png
```

El script valida la presencia de todos ellos antes de generar nada.

---

## Assets compartidos

Los kamon y kanji no pertenecen a ninguna livery concreta — son recursos globales:

- `resources/kamon/*.png` — emblemas laterales y de maletero
- `resources/kamon/previews/*_preview.png` — previsualización en contexto
- `resources/kanji/*.png` — grafías japonesas
- `resources/kanji/previews/*_preview.png`

El script los escanea automáticamente. Para añadir uno nuevo, basta con colocar el PNG en la carpeta correspondiente y (opcionalmente) su preview, luego regenerar.

---

## Servir el catálogo

**Opción A — Servidor HTTP (recomendado)**

Con Caddy, nginx, Apache o cualquier servidor estático apuntando a la raíz del proyecto. También funciona con el servidor de desarrollo de Python:

```bash
python3 -m http.server 8080
```

**Opción B — Doble clic**

Abrir `index.html` directamente desde el explorador de archivos (`file://`). Requiere que `assets/catalog-data.js` esté generado en disco.

---

## Archivos no versionados

Estos archivos son locales y están en `.gitignore`:

| Ruta | Motivo |
|------|--------|
| `resources/` | Imágenes y assets de gran tamaño, contenido dinámico |
| `assets/catalog-data.js` | Generado por el script; cada entorno lo regenera localmente |
