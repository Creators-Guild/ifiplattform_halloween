// Per-card expand/collapse for the homepage newsbar grid
// (.newsbar-layout, loaded by home_newsbar.html -- the init guard below
// keeps a repeat include from binding every handler twice). Default on load
// matches the old CSS-only behavior this replaces (every card past the
// first two starts collapsed) -- but only on narrow screens, same
// (max-width: 45rem) breakpoint as .articlecard-toggle's own CSS
// visibility (newsbar_layout.css/articlecard.css). The toggle arrow that
// lets a visitor flip a card back to expanded is only ever shown below
// that width in the first place, so defaulting cards to collapsed above
// it left them stuck that way with no way to reopen them -- on a normal
// desktop browser, every card now just starts expanded.
if (!window.__ifiArticleListToggleInit) {
  window.__ifiArticleListToggleInit = true;

  document.addEventListener("DOMContentLoaded", () => {
    const setCardState = (card, collapsed) => {
      card.classList.toggle("articlecard--list", collapsed);
      const toggle = card.querySelector(".articlecard-toggle");
      if (toggle) {
        toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      }
    };

    const isNarrowScreen = window.matchMedia("(max-width: 45rem)").matches;

    document.querySelectorAll(".newsbar-layout").forEach((layout) => {
      const cards = Array.from(layout.querySelectorAll(".articlecard"));
      cards.forEach((card, index) => {
        setCardState(card, isNarrowScreen && index >= 2);
      });
    });

    document.querySelectorAll(".newsbar-layout .articlecard-toggle").forEach((toggle) => {
      toggle.addEventListener("click", (event) => {
        // .articlecard-toggle lives inside the card's own <a> (see
        // article_card.html's comment on that nesting tradeoff) -- without
        // this, the click would also navigate to the article itself.
        event.preventDefault();
        event.stopPropagation();

        const card = toggle.closest(".articlecard");
        if (!card) {
          return;
        }
        setCardState(card, !card.classList.contains("articlecard--list"));
      });
    });
  });
}
