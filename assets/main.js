(() => {
  "use strict";

  const payload = JSON.parse(document.getElementById("catalog-data").textContent);
  const DATA = payload.items || [];
  const META = payload.meta || {};
  const ORDER = META.order || {};
  const LIVERIES_META = META.liveries || {};
  const $ = id => document.getElementById(id);

  const humanize = value => String(value || "")
    .replace(/[_\-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, ch => ch.toUpperCase()) || "Sin nombre";

  const metaFor = (group, key, fallback = {}) => {
    const src = (META[group] && META[group][key]) || {};
    return Object.assign({}, fallback, src);
  };

  const orderedKeys = (values, preferred = []) => {
    const set = new Set(values);
    const ordered = preferred.filter(key => set.has(key));
    Array.from(set).sort().forEach(key => {
      if (!ordered.includes(key)) ordered.push(key);
    });
    return ordered;
  };

  const views = orderedKeys(DATA.map(item => item.view), ORDER.views || []);
  const liveries = orderedKeys(DATA.map(item => item.livery).filter(Boolean), ORDER.liveries || []);
  const shots = ORDER.shots || [];
  const viewOrder = ORDER.views || [];

  const shotSortIndex = shot => {
    const i = shots.indexOf(shot);
    return i === -1 ? 10000 : i;
  };

  const viewSortIndex = view => {
    const i = viewOrder.indexOf(view);
    return i === -1 ? 10000 : i;
  };

  const text = (tag, className, value) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    el.textContent = value;
    return el;
  };

  const setText = (id, value) => {
    const el = $(id);
    if (el) el.textContent = value;
  };

  const prefersReducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

  const activeScrollArea = () => {
    const resourcesPanel = $("resourcesPanel");
    if (resourcesPanel && !resourcesPanel.hidden) return resourcesPanel;
    return $("galleryPanel") || $("itemScroll");
  };

  const scrollItemsToTop = () => {
    const scrollArea = activeScrollArea();
    const behavior = prefersReducedMotion() ? "auto" : "smooth";
    if (scrollArea) scrollArea.scrollTo({ top: 0, left: 0, behavior });
    window.scrollTo({ top: 0, left: 0, behavior });
  };

  const setTab = tab => {
    const page = $("top");
    const isResources = tab === "resources";
    document.querySelectorAll(".tab-button").forEach(button => {
      const active = button.dataset.tab === tab;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", active ? "true" : "false");
      button.tabIndex = active ? 0 : -1;
    });

    document.querySelectorAll(".gallery-only").forEach(el => {
      el.classList.toggle("is-hidden-tab", isResources);
      el.hidden = isResources;
    });

    const resourcesPanel = $("resourcesPanel");
    if (resourcesPanel) {
      resourcesPanel.classList.toggle("is-hidden-tab", !isResources);
      resourcesPanel.hidden = !isResources;
    }

    if (page) page.classList.toggle("resources-mode", isResources);

    const sidebarTitle = document.querySelector(".filtros_css");
    if (sidebarTitle) sidebarTitle.textContent = isResources ? "Livery" : "Filtros";
    const paletaLabel = document.querySelector("#liveryChips")
      ?.closest(".fgroup")?.querySelector(".fgroup__label");
    if (paletaLabel) paletaLabel.textContent = isResources ? "Especificación" : "Paleta";

    const activePanel = isResources ? resourcesPanel : $("galleryPanel");
    if (activePanel) {
      activePanel.querySelectorAll(".reveal").forEach(el => el.classList.add("in"));
    }

    scrollItemsToTop();
  };

  document.querySelectorAll(".tab-button").forEach(button => {
    button.addEventListener("click", () => setTab(button.dataset.tab || "gallery"));
    button.addEventListener("keydown", event => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      event.preventDefault();
      const next = (button.dataset.tab === "gallery") ? "resources" : "gallery";
      const nextButton = document.querySelector(`.tab-button[data-tab="${next}"]`);
      if (nextButton) nextButton.focus();
      setTab(next);
    });
  });

  const brandLink = document.querySelector(".brand");
  if (brandLink) {
    brandLink.addEventListener("click", event => {
      event.preventDefault();
      setTab("gallery");
    });
  }

  const itemLabel = item => {
    const vm = metaFor("views", item.view, { name: humanize(item.view), short: humanize(item.view), glyph: "◆", sub: "Vista" });
    const sm = metaFor("shots", item.shot, { name: humanize(item.shot), dot: "#888888" });
    const lm = (LIVERIES_META[item.livery]) || { name: humanize(item.livery || ""), hex: "#888888", glyph: "◆" };
    return { vm, sm, lm };
  };

  let fView = "all";
  let fLivery = "all";

  const chip = (label, jp, pressed) => {
    const b = document.createElement("button");
    b.className = "chip";
    b.type = "button";
    b.setAttribute("aria-pressed", pressed ? "true" : "false");
    if (jp) b.append(text("span", "jp", jp));
    b.append(document.createTextNode(label));
    return b;
  };

  const syncPressed = (container, key) => {
    if (!container) return;
    container.querySelectorAll(".chip").forEach(c => {
      c.setAttribute("aria-pressed", c.dataset.key === key ? "true" : "false");
    });
  };

  // Livery chips
  const liveryChips = $("liveryChips");
  if (liveryChips) {
    const allLiveries = chip("Todas", null, true);
    allLiveries.dataset.key = "all";
    allLiveries.addEventListener("click", () => {
      fLivery = "all";
      syncPressed(liveryChips, fLivery);
      applyFilters();
      renderResources();
    });
    liveryChips.append(allLiveries);

    liveries.forEach(key => {
      const lm = LIVERIES_META[key] || { name: humanize(key), glyph: "◆" };
      const b = chip(lm.name, lm.glyph, false);
      b.dataset.key = key;
      if (lm.hex) b.style.setProperty("--livery-chip-color", lm.hex);
      b.addEventListener("click", () => {
        fLivery = key;
        syncPressed(liveryChips, fLivery);
        applyFilters();
        renderResources();
      });
      liveryChips.append(b);
    });
  }

  // View chips
  const viewChips = $("viewChips");
  if (viewChips) {
    const allViews = chip("Todas", null, true);
    allViews.dataset.key = "all";
    allViews.addEventListener("click", () => { fView = "all"; syncPressed(viewChips, fView); applyFilters(); });
    viewChips.append(allViews);

    views.forEach(key => {
      const vm = metaFor("views", key, { name: humanize(key), short: humanize(key), glyph: "◆" });
      const b = chip(vm.name, vm.glyph, false);
      b.dataset.key = key;
      b.addEventListener("click", () => { fView = key; syncPressed(viewChips, fView); applyFilters(); });
      viewChips.append(b);
    });
  }

  const gallery = $("gallery");
  const cardEls = [];

  views.forEach((vkey, vi) => {
    const items = DATA.filter(item => item.view === vkey)
      .sort((a, b) =>
        viewSortIndex(a.view) - viewSortIndex(b.view)
        || shotSortIndex(a.shot) - shotSortIndex(b.shot)
        || a.uri.localeCompare(b.uri)
      );
    if (!items.length || !gallery) return;

    const vm = metaFor("views", vkey, { name: humanize(vkey), glyph: "◆", sub: "Vista" });

    const section = document.createElement("section");
    section.className = "vsec";
    section.dataset.view = vkey;
    section.id = `v-${vkey}`;

    const head = document.createElement("div");
    head.className = "dhead";

    const glyph = text("div", "dhead__glyph", vm.glyph || "◆");
    glyph.setAttribute("aria-hidden", "true");
    head.append(glyph);

    const body = document.createElement("div");
    body.className = "dhead__body";

    const eyebrow = document.createElement("div");
    eyebrow.className = "dhead__eyebrow";
    eyebrow.append(text("span", "num", String(vi + 1).padStart(2, "0")));
    eyebrow.append(document.createTextNode(" Vista"));
    body.append(eyebrow);

    body.append(text("h2", "", vm.name));

    const metaLine = document.createElement("div");
    metaLine.className = "dhead__meta";
    metaLine.append(document.createTextNode(`${vm.sub || "Vista"} · `));

    const imgText = items.length > 1 ? " imágenes" : " imagen";

    const strong = document.createElement("b");
    strong.append(text("span", "cnt", items.length));
    strong.append(document.createTextNode(imgText));
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
      const { vm, sm, lm } = itemLabel(item);
      const card = document.createElement("button");
      card.className = "card reveal";
      card.type = "button";
      card.setAttribute("aria-label", `Ampliar ${vm.name} · ${sm.name}`);
      card.dataset.view = item.view;
      card.dataset.shot = item.shot;
      card.dataset.livery = item.livery || "";

      const imgBox = document.createElement("div");
      imgBox.className = "card__img";
      const img = document.createElement("img");
      img.loading = "lazy";
      img.decoding = "async";
      img.src = item.uri;
      img.alt = `Suzuki Swift Sport ZC33S, vista ${vm.name.toLowerCase()}, toma ${sm.name.toLowerCase()}.`;
      imgBox.append(img);
      card.append(imgBox);

      const cap = document.createElement("div");
      cap.className = "card__cap";
      const dot = document.createElement("span");
      dot.className = "dot";
      dot.style.background = sm.dot || "#888888";
      cap.append(dot);
      cap.append(text("span", "card__name", sm.name));
      cap.append(text("span", "tag tag--view", vm.short || vm.name));

      if (liveries.length > 1 && item.livery) {
        const livTag = text("span", "tag tag--livery", lm.short || lm.name);
        livTag.style.setProperty("--livery-tag-color", lm.hex || "#888888");
        cap.append(livTag);
      }

      card.append(cap);

      card.addEventListener("click", () => openLB(item));
      grid.append(card);
      cardEls.push({ el: card, view: item.view, livery: item.livery || "", item });
    });

    section.append(grid);
    gallery.append(section);
  });

  const finishBadge = (label, level) => {
    const badge = text("span", `finish-badge finish-badge--${level || "none"}`, label);
    return badge;
  };

  const specRow = (label, value, extraClass = "") => {
    const row = document.createElement("div");
    row.className = `spec-row ${extraClass}`.trim();
    row.append(text("dt", "spec-row__label", label));
    row.append(text("dd", "spec-row__value", value));
    return row;
  };

  const sectionHead = (title, subtitle) => {
    const head = document.createElement("div");
    head.className = "resource-head";
    head.append(text("p", "eyebrow", "Recursos"));
    head.append(text("h2", "", title));
    head.append(text("p", "", subtitle));
    return head;
  };

  // Resolve resources for the current livery filter.
  // Supports both the new per-livery structure ({ purpura: { colors, kamon, kanji } })
  // and the legacy flat structure ({ colors, kamon, kanji }) for backwards compatibility.
  const resolveResources = () => {
    const raw = META.resources || {};
    const firstLiveryKey = Object.keys(raw)[0];
    const isPerLivery = firstLiveryKey && raw[firstLiveryKey] && (
      Array.isArray(raw[firstLiveryKey].colors) ||
      Array.isArray(raw[firstLiveryKey].kamon) ||
      Array.isArray(raw[firstLiveryKey].kanji)
    );

    if (!isPerLivery) return raw;

    if (fLivery !== "all") return raw[fLivery] || {};

    // "all" mode: merge resources from all liveries
    const merged = { intro: "", colors: [], kamon: [], kanji: [] };
    (ORDER.liveries || Object.keys(raw)).forEach(key => {
      const r = raw[key] || {};
      if (!merged.intro && r.intro) merged.intro = r.intro;
      merged.colors.push(...(r.colors || []));
      merged.kamon.push(...(r.kamon || []));
      merged.kanji.push(...(r.kanji || []));
    });
    return merged;
  };

  const renderResources = () => {
    const root = $("resourcesRoot");
    if (!root) return;
    root.innerHTML = "";

    const RESOURCES = resolveResources();
    const lm = fLivery !== "all" ? (LIVERIES_META[fLivery] || {}) : {};
    const liveryLabel = fLivery !== "all" ? ` · ${lm.name || fLivery}` : "";

    const intro = document.createElement("section");
    intro.className = "resource-hero";
    intro.innerHTML = `
      <p class="hero__eyebrow eyebrow"><span></span>Suzuki Swift Sport ZC33S · Recursos de producción${liveryLabel}</p>
      <h1>Especificaciones <span class="y">del diseño</span></h1>
      <p>${RESOURCES.intro || "Especificación visual de colores, acabados y emblemas."}</p>
    `;
    root.append(intro);

    const colorsSection = document.createElement("section");
    colorsSection.className = "resource-section";
    colorsSection.append(sectionHead("Colores", "Códigos técnicos listos para rotulación y referencia visual."));

    const colorGrid = document.createElement("div");
    colorGrid.className = "resource-grid resource-grid--colors";

    (RESOURCES.colors || []).forEach(item => {
      const card = document.createElement("article");
      card.className = "resource-card color-card reveal";
      card.style.setProperty("--swatch", item.hex || "#888888");
      card.style.setProperty("--wheel-hue", `${Number(item.hsvHue || 0)}deg`);

      const visual = document.createElement("div");
      visual.className = "color-card__visual";

      const wheel = document.createElement("div");
      wheel.className = "color-wheel";
      wheel.setAttribute("aria-label", `Ruleta HSV: ${item.hsv}`);
      wheel.append(text("span", "color-wheel__core", ""));
      visual.append(wheel);

      const swatch = document.createElement("div");
      swatch.className = "swatch";
      swatch.setAttribute("aria-label", `Muestra de color ${item.hex}`);
      visual.append(swatch);
      card.append(visual);

      const body = document.createElement("div");
      body.className = "resource-card__body";
      body.append(text("p", "resource-card__role", item.role || "Recurso"));
      body.append(text("h3", "", item.name || "Recurso de color"));

      const specs = document.createElement("dl");
      specs.className = "spec-grid";
      specs.append(specRow("HEX", item.hex || "—", "spec-row--hex"));
      specs.append(specRow("RGB", item.rgb || "—"));
      specs.append(specRow("CMYK", item.cmyk || "—"));
      specs.append(specRow("Pantone", item.pantone || "—"));
      body.append(specs);

      const finishes = document.createElement("div");
      finishes.className = "finish-list";
      body.append(finishes);

      card.append(body);
      colorGrid.append(card);
    });

    colorsSection.append(colorGrid);
    root.append(colorsSection);

    const renderImageResourceSection = ({ key, title, subtitle, cardClass, gridClass, fallbackName }) => {
      const section = document.createElement("section");
      section.className = "resource-section";
      section.append(sectionHead(title, subtitle));

      const grid = document.createElement("div");
      grid.className = `resource-grid ${gridClass}`;

      (RESOURCES[key] || []).forEach(item => {
        const card = document.createElement("article");
        card.className = `resource-card ${cardClass} reveal`;

        const frame = document.createElement("div");
        frame.className = `${cardClass}__frame`;
        const img = document.createElement("img");
        img.loading = "lazy";
        img.decoding = "async";
        img.src = item.preview || item.uri;
        img.alt = `${item.name || fallbackName} · ${item.placement || "ubicación"}`;
        img.addEventListener("error", () => {
          if (item.uri && img.src !== item.uri) img.src = item.uri;
        }, { once: true });
        frame.append(img);
        card.append(frame);

        const body = document.createElement("div");
        body.className = "resource-card__body";
        body.append(text("p", "resource-card__role", item.placement || fallbackName));
        body.append(text("h3", "", item.name || fallbackName));
        body.append(text("p", "file-path", item.uri || item.filename || ""));

        const open = document.createElement("a");
        open.className = "resource-link";
        open.href = item.uri || "#";
        open.target = "_blank";
        open.rel = "noopener";
        open.textContent = "Abrir PNG original";
        body.append(open);
        card.append(body);
        grid.append(card);
      });

      section.append(grid);
      root.append(section);
    };

    renderImageResourceSection({
      key: "kamon",
      title: "Kamon",
      subtitle: "Emblemas PNG incluidos en la carpeta local 'resources/kamon/'",
      cardClass: "kamon-card",
      gridClass: "resource-grid--kamon",
      fallbackName: "Kamon"
    });

    renderImageResourceSection({
      key: "kanji",
      title: "Kanji",
      subtitle: "Grafías PNG incluidas en la carpeta local 'resources/kanji/'",
      cardClass: "kanji-card",
      gridClass: "resource-grid--kanji",
      fallbackName: "Kanji"
    });

    if ("IntersectionObserver" in window && !prefersReducedMotion()) {
      const io = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: .05 });
      root.querySelectorAll(".reveal").forEach(el => io.observe(el));
    } else {
      root.querySelectorAll(".reveal").forEach(el => el.classList.add("in"));
    }
  };

  renderResources();

  const applyFilters = () => {
    let shown = 0;
    cardEls.forEach(c => {
      const ok = (fView === "all" || c.view === fView)
        && (fLivery === "all" || c.livery === fLivery);
      c.el.classList.toggle("is-hidden", !ok);
      if (ok) shown++;
    });

    document.querySelectorAll(".vsec").forEach(sec => {
      const vkey = sec.dataset.view;
      const viewOk = fView === "all" || fView === vkey;
      const visible = Array.from(sec.querySelectorAll(".card")).filter(c => !c.classList.contains("is-hidden")).length;
      sec.classList.toggle("is-hidden", !viewOk || visible === 0);
      const cnt = sec.querySelector(".cnt");
      if (cnt) cnt.textContent = visible;
    });

    setText("count", shown);
    const empty = $("empty");
    if (empty) empty.classList.toggle("is-on", shown === 0);
  };

  const lb = $("lb");
  const lbImg = $("lbImg");
  let lastFocus = null;
  let lbList = [];
  let lbIdx = 0;

  const visibleItems = () => cardEls.filter(c => !c.el.classList.contains("is-hidden")).map(c => c.item);

  const renderLB = () => {
    const item = lbList[lbIdx];
    if (!item || !lbImg) return;
    const { vm, sm } = itemLabel(item);
    lbImg.src = item.uri;
    lbImg.alt = `Suzuki Swift Sport ZC33S, vista ${vm.name.toLowerCase()}, toma ${sm.name.toLowerCase()}.`;
    setText("lbGlyph", vm.glyph || "◆");
    setText("lbName", sm.name);
    setText("lbSub", vm.name);
    setText("lbCur", lbIdx + 1);
    setText("lbTot", lbList.length);
  };

  const openLB = item => {
    if (!lb) return;
    lbList = visibleItems();
    lbIdx = Math.max(0, lbList.findIndex(x => x === item));
    lastFocus = document.activeElement;
    renderLB();
    lb.classList.add("is-open");
    document.body.style.overflow = "hidden";
    const closeButton = $("lbClose");
    if (closeButton) closeButton.focus();
  };

  const closeLB = () => {
    if (!lb) return;
    lb.classList.remove("is-open");
    document.body.style.overflow = "";
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  };

  const step = d => {
    if (!lbList.length) return;
    lbIdx = (lbIdx + d + lbList.length) % lbList.length;
    renderLB();
  };

  const lbClose = $("lbClose");
  const lbPrev = $("lbPrev");
  const lbNext = $("lbNext");
  const sidebarToggleBtn = $("sidebarToggle");
  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener("click", () => {
      const collapsed = $("top").classList.toggle("sidebar-collapsed");
      sidebarToggleBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    });
  }

  if (lbClose) lbClose.addEventListener("click", closeLB);
  if (lbPrev) lbPrev.addEventListener("click", () => step(-1));
  if (lbNext) lbNext.addEventListener("click", () => step(1));
  if (lb) lb.addEventListener("click", e => { if (e.target === lb) closeLB(); });
  document.addEventListener("keydown", e => {
    if (!lb || !lb.classList.contains("is-open")) return;
    if (e.key === "Escape") closeLB();
    else if (e.key === "ArrowLeft") step(-1);
    else if (e.key === "ArrowRight") step(1);
  });

  if ("IntersectionObserver" in window && !prefersReducedMotion()) {
    const io = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: .05 });
    document.querySelectorAll(".reveal").forEach(el => io.observe(el));
  } else {
    document.querySelectorAll(".reveal").forEach(el => el.classList.add("in"));
  }

  applyFilters();

  if (location.hash === "#recursos" || location.hash === "#resources") {
    setTab("resources");
  } else {
    setTab("gallery");
  }

  const setVh = () => {
    const h = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    document.documentElement.style.setProperty('--vh', h + 'px');
  };
  setVh();
  if (window.visualViewport) window.visualViewport.addEventListener('resize', setVh);
  else window.addEventListener('resize', setVh);
})();
