(function () {
  if (
    !document.body.classList.contains("space-teacher") &&
    !document.body.classList.contains("space-admin")
  )
    return;

  function csrfToken() {
    const el = document.querySelector("[name=csrfmiddlewaretoken]");
    if (el) return el.value;
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  }

  function ensureToastStack() {
    let stack = document.querySelector(".toast-stack");
    if (!stack) {
      stack = document.createElement("div");
      stack.className = "toast-stack";
      stack.setAttribute("aria-live", "polite");
      stack.setAttribute("aria-relevant", "additions");
      document.body.appendChild(stack);
    }
    return stack;
  }

  function toastType(type) {
    if (type === "err" || type === "error" || type === "danger") return "err";
    if (type === "warn" || type === "warning") return "warn";
    return "ok";
  }

  window.TeacherToast = function (message, type) {
    const text = (message || "").toString().trim();
    if (!text) return;
    const stack = ensureToastStack();
    const toast = document.createElement("div");
    toast.className = "toast " + toastType(type);
    toast.setAttribute("role", "status");
    toast.textContent = text;
    stack.appendChild(toast);
    window.setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(8px)";
      toast.style.transition = "0.25s";
      window.setTimeout(() => toast.remove(), 260);
    }, 3200);
  };

  // Django messages → toasts
  document.querySelectorAll(".app-messages .alert").forEach((el) => {
    const tags = el.className || "";
    let kind = "ok";
    if (/\balert-(error|danger)\b/.test(tags)) kind = "err";
    else if (/\balert-warning\b/.test(tags)) kind = "warn";
    TeacherToast(el.textContent, kind);
    el.remove();
  });
  const msgWrap = document.querySelector(".app-messages");
  if (msgWrap && !msgWrap.children.length) msgWrap.remove();

  // Submit loading on traditional posts (skip if another handler preventDefault)
  document.querySelectorAll("form:not([data-no-busy])").forEach((form) => {
    form.addEventListener("submit", (e) => {
      window.setTimeout(() => {
        if (e.defaultPrevented || form.dataset.busyBound) return;
        form.dataset.busyBound = "1";
        const btn =
          form.querySelector('button[type="submit"]:not([disabled])') ||
          form.querySelector("button:not([type]):not([disabled])");
        if (btn) btn.classList.add("is-loading");
      }, 0);
    });
  });

  function syncStudioState(root, data) {
    if (!data || !data.studio_state) return;
    const scope = root || document;
    scope.querySelectorAll("[data-studio-state]").forEach((el) => {
      el.setAttribute("data-state", data.studio_state);
      const label = el.querySelector("[data-studio-label]");
      if (label && data.studio_state_label) {
        label.textContent = data.studio_state_label;
      }
    });
    scope.querySelectorAll("[data-studio-label]").forEach((el) => {
      if (!el.closest("[data-studio-state]") && data.studio_state_label) {
        el.textContent = data.studio_state_label;
      }
    });
    const card = scope.closest?.(".studio-course-card") || document.querySelector(
      `.studio-course-card [data-toggle-visibility]`
    )?.closest(".studio-course-card");
    if (card) {
      card.dataset.visible = data.student_accessible ? "1" : "0";
      if (data.status) card.dataset.status = data.status;
      const stateEl = card.querySelector("[data-studio-state]");
      if (stateEl) {
        stateEl.setAttribute("data-state", data.studio_state);
        const lab = stateEl.querySelector("[data-studio-label]");
        if (lab) lab.textContent = data.studio_state_label;
      }
    }
    document.querySelectorAll("#course-vis-panel .studio-vis-option").forEach((opt) => {
      const input = opt.querySelector("input");
      const want = data.is_visible ? "1" : "0";
      opt.classList.toggle("is-active", input && input.value === want);
      if (input) input.checked = input.value === want;
    });
  }

  async function postVisibility(url, opts) {
    const body = new URLSearchParams();
    if (opts && Object.prototype.hasOwnProperty.call(opts, "is_visible")) {
      body.set("is_visible", opts.is_visible ? "1" : "0");
    }
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrfToken(),
        Accept: "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.message || "Update failed");
    return data;
  }

  async function postToggle(url, btn) {
    btn.classList.add("is-busy");
    try {
      const data = await postVisibility(url);
      const pill = btn.querySelector(".vis-pill") || btn;
      const on = !!(data.student_accessible || data.is_visible);
      pill.classList.toggle("on", on);
      pill.classList.toggle("off", !on);
      const label = data.label || (on ? "Visible" : "Hidden");
      if (pill.querySelector(".vis-text")) {
        pill.querySelector(".vis-text").textContent = label;
      } else {
        pill.textContent = (on ? "🟢 " : "🔒 ") + label;
      }
      btn.classList.add("flash");
      window.setTimeout(() => btn.classList.remove("flash"), 450);
      syncStudioState(btn.closest(".studio-course-card") || document, data);
      TeacherToast(data.message || "Updated", "ok");
      return data;
    } catch (e) {
      TeacherToast(e.message || "Update failed", "err");
      return null;
    } finally {
      btn.classList.remove("is-busy");
    }
  }

  document.querySelectorAll("[data-toggle-visibility]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const url = btn.getAttribute("data-toggle-visibility");
      if (url) postToggle(url, btn);
    });
  });

  document.querySelectorAll("[data-set-visibility]").forEach((input) => {
    input.addEventListener("change", async () => {
      const url = input.getAttribute("data-set-visibility");
      if (!url) return;
      const wantVisible = input.getAttribute("data-visible") === "1";
      input.disabled = true;
      try {
        const data = await postVisibility(url, { is_visible: wantVisible });
        syncStudioState(document, data);
        TeacherToast(data.message || "Visibility updated", "ok");
      } catch (e) {
        TeacherToast(e.message || "Update failed", "err");
        input.checked = !wantVisible;
      } finally {
        input.disabled = false;
      }
    });
  });

  // Resource modal
  const backdrop = document.getElementById("res-modal-backdrop");
  const form = document.getElementById("res-modal-form");
  const openers = document.querySelectorAll("[data-open-res-modal]");
  const closer = document.getElementById("res-modal-close");
  const dropzone = document.getElementById("res-dropzone");
  const fileInput = form?.querySelector('input[type="file"]');
  const bar = document.getElementById("res-upload-bar");
  const barFill = bar?.querySelector("i");
  const listBody = document.getElementById("res-table-body");

  function openModal() {
    if (!backdrop) return;
    backdrop.classList.add("is-open");
    form?.reset();
  }
  function closeModal() {
    backdrop?.classList.remove("is-open");
  }

  openers.forEach((b) => b.addEventListener("click", (e) => {
    e.preventDefault();
    openModal();
  }));
  closer?.addEventListener("click", closeModal);
  backdrop?.addEventListener("click", (e) => {
    if (e.target === backdrop) closeModal();
  });

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("is-drag");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("is-drag"));
    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("is-drag");
      if (e.dataTransfer.files?.length) {
        fileInput.files = e.dataTransfer.files;
        dropzone.querySelector("strong").textContent = e.dataTransfer.files[0].name;
      }
    });
    fileInput.addEventListener("change", () => {
      if (fileInput.files?.[0]) {
        dropzone.querySelector("strong").textContent = fileInput.files[0].name;
      }
    });
  }

  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    const url = form.getAttribute("action");
    const fd = new FormData(form);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url);
    xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
    xhr.setRequestHeader("Accept", "application/json");
    if (bar && barFill) {
      bar.classList.add("is-on");
      barFill.style.width = "8%";
    }
    xhr.upload.onprogress = (ev) => {
      if (!ev.lengthComputable || !barFill) return;
      barFill.style.width = Math.round((ev.loaded / ev.total) * 100) + "%";
    };
    xhr.onload = () => {
      if (bar) bar.classList.remove("is-on");
      let data = {};
      try {
        data = JSON.parse(xhr.responseText);
      } catch (_) {}
      if (xhr.status >= 200 && xhr.status < 300 && data.ok) {
        closeModal();
        TeacherToast(data.message || "Ressource ajoutée", "ok");
        if (listBody && data.resource) {
          const r = data.resource;
          const tr = document.createElement("tr");
          tr.className = "res-row-enter";
          tr.dataset.resId = r.id;
          tr.innerHTML = `
            <td>${r.order}</td>
            <td>${r.icon || ""} ${r.title}</td>
            <td>${r.type}</td>
            <td><span class="chip">${r.target_level}</span></td>
            <td>
              <button type="button" class="vis-toggle" data-toggle-visibility="${r.toggle_url}">
                <span class="vis-pill ${r.is_visible ? "on" : "off"}">
                  <span class="vis-text">${r.visibility_label}</span>
                </span>
              </button>
            </td>
            <td>${r.is_required ? "Oui" : "Non"}</td>
            <td class="actions">
              <a href="${r.edit_url}" class="btn btn-sm btn-secondary">Modifier</a>
              <form method="post" action="${r.delete_url}" data-confirm="Supprimer cette ressource ?">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken()}">
                <button type="submit" class="btn btn-sm btn-danger">Supprimer</button>
              </form>
            </td>`;
          listBody.prepend(tr);
          tr.querySelector("[data-toggle-visibility]")?.addEventListener("click", (ev) => {
            ev.preventDefault();
            postToggle(r.toggle_url, ev.currentTarget);
          });
          const empty = document.getElementById("res-empty");
          if (empty) empty.hidden = true;
        }
      } else {
        const msg =
          (data.errors && Object.values(data.errors).flat().join(" ")) ||
          "Impossible d’ajouter la ressource.";
        TeacherToast(msg, "err");
      }
    };
    xhr.onerror = () => {
      if (bar) bar.classList.remove("is-on");
      TeacherToast("Erreur réseau", "err");
    };
    xhr.send(fd);
  });
})();
