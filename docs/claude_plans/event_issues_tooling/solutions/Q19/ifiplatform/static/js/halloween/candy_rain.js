// The Konami code (↑ ↑ ↓ ↓ ← → ← → B A) makes it rain candy. With
// animations turned off, a message shows instead.
document.addEventListener("DOMContentLoaded", () => {
  const code = ["arrowup", "arrowup", "arrowdown", "arrowdown", "arrowleft", "arrowright", "arrowleft", "arrowright", "b", "a"];
  const candy = ["🍬", "🍭", "🍫", "🎃"];
  let typed = [];

  function rain() {
    for (let i = 0; i < 40; i += 1) {
      const piece = document.createElement("span");
      piece.textContent = candy[Math.floor(Math.random() * candy.length)];
      piece.setAttribute("aria-hidden", "true");
      Object.assign(piece.style, {
        position: "fixed",
        top: "-3rem",
        left: `${Math.random() * 100}vw`,
        zIndex: 60,
        fontSize: `${1.2 + Math.random() * 1.6}rem`,
        pointerEvents: "none",
      });
      document.body.append(piece);
      const fall = piece.animate(
        [
          { transform: "translateY(0) rotate(0deg)" },
          { transform: `translateY(calc(100vh + 6rem)) rotate(${Math.random() * 720 - 360}deg)` },
        ],
        { duration: 2000 + Math.random() * 2500, delay: Math.random() * 1500, easing: "ease-in" },
      );
      fall.onfinish = () => piece.remove();
    }
  }

  function message() {
    const note = document.createElement("p");
    note.textContent = "🍬 You found the secret candy code!";
    note.setAttribute("role", "status");
    Object.assign(note.style, {
      position: "fixed", left: "50%", bottom: "2rem", transform: "translateX(-50%)", zIndex: 60,
      margin: 0, padding: "0.8rem 1.2rem", border: "2px solid #000", borderRadius: "6px",
      background: "#ff7518", color: "#000", fontWeight: "700",
    });
    document.body.append(note);
    setTimeout(() => note.remove(), 4000);
  }

  document.addEventListener("keydown", (event) => {
    typed = [...typed, event.key.toLowerCase()].slice(-code.length);
    if (typed.join() !== code.join()) {
      return;
    }
    typed = [];
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      message();
    } else {
      rain();
    }
  });
});
