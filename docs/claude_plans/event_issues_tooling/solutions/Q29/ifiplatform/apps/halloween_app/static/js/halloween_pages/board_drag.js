// Drag the notes on the haunted board; where you put them is kept in this
// browser only (localStorage), keyed by the note's title.
document.addEventListener("DOMContentLoaded", () => {
  const board = document.querySelector(".board");
  if (!board) {
    return;
  }
  const KEY = "haunted-board-spots";
  let spots = {};
  try {
    spots = JSON.parse(localStorage.getItem(KEY)) || {};
  } catch (e) {
    spots = {};
  }

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(spots));
    } catch (e) {
      // Private window or blocked storage: dragging still works, it just isn't kept.
    }
  }

  function place(note, x, y) {
    note.style.translate = `${x}px ${y}px`;
  }

  board.querySelectorAll(".note").forEach((note) => {
    const title = note.querySelector(".note__title").textContent;
    const spot = spots[title] || { x: 0, y: 0 };
    place(note, spot.x, spot.y);
    note.style.touchAction = "none";
    note.style.cursor = "grab";

    note.addEventListener("pointerdown", (down) => {
      const start = { x: down.clientX - spot.x, y: down.clientY - spot.y };
      note.setPointerCapture(down.pointerId);
      note.style.zIndex = 10;
      const move = (event) => {
        spot.x = event.clientX - start.x;
        spot.y = event.clientY - start.y;
        place(note, spot.x, spot.y);
      };
      const up = () => {
        note.removeEventListener("pointermove", move);
        note.style.zIndex = "";
        spots[title] = { x: spot.x, y: spot.y };
        save();
      };
      note.addEventListener("pointermove", move);
      note.addEventListener("pointerup", up, { once: true });
    });
  });

  const tidy = document.createElement("button");
  tidy.type = "button";
  tidy.textContent = "Tidy the board";
  tidy.addEventListener("click", () => {
    spots = {};
    save();
    window.location.reload();
  });
  board.before(tidy);
});
