document.addEventListener("DOMContentLoaded", () => {
  const lightbox = document.querySelector(".tool-lightbox");
  const triggers = document.querySelectorAll(".tool-preview-trigger");
  if (!lightbox || triggers.length === 0) {
    return;
  }

  const lightboxImage = lightbox.querySelector(".tool-lightbox-image");
  const closeButton = lightbox.querySelector(".tool-lightbox-close");

  const open = (trigger) => {
    const triggerImage = trigger.querySelector("img");
    lightboxImage.src = trigger.dataset.full;
    lightboxImage.alt = triggerImage ? triggerImage.alt : "";
    lightbox.hidden = false;
    document.body.classList.add("tool-lightbox-open");
    closeButton.focus();
  };

  const close = () => {
    lightbox.hidden = true;
    lightboxImage.src = "";
    document.body.classList.remove("tool-lightbox-open");
  };

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", () => open(trigger));
  });

  closeButton.addEventListener("click", close);

  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) {
      close();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !lightbox.hidden) {
      close();
    }
  });
});
