// Bat snake. Half built: the board, the arrow keys and the game loop are
// here; moving, eating and crashing are the event issue's job (the TODOs).
// The board is SIZE × SIZE cells; a spot is { x, y } with 0 at the top left.
document.addEventListener("DOMContentLoaded", () => {
  const boardElement = document.getElementById("bs-board");
  const scoreOut = document.getElementById("bs-score");
  const message = document.getElementById("bs-message");
  const SIZE = 15;
  const cells = [];
  let snake = [];
  let direction = { x: 1, y: 0 };
  let candy = null;
  let score = 0;
  let loop = null;

  for (let i = 0; i < SIZE * SIZE; i += 1) {
    const cell = document.createElement("div");
    cell.className = "bs-cell";
    boardElement.append(cell);
    cells.push(cell);
  }

  function cellAt(spot) {
    return cells[spot.y * SIZE + spot.x];
  }

  function draw() {
    cells.forEach((cell) => {
      cell.className = "bs-cell";
      cell.textContent = "";
    });
    snake.forEach((spot) => cellAt(spot).classList.add("bs-cell--snake"));
    if (snake.length) {
      cellAt(snake[0]).textContent = "🦇";
    }
    if (candy) {
      cellAt(candy).classList.add("bs-cell--candy");
      cellAt(candy).textContent = "🍬";
    }
    scoreOut.textContent = score;
  }

  function placeCandy() {
    // TODO 1: put candy on a random spot that isn't part of the snake.
  }

  function step() {
    // TODO 2: the new head is snake[0] moved one cell in direction. Put it
    // first in snake (unshift). If it's on the candy: score + 1 and
    // placeCandy(). If not: remove the tail (pop), so the snake keeps its
    // length.
    // TODO 3: if the new head is outside the board or on the snake itself:
    // gameOver() instead.
    draw();
  }

  function gameOver() {
    clearInterval(loop);
    message.textContent = `Game over! The bat ate ${score} candy.`;
  }

  document.addEventListener("keydown", (event) => {
    const turns = {
      ArrowUp: { x: 0, y: -1 },
      ArrowDown: { x: 0, y: 1 },
      ArrowLeft: { x: -1, y: 0 },
      ArrowRight: { x: 1, y: 0 },
    };
    if (!turns[event.key] || !loop) {
      return;
    }
    event.preventDefault();
    direction = turns[event.key];
  });

  document.getElementById("bs-start").addEventListener("click", () => {
    snake = [{ x: 3, y: 7 }, { x: 2, y: 7 }, { x: 1, y: 7 }];
    direction = { x: 1, y: 0 };
    score = 0;
    message.textContent = "";
    placeCandy();
    clearInterval(loop);
    loop = setInterval(step, 160);
    draw();
  });
});
