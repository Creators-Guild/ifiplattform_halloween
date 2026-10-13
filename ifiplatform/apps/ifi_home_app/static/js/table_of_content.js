document.addEventListener("DOMContentLoaded", () => {
  // The desktop floating icon (popover, no backdrop) and the mobile
  // title-row icon (full-screen dialog, with backdrop) are two entirely
  // separate components -- CSS shows only one at a time per viewport width,
  // but both can exist in the DOM together, so each is wired up here
  // regardless of which is currently visible.
  document.querySelectorAll(".toc-widget").forEach((widget) => {
    const openButton = widget.querySelector(".toc-open-button");
    const panel = widget.querySelector(".toc-overlay-panel");
    const closeButton = widget.querySelector(".toc-overlay-close");
    if (!openButton || !panel || !closeButton) {
      return;
    }

    const openPanel = () => {
      panel.hidden = false;
      openButton.setAttribute("aria-expanded", "true");
      closeButton.focus();
    };

    const closePanel = () => {
      panel.hidden = true;
      openButton.setAttribute("aria-expanded", "false");
    };

    openButton.addEventListener("click", (event) => {
      event.stopPropagation();
      if (panel.hidden) {
        openPanel();
      } else {
        closePanel();
      }
    });

    closeButton.addEventListener("click", closePanel);

    panel.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        closePanel();
      }
    });

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

  const modalOpenButton = document.getElementById("toc-modal-open");
  const modal = document.getElementById("toc-modal");
  const modalCloseButton = document.getElementById("toc-modal-close");
  const modalBackdrop = document.getElementById("toc-modal-backdrop");
  if (modalOpenButton && modal && modalCloseButton && modalBackdrop) {
    const openModal = () => {
      modal.hidden = false;
      document.body.classList.add("toc-modal-open");
      modalCloseButton.focus();
    };

    const closeModal = () => {
      modal.hidden = true;
      document.body.classList.remove("toc-modal-open");
      modalOpenButton.focus();
    };

    modalOpenButton.addEventListener("click", openModal);
    modalCloseButton.addEventListener("click", closeModal);
    modalBackdrop.addEventListener("click", closeModal);

    modal.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        closeModal();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal.hidden) {
        closeModal();
      }
    });
  }
});
