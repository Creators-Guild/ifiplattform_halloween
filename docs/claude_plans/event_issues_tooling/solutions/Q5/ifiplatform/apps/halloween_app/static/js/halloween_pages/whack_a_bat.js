// Whack-a-bat. Half built: the board, the buttons and the timer are here; the
// bats are the event issue's job (the TODOs). Each hole is a <button
// class="wab-hole"> in templates/halloween/whack_a_bat.html.
document.addEventListener("DOMContentLoaded", () => {
  const holes = [...document.querySelectorAll(".wab-hole")];
  const scoreOut = document.getElementById("wab-score");
  const timeOut = document.getElementById("wab-time");
  const start = document.getElementById("wab-start");
  let score = 0;
  let timeLeft = 30;
  let ticker = null;

  function clearHoles() {
    holes.forEach((hole) => {
      hole.textContent = "";
    });
  }

  function showBat() {
    clearHoles();
    holes[Math.floor(Math.random() * holes.length)].textContent = "🦇";
  }

  holes.forEach((hole) => {
    hole.addEventListener("click", () => {
      if (hole.textContent === "🦇") {
        score += 1;
        scoreOut.textContent = score;
        hole.textContent = "";
      }
    });
  });

  start.addEventListener("click", () => {
    score = 0;
    timeLeft = 30;
    scoreOut.textContent = score;
    clearInterval(ticker);
    ticker = setInterval(() => {
      timeLeft -= 1;
      timeOut.textContent = timeLeft;
      if (timeLeft <= 0) {
        clearInterval(ticker);
        clearHoles();
        timeOut.textContent = "Game over!";
        return;
      }
      showBat();
    }, 1000);
  });
});
