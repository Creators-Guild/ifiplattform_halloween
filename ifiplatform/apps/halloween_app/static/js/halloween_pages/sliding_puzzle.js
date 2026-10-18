// The moon puzzle: a 3×3 sliding puzzle. Half built: the board is drawn
// here; moving the pieces is the event issue's job (the TODOs).
// board is a list of 9 numbers, row by row: 1-8 are the pieces, 0 is the
// empty spot. Solved is [1, 2, 3, 4, 5, 6, 7, 8, 0].
document.addEventListener("DOMContentLoaded", () => {
  const boardElement = document.getElementById("sp-board");
  const movesOut = document.getElementById("sp-moves");
  const message = document.getElementById("sp-message");
  const SOLVED = [1, 2, 3, 4, 5, 6, 7, 8, 0];
  let board = [...SOLVED];
  let moves = 0;

  function draw() {
    boardElement.textContent = "";
    board.forEach((piece, spot) => {
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = piece === 0 ? "sp-tile sp-tile--empty" : "sp-tile";
      tile.disabled = piece === 0;
      tile.setAttribute("aria-label", piece === 0 ? "Empty" : `Piece ${piece}`);
      // Where this piece belongs, for the picture: column and row 0-2.
      tile.style.setProperty("--col", (piece - 1) % 3);
      tile.style.setProperty("--row", Math.floor((piece - 1) / 3));
      tile.addEventListener("click", () => move(spot));
      boardElement.append(tile);
    });
    movesOut.textContent = moves;
  }

  function isNextToEmpty(spot) {
    // TODO 1: true if spot is right above, below, left or right of the
    // empty spot (board.indexOf(0)). Careful: spot 2 and spot 3 are next
    // to each other in the list, but not on the board.
    return false;
  }

  function move(spot) {
    // TODO 2: if isNextToEmpty(spot): swap the piece with the empty spot,
    // moves + 1, and draw() again. When board is the same as SOLVED, show
    // a message.
  }

  function shuffle() {
    // TODO 3: make about 200 random moves that are allowed (use
    // isNextToEmpty). Random swaps can make a puzzle that can't be solved.
    moves = 0;
    message.textContent = "";
    draw();
  }

  document.getElementById("sp-shuffle").addEventListener("click", shuffle);
  draw();
});
