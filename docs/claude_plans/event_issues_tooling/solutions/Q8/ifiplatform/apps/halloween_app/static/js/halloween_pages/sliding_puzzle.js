// The moon puzzle: a 3×3 sliding puzzle.
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
    const empty = board.indexOf(0);
    const sameRow = Math.floor(spot / 3) === Math.floor(empty / 3);
    const sameColumn = spot % 3 === empty % 3;
    return (sameRow && Math.abs(spot - empty) === 1) || (sameColumn && Math.abs(spot - empty) === 3);
  }

  function swapWithEmpty(spot) {
    const empty = board.indexOf(0);
    [board[spot], board[empty]] = [board[empty], board[spot]];
  }

  function move(spot) {
    if (!isNextToEmpty(spot)) {
      return;
    }
    swapWithEmpty(spot);
    moves += 1;
    draw();
    if (board.every((piece, i) => piece === SOLVED[i])) {
      message.textContent = `The moon is whole again, in ${moves} moves! 🌕`;
    }
  }

  function shuffle() {
    for (let i = 0; i < 200; i += 1) {
      const allowed = board.map((_piece, spot) => spot).filter(isNextToEmpty);
      swapWithEmpty(allowed[Math.floor(Math.random() * allowed.length)]);
    }
    moves = 0;
    message.textContent = "";
    draw();
  }

  document.getElementById("sp-shuffle").addEventListener("click", shuffle);
  draw();
});
