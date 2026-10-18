// The countdown to Halloween. The page gets the date from the server
// (data-target on #countdown); this makes the clock tick. Nothing to do on
// Halloween itself: then the page has no #countdown.
document.addEventListener("DOMContentLoaded", () => {
  const countdown = document.getElementById("countdown");
  if (!countdown) {
    return;
  }
  const target = new Date(`${countdown.dataset.target}T00:00:00`);
  const parts = {
    days: document.getElementById("countdown-days"),
    hours: document.getElementById("countdown-hours"),
    minutes: document.getElementById("countdown-minutes"),
    seconds: document.getElementById("countdown-seconds"),
  };

  function tick() {
    const left = Math.max(0, Math.floor((target - new Date()) / 1000));
    parts.days.textContent = Math.floor(left / 86400);
    parts.hours.textContent = Math.floor((left % 86400) / 3600);
    parts.minutes.textContent = Math.floor((left % 3600) / 60);
    parts.seconds.textContent = String(left % 60).padStart(2, "0");
  }

  tick();
  setInterval(tick, 1000);
});
