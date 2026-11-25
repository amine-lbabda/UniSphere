(function () {
  const KEY = "unisphere-study-mode";
  const body = document.body;
  const supported =
    body.classList.contains("space-student") ||
    body.classList.contains("space-teacher") ||
    body.classList.contains("space-admin");
  if (!supported) return;

  function apply(on) {
    body.classList.toggle("theme-study", on);
    const btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      btn.innerHTML = on
        ? "<span aria-hidden='true'>☀️</span> Light"
        : "<span aria-hidden='true'>🌙</span> Study Mode";
    }
  }

  apply(localStorage.getItem(KEY) === "1");

  document.getElementById("theme-toggle")?.addEventListener("click", () => {
    const next = !body.classList.contains("theme-study");
    localStorage.setItem(KEY, next ? "1" : "0");
    apply(next);
  });
})();
