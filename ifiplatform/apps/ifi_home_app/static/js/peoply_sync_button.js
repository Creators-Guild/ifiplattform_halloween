// "Sync Peoply now" button (events/partials/peoply_sync_button.html) --
// disables itself for 5s after a click, purely to absorb an accidental
// double-click; not a real rate limit (the button is staff-only, and
// every click is logged server-side regardless -- see PeoplySyncLog).
//
// The click itself is a plain form POST, which navigates away and
// destroys this whole JS context -- a setTimeout alone wouldn't survive
// that, so the button would come back fully enabled the instant the
// redirected page loads. localStorage carries the cooldown's end time
// across that navigation instead: one shared key, since all three button
// instances (homepage, overview, event page) hit the same endpoint and
// the guard is about not spamming *that*, not about any one page's copy
// of the button. Guarded against double-init since this script can be
// included from multiple partials on the same page.
if (!window.__ifiPeoplySyncButtonInit) {
  window.__ifiPeoplySyncButtonInit = true;

  var COOLDOWN_MS = 5000;
  var STORAGE_KEY = "peoplySyncCooldownUntil";

  function disableFor(button, ms) {
    button.disabled = true;
    setTimeout(function () {
      button.disabled = false;
    }, ms);
  }

  document.querySelectorAll(".peoply-sync-form").forEach(function (form) {
    var button = form.querySelector(".peoply-sync-button");

    // Picks up a cooldown started on the page we just navigated away
    // from, e.g. right after the redirect a click causes.
    var remaining = parseInt(localStorage.getItem(STORAGE_KEY) || "0", 10) - Date.now();
    if (remaining > 0) {
      disableFor(button, remaining);
    }

    form.addEventListener("submit", function () {
      localStorage.setItem(STORAGE_KEY, String(Date.now() + COOLDOWN_MS));
      disableFor(button, COOLDOWN_MS);
    });
  });
}
