// Tap-to-toggle behavior for hover-driven menu components (the top navbar's
// .dropdown-menu and the profile menu), shared since they all need
// the same fix: on touch there's no hover to reveal a submenu, so the first
// tap has to open it instead of navigating away. Guarded against double-init
// since this script is included from multiple partials that can appear
// together on the same page.
if (!window.__ifiTapToggleMenusInit) {
  window.__ifiTapToggleMenusInit = true;

  // News/Info Articles/etc. dropdown, and each sidebar item's submenu:
  // tapping the trigger toggles that one container open/closed, tapping
  // outside closes it, and only one container in the group is open at a
  // time. A .drop-option--all link inside is how a touch user actually
  // navigates, since the trigger no longer does. Defined outside the
  // DOMContentLoaded handler below since .profile-dropdown needs it
  // unconditionally (click-only, no hover reveal ever), not just gated to
  // touch devices like the rest of this file.
  const setupTapToggle = (containerSelector, triggerSelector) => {
    const containers = document.querySelectorAll(containerSelector);

    const closeContainer = (container) => {
      container.classList.remove("is-open");
      const trigger = container.querySelector(triggerSelector);
      if (trigger) {
        trigger.setAttribute("aria-expanded", "false");
      }
    };

    containers.forEach((container) => {
      // listen on the trigger (not necessarily the inner <a>) -- the
      // navbar's trigger is a <button> wrapping an <a>, which is invalid
      // nesting where exactly which element a tap resolves to isn't
      // reliable on touch. preventDefault() during bubble still cancels
      // the inner link's navigation either way.
      const trigger = container.querySelector(triggerSelector);
      if (!trigger) {
        return;
      }
      trigger.setAttribute("aria-expanded", "false");

      trigger.addEventListener("click", (event) => {
        event.preventDefault();
        const wasOpen = container.classList.contains("is-open");
        containers.forEach(closeContainer);
        if (!wasOpen) {
          container.classList.add("is-open");
          trigger.setAttribute("aria-expanded", "true");
        }
      });
    });

    document.addEventListener("click", (event) => {
      containers.forEach((container) => {
        if (
          container.classList.contains("is-open") &&
          !container.contains(event.target)
        ) {
          closeContainer(container);
        }
      });
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    // .profile-dropdown opts out of the hover-reveal .dropdown-menu
    // otherwise gets (see dropdownmenu.css) -- click-only on every device,
    // so it's wired up here regardless of hover capability.
    setupTapToggle(".profile-dropdown", "button.link");

    if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
      return; // mouse devices keep the CSS :hover reveal for these
    }

    setupTapToggle(".dropdown-menu:not(.profile-dropdown)", "button.link");
  });
}
