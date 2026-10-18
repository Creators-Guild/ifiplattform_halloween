// Memory pairs. Half built: the cards are dealt here; turning them over and
// matching them is the event issue's job (the TODOs).
document.addEventListener("DOMContentLoaded", () => {
  const board = document.getElementById("memory-board");
  const foundOut = document.getElementById("memory-found");
  const triesOut = document.getElementById("memory-tries");
  const symbols = ["🎃", "👻", "🦇", "🕷️", "💀", "🍬"];

  function newGame() {
    board.textContent = "";
    foundOut.textContent = 0;
    triesOut.textContent = 0;
    const cards = [...symbols, ...symbols];
    // TODO 1: shuffle cards (for example: sort with () => Math.random() - 0.5).
    cards.forEach((symbol) => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "memory-card";
      card.dataset.symbol = symbol;
      card.textContent = "?";
      card.addEventListener("click", () => flip(card));
      board.append(card);
    });
  }

  function flip(card) {
    // TODO 2: show the symbol (card.textContent = card.dataset.symbol).
    // TODO 3: when two cards are turned over: tries + 1. Same symbol ->
    // leave them open and found + 1. Different -> turn both back to "?"
    // after a short wait (setTimeout, about 800 ms).
  }

  document.getElementById("memory-new").addEventListener("click", newGame);
  newGame();
});
