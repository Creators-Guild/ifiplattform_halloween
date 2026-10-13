document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("beta-notice-modal");
  if (!modal) {
    return;
  }

  const STORAGE_KEY = "ifiBetaNoticeSeen";
  // Dev/QA escape hatch: append ?beta_notice to any URL (e.g.
  // /en/?beta_notice) to see the modal again without clearing
  // localStorage by hand in devtools.
  const forceShow = new URLSearchParams(window.location.search).has("beta_notice");
  if (!forceShow && localStorage.getItem(STORAGE_KEY) === "true") {
    return;
  }

  const backdrop = document.getElementById("beta-notice-backdrop");
  const dismissButton = document.getElementById("beta-notice-dismiss");

  const dismiss = () => {
    localStorage.setItem(STORAGE_KEY, "true");
    modal.hidden = true;
  };

  modal.hidden = false;
  if (dismissButton) {
    dismissButton.addEventListener("click", dismiss);
  }
  if (backdrop) {
    backdrop.addEventListener("click", dismiss);
  }
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) {
      dismiss();
    }
  });
});
