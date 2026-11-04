/* archon-document runtime: theme toggle, palette-driven Mermaid theming, TOC scroll-spy,
   and the collection-index filter.
   Runs inline in <head> so the stored theme applies before first paint. */
(() => {
  const STORAGE_KEY = "ar-theme";
  const MODES = ["auto", "light", "dark"];
  const TOC_SPY_MARGIN = "0px 0px -75% 0px";
  // Mermaid theme variable -> Archon token. Diagrams follow the palette in both themes.
  const MERMAID_TOKENS = {
    background: "--ar-surface",
    primaryColor: "--ar-surface-2",
    primaryBorderColor: "--ar-border-strong",
    primaryTextColor: "--ar-text",
    secondaryColor: "--ar-accent-soft",
    secondaryBorderColor: "--ar-accent",
    secondaryTextColor: "--ar-text",
    tertiaryColor: "--ar-bg",
    tertiaryBorderColor: "--ar-border",
    tertiaryTextColor: "--ar-text",
    mainBkg: "--ar-surface-2",
    nodeBorder: "--ar-border-strong",
    textColor: "--ar-text",
    titleColor: "--ar-text",
    lineColor: "--ar-text-3",
    clusterBkg: "--ar-bg",
    clusterBorder: "--ar-border",
    edgeLabelBackground: "--ar-surface",
    noteBkgColor: "--ar-warn-soft",
    noteBorderColor: "--ar-warn",
    noteTextColor: "--ar-text",
    actorBkg: "--ar-surface-2",
    actorBorder: "--ar-border-strong",
    actorTextColor: "--ar-text",
    actorLineColor: "--ar-border-strong",
    signalColor: "--ar-text-2",
    signalTextColor: "--ar-text",
    labelBoxBkgColor: "--ar-surface-2",
    labelBoxBorderColor: "--ar-border-strong",
    labelTextColor: "--ar-text",
    loopTextColor: "--ar-text-2",
    activationBkgColor: "--ar-accent-soft",
    activationBorderColor: "--ar-accent",
    sequenceNumberColor: "--ar-surface",
    fontFamily: "--ar-font",
    fontSize: "--ar-diagram-font-size",
  };

  const root = document.documentElement;
  const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

  const readMode = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return MODES.includes(stored) ? stored : MODES[0];
    } catch {
      return MODES[0];
    }
  };
  const saveMode = (value) => {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch {
      /* storage unavailable: the choice lasts for this view only */
    }
  };

  let mode = readMode();
  const applyTheme = () => {
    if (mode === MODES[0]) root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", mode);
  };
  applyTheme();

  const isDark = () => mode === "dark" || (mode === MODES[0] && darkQuery.matches);
  const cssVar = (name) => getComputedStyle(root).getPropertyValue(name).trim();

  let diagrams = [];
  const renderDiagrams = () => {
    if (!window.mermaid || !diagrams.length) return;
    const themeVariables = Object.fromEntries(
      Object.entries(MERMAID_TOKENS).map(([key, token]) => [key, cssVar(token)]),
    );
    themeVariables.darkMode = isDark();
    window.mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "base", themeVariables });
    diagrams.forEach((el) => {
      el.removeAttribute("data-processed");
      el.innerHTML = el.dataset.arSrc;
    });
    window.mermaid.run({ nodes: diagrams }).catch((err) => console.warn("archon: diagram failed to render", err));
  };

  const labelFor = (value) => value.charAt(0).toUpperCase() + value.slice(1);

  const initThemeToggle = () => {
    const button = document.querySelector("[data-ar-theme-toggle]");
    if (!button) return;
    button.textContent = labelFor(mode);
    button.addEventListener("click", () => {
      mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length];
      saveMode(mode);
      applyTheme();
      button.textContent = labelFor(mode);
      renderDiagrams();
    });
    darkQuery.addEventListener("change", () => {
      if (mode === MODES[0]) renderDiagrams();
    });
  };

  const initTocSpy = () => {
    const links = [...document.querySelectorAll(".ar-toc a[href^='#']")];
    if (!links.length || !("IntersectionObserver" in window)) return;
    const setActive = (id) => links.forEach((a) => a.classList.toggle("is-active", a.hash === `#${id}`));
    const observer = new IntersectionObserver(
      (entries) => entries.filter((e) => e.isIntersecting).forEach((e) => setActive(e.target.id)),
      { rootMargin: TOC_SPY_MARGIN },
    );
    links.forEach((a) => {
      const target = document.getElementById(decodeURIComponent(a.hash.slice(1)));
      if (target) observer.observe(target);
    });
  };

  // Collection index: every word typed must appear in a card's text; empty groups hide.
  const initFilter = () => {
    const input = document.querySelector("[data-ar-filter]");
    if (!input) return;
    const items = [...document.querySelectorAll("[data-ar-filter-text]")];
    const groups = [...document.querySelectorAll("[data-ar-filter-group]")];
    const empty = document.querySelector("[data-ar-filter-empty]");
    input.addEventListener("input", () => {
      const terms = input.value.toLowerCase().split(/\s+/).filter(Boolean);
      let shown = 0;
      items.forEach((el) => {
        const hit = terms.every((t) => el.dataset.arFilterText.includes(t));
        el.hidden = !hit;
        if (hit) shown += 1;
      });
      groups.forEach((g) => {
        g.hidden = !g.querySelector("[data-ar-filter-text]:not([hidden])");
      });
      if (empty) empty.hidden = shown > 0;
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "/" && document.activeElement !== input) {
        e.preventDefault();
        input.focus();
      }
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    diagrams = [...document.querySelectorAll("pre.mermaid")];
    diagrams.forEach((el) => {
      el.dataset.arSrc = el.innerHTML;
    });
    initThemeToggle();
    initTocSpy();
    initFilter();
    renderDiagrams();
  });
})();
