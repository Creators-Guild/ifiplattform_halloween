// The countdown to Halloween. Half built: the page gets the date from the
// server (data-target on #countdown); making the clock tick is the event
// issue's job (the TODO). Nothing to do on Halloween itself: then the page
// has no #countdown.
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
    // TODO: work out how long it is from now until target, and show it in
    // parts.days, parts.hours, parts.minutes and parts.seconds.
  }

  tick();
  setInterval(tick, 1000);
});
