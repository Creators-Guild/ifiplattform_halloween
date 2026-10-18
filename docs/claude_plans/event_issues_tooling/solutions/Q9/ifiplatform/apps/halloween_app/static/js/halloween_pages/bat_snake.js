// Bat snake: steer the bat to the candy; it grows with every one.
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

  function onSnake(spot) {
    return snake.some((part) => part.x === spot.x && part.y === spot.y);
  }

  function placeCandy() {
    do {
      candy = { x: Math.floor(Math.random() * SIZE), y: Math.floor(Math.random() * SIZE) };
    } while (onSnake(candy));
  }

  function step() {
    const head = { x: snake[0].x + direction.x, y: snake[0].y + direction.y };
    const outside = head.x < 0 || head.y < 0 || head.x >= SIZE || head.y >= SIZE;
    if (outside || onSnake(head)) {
      gameOver();
      return;
    }
    snake.unshift(head);
    if (head.x === candy.x && head.y === candy.y) {
      score += 1;
      placeCandy();
    } else {
      snake.pop();
    }
    draw();
  }

  function gameOver() {
    clearInterval(loop);
    loop = null;
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
    const turn = turns[event.key];
    const second = snake[1];
    if (second && snake[0].x + turn.x === second.x && snake[0].y + turn.y === second.y) {
      return;
    }
    direction = turn;
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
