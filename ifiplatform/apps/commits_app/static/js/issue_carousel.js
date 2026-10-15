// The issue list's groups (core/issue_sections.html) scroll sideways on their
// own, snapping to pages (issue_list.css). This only adds the prev/next
// buttons and the "1 / 3" counter, and hides the scrollbar once they work.
document.querySelectorAll("[data-carousel]").forEach((section) => {
  const track = section.querySelector("[data-carousel-track]");
  const controls = section.querySelector("[data-carousel-controls]");
  const prev = section.querySelector("[data-carousel-prev]");
  const next = section.querySelector("[data-carousel-next]");
  const status = section.querySelector("[data-carousel-status]");
  const motion = window.matchMedia("(prefers-reduced-motion: no-preference)");

  track.classList.add("issue-list--js");

  const page = () => track.clientWidth + (parseFloat(getComputedStyle(track).columnGap) || 0);

  const update = () => {
    const max = track.scrollWidth - track.clientWidth;
    controls.hidden = max <= 1;
    prev.disabled = track.scrollLeft <= 1;
    next.disabled = track.scrollLeft >= max - 1;
    // A last page that's only partly full scrolls less than a whole page,
    // so any leftover counts as one more page.
    const pages = 1 + Math.ceil(Math.max(0, max - 1) / page());
    const current = next.disabled ? pages : Math.round(track.scrollLeft / page()) + 1;
    status.textContent = `${current} / ${pages}`;
  };

  const go = (direction) =>
    track.scrollBy({ left: direction * page(), behavior: motion.matches ? "smooth" : "auto" });

  prev.addEventListener("click", () => go(-1));
  next.addEventListener("click", () => go(1));
  track.addEventListener("scroll", update, { passive: true });
  new ResizeObserver(update).observe(track);
  update();
});
