// Click "Trick or Treat?" in the header: a random trick or treat shows for
// a few seconds, then the question comes back.
document.addEventListener("DOMContentLoaded", () => {
  const tagline = document.querySelector(".header-tagline");
  if (!tagline) {
    return;
  }
  const question = tagline.textContent.trim();
  const tricks = [
    "Trick! Your next commit message is now in Latin.",
    "Trick! Every semicolon has gone missing.",
    "Trick! The printer on the 3rd floor knows your name.",
  ];
  const treats = [
    "Treat! 🍬 A bug fixes itself.",
    "Treat! 🍫 The coffee machine works today.",
    "Treat! 🎃 All your tests pass on the first try.",
  ];
  let timer = null;

  tagline.setAttribute("aria-live", "polite");
  tagline.addEventListener("click", () => {
    const answers = Math.random() < 0.5 ? tricks : treats;
    tagline.textContent = answers[Math.floor(Math.random() * answers.length)];
    clearTimeout(timer);
    timer = setTimeout(() => {
      tagline.textContent = question;
    }, 4000);
  });
});
