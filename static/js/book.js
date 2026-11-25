(function () {
  const book = document.getElementById("academic-book");
  if (!book) return;

  const stage = document.getElementById("book-stage");
  const cover = book.querySelector(".book-cover");
  const spreads = Array.from(book.querySelectorAll(".book-spread"));
  const prevBtn = document.getElementById("book-prev");
  const nextBtn = document.getElementById("book-next");
  const dots = document.getElementById("book-dots");
  const openBtn = document.getElementById("desk-skip-open");
  const closeBtn = document.getElementById("desk-skip-close");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let page = 0;
  let flipping = false;

  function syncButtons(open) {
    if (openBtn) openBtn.hidden = open;
    if (closeBtn) closeBtn.hidden = !open;
  }

  function openBook() {
    book.classList.remove("is-closed");
    book.classList.add("is-open");
    stage?.classList.add("is-zoomed");
    syncButtons(true);
  }

  function closeBook() {
    book.classList.add("is-closed");
    book.classList.remove("is-open");
    stage?.classList.remove("is-zoomed");
    showPage(0, true);
    syncButtons(false);
  }

  function showPage(index, instant) {
    if (!spreads.length) return;
    const next = Math.max(0, Math.min(index, spreads.length - 1));
    if (next === page && !instant) return;

    const goingForward = next > page;
    const current = spreads[page];
    const target = spreads[next];

    function activate() {
      spreads.forEach((s, i) => s.classList.toggle("is-active", i === next));
      page = next;
      if (dots) dots.textContent = page + 1 + " / " + spreads.length;
      if (prevBtn) prevBtn.disabled = page === 0;
      if (nextBtn) nextBtn.disabled = page === spreads.length - 1;
      flipping = false;
    }

    if (instant || reduceMotion || !current || !target || !book.classList.contains("is-open")) {
      activate();
      return;
    }

    if (flipping) return;
    flipping = true;

    const flipClass = goingForward ? "is-flipping-next" : "is-flipping-prev";
    book.classList.add(flipClass);
    current.classList.add(goingForward ? "page-exit-left" : "page-exit-right");

    window.setTimeout(() => {
      activate();
      target.classList.add(goingForward ? "page-enter-right" : "page-enter-left");
      book.classList.remove(flipClass);
      window.setTimeout(() => {
        target.classList.remove("page-enter-right", "page-enter-left");
        current.classList.remove("page-exit-left", "page-exit-right");
      }, 420);
    }, 220);
  }

  cover?.addEventListener("click", openBook);
  cover?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openBook();
    }
  });

  openBtn?.addEventListener("click", openBook);
  closeBtn?.addEventListener("click", closeBook);
  prevBtn?.addEventListener("click", () => showPage(page - 1));
  nextBtn?.addEventListener("click", () => showPage(page + 1));

  showPage(0, true);
  syncButtons(false);

  if (reduceMotion) {
    openBook();
  }
})();
