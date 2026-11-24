(function () {
  if (
    !document.body.classList.contains("space-teacher") &&
    !document.body.classList.contains("space-admin")
  )
    return;

  const toggle = document.getElementById("studio-nav-toggle");
  const backdrop = document.getElementById("studio-nav-backdrop");

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

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const blobs = document.querySelectorAll(".living-bg span");
  if (!reduce && blobs.length) {
    window.addEventListener(
      "pointermove",
      (e) => {
        const x = (e.clientX / window.innerWidth - 0.5) * 14;
        const y = (e.clientY / window.innerHeight - 0.5) * 10;
        blobs.forEach((b, i) => {
          const f = (i + 1) * 0.3;
          b.style.transform = `translate(${x * f}px, ${y * f}px)`;
        });
      },
      { passive: true }
    );
  }

  // Soft reveal on scroll for studio panels/cards
  const reveals = document.querySelectorAll(".reveal");
  if (reveals.length) {
    if (reduce || !("IntersectionObserver" in window)) {
      reveals.forEach((el) => el.classList.add("visible"));
    } else {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("visible");
              io.unobserve(entry.target);
            }
          });
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
      );
      reveals.forEach((el) => io.observe(el));
    }
  }
})();
