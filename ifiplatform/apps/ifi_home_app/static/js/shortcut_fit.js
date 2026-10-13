// Fits each homepage shortcut title beside its icon: full title if it fits,
// else the group's short title (if it has one), else shrink the text down to
// MIN_FONT_PX -- anything still too long is cut off with an ellipsis by
// home_shortcuts.css. CSS alone can't tell whether a title overflows, hence
// this script. Re-runs on resize and once the web font has loaded, since
// both change how wide a title is.
(() => {
  const MIN_FONT_PX = 14;

  const fit = (title) => {
    const box = title.parentElement;
    title.textContent = title.dataset.full;
    box.style.fontSize = "";
    let size = parseFloat(getComputedStyle(box).fontSize);
    if (!size) {
      return; // mobile: titles are hidden, only the icon shows
    }
    const overflows = () => box.scrollWidth > box.clientWidth;
    if (overflows() && title.dataset.short) {
      title.textContent = title.dataset.short;
    }
    while (overflows() && size > MIN_FONT_PX) {
      size = Math.max(size - 1, MIN_FONT_PX);
      box.style.fontSize = `${size}px`;
    }
  };

  const fitAll = () => document.querySelectorAll("#home-shortcuts .shortcut-title").forEach(fit);

  document.addEventListener("DOMContentLoaded", () => {
    const shortcuts = document.getElementById("home-shortcuts");
    if (!shortcuts) {
      return;
    }
    fitAll();
    document.fonts.ready.then(fitAll);
    let lastWidth = shortcuts.clientWidth;
    new ResizeObserver(() => {
      if (shortcuts.clientWidth !== lastWidth) {
        lastWidth = shortcuts.clientWidth;
        fitAll();
      }
    }).observe(shortcuts);
  });
})();
