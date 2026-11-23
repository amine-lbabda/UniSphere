document.addEventListener("DOMContentLoaded", () => {
  const nav = document.querySelector(".site-nav");
  if (nav) {
    const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  const reveals = document.querySelectorAll(".reveal");
  if (reveals.length && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("visible");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("visible"));
  }

  document.querySelectorAll(".alert").forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.4s, transform 0.4s";
      alert.style.opacity = "0";
      alert.style.transform = "translateX(20px)";
      setTimeout(() => alert.remove(), 400);
    }, 4200);
  });

  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("submit", (e) => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // Animated counters
  document.querySelectorAll("[data-count]").forEach((el) => {
    const target = Number(el.dataset.count) || 0;
    const duration = 900;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(target * eased);
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  // Soft tilt on cards
  document.querySelectorAll("[data-tilt]").forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      card.style.transform = `perspective(800px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateY(-4px)`;
    });
    card.addEventListener("mouseleave", () => {
      card.style.transform = "";
    });
  });

  // Quiz timer + answered progress
  const timerEl = document.getElementById("quiz-timer");
  const form = document.getElementById("quiz-form");
  if (timerEl && form) {
    let remaining = (Number(timerEl.dataset.minutes) || 15) * 60;
    const display = document.getElementById("timer-display");
    const answeredBar = document.getElementById("quiz-answered-bar");
    const answeredCount = document.getElementById("answered-count");
    const questions = form.querySelectorAll("[data-question]");

    const updateAnswered = () => {
      let n = 0;
      questions.forEach((q) => {
        if (q.querySelector('input[type="radio"]:checked')) n += 1;
      });
      if (answeredCount) answeredCount.textContent = String(n);
      if (answeredBar && questions.length) {
        answeredBar.style.width = `${(n / questions.length) * 100}%`;
      }
    };
    form.addEventListener("change", updateAnswered);
    updateAnswered();

    const tickTimer = () => {
      const m = Math.floor(remaining / 60);
      const s = remaining % 60;
      if (display) display.textContent = `${m}:${String(s).padStart(2, "0")}`;
      if (remaining <= 60) timerEl.classList.add("urgent");
      if (remaining <= 0) {
        form.requestSubmit ? form.requestSubmit() : form.submit();
        return;
      }
      remaining -= 1;
      setTimeout(tickTimer, 1000);
    };
    tickTimer();
  }

  // Animate progress bars on view
  document.querySelectorAll(".bar-fill").forEach((bar) => {
    const w = bar.style.width;
    bar.style.width = "0%";
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        bar.style.width = w;
      });
    });
  });
});
