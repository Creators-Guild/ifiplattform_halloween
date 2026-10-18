// Zombie typing. Half built: the field, the buttons and the game loop are
// here; the zombies are the event issue's job (the TODOs). Each zombie is a
// <div class="zt-zombie"> inside #zt-field, with its word as text.
document.addEventListener("DOMContentLoaded", () => {
  const field = document.getElementById("zt-field");
  const input = document.getElementById("zt-input");
  const scoreOut = document.getElementById("zt-score");
  const livesOut = document.getElementById("zt-lives");
  const message = document.getElementById("zt-message");
  const words = ["bug", "merge", "commit", "deadline", "segfault", "pumpkin", "python", "linux"];
  let zombies = [];
  let score = 0;
  let lives = 3;
  let loop = null;
  let ticks = 0;

  function spawnZombie() {
    // TODO 1: make a <div class="zt-zombie"> with a random word from words,
    // put it in field at the far right, at a random height, and remember
    // it in zombies (for example as { element, word, x: 100 }).
  }

  function moveZombies() {
    // TODO 2: move every zombie a little to the left (x goes from 100 to
    // 0, in %). A zombie that reaches 0 bites: remove it, lives - 1, and
    // at 0 lives call gameOver().
  }

  function gameOver() {
    clearInterval(loop);
    input.disabled = true;
    message.textContent = `Game over! You stopped ${score} zombies.`;
  }

  input.addEventListener("input", () => {
    // TODO 3: if input.value is the word of a zombie: remove that zombie,
    // score + 1, show the score, and empty the input.
  });

  document.getElementById("zt-start").addEventListener("click", () => {
    zombies.forEach((zombie) => zombie.element.remove());
    zombies = [];
    score = 0;
    lives = 3;
    ticks = 0;
    scoreOut.textContent = score;
    livesOut.textContent = lives;
    message.textContent = "";
    input.disabled = false;
    input.value = "";
    input.focus();
    clearInterval(loop);
    loop = setInterval(() => {
      ticks += 1;
      if (ticks % 20 === 1) {
        spawnZombie();
      }
      moveZombies();
    }, 100);
  });
});
