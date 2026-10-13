document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("deploy-notice-root");
  if (!root) {
    return;
  }

  const message = root.dataset.message;
  const restartingText = root.dataset.restartingText;
  const statusUrl = root.dataset.statusUrl;

  // How often an already-open tab checks whether an announcement has
  // appeared/been cleared -- the context processor alone only runs
  // per-request, so without this a visitor who never reloads or navigates
  // would never see the banner at all. 20s keeps it feeling reasonably
  // live without polling aggressively for what's normally a rare event.
  const POLL_INTERVAL_SECONDS = 20;

  // Gives the actual restart (git reset/migrate/collectstatic/systemctl
  // restart, kicked off server-side right as the countdown's own sleep
  // ends) a short head start before reloading -- the deploy script clears
  // the announcement once the restart completes (see announce_deploy
  // --clear in deploy/deploy.sh), so by the time this reload lands the banner
  // should be gone; if the restart is still mid-flight the browser just
  // shows its own transient connection error, same as it would for anyone
  // else hitting the site at that exact moment.
  const RELOAD_DELAY_SECONDS = 10;

  // Seconds since epoch, or null -- computing remaining time from a fixed
  // target (rather than counting down from a fixed "10:00" on page load)
  // means this stays correct no matter when a given visitor's page
  // actually loaded, or when they picked up the announcement via a poll
  // rather than the initial server render.
  let target = root.dataset.target ? parseInt(root.dataset.target, 10) : null;
  let countdownIntervalId = null;
  let reloadScheduled = false;

  function buildBanner() {
    if (root.querySelector(".deploy-notice")) {
      return; // already built (e.g. re-triggered by a poll while still counting down)
    }
    root.innerHTML =
      '<div class="deploy-notice" role="status"><p>' +
      message +
      ' <span id="deploy-notice-countdown" class="deploy-notice__countdown"></span></p></div>';
  }

  function removeBanner() {
    root.innerHTML = "";
    if (countdownIntervalId) {
      clearInterval(countdownIntervalId);
      countdownIntervalId = null;
    }
  }

  function tick() {
    const el = document.getElementById("deploy-notice-countdown");
    if (!el) {
      return;
    }
    const remaining = target - Math.floor(Date.now() / 1000);
    if (remaining <= 0) {
      el.textContent = restartingText;
      clearInterval(countdownIntervalId);
      countdownIntervalId = null;
      if (!reloadScheduled) {
        reloadScheduled = true;
        setTimeout(() => window.location.reload(), RELOAD_DELAY_SECONDS * 1000);
      }
      return;
    }
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    el.textContent = `${minutes}:${String(seconds).padStart(2, "0")}`;
  }

  function startCountdown() {
    buildBanner();
    tick();
    if (!countdownIntervalId) {
      countdownIntervalId = setInterval(tick, 1000);
    }
  }

  function poll() {
    fetch(statusUrl)
      .then((response) => response.json())
      .then((data) => {
        if (data.target) {
          if (target !== data.target) {
            target = data.target;
            startCountdown();
          }
        } else if (target !== null) {
          // was active, now isn't (cleared, or its own timeout expired) --
          // remove it for anyone who already had it showing.
          target = null;
          removeBanner();
        }
      })
      .catch(() => {
        // a failed poll (e.g. the server is genuinely restarting right
        // now) isn't itself meaningful -- just try again next interval.
      });
  }

  if (target) {
    startCountdown();
  }
  setInterval(poll, POLL_INTERVAL_SECONDS * 1000);
});
