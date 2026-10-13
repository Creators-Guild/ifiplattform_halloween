# Global CSS

The sitewide CSS architecture (ITCSS layers, how stylesheets are loaded,
BEM) is described in [docs/architecture/frontend.md](../../../docs/architecture/frontend.md). This
file only covers what is specific to this folder.

This is the global static folder: CSS shared sitewide. Each app's own CSS
lives in that app's `static/css/`, with its own README.

Everything every page needs is linked from one partial,
`templates/css_links/global.html`, in cascade order.
