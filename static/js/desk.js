(function () {
  if (!document.body.classList.contains("space-student")) return;

  const toggle = document.getElementById("desk-nav-toggle");
  const backdrop = document.getElementById("desk-nav-backdrop");

  function setNav(open) {
    document.body.classList.toggle("nav-open", open);
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  toggle?.addEventListener("click", () => {
    setNav(!document.body.classList.contains("nav-open"));
  });
  backdrop?.addEventListener("click", () => setNav(false));
  document.querySelectorAll(".app-side-nav a").forEach((a) => {
    a.addEventListener("click", () => setNav(false));
  });

  // Subtle living background parallax
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const blobs = document.querySelectorAll(".living-bg span");
  if (!reduce && blobs.length) {
    window.addEventListener(
      "pointermove",
      (e) => {
        const x = (e.clientX / window.innerWidth - 0.5) * 16;
        const y = (e.clientY / window.innerHeight - 0.5) * 12;
        blobs.forEach((b, i) => {
          const f = (i + 1) * 0.35;
          b.style.transform = `translate(${x * f}px, ${y * f}px)`;
        });
      },
      { passive: true }
    );
  }

  // Count-up stats
  document.querySelectorAll("[data-count-up]").forEach((el) => {
    const target = Number(el.getAttribute("data-count-up") || 0);
    if (reduce) {
      el.textContent = target;
      return;
    }
    const suffix = el.getAttribute("data-suffix") || "";
    const duration = 900;
    const start = performance.now();
    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.round(target * eased) + suffix;
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });

  // Progress ring SVG
  document.querySelectorAll(".progress-ring[data-percent]").forEach((ring) => {
    const pct = Math.max(0, Math.min(100, Number(ring.dataset.percent) || 0));
    const circle = ring.querySelector(".progress-ring-value");
    if (!circle) return;
    const radius = Number(circle.getAttribute("r") || 40);
    const circ = 2 * Math.PI * radius;
    circle.style.strokeDasharray = String(circ);
    circle.style.strokeDashoffset = String(circ);
    requestAnimationFrame(() => {
      const offset = circ - (pct / 100) * circ;
      circle.style.transition = reduce
        ? "none"
        : "stroke-dashoffset 1s cubic-bezier(0.22, 1, 0.36, 1)";
      circle.style.strokeDashoffset = String(offset);
    });
  });
})();
