// Previous/Next on UnionPage's calendar (union_page.html /
// info_articles/partials/union_calendar_panel.html) fetch just the
// calendar panel and swap it in, instead of following the link as a real
// navigation -- a full reload on this site loses scroll position (html/body
// is its own scroll box, see elements.css; window.scrollY never reflects
// it, so there's nothing reliable a reload could restore scroll from).
// ?calendar_partial=1 (UnionPage.get_template) renders that same panel
// with no page chrome around it. Same local-DB-only query either way --
// this never calls Peoply's own API, just re-renders from already-synced
// EventPages.
if (!window.__ifiUnionCalendarInit) {
  window.__ifiUnionCalendarInit = true;

  function wireCalendarSection(section) {
    section.querySelectorAll(".union-calendar-nav a").forEach(function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();

        var url = new URL(link.href, window.location.href);
        url.searchParams.set("calendar_partial", "1");

        fetch(url)
          .then(function (response) {
            return response.text();
          })
          .then(function (html) {
            var wrapper = document.createElement("div");
            wrapper.innerHTML = html.trim();
            var newSection = wrapper.firstElementChild;
            if (!newSection) {
              return;
            }
            section.replaceWith(newSection);
            history.replaceState(null, "", link.href);
            wireCalendarSection(newSection);
          });
      });
    });
  }

  var initialSection = document.getElementById("union-calendar");
  if (initialSection) {
    wireCalendarSection(initialSection);
  }
}
