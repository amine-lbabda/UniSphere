(function () {
  if (!document.body.classList.contains("space-student")) return;
  const content = document.querySelector(".app-content");
  if (content) content.classList.add("page-enter");
})();
