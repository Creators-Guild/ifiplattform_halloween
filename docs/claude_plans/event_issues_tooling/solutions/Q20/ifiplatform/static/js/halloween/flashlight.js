// Flashlight mode: a 🔦 button in the corner makes the page dark, except
// for a circle of light around the mouse. Esc turns it off again.
document.addEventListener("DOMContentLoaded", () => {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "flashlight-toggle";
  button.textContent = "🔦";
  button.setAttribute("aria-label", "Flashlight mode");
  button.setAttribute("aria-pressed", "false");

  const dark = document.createElement("div");
  dark.className = "flashlight";
  dark.hidden = true;
  dark.setAttribute("aria-hidden", "true");
  document.body.append(dark, button);

  function aim(x, y) {
    dark.style.setProperty("--x", `${x}px`);
    dark.style.setProperty("--y", `${y}px`);
  }

  function turn(on) {
    dark.hidden = !on;
    button.setAttribute("aria-pressed", String(on));
    aim(window.innerWidth / 2, window.innerHeight / 2);
  }

  button.addEventListener("click", () => turn(dark.hidden));
  document.addEventListener("pointermove", (event) => aim(event.clientX, event.clientY));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !dark.hidden) {
      turn(false);
    }
  });
});
