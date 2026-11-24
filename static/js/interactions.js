(function () {
  // Soft press feedback on desk buttons
  document.addEventListener("pointerdown", (e) => {
    const btn = e.target.closest(".desk-btn, .academic-card, .library-book");
    if (!btn) return;
    btn.style.setProperty("--press", "1");
  });
  document.addEventListener("pointerup", () => {
    document.querySelectorAll("[style*='--press']").forEach((el) => {
      el.style.removeProperty("--press");
    });
  });
})();
