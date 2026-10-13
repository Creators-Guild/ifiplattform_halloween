# home_layout.css — design rationale

Last updated: 2026-09-24
Covers: ifiplatform/apps/ifi_home_app/static/css/05_objects/home_layout.css, ifiplatform/apps/ifi_home_app/static/css/06_components/home/home_navbar_mobile.css

Covers `ifi_home_app/static/css/05_objects/home_layout.css` (the homepage
grid, `home/home_index.html`), plus `06_components/home/home_navbar_mobile.css`.
`06_components/home/home_eventsbox.css` holds the card look of the
same `.eventsbox_container` selector; the box's contents are covered in
`home_eventsbox.md`.

## The grid

`.home-layout .maincontent` is a named-area grid: `nav`, `shortcuts`, then
`content` (`#home-subcontent`: message board + suggestions row) beside
`details` (`.eventsbox_container`). Columns are `minmax(0, 1fr) auto` —
`minmax(0, …)` rather than plain `1fr` so the content column can shrink
below its content's min-content width instead of pushing the events box
off-screen (a plain `1fr` track has an `auto` minimum).

## Below 72rem: `#home-subcontent { display: contents }`

The layout goes single-column, and the goal order is message board, then
Events, then News/Articles — but in the DOM the events box comes after
`#home-subcontent` (which holds both `#msg-board` and `.suggestions-row`).
`display: contents` un-boxes `#home-subcontent` so its children become
direct grid items of `.maincontent`, letting `#msg-board` (`msg`) and
`.suggestions-row` (`suggestions`) be placed on either side of
`details`. Their `grid-area` rules exist only inside this media query;
above 72rem they're ordinary children of `#home-subcontent`.

The `72rem` value is shared by eye with `home_eventsbox.css`
and `messageboard_slideshow.css` (plus
`messageboard.js`'s `MOBILE_QUERY`) — there's no shared variable between
plain CSS files. It's wider than the `45rem` breakpoint used elsewhere
because, with the events box beside it, the content column has already
lost the box's width plus margins long before the viewport is phone-sized.

## `home_navbar_mobile.css` (below 45rem)

The navbar's dropdowns open as a full-navbar-width panel: `.home-navbar`
gets `position: relative` and `.home-navbar .dropdown-menu` is forced to
`position: static`, so the absolutely-positioned `.drop-content` resolves
against the navbar rather than its own menu item — both are required for
`left: 0; right: 0` to mean "navbar width". `top: calc(100% + 0.75rem)`
pushes the panel below the side menu's icon box. Dropdowns whose menu slot
has "hide on mobile" (`.dropdown-menu--hide-mobile`, News/Info by default)
are hidden, and a menu group's short title (`.drop-option-full`/`-short`)
replaces its title.
`home_layout.css`'s `.home-navbar { padding-left: 3rem }` at the same
breakpoint belongs to this layout.
