// Memory pairs. Half built: the cards are dealt here; turning them over and
// matching them is the event issue's job (the TODOs).
document.addEventListener("DOMContentLoaded", () => {
  const board = document.getElementById("memory-board");
  const foundOut = document.getElementById("memory-found");
  const triesOut = document.getElementById("memory-tries");
  const symbols = ["🎃", "👻", "🦇", "🕷️", "💀", "🍬"];

  let open = [];

  function newGame() {
    board.textContent = "";
    foundOut.textContent = 0;
    triesOut.textContent = 0;
    const cards = [...symbols, ...symbols];
    cards.sort(() => Math.random() - 0.5);
    open = [];
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
    if (open.length === 2 || open.includes(card) || card.classList.contains("memory-card--found")) {
      return;
    }
    card.textContent = card.dataset.symbol;
    open.push(card);
    if (open.length < 2) {
      return;
    }
    triesOut.textContent = Number(triesOut.textContent) + 1;
    const [first, second] = open;
    if (first.dataset.symbol === second.dataset.symbol) {
      first.classList.add("memory-card--found");
      second.classList.add("memory-card--found");
      foundOut.textContent = Number(foundOut.textContent) + 1;
      open = [];
    } else {
      setTimeout(() => {
        first.textContent = "?";
        second.textContent = "?";
        open = [];
      }, 800);
    }
  }

  document.getElementById("memory-new").addEventListener("click", newGame);
  newGame();
});
