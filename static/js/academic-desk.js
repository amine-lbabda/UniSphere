(function () {
  // Animate progress bars when they enter viewport
  const bars = document.querySelectorAll(".academic-card-progress .fill[data-width], .book-bar i[data-width]");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          el.style.width = (el.getAttribute("data-width") || "0") + "%";
          io.unobserve(el);
        });
      },
      { threshold: 0.35 }
    );
    bars.forEach((b) => io.observe(b));
  } else {
    bars.forEach((b) => {
      b.style.width = (b.getAttribute("data-width") || "0") + "%";
    });
  }

  // Reveal on scroll
  const reveals = document.querySelectorAll(".reveal-up");
  if ("IntersectionObserver" in window) {
    const rio = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("is-in");
            rio.unobserve(e.target);
          }
        });
      },
      { threshold: 0.15 }
    );
    reveals.forEach((el) => rio.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-in"));
  }
})();
