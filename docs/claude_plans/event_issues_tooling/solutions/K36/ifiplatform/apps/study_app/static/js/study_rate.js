// Rate the excuse on the study page: 👍 or 👎, remembered in this browser
// (localStorage), per joke. Another issue can swap the joke without a
// reload, so the joke's text is read again on every click and change.
document.addEventListener("DOMContentLoaded", () => {
  const joke = document.getElementById("study-joke");
  const tools = document.getElementById("study-joke-tools");
  if (!joke || !tools) {
    return;
  }
  const KEY = "study-joke-votes";

  function loadVotes() {
    try {
      return JSON.parse(localStorage.getItem(KEY)) || {};
    } catch (error) {
      return {};
    }
  }

  function saveVotes(votes) {
    try {
      localStorage.setItem(KEY, JSON.stringify(votes));
    } catch (error) {
      // Private window or storage full: the vote just isn't remembered.
    }
  }

  const rating = document.createElement("div");
  rating.className = "joke-rating";
  rating.setAttribute("role", "group");
  rating.setAttribute("aria-label", "Rate this excuse");
  const buttons = {};
  [["up", "👍", "Good excuse"], ["down", "👎", "Bad excuse"]].forEach(([vote, emoji, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `joke-rating__button joke-rating__button--${vote}`;
    button.textContent = emoji;
    button.setAttribute("aria-label", label);
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
      const votes = loadVotes();
      const text = joke.textContent.trim();
      if (votes[text] === vote) {
        delete votes[text];
      } else {
        votes[text] = vote;
      }
      saveVotes(votes);
      show();
    });
    buttons[vote] = button;
    rating.append(button);
  });
  tools.append(rating);

  function show() {
    const current = loadVotes()[joke.textContent.trim()];
    Object.entries(buttons).forEach(([vote, button]) => {
      button.setAttribute("aria-pressed", String(current === vote));
    });
  }

  new MutationObserver(show).observe(joke, { childList: true, characterData: true, subtree: true });
  show();
});
