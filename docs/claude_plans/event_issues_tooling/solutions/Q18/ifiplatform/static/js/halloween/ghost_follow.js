// A little ghost that follows the mouse around, a bit behind it. Only with
// a mouse (not on touch screens), and not when animations are turned off.
document.addEventListener("DOMContentLoaded", () => {
  const hasMouse = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!hasMouse || reduceMotion) {
    return;
  }
  const ghost = document.createElement("div");
  ghost.className = "ghost-follower";
  ghost.setAttribute("aria-hidden", "true");
  ghost.textContent = "👻";
  document.body.append(ghost);

  const target = { x: -100, y: -100 };
  const position = { x: -100, y: -100 };

  document.addEventListener("pointermove", (event) => {
    target.x = event.clientX + 18;
    target.y = event.clientY + 18;
    ghost.classList.add("ghost-follower--visible");
  });
  document.documentElement.addEventListener("pointerleave", () => {
    ghost.classList.remove("ghost-follower--visible");
  });

  function follow() {
    position.x += (target.x - position.x) * 0.08;
    position.y += (target.y - position.y) * 0.08;
    ghost.style.translate = `${position.x}px ${position.y}px`;
    requestAnimationFrame(follow);
  }
  follow();
});
