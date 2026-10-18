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

  function showBat() {
    // TODO 1: clear every hole (textContent = ""), pick a random hole,
    // and put a "🦇" in it.
  }

  holes.forEach((hole) => {
    hole.addEventListener("click", () => {
      // TODO 2: if this hole has a bat: score + 1, show the score in
      // scoreOut, and empty the hole.
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
      // TODO 3: move the bat (showBat) every second, and when timeLeft
      // reaches 0: stop the interval, empty the holes, show "Game over!".
    }, 1000);
  });
});
