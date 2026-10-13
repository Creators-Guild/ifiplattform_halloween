document.addEventListener("DOMContentLoaded", () => {
  // scatters a handful of soft, flat-color circles behind an optional
  // title banner (see .title-banner in category_card.css, CategoryPage.
  // show_banner/ArticleIndexPage.show_banner) -- generated here rather
  // than a fixed background image so it's genuinely "generic": no asset to
  // keep up to date, same random-ish look on every load.
  const CIRCLE_COUNT = 14;
  document.querySelectorAll(".title-banner").forEach((banner) => {
    for (let i = 0; i < CIRCLE_COUNT; i++) {
      const circle = document.createElement("span");
      circle.className = "title-banner-circle";
      const size = 20 + Math.random() * 70;
      circle.style.width = `${size}px`;
      circle.style.height = `${size}px`;
      circle.style.left = `${Math.random() * 100}%`;
      circle.style.top = `${Math.random() * 100}%`;
      banner.appendChild(circle);
    }
  });
});
