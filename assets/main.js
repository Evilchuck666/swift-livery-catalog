(() => {
  "use strict";

  const payload = window.CATALOG_DATA || {};
  const DATA = payload.items || [];
  const META = payload.meta || {};
  const ORDER = META.order || {};
  const LIVERIES_META = META.liveries || {};

  const byId = id => document.getElementById(id);

  const humanize = value => String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, ch => ch.toUpperCase()) || "Sin nombre";

  const createText = (tag, className, value) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = value;
    return el;
  };

  const setText = (id, value) => {
    const el = byId(id);
    if (el) el.textContent = value;
  };

  const createDownloadLink = (uri, extraClass = "") => {
    const link = document.createElement("a");
    link.className = extraClass ? `resource-link ${extraClass}` : "resource-link";
    link.href = uri || "#";
    link.download = (uri || "").split("/").pop();
    link.rel = "noopener";
    link.title = "Descargar PNG";
    link.textContent = "⬇";
    return link;
  };

  const metaFor = (group, key, fallback = {}) => ({
    ...fallback,
    ...((META[group] && META[group][key]) || {})
  });

  const orderedKeys = (values, preferred = []) => {
    const unique = new Set(values.filter(Boolean));
    const ordered = preferred.filter(key => unique.has(key));

    Array.from(unique).sort().forEach(key => {
      if (!ordered.includes(key)) ordered.push(key);
    });

    return ordered;
  };

  const orderIndex = (list, key) => {
    const index = list.indexOf(key);
    return index === -1 ? 10000 : index;
  };

  const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const isDarkColor = hex => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return (0.299 * r + 0.587 * g + 0.114 * b) < 128;
  };

  const revealElements = (scope = document) => {
    const items = scope.querySelectorAll(".reveal");

    if (!("IntersectionObserver" in window) || prefersReducedMotion()) {
      items.forEach(el => el.classList.add("in"));
      return;
    }

    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("in");
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });

    items.forEach(el => observer.observe(el));
  };

  const views = orderedKeys(DATA.map(item => item.view), ORDER.views || []);
  const liveries = orderedKeys(DATA.map(item => item.livery), ORDER.liveries || []);
  const shots = ORDER.shots || [];

  let activeView = "all";
  let lastFocus = null;
  let lightboxItems = [];
  let lightboxIndex = 0;

  const cards = [];
  const gallery = byId("gallery");
  const lightbox = byId("lb");
  const lightboxImg = byId("lbImg");

  const labelFor = item => {
    const view = metaFor("views", item.view, {
      name: humanize(item.view),
      glyph: "◆",
      sub: "Vista"
    });
    const shot = metaFor("shots", item.shot, {
      name: humanize(item.shot)
    });
    const livery = LIVERIES_META[item.livery] || {
      name: humanize(item.livery),
      short: humanize(item.livery),
      glyph: "◆",
      hex: "#888888"
    };

    return { view, shot, livery };
  };

  const currentPanel = () => {
    const resourcesPanel = byId("resourcesPanel");
    return resourcesPanel && !resourcesPanel.hidden ? resourcesPanel : byId("galleryPanel");
  };

  const scrollToPanelTop = () => {
    const behavior = prefersReducedMotion() ? "auto" : "smooth";
    currentPanel()?.scrollTo({ top: 0, left: 0, behavior });
    window.scrollTo({ top: 0, left: 0, behavior });
  };

  const setTab = tab => {
    const isResources = tab === "resources";

    document.querySelectorAll(".tab-button").forEach(button => {
      const isActive = button.dataset.tab === tab;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
      button.tabIndex = isActive ? 0 : -1;
    });

    document.querySelectorAll(".gallery-only").forEach(el => {
      el.classList.toggle("is-hidden-tab", isResources);
      el.hidden = isResources;
    });

    const resourcesPanel = byId("resourcesPanel");
    if (resourcesPanel) {
      resourcesPanel.classList.toggle("is-hidden-tab", !isResources);
      resourcesPanel.hidden = !isResources;
    }

    byId("top")?.classList.toggle("is-resources", isResources);
    const sidebarToggle = byId("sidebarToggle");
    if (sidebarToggle) sidebarToggle.classList.toggle("is-res-hidden", isResources);

    currentPanel()?.querySelectorAll(".reveal").forEach(el => el.classList.add("in"));
    scrollToPanelTop();
  };

  const createChip = (label, glyph, pressed) => {
    const button = document.createElement("button");
    button.className = "chip";
    button.type = "button";
    button.setAttribute("aria-pressed", pressed ? "true" : "false");

    if (glyph) button.append(createText("span", "jp", glyph));
    button.append(document.createTextNode(label));

    return button;
  };

  const syncPressed = (container, key) => {
    container?.querySelectorAll(".chip").forEach(chip => {
      chip.setAttribute("aria-pressed", chip.dataset.key === key ? "true" : "false");
    });
  };

  const renderFilterChips = () => {
    const viewChips = byId("viewChips");

    if (viewChips) {
      const allViews = createChip("Todas", "全", true);
      allViews.dataset.key = "all";
      allViews.addEventListener("click", () => {
        activeView = "all";
        syncPressed(viewChips, activeView);
        applyFilters();
      });
      viewChips.append(allViews);

      views.forEach(key => {
        const meta = metaFor("views", key, { name: humanize(key), glyph: "◆" });
        const button = createChip(meta.name, meta.glyph, false);
        button.dataset.key = key;
        button.addEventListener("click", () => {
          activeView = key;
          syncPressed(viewChips, activeView);
          applyFilters();
        });
        viewChips.append(button);
      });
    }
  };

  const renderGallery = () => {
    if (!gallery) return;

    views.forEach((viewKey, viewIndex) => {
      const items = DATA
        .filter(item => item.view === viewKey)
        .sort((a, b) =>
          orderIndex(shots, a.shot) - orderIndex(shots, b.shot)
          || a.uri.localeCompare(b.uri)
        );

      if (!items.length) return;

      const viewMeta = metaFor("views", viewKey, {
        name: humanize(viewKey),
        glyph: "◆",
        sub: "Vista"
      });

      const section = document.createElement("section");
      section.className = "vsec";
      section.dataset.view = viewKey;
      section.id = `v-${viewKey}`;

      const head = document.createElement("div");
      head.className = "dhead";

      const glyph = createText("div", "dhead__glyph", viewMeta.glyph || "◆");
      glyph.setAttribute("aria-hidden", "true");
      head.append(glyph);

      const body = document.createElement("div");
      body.className = "dhead__body";

      const eyebrow = document.createElement("div");
      eyebrow.className = "dhead__eyebrow";
      eyebrow.append(createText("span", "num", String(viewIndex + 1).padStart(2, "0")));
      eyebrow.append(document.createTextNode(" Vista"));
      body.append(eyebrow);

      body.append(createText("h2", "", viewMeta.name));

      const metaLine = document.createElement("div");
      metaLine.className = "dhead__meta";
      metaLine.append(document.createTextNode(`${viewMeta.sub || "Vista"} · `));

      const countLabel = items.length > 1 ? " imágenes" : " imagen";
      const strong = document.createElement("b");
      strong.append(createText("span", "cnt", items.length));
      strong.append(document.createTextNode(countLabel));
      metaLine.append(strong);
      body.append(metaLine);

      head.append(body);
      section.append(head);

      const rule = document.createElement("div");
      rule.className = "pinstripe";
      section.append(rule);

      const grid = document.createElement("div");
      grid.className = "grid";

      items.forEach(item => {
        const { view, shot, livery } = labelFor(item);
        const card = document.createElement("button");
        card.className = "card reveal";
        card.type = "button";
        card.dataset.view = item.view;
        card.dataset.shot = item.shot;
        card.dataset.livery = item.livery || "";
        card.setAttribute("aria-label", `Ampliar ${view.name} · ${shot.name}`);

        const imageWrap = document.createElement("div");
        imageWrap.className = "card__img";

        const image = document.createElement("img");
        image.loading = "lazy";
        image.decoding = "async";
        image.src = item.preview || item.uri;
        image.alt = `Suzuki Swift Sport ZC33S, vista ${view.name.toLowerCase()}, toma ${shot.name.toLowerCase()}.`;
        imageWrap.append(image);
        card.append(imageWrap);

        const caption = document.createElement("div");
        caption.className = "card__cap";

        caption.append(createText("span", "tag tag--view", shot.name));

        if (liveries.length > 1 && item.livery) {
          const tag = createText("span", "tag tag--livery", livery.short || livery.name);
          tag.style.setProperty("--livery-tag-color", livery.hex || "#888888");
          caption.append(tag);
        }

        card.append(caption);
        card.addEventListener("click", () => openLightbox(item));

        const wrap = document.createElement("div");
        wrap.className = "card-wrap";
        wrap.append(card);

        wrap.append(createDownloadLink(item.uri, "card-download"));

        grid.append(wrap);
        cards.push({ el: card, view: item.view, livery: item.livery || "", item });
      });

      section.append(grid);
      gallery.append(section);
    });
  };

  const specRow = (label, value, extraClass = "") => {
    const row = document.createElement("div");
    row.className = `spec-row ${extraClass}`.trim();
    row.append(createText("dt", "spec-row__label", label));
    row.append(createText("dd", "spec-row__value", value));
    return row;
  };

  const sectionHead = (title, subtitle) => {
    const head = document.createElement("div");
    head.className = "resource-head";
    head.append(createText("p", "eyebrow", "Recursos"));
    head.append(createText("h2", "", title));
    head.append(createText("p", "section-subtitle", subtitle));
    return head;
  };

  const finishBadge = item => {
    if (!item.matte) return null;
    const level = item.matteLevel || "none";
    return createText("span", `finish-badge finish-badge--${level}`, item.matte);
  };

  const resolveResources = () => {
    const resources = META.resources || {};
    const sharedKamon = resources.kamon || [];
    const sharedKanji = resources.kanji || [];
    const sharedModels3D = resources.models_3d || [];

    const merged = liveries.reduce((acc, key) => {
      const current = resources[key] || {};
      if (!acc.intro && current.intro) acc.intro = current.intro;
      acc.colors.push(...(current.colors || []));
      return acc;
    }, { intro: "", colors: [], kamon: sharedKamon, kanji: sharedKanji, models_3d: sharedModels3D });

    const counts = new Map();
    merged.colors.forEach(c => {
      const id = `${c.name}|${c.hex}`;
      counts.set(id, (counts.get(id) || 0) + 1);
    });

    const seen = new Set();
    const perLivery = [], shared = [];
    for (const c of merged.colors) {
      const id = `${c.name}|${c.hex}`;
      if (seen.has(id)) continue;
      seen.add(id);
      (counts.get(id) > 1 ? shared : perLivery).push(c);
    }
    merged.colors = [...perLivery, ...shared];
    return merged;
  };

  const renderColorResources = (root, resources) => {
    const section = document.createElement("section");
    section.className = "resource-section";
    section.append(sectionHead("Colores", "Códigos técnicos listos para rotulación y referencia visual."));

    const grid = document.createElement("div");
    grid.className = "resource-grid resource-grid--colors";

    (resources.colors || []).forEach(item => {
      const card = document.createElement("article");
      card.className = "resource-card color-card reveal";
      const hsv = item.hsv || {};
      const hsvStr = (hsv.hue != null)
        ? `${Number(hsv.hue).toFixed(2)}°, ${Number(hsv.saturation).toFixed(2)}%, ${Number(hsv.value).toFixed(2)}%`
        : "—";
      card.style.setProperty("--swatch", item.hex || "#888888");
      card.style.setProperty("--wheel-hue", `${Number(hsv.hue || 0)}deg`);
      card.style.setProperty("--wheel-hue-pct", ((Number(hsv.hue || 0) / 360) * 100).toFixed(2));
      card.style.setProperty("--wheel-sat", Number(hsv.saturation ?? 100));
      card.style.setProperty("--wheel-val", Number(hsv.value ?? 100));

      const visual = document.createElement("div");
      visual.className = "color-card__visual";

      const wheel = document.createElement("div");
      wheel.className = "color-wheel";
      wheel.setAttribute("aria-label", `Mapa HSV: ${hsvStr}`);
      visual.append(wheel);

      const hueStrip = document.createElement("div");
      hueStrip.className = "hue-strip";
      hueStrip.setAttribute("aria-label", `Tono: ${Math.round(hsv.hue || 0)}°`);
      visual.append(hueStrip);

      const swatch = document.createElement("div");
      swatch.className = "swatch";
      swatch.setAttribute("aria-label", `Muestra de color ${item.hex || "sin valor"}`);
      visual.append(swatch);
      card.append(visual);

      const body = document.createElement("div");
      body.className = "resource-card__body";
      body.append(createText("p", "resource-card__role", item.role || "Recurso"));
      body.append(createText("h3", "", item.name || "Recurso de color"));

      const specs = document.createElement("dl");
      specs.className = "spec-grid";
      specs.append(specRow("HEX", item.hex || "—", "spec-row--hex"));
      specs.append(specRow("RGB", item.rgb || "—"));
      specs.append(specRow("HSV", hsvStr));
      specs.append(specRow("CMYK", item.cmyk || "—"));
      specs.append(specRow("Pantone", item.pantone || "—"));
      body.append(specs);

      const badge = finishBadge(item);
      if (badge) {
        const finishes = document.createElement("div");
        finishes.className = "finish-list";
        finishes.append(badge);
        body.append(finishes);
      }

      card.append(body);
      grid.append(card);
    });

    section.append(grid);
    root.append(section);
  };

  const renderImageResources = (root, resources, config) => {
    const section = document.createElement("section");
    section.className = "resource-section";
    section.append(sectionHead(config.title, config.subtitle));

    const grid = document.createElement("div");
    grid.className = `resource-grid ${config.gridClass}`;

    (resources[config.key] || []).forEach(item => {
      const card = document.createElement("article");
      card.className = `resource-card ${config.cardClass} reveal`;

      const frame = document.createElement("div");
      frame.className = `${config.cardClass}__frame`;

      const image = document.createElement("img");
      image.loading = "lazy";
      image.decoding = "async";
      image.src = item.preview || item.uri;
      image.alt = `${item.name || config.fallbackName} · ${item.placement || "ubicación"}`;
      image.addEventListener("error", () => {
        if (item.uri && image.src !== item.uri) image.src = item.uri;
      }, { once: true });
      frame.append(image);
      card.append(frame);

      const body = document.createElement("div");
      body.className = "resource-card__body";
      body.append(createText("p", "resource-card__role", item.placement || config.fallbackName));

      const titleRow = document.createElement("div");
      titleRow.className = "resource-card__title-row";
      titleRow.append(createText("h3", "", item.name || config.fallbackName));

      titleRow.append(createDownloadLink(item.uri));
      body.append(titleRow);

      body.append(createText("p", "file-path", item.uri || ""));

      card.append(body);
      grid.append(card);
    });

    section.append(grid);
    root.append(section);
  };

  const FONT_URI = "resources/fonts/YujiSyuku-Regular.ttf";

  const renderFontResources = (root) => {
    const section = document.createElement("section");
    section.className = "resource-section";
    section.append(sectionHead("Tipografía", "Fuente usada para generar los kanji San y Gatsu."));

    const grid = document.createElement("div");
    grid.className = "resource-grid resource-grid--font";

    const card = document.createElement("article");
    card.className = "resource-card font-card reveal";

    const frame = document.createElement("div");
    frame.className = "font-card__frame";
    frame.append(createText("span", "font-card__preview", "三月"));
    card.append(frame);

    const body = document.createElement("div");
    body.className = "resource-card__body";
    body.append(createText("p", "resource-card__role", "Kanji San · Gatsu"));

    const titleRow = document.createElement("div");
    titleRow.className = "resource-card__title-row";
    titleRow.append(createText("h3", "", "Yuji Syuku"));
    const dl = createDownloadLink(FONT_URI);
    dl.title = "Descargar TTF";
    titleRow.append(dl);
    body.append(titleRow);
    body.append(createText("p", "file-path", FONT_URI));

    card.append(body);
    grid.append(card);

    for (let i = 0; i < 2; i++) {
      const ghost = document.createElement("div");
      ghost.className = "resource-card resource-card--ghost";
      ghost.setAttribute("aria-hidden", "true");
      grid.append(ghost);
    }

    section.append(grid);
    root.append(section);
  };

  const render3DModelResources = (root, resources) => {
    if (!(resources.models_3d || []).length) return;
    const section = document.createElement("section");
    section.className = "resource-section";
    section.append(sectionHead("Modelos 3D", "Archivos Blender para importar y editar el coche y el entorno."));

    const grid = document.createElement("div");
    grid.className = "resource-grid resource-grid--3d";

    (resources.models_3d || []).forEach(item => {
      const card = document.createElement("article");
      card.className = "resource-card model-3d-card reveal";

      const frame = document.createElement("div");
      frame.className = "model-3d-card__frame";
      if (item.preview) {
        const img = document.createElement("img");
        img.src = item.preview;
        img.alt = item.name || "Modelo 3D";
        img.loading = "lazy";
        frame.append(img);
      } else {
        frame.append(createText("span", "model-3d-card__placeholder", "3D"));
      }
      card.append(frame);

      const body = document.createElement("div");
      body.className = "resource-card__body";
      body.append(createText("p", "resource-card__role", item.role || "Modelo 3D"));

      const titleRow = document.createElement("div");
      titleRow.className = "resource-card__title-row";
      titleRow.append(createText("h3", "", item.name || "Modelo 3D"));
      const dl = createDownloadLink(item.uri);
      dl.title = "Descargar Blend";
      titleRow.append(dl);
      body.append(titleRow);
      body.append(createText("p", "file-path", item.uri || ""));
      card.append(body);

      grid.append(card);
    });

    section.append(grid);
    root.append(section);
  };

  const renderResources = () => {
    const root = byId("resourcesRoot");
    if (!root) return;

    root.innerHTML = "";

    const resources = resolveResources();

    const intro = document.createElement("section");
    intro.className = "resource-hero";

    const eyebrow = createText("p", "hero__eyebrow eyebrow", "");
    eyebrow.append(createText("span", "", ""));
    eyebrow.append(document.createTextNode(`Suzuki Swift Sport ZC33S · Recursos de producción`));
    intro.append(eyebrow);

    const title = document.createElement("h1");
    title.append(document.createTextNode("Especificaciones "));
    title.append(createText("span", "y", "del diseño"));
    intro.append(title);

    intro.append(createText("p", "", "Colores y acabados para los vinilos principales del Suzuki Swift Sport ZC33S."));
    root.append(intro);

    renderColorResources(root, resources);
    
    renderImageResources(root, resources, {
      key: "kamon",
      title: "Kamon",
      subtitle: "Emblemas PNG incluidos en la carpeta local 'resources/kamon/'.",
      cardClass: "kamon-card",
      gridClass: "resource-grid--kamon",
      fallbackName: "Kamon"
    });

    renderImageResources(root, resources, {
      key: "kanji",
      title: "Kanji",
      subtitle: "Grafías PNG incluidas en la carpeta local 'resources/kanji/'.",
      cardClass: "kanji-card",
      gridClass: "resource-grid--kanji",
      fallbackName: "Kanji"
    });

    const kanjiGrid = root.querySelector(".resource-grid--kanji");
    if (kanjiGrid) {
      for (let i = 0; i < 1; i++) {
        const ghost = document.createElement("div");
        ghost.className = "resource-card resource-card--ghost";
        ghost.setAttribute("aria-hidden", "true");
        kanjiGrid.append(ghost);
      }
    }

    renderFontResources(root);
    render3DModelResources(root, resources);

    revealElements(root);
  };

  const applyFilters = () => {
    let shown = 0;

    cards.forEach(card => {
      const isVisible = activeView === "all" || card.view === activeView;
      card.el.classList.toggle("is-hidden", !isVisible);
      if (isVisible) shown += 1;
    });

    document.querySelectorAll(".vsec").forEach(section => {
      const viewKey = section.dataset.view;
      const viewMatches = activeView === "all" || activeView === viewKey;
      const visibleCards = section.querySelectorAll(".card:not(.is-hidden)").length;
      section.classList.toggle("is-hidden", !viewMatches || visibleCards === 0);

      const count = section.querySelector(".cnt");
      if (count) count.textContent = visibleCards;
    });

    setText("count", shown);
    byId("empty")?.classList.toggle("is-on", shown === 0);
  };

  const visibleItems = () => cards
    .filter(card => !card.el.classList.contains("is-hidden"))
    .map(card => card.item);

  const renderLightbox = () => {
    const item = lightboxItems[lightboxIndex];
    if (!item || !lightboxImg) return;

    const { view, shot } = labelFor(item);
    lightboxImg.src = item.webp || item.uri;
    lightboxImg.alt = `Suzuki Swift Sport ZC33S, vista ${view.name.toLowerCase()}, toma ${shot.name.toLowerCase()}.`;
    setText("lbGlyph", view.glyph || "◆");
    setText("lbName", shot.name);
    setText("lbSub", view.name);
    setText("lbCur", lightboxIndex + 1);
    setText("lbTot", lightboxItems.length);
    const lbDownload = byId("lbDownload");
    if (lbDownload && item.uri) {
      lbDownload.href = item.uri;
      lbDownload.download = item.uri.split("/").pop();
    }
  };

  function openLightbox(item) {
    if (!lightbox) return;

    lightboxItems = visibleItems();
    lightboxIndex = Math.max(0, lightboxItems.findIndex(candidate => candidate === item));
    lastFocus = document.activeElement;
    renderLightbox();
    lightbox.classList.add("is-open");
    document.body.classList.add("lb-open");
    byId("lbClose")?.focus();
  }

  const closeLightbox = () => {
    if (!lightbox) return;

    lightbox.classList.remove("is-open");
    document.body.classList.remove("lb-open");
    if (lastFocus?.focus) lastFocus.focus();
  };

  const stepLightbox = direction => {
    if (!lightboxItems.length) return;
    lightboxIndex = (lightboxIndex + direction + lightboxItems.length) % lightboxItems.length;
    renderLightbox();
  };

  const setupTabs = () => {
    document.querySelectorAll(".tab-button").forEach(button => {
      button.addEventListener("click", () => setTab(button.dataset.tab || "gallery"));
      button.addEventListener("keydown", event => {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();

        const next = button.dataset.tab === "gallery" ? "resources" : "gallery";
        document.querySelector(`.tab-button[data-tab="${next}"]`)?.focus();
        setTab(next);
      });
    });

    document.querySelector(".brand")?.addEventListener("click", event => {
      event.preventDefault();
      setTab("gallery");
    });
  };

  const setupSidebar = () => {
    const toggle = byId("sidebarToggle");
    const page = byId("top");
    if (!toggle || !page) return;

    if (window.innerWidth < 981) {
      page.classList.add("sidebar-collapsed");
      toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", () => {
      const collapsed = page.classList.toggle("sidebar-collapsed");
      toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
    });
  };

  const setupLightbox = () => {
    byId("lbClose")?.addEventListener("click", closeLightbox);
    byId("lbPrev")?.addEventListener("click", () => stepLightbox(-1));
    byId("lbNext")?.addEventListener("click", () => stepLightbox(1));

    lightbox?.addEventListener("click", event => {
      if (event.target === lightbox) closeLightbox();
    });

    document.addEventListener("keydown", event => {
      if (!lightbox?.classList.contains("is-open")) return;

      if (event.key === "Escape") closeLightbox();
      if (event.key === "ArrowLeft") stepLightbox(-1);
      if (event.key === "ArrowRight") stepLightbox(1);
    });
  };

  const setupScrollTop = () => {
    const btn = byId("scrollTop");
    if (!btn) return;

    const toggle = () => {
      btn.hidden = false;
      btn.classList.toggle("is-visible", window.scrollY >= 1000);
    };

    window.addEventListener("scroll", toggle, { passive: true });
    btn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" });
    });
  };

  const setupDownloadSite = () => {
    const btn = byId("siteDownload");
    if (!btn) return;

    if (location.protocol === "file:") {
      btn.hidden = true;
      return;
    }

    let jszipLoaded = false;

    const dlDialog = byId("dlDialog");
    const dlCheck  = byId("dlBlendCheck");
    const dlWarn   = byId("dlBlendWarn");

    dlCheck?.addEventListener("change", function () {
      if (dlWarn) dlWarn.hidden = !this.checked;
    });

    btn.addEventListener("click", async () => {
      // Reset and show confirmation dialog
      if (dlCheck) dlCheck.checked = false;
      if (dlWarn) dlWarn.hidden = true;
      if (dlDialog) dlDialog.returnValue = "";

      const confirmed = await new Promise(resolve => {
        if (!dlDialog) { resolve(true); return; }
        dlDialog.showModal();
        dlDialog.addEventListener("close", () => resolve(dlDialog.returnValue === "confirm"), { once: true });
      });

      if (!confirmed) return;

      const includeBlend = dlCheck?.checked ?? false;

      btn.disabled = true;
      const originalLabel = btn.getAttribute("aria-label");
      btn.setAttribute("aria-label", "Preparando...");

      try {
        if (!jszipLoaded) {
          await new Promise((resolve, reject) => {
            const s = document.createElement("script");
            s.src = "assets/jszip.min.js";
            s.onload = () => { jszipLoaded = true; resolve(); };
            s.onerror = reject;
            document.head.append(s);
          });
        }

        const zip = new JSZip();

        const staticFiles = [
          "index.html",
          "assets/fonts.css",
          "assets/styles.css",
          "assets/main.js",
          "assets/catalog-data.js",
          "assets/jszip.min.js",
          "assets/favicon.svg",
          "assets/favicon-32.png",
          "resources/fonts/1Ptgg87LROyAm0K0.ttf",
          "resources/fonts/-F6jfjtqLzI2JPCgQBnw7HFyzSD-AsregP8VFCMj75s.ttf",
          "resources/fonts/-F6jfjtqLzI2JPCgQBnw7HFyzSD-AsregP8VFLgk75s.ttf",
          "resources/fonts/-F6jfjtqLzI2JPCgQBnw7HFyzSD-AsregP8VFPYk75s.ttf",
          "resources/fonts/k3k6o8UDI-1M0wlSV9XAw6lQkqWY8Q82sJaRE-NWIDdgffTT0zRp8A.ttf",
          "resources/fonts/k3k6o8UDI-1M0wlSV9XAw6lQkqWY8Q82sJaRE-NWIDdgffTT6jRp8A.ttf",
          "resources/fonts/k3k6o8UDI-1M0wlSV9XAw6lQkqWY8Q82sJaRE-NWIDdgffTTBjNp8A.ttf",
          "resources/fonts/k3k6o8UDI-1M0wlSV9XAw6lQkqWY8Q82sJaRE-NWIDdgffTTNDNp8A.ttf",
          "resources/fonts/k3k6o8UDI-1M0wlSV9XAw6lQkqWY8Q82sJaRE-NWIDdgffTTtDRp8A.ttf",
          "resources/fonts/YujiSyuku-Regular.ttf",
        ];

        const imageUris = new Set();
        DATA.forEach(item => { if (item.uri) imageUris.add(item.uri); });
        const res = META.resources || {};
        const addFromArray = arr => (arr || []).forEach(item => {
          if (item?.uri)     imageUris.add(item.uri);
          if (item?.preview) imageUris.add(item.preview);
        });
        addFromArray(res.kamon);
        addFromArray(res.kanji);
        liveries.forEach(key => {
          const r = res[key] || {};
          addFromArray(r.kamon);
          addFromArray(r.kanji);
          addFromArray(r.colors);
        });

        // Directorio 3d completo (previews + .blend) solo si el usuario lo pidió
        if (includeBlend) {
          (res.models_3d || []).forEach(item => {
            if (item?.preview) imageUris.add(item.preview);
            if (item?.uri)     imageUris.add(item.uri);
          });
        }

        for (const path of [...staticFiles, ...imageUris]) {
          const resp = await fetch(path);
          if (!resp.ok) continue;
          zip.file(path, await resp.blob());
        }

        const blob = await zip.generateAsync({ type: "blob", compression: "DEFLATE", compressionOptions: { level: 6 } });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "catalogo-swift.zip";
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error("Error generando zip:", err);
      } finally {
        btn.disabled = false;
        btn.setAttribute("aria-label", originalLabel);
      }
    });
  };

  const setupViewportHeightVar = () => {
    const setAppHeight = () => {
      const height = window.visualViewport ? window.visualViewport.height : window.innerHeight;
      document.documentElement.style.setProperty("--app-vh", `${height}px`);
    };

    setAppHeight();
    if (window.visualViewport) window.visualViewport.addEventListener("resize", setAppHeight);
    else window.addEventListener("resize", setAppHeight);
  };

  if (location.protocol === "file:") document.body.classList.add("is-local");
  history.scrollRestoration = "manual";
  window.scrollTo(0, 0);
  renderFilterChips();
  renderGallery();
  renderResources();
  applyFilters();
  revealElements(document);
  setupTabs();
  setupSidebar();
  setupLightbox();
  setupViewportHeightVar();
  setupScrollTop();
  setupDownloadSite();
  setTab(location.hash === "#recursos" || location.hash === "#resources" ? "resources" : "gallery");
})();
