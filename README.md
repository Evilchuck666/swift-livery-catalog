# 🍋 Livery Catalogue — Suzuki Swift Sport ZC33S

![Platform](https://img.shields.io/badge/platform-Web-blue)
![HTML](https://img.shields.io/badge/HTML-5-blue)
![CSS](https://img.shields.io/badge/CSS-3-blue)
![JavaScript](https://img.shields.io/badge/JavaScript-ES2020-blue)
![Requires](https://img.shields.io/badge/requires-modern%20browser-blue)
[![License](https://img.shields.io/badge/license-GPLv3-green)](LICENSE)
[![Build and tests](https://github.com/Evilchuck666/swift-livery-catalog/actions/workflows/checks.yaml/badge.svg?branch=main)](https://github.com/Evilchuck666/swift-livery-catalog/actions/workflows/checks.yaml)

**Every angle, colour and resource of a Suzuki Swift Sport livery, in one page.**

A static visual catalogue of vinyl livery designs for the Suzuki Swift Sport ZC33S. Displays renders by angle and view, colour specifications (HEX, RGB, HSV, CMYK), kamon and kanji production resources, and 3D model assets.

No build system. No backend. No Node dependencies. Pure HTML, CSS and JavaScript.

🌐 **Website:** https://suifutoremon.es/

## ✨ Features

- Renders of each livery by angle and view, with a lightbox.
- Colour specifications in HEX, RGB, HSV and CMYK.
- Kamon and kanji production resources, with contextual previews.
- 3D model renders.
- Filters across the gallery and resources, and a ZIP download of the catalogue.
- An **About** tab loaded from versioned Markdown files.

## 🚀 Getting started

**Option A — HTTP server (recommended)**

Point Caddy, nginx, Apache or any static server at the project root. For quick local testing:

```bash
python3 -m http.server 8080
```

**Option B — Double-click**

Open `index.html` directly from the file manager (`file://`). The gallery and resources tabs work offline. The About tab and the catalogue ZIP download require HTTP and will not work over `file://`.

The image assets in `resources/` are not versioned, so a fresh clone shows an
empty catalogue until you add them and run the build script. See the
[technical guide](TECHNICAL_GUIDE.md) for the folder layout and build steps.

## 📋 Requirements

- **Python 3 + Pillow** — required only to regenerate thumbnails and `catalog-data.js`.

```bash
pip install Pillow
```

No requirements to view the catalogue — any modern browser works.

## 📚 Learn more

- [Technical guide](TECHNICAL_GUIDE.md): project structure, adding a livery,
  the build script, required shots, shared assets, the About tab, tests and
  unversioned files.

## ⚖️ License

Livery Catalogue is free software released under the **GNU General Public License v3.0** (GPL-3.0). See [LICENSE](LICENSE).
