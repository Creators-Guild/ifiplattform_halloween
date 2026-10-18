// The pumpkin carver. Half built: the pumpkin's grid of cells is made here;
// carving and lighting it are the event issue's job (the TODOs). Each cell
// is a <button class="carver-cell"> inside #carver-pumpkin.
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

  // TODO 1: clicking a cell carves it (class "carver-cell--carved",
  // aria-pressed "true"), and clicking a carved cell fills it in again.

  // TODO 2: "Light the candle" (#carver-light) turns the light on and off:
  // the class "carver-pumpkin--lit" on the pumpkin. Change the button's
  // text too.

  // TODO 3: "Start over" (#carver-clear) fills in every cell again.
});
