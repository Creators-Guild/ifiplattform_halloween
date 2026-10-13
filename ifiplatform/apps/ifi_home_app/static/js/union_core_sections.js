// Purpose/Activities/Bylaws/Sitting Members/Open Positions (.union-section,
// union_page.html) are plain <details open> so they degrade to
// always-visible content with no JS -- this only closes them on initial
// load, and only on mobile (union_sections.css leaves them non-interactive
// above that breakpoint). One-time check, not a resize listener: collapsing
// content out from under a reader who resizes their window would be
// jarring.
document.addEventListener("DOMContentLoaded", () => {
  if (!window.matchMedia("(max-width: 45rem)").matches) {
    return;
  }
  document.querySelectorAll(".union-section").forEach((section) => {
    section.open = false;
  });
});
