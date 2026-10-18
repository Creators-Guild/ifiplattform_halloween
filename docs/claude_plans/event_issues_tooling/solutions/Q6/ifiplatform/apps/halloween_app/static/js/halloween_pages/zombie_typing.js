// Zombie typing: words walk in from the right; type one to stop that
// zombie. Each zombie is a <div class="zt-zombie"> inside #zt-field.
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
    const word = words[Math.floor(Math.random() * words.length)];
    const element = document.createElement("div");
    element.className = "zt-zombie";
    element.textContent = word;
    element.style.top = `${10 + Math.random() * 70}%`;
    field.append(element);
    zombies.push({ element, word, x: 100 });
  }

  function moveZombies() {
    const speed = 0.4 + score * 0.03;
    zombies.forEach((zombie) => {
      zombie.x -= speed;
      zombie.element.style.left = `${zombie.x}%`;
    });
    const biters = zombies.filter((zombie) => zombie.x <= 0);
    biters.forEach((zombie) => zombie.element.remove());
    zombies = zombies.filter((zombie) => zombie.x > 0);
    if (biters.length) {
      lives = Math.max(0, lives - biters.length);
      livesOut.textContent = lives;
      if (lives === 0) {
        gameOver();
      }
    }
  }

  function gameOver() {
    clearInterval(loop);
    input.disabled = true;
    message.textContent = `Game over! You stopped ${score} zombies.`;
  }

  input.addEventListener("input", () => {
    const typed = input.value.trim().toLowerCase();
    const hit = zombies.find((zombie) => zombie.word === typed);
    if (!hit) {
      return;
    }
    hit.element.remove();
    zombies = zombies.filter((zombie) => zombie !== hit);
    score += 1;
    scoreOut.textContent = score;
    input.value = "";
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
