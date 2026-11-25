(function () {
  const root = document.getElementById("course-builder");
  if (!root) return;

  const reorderUrl = root.dataset.reorderUrl;
  const createUrl = root.dataset.createUrl;
  const csrf = () => {
    const el = document.querySelector("[name=csrfmiddlewaretoken]");
    if (el) return el.value;
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  };

  const statusEl = document.getElementById("builder-save-status");
  const chaptersHost = document.getElementById("builder-chapters");
  const unassignedList = document.getElementById("builder-unassigned-list");
  let saveTimer = null;
  let dragItem = null;
  let dragChapter = null;
  let placeholder = null;

  function setStatus(text, cls) {
    if (!statusEl) return;
    statusEl.textContent = text || "";
    statusEl.className = "builder-save-status" + (cls ? " " + cls : "");
  }

  function collectPayload() {
    const chapters = [...chaptersHost.querySelectorAll(".builder-chapter")].map((ch) => ({
      id: Number(ch.dataset.chapterId),
      items: [...ch.querySelectorAll(".builder-item-list .builder-item")].map((it) => ({
        type: it.dataset.type,
        id: Number(it.dataset.id),
      })),
    }));
    const unassigned = [...unassignedList.querySelectorAll(".builder-item")].map((it) => ({
      type: it.dataset.type,
      id: Number(it.dataset.id),
    }));
    return { chapters, unassigned };
  }

  async function persist() {
    setStatus("Saving structure…", "is-busy");
    try {
      const res = await fetch(reorderUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrf(),
        },
        body: JSON.stringify(collectPayload()),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.message || "Save failed");
      setStatus("✓ Structure saved", "is-ok");
      if (window.TeacherToast) TeacherToast(data.message || "Structure saved", "ok");
      window.setTimeout(() => setStatus(""), 2200);
      reindexChapters();
    } catch (e) {
      setStatus(e.message || "Unable to save", "is-err");
      if (window.TeacherToast) TeacherToast(e.message || "Unable to save", "err");
    }
  }

  function scheduleSave() {
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(persist, 350);
  }

  function reindexChapters() {
    chaptersHost.querySelectorAll(".builder-chapter").forEach((ch, i) => {
      const label = ch.querySelector(".builder-chapter-label");
      if (label) label.textContent = "Chapter " + (i + 1);
    });
    document.querySelectorAll(".builder-item-list").forEach((list) => {
      const hint = list.querySelector(".builder-empty-hint");
      const hasItems = list.querySelector(".builder-item");
      if (hint) hint.hidden = !!hasItems;
    });
  }

  function ensurePlaceholder() {
    if (!placeholder) {
      placeholder = document.createElement("div");
      placeholder.className = "builder-item-placeholder";
      placeholder.setAttribute("aria-hidden", "true");
    }
    return placeholder;
  }

  function bindItemDrag(item) {
    item.setAttribute("draggable", "true");
    item.addEventListener("dragstart", (e) => {
      dragItem = item;
      dragChapter = null;
      item.classList.add("is-dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", item.dataset.type + ":" + item.dataset.id);
      window.setTimeout(() => ensurePlaceholder(), 0);
    });
    item.addEventListener("dragend", () => {
      item.classList.remove("is-dragging");
      placeholder?.remove();
      dragItem = null;
      scheduleSave();
    });
  }

  function bindListDrop(list) {
    list.addEventListener("dragover", (e) => {
      if (!dragItem) return;
      e.preventDefault();
      list.classList.add("is-drop-target");
      const ph = ensurePlaceholder();
      const after = getDragAfterElement(list, e.clientY);
      if (after == null) list.appendChild(ph);
      else list.insertBefore(ph, after);
    });
    list.addEventListener("dragleave", () => list.classList.remove("is-drop-target"));
    list.addEventListener("drop", (e) => {
      e.preventDefault();
      list.classList.remove("is-drop-target");
      if (!dragItem) return;
      const ph = ensurePlaceholder();
      if (ph.parentNode === list) list.insertBefore(dragItem, ph);
      else list.appendChild(dragItem);
      ph.remove();
      const hint = list.querySelector(".builder-empty-hint");
      if (hint) hint.hidden = true;
      reindexChapters();
    });
  }

  function getDragAfterElement(container, y) {
    const els = [...container.querySelectorAll(".builder-item:not(.is-dragging)")];
    return els.reduce(
      (closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
          return { offset, element: child };
        }
        return closest;
      },
      { offset: Number.NEGATIVE_INFINITY, element: null }
    ).element;
  }

  function bindChapterDrag(chapter) {
    const head = chapter.querySelector(".builder-chapter-head");
    if (!head) return;
    head.setAttribute("draggable", "true");
    head.addEventListener("dragstart", (e) => {
      if (e.target.closest("input,button,a")) {
        e.preventDefault();
        return;
      }
      dragChapter = chapter;
      dragItem = null;
      chapter.classList.add("is-dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", "chapter:" + chapter.dataset.chapterId);
    });
    head.addEventListener("dragend", () => {
      chapter.classList.remove("is-dragging");
      dragChapter = null;
      chaptersHost.querySelectorAll(".builder-chapter").forEach((c) =>
        c.classList.remove("is-drop-target")
      );
      scheduleSave();
    });
    chapter.addEventListener("dragover", (e) => {
      if (!dragChapter || dragChapter === chapter) return;
      e.preventDefault();
      chapter.classList.add("is-drop-target");
      const rect = chapter.getBoundingClientRect();
      const before = e.clientY < rect.top + rect.height / 2;
      if (before) chaptersHost.insertBefore(dragChapter, chapter);
      else chaptersHost.insertBefore(dragChapter, chapter.nextSibling);
    });
    chapter.addEventListener("dragleave", () => chapter.classList.remove("is-drop-target"));
    chapter.addEventListener("drop", (e) => {
      e.preventDefault();
      chapter.classList.remove("is-drop-target");
      reindexChapters();
    });
  }

  function wireChapter(chapter) {
    bindChapterDrag(chapter);
    const list = chapter.querySelector(".builder-item-list");
    if (list) bindListDrop(list);
    chapter.querySelectorAll(".builder-item").forEach(bindItemDrag);

    const titleInput = chapter.querySelector(".builder-chapter-title");
    titleInput?.addEventListener("change", async () => {
      const url = chapter.dataset.renameUrl;
      const fd = new FormData();
      fd.set("title", titleInput.value.trim());
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrf(),
            Accept: "application/json",
          },
          body: fd,
        });
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.message || "Rename failed");
        if (window.TeacherToast) TeacherToast("Chapter renamed", "ok");
      } catch (e) {
        if (window.TeacherToast) TeacherToast(e.message || "Rename failed", "err");
      }
    });

    chapter.querySelector("[data-delete-chapter]")?.addEventListener("click", async () => {
      if (!confirm("Remove this chapter? Items move to Unassigned.")) return;
      const url = chapter.dataset.deleteUrl;
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrf(),
            Accept: "application/json",
          },
        });
        const data = await res.json();
        if (!res.ok || !data.ok) throw new Error(data.message || "Delete failed");
        const items = chapter.querySelectorAll(".builder-item");
        items.forEach((it) => unassignedList.appendChild(it));
        chapter.remove();
        reindexChapters();
        scheduleSave();
        if (window.TeacherToast) TeacherToast(data.message || "Chapter removed", "ok");
      } catch (e) {
        if (window.TeacherToast) TeacherToast(e.message || "Delete failed", "err");
      }
    });
  }

  chaptersHost.querySelectorAll(".builder-chapter").forEach(wireChapter);
  if (unassignedList) {
    bindListDrop(unassignedList);
    unassignedList.querySelectorAll(".builder-item").forEach(bindItemDrag);
  }

  document.getElementById("builder-add-chapter")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.currentTarget;
    const input = form.querySelector('[name="title"]');
    const fd = new FormData(form);
    try {
      const res = await fetch(createUrl, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrf(),
          Accept: "application/json",
        },
        body: fd,
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.message || "Could not add chapter");
      const ch = data.chapter;
      const index = chaptersHost.querySelectorAll(".builder-chapter").length + 1;
      const el = document.createElement("section");
      el.className = "builder-chapter";
      el.dataset.chapterId = ch.id;
      el.dataset.renameUrl = (root.dataset.renameUrlTemplate || "").replace("/0/", "/" + ch.id + "/");
      el.dataset.deleteUrl = (root.dataset.deleteUrlTemplate || "").replace("/0/", "/" + ch.id + "/");
      el.innerHTML = `
        <div class="builder-chapter-head">
          <span class="builder-chapter-handle" aria-hidden="true">☰</span>
          <span class="builder-chapter-label">Chapter ${index}</span>
          <input class="builder-chapter-title" type="text" value="${escapeAttr(ch.title)}" aria-label="Chapter title">
          <div class="builder-chapter-actions">
            <button type="button" class="btn btn-ghost btn-sm" data-delete-chapter>Remove</button>
          </div>
        </div>
        <ul class="builder-item-list" data-list="chapter">
          <li class="builder-empty-hint">Drop resources or quizzes here</li>
        </ul>`;
      chaptersHost.appendChild(el);
      wireChapter(el);
      if (input) input.value = "";
      if (window.TeacherToast) TeacherToast(data.message || "Chapter added", "ok");
      scheduleSave();
    } catch (err) {
      if (window.TeacherToast) TeacherToast(err.message || "Could not add chapter", "err");
    }
  });

  document.getElementById("builder-save-now")?.addEventListener("click", (e) => {
    e.preventDefault();
    persist();
  });

  function escapeAttr(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;");
  }

  reindexChapters();
})();
