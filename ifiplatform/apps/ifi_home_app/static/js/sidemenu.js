// A <details> never closes on an outside click by itself -- close an open
// sidemenu when a tap/click lands anywhere outside it. Only matters on
// touch/mobile: on desktop the sidemenu opens on hover and ignores [open]
// (see sidemenu.css). Guarded since both sidemenu partials include this.
if (!window.__ifiSidemenuInit) {
  window.__ifiSidemenuInit = true;

  document.addEventListener("click", (event) => {
    document.querySelectorAll("details.sidemenu[open]").forEach((menu) => {
      if (!menu.contains(event.target)) {
        menu.open = false;
      }
    });
  });
}
