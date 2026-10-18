// Type "boo" anywhere on the page (not in a text field): the whole page
// spins around once. Nothing moves when animations are turned off.
document.addEventListener("DOMContentLoaded", () => {
  const code = "boo";
  const page = document.querySelector(".page-layout");
  let typed = "";

  document.addEventListener("keydown", (event) => {
    if (event.target.closest("input, textarea, select, [contenteditable]")) {
      return;
    }
    typed = (typed + event.key.toLowerCase()).slice(-code.length);
    if (typed !== code || !page) {
      return;
    }
    typed = "";
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }
    page.animate([{ rotate: "0deg" }, { rotate: "360deg" }], { duration: 1500, easing: "ease-in-out" });
  });
});
