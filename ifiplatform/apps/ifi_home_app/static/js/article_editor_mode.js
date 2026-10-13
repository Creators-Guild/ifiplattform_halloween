document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("editor-mode-toggle");
  if (!toggle) {
    return;
  }

  const stateLabel = document.getElementById("editor-mode-toggle-state");
  const STORAGE_KEY = "ifiEditorMode";

  const apply = (isOn) => {
    document.body.classList.toggle("editor-mode-on", isOn);
    toggle.setAttribute("aria-pressed", String(isOn));
    toggle.classList.toggle("is-on", isOn);
    if (stateLabel) {
      stateLabel.textContent = isOn ? "On" : "Off";
    }
  };

  apply(localStorage.getItem(STORAGE_KEY) === "true");

  toggle.addEventListener("click", () => {
    const isOn = !document.body.classList.contains("editor-mode-on");
    localStorage.setItem(STORAGE_KEY, String(isOn));
    apply(isOn);
  });
});
