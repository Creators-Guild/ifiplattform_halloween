// Click the spider: it climbs up its thread, waits, and comes back down.
document.addEventListener("DOMContentLoaded", () => {
  const spider = document.querySelector(".spider");
  if (!spider) {
    return;
  }
  let timer = null;

  spider.addEventListener("click", () => {
    spider.classList.add("spider--startled");
    clearTimeout(timer);
    timer = setTimeout(() => spider.classList.remove("spider--startled"), 1500);
  });
});
