// "Give me another excuse" on the study page, without reloading: asks the
// excuse API for a new joke and swaps it in. If that fails, the link just
// works like a normal link and reloads the page.
document.addEventListener("DOMContentLoaded", () => {
  const joke = document.getElementById("study-joke");
  const link = document.getElementById("study-another");
  if (!joke || !link || !link.dataset.api) {
    return;
  }

  link.addEventListener("click", async (event) => {
    event.preventDefault();
    const url = `${link.dataset.api}?not=${encodeURIComponent(joke.textContent.trim())}`;
    try {
      const response = await fetch(url, { headers: { Accept: "application/json" } });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      joke.textContent = data.joke;
    } catch (error) {
      window.location.href = link.href;
    }
  });
});
