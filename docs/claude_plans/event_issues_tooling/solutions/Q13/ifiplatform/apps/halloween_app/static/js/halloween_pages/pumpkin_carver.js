// The pumpkin carver: click cells to carve them, then light the candle.
// Each cell is a <button class="carver-cell"> inside #carver-pumpkin.
document.addEventListener("DOMContentLoaded", () => {
  const pumpkin = document.getElementById("carver-pumpkin");
  const COLUMNS = 14;
  const ROWS = 11;

  for (let i = 0; i < COLUMNS * ROWS; i += 1) {
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "carver-cell";
    cell.setAttribute("aria-label", `Row ${Math.floor(i / COLUMNS) + 1}, column ${(i % COLUMNS) + 1}`);
    cell.setAttribute("aria-pressed", "false");
    pumpkin.append(cell);
  }

  const light = document.getElementById("carver-light");

  pumpkin.addEventListener("click", (event) => {
    const cell = event.target.closest(".carver-cell");
    if (!cell) {
      return;
    }
    const carved = cell.classList.toggle("carver-cell--carved");
    cell.setAttribute("aria-pressed", String(carved));
  });

  light.addEventListener("click", () => {
    const lit = pumpkin.classList.toggle("carver-pumpkin--lit");
    light.textContent = lit ? "Blow out the candle" : "Light the candle";
  });

  document.getElementById("carver-clear").addEventListener("click", () => {
    pumpkin.querySelectorAll(".carver-cell--carved").forEach((cell) => {
      cell.classList.remove("carver-cell--carved");
      cell.setAttribute("aria-pressed", "false");
    });
  });
});
