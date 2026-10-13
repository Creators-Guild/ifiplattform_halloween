document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".position-info-widget").forEach((widget) => {
    const openButton = widget.querySelector(".position-info-button");
    const panel = widget.querySelector(".position-info-panel");
    const closeButton = widget.querySelector(".position-info-close");
    if (!openButton || !panel || !closeButton) {
      return;
    }

    // Mobile only (union_position_info.css switches the panel to
    // position:fixed there) -- places the panel just under the icon, same
    // gap as dropdown_menu.js's profile-dropdown positioning, but pushed
    // back up if that would run it off the bottom of the screen.
    // offsetHeight needs the panel already unhidden to measure.
    const positionPanelForMobile = () => {
      if (!window.matchMedia("(max-width: 45rem)").matches) {
        panel.style.top = "";
        return;
      }
      const rect = openButton.getBoundingClientRect();
      const margin = 8;
      const maxTop = Math.max(window.innerHeight - panel.offsetHeight - margin, margin);
      const top = Math.min(rect.bottom + margin, maxTop);
      panel.style.top = `${top}px`;
    };

    const openPanel = () => {
      panel.hidden = false;
      openButton.setAttribute("aria-expanded", "true");
      closeButton.focus();
      positionPanelForMobile();
    };

    const closePanel = () => {
      panel.hidden = true;
      openButton.setAttribute("aria-expanded", "false");
    };

    window.addEventListener("resize", () => {
      if (!panel.hidden) {
        positionPanelForMobile();
      }
    });

    openButton.addEventListener("click", (event) => {
      event.stopPropagation();
      if (panel.hidden) {
        openPanel();
      } else {
        closePanel();
      }
    });

    closeButton.addEventListener("click", closePanel);

    // No backdrop by design -- the rest of the page stays interactable, so
    // closing on an outside click means listening document-wide instead.
    document.addEventListener("click", (event) => {
      if (!panel.hidden && !panel.contains(event.target) && !widget.contains(event.target)) {
        closePanel();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !panel.hidden) {
        closePanel();
        openButton.focus();
      }
    });
  });
});
