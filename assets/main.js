(() => {
  "use strict";

  const payload = window.CATALOG_DATA || JSON.parse(document.getElementById("catalog-data")?.textContent || "{}");
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
  const viewOrder = ORDER.views || [];

  let activeView = "all";
  let activeLivery = "all";
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
      short: humanize(item.view),
      glyph: "◆",
      sub: "Vista"
    });
    const shot = metaFor("shots", item.shot, {
      name: humanize(item.shot),
      dot: "#888888"
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

    const sidebarTitle = document.querySelector(".controls__heading-label");
    if (sidebarTitle) sidebarTitle.textContent = isResources ? "Livery" : "Filtros";

    const liveryLabel = byId("liveryChips")?.closest(".fgroup")?.querySelector(".fgroup__label");
    if (liveryLabel) liveryLabel.textContent = isResources ? "Especificación" : "Paleta";

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
    const liveryChips = byId("liveryChips");
    const viewChips = byId("viewChips");

    if (liveryChips) {
      const allLiveries = createChip("Todas", null, true);
      allLiveries.dataset.key = "all";
      allLiveries.addEventListener("click", () => {
        activeLivery = "all";
        syncPressed(liveryChips, activeLivery);
        applyFilters();
        renderResources();
      });
      liveryChips.append(allLiveries);

      liveries.forEach(key => {
        const meta = LIVERIES_META[key] || { name: humanize(key), glyph: "◆" };
        const button = createChip(meta.name, meta.glyph, false);
        button.dataset.key = key;
        if (meta.hex) button.style.setProperty("--livery-chip-color", meta.hex);
        button.addEventListener("click", () => {
          activeLivery = key;
          syncPressed(liveryChips, activeLivery);
          applyFilters();
          renderResources();
        });
        liveryChips.append(button);
      });
    }

    if (viewChips) {
      const allViews = createChip("Todas", null, true);
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
          orderIndex(viewOrder, a.view) - orderIndex(viewOrder, b.view)
          || orderIndex(shots, a.shot) - orderIndex(shots, b.shot)
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
        image.src = item.uri;
        image.alt = `Suzuki Swift Sport ZC33S, vista ${view.name.toLowerCase()}, toma ${shot.name.toLowerCase()}.`;
        imageWrap.append(image);
        card.append(imageWrap);

        const caption = document.createElement("div");
        caption.className = "card__cap";

        const dot = document.createElement("span");
        dot.className = "dot";
        dot.style.background = shot.dot || "#888888";
        caption.append(dot);
        caption.append(createText("span", "card__name", shot.name));
        caption.append(createText("span", "tag tag--view", view.short || view.name));

        if (liveries.length > 1 && item.livery) {
          const tag = createText("span", "tag tag--livery", livery.short || livery.name);
          tag.style.setProperty("--livery-tag-color", livery.hex || "#888888");
          caption.append(tag);
        }

        card.append(caption);
        card.addEventListener("click", () => openLightbox(item));
        grid.append(card);
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
    head.append(createText("p", "", subtitle));
    return head;
  };

  const finishBadge = item => {
    if (!item.matte) return null;
    const level = item.matteLevel || "none";
    return createText("span", `finish-badge finish-badge--${level}`, item.matte);
  };

  const resolveResources = () => {
    const resources = META.resources || {};

    if (activeLivery !== "all") return resources[activeLivery] || {};

    return liveries.reduce((merged, key) => {
      const current = resources[key] || {};
      if (!merged.intro && current.intro) merged.intro = current.intro;
      merged.colors.push(...(current.colors || []));
      merged.kamon.push(...(current.kamon || []));
      merged.kanji.push(...(current.kanji || []));
      return merged;
    }, { intro: "", colors: [], kamon: [], kanji: [] });
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
      card.style.setProperty("--swatch", item.hex || "#888888");
      card.style.setProperty("--wheel-hue", `${Number(item.hsvHue || 0)}deg`);

      const visual = document.createElement("div");
      visual.className = "color-card__visual";

      const wheel = document.createElement("div");
      wheel.className = "color-wheel";
      wheel.setAttribute("aria-label", `Ruleta HSV: ${item.hsv || item.hex || "sin valor"}`);
      wheel.append(createText("span", "color-wheel__core", ""));
      visual.append(wheel);

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
      specs.append(specRow("HSV", item.hsv || "—"));
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
      body.append(createText("h3", "", item.name || config.fallbackName));
      body.append(createText("p", "file-path", item.uri || ""));

      const link = document.createElement("a");
      link.className = "resource-link";
      link.href = item.uri || "#";
      link.target = "_blank";
      link.rel = "noopener";
      link.textContent = "Abrir PNG original";
      body.append(link);

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
    const liveryMeta = activeLivery !== "all" ? LIVERIES_META[activeLivery] || {} : {};
    const liveryLabel = activeLivery !== "all" ? ` · ${liveryMeta.name || humanize(activeLivery)}` : "";

    const intro = document.createElement("section");
    intro.className = "resource-hero";

    const eyebrow = createText("p", "hero__eyebrow eyebrow", "");
    eyebrow.append(createText("span", "", ""));
    eyebrow.append(document.createTextNode(`Suzuki Swift Sport ZC33S · Recursos de producción${liveryLabel}`));
    intro.append(eyebrow);

    const title = document.createElement("h1");
    title.append(document.createTextNode("Especificaciones "));
    title.append(createText("span", "y", "del diseño"));
    intro.append(title);

    intro.append(createText("p", "", resources.intro || "Especificación visual de colores, acabados y emblemas."));
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

    revealElements(root);
  };

  const applyFilters = () => {
    let shown = 0;

    cards.forEach(card => {
      const isVisible = (activeView === "all" || card.view === activeView)
        && (activeLivery === "all" || card.livery === activeLivery);
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
    lightboxImg.src = item.uri;
    lightboxImg.alt = `Suzuki Swift Sport ZC33S, vista ${view.name.toLowerCase()}, toma ${shot.name.toLowerCase()}.`;
    setText("lbGlyph", view.glyph || "◆");
    setText("lbName", shot.name);
    setText("lbSub", view.name);
    setText("lbCur", lightboxIndex + 1);
    setText("lbTot", lightboxItems.length);
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

  const setupViewportHeightVar = () => {
    const setAppHeight = () => {
      const height = window.visualViewport ? window.visualViewport.height : window.innerHeight;
      document.documentElement.style.setProperty("--app-vh", `${height}px`);
    };

    setAppHeight();
    if (window.visualViewport) window.visualViewport.addEventListener("resize", setAppHeight);
    else window.addEventListener("resize", setAppHeight);
  };

  renderFilterChips();
  renderGallery();
  renderResources();
  applyFilters();
  revealElements(document);
  setupTabs();
  setupSidebar();
  setupLightbox();
  setupViewportHeightVar();
  setTab(location.hash === "#recursos" || location.hash === "#resources" ? "resources" : "gallery");
})();
