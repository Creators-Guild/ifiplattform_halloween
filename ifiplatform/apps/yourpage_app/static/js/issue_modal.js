// Opens an issue card's page in a pop-up (core/issue_modal.html) instead of
// navigating: fetches the page and shows its [data-issue-panel]. The links
// are real, so middle-click, no JS or a failed fetch just go to the page.
// <dialog> + showModal() gives the dark backdrop, Esc and the focus trap.
const modal = document.querySelector("[data-issue-modal]");

if (modal) {
  const body = modal.querySelector("[data-issue-modal-body]");
  let opener = null;

  const show = async (url) => {
    const response = await fetch(url, { headers: { Accept: "text/html" } });
    if (!response.ok) throw new Error(response.status);
    const page = new DOMParser().parseFromString(await response.text(), "text/html");
    const panel = page.querySelector("[data-issue-panel]");
    if (!panel) throw new Error("no panel");
    body.replaceChildren(document.importNode(panel, true));
    if (!modal.open) modal.showModal();
    const target = url.hash && body.querySelector(url.hash);
    if (target) target.scrollIntoView();
    else modal.scrollTop = 0;
  };

  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-issue-link]");
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
      return;
    }
    event.preventDefault();
    if (!modal.open) opener = link;
    // Opening a new claim marks it seen (the issue page does that on the
    // server); drop the highlight now rather than on the next reload.
    link.closest(".issue-card--new")?.classList.remove("issue-card--new");
    show(new URL(link.href)).catch(() => {
      window.location.href = link.href;
    });
  });

  // "Give me an issue" (core/lucky_panel.html) is a GET form that lands on a
  // random free issue's page, so it opens in the pop-up the same way. When
  // nothing matches, the page has no panel: load it for its message.
  document.addEventListener("submit", (event) => {
    const form = event.target.closest("form[data-issue-lucky]");
    if (!form) return;
    event.preventDefault();
    const url = new URL(form.action, window.location.href);
    url.search = new URLSearchParams(new FormData(form)).toString();
    if (!modal.open) opener = event.submitter || form;
    show(url).catch(() => {
      window.location.href = url.href;
    });
  });

  // A click on the backdrop lands on the dialog itself, outside its content.
  modal.addEventListener("click", (event) => {
    if (event.target === modal) modal.close();
  });

  modal.addEventListener("close", () => {
    body.replaceChildren();
    if (opener && opener.isConnected) opener.focus();
    opener = null;
  });
}
