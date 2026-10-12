(() => {
  "use strict";

  document.documentElement.classList.add("has-js");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const reveal = () => {
    const elements = document.querySelectorAll("[data-reveal]");
    if (reducedMotion || !("IntersectionObserver" in window)) {
      elements.forEach((element) => element.classList.add("is-visible"));
      return;
    }
    const observer = new IntersectionObserver((entries, instance) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          instance.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    elements.forEach((element) => observer.observe(element));
  };

  const countUp = () => {
    document.querySelectorAll("[data-count]").forEach((element) => {
      const target = Number(element.dataset.count || 0);
      if (reducedMotion || !Number.isFinite(target) || target === 0) {
        element.textContent = String(target);
        return;
      }
      const duration = 620;
      const start = performance.now();
      const tick = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = String(Math.round(target * eased));
        if (progress < 1) window.requestAnimationFrame(tick);
      };
      window.requestAnimationFrame(tick);
    });
  };

  const enhanceForms = () => {
    document.querySelectorAll("form[data-loading-form]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        if (event.defaultPrevented || !form.checkValidity()) return;
        const button = form.querySelector("button[type='submit'], input[type='submit']");
        if (!button) return;
        button.classList.add("is-loading");
        button.dataset.originalLabel = button.tagName === "INPUT" ? button.value : button.innerHTML;
        const label = form.dataset.loadingLabel || "Saving…";
        if (button.tagName === "INPUT") button.value = label;
        else {
          button.textContent = label;
          const spinner = document.createElement("span");
          spinner.className = "button-spinner";
          spinner.setAttribute("aria-hidden", "true");
          button.prepend(spinner);
        }
        button.setAttribute("aria-busy", "true");
      });
    });
    window.addEventListener("pageshow", () => {
      document.querySelectorAll("[data-original-label]").forEach((button) => {
        if (button.tagName === "INPUT") button.value = button.dataset.originalLabel;
        else button.innerHTML = button.dataset.originalLabel;
        button.classList.remove("is-loading");
        button.removeAttribute("aria-busy");
      });
    });
  };

  const scrollReveal = () => {
    document.querySelectorAll(".table tbody tr").forEach((row, index) => {
      row.style.setProperty("--row-delay", `${Math.min(index, 8) * 35}ms`);
    });
  };

  const landingNavigation = () => {
    const links = [...document.querySelectorAll("[data-section-link]")];
    const sections = links
      .map((link) => document.querySelector(`[data-section='${link.dataset.sectionLink}']`))
      .filter(Boolean);
    if (!links.length || !sections.length) return;
    const header = document.querySelector(".landing-header");
    let scheduled = false;
    const update = () => {
      let active = sections[0].dataset.section;
      sections.forEach((section) => {
        if (section.getBoundingClientRect().top <= 150) active = section.dataset.section;
      });
      links.forEach((link) => {
        const selected = link.dataset.sectionLink === active;
        link.classList.toggle("active", selected);
        if (selected) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
      header?.classList.toggle("is-scrolled", window.scrollY > 12);
      scheduled = false;
    };
    window.addEventListener("scroll", () => {
      if (!scheduled) { scheduled = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  };

  const responsiveMenus = () => {
    document.querySelectorAll(".navbar-toggler").forEach((toggle) => {
      const target = document.getElementById(toggle.dataset.menuTarget);
      if (!target) return;
      const close = () => {
        target.classList.remove("show");
        toggle.setAttribute("aria-expanded", "false");
      };
      toggle.addEventListener("click", () => {
        const open = target.classList.toggle("show");
        toggle.setAttribute("aria-expanded", String(open));
      });
      target.querySelectorAll("a").forEach((link) => link.addEventListener("click", close));
      target.addEventListener("keydown", (event) => {
        if (event.key === "Escape") { close(); toggle.focus(); }
      });
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    reveal();
    countUp();
    enhanceForms();
    scrollReveal();
    landingNavigation();
    responsiveMenus();
  });
})();
