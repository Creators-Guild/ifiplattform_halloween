# Site header — design rationale

Last updated: 2026-09-22
Covers: ifiplatform/apps/account_app/static/css/06_components/profile_dropdown.css, ifiplatform/static/css/06_components/header.css, ifiplatform/static/css/06_components/select_language.css

Covers `templates/partials/header.html` and
`templates/partials/select_language.html`, styled by
`static/css/06_components/header.css`,
`static/css/06_components/select_language.css` and
`apps/account_app/static/css/06_components/profile_dropdown.css`.
The header sits in `.topheader-content` (`static/css/05_objects/page_layout.css`).

## Layout: plain flexbox, no measuring

Above 45rem `.header-bar` is always a single, non-wrapping flex row:
`.ifiplatform-logo-box` and
`.nav_links`. `.nav_links` is `flex: 1 1 auto; max-width: 40rem;
justify-content: space-between; gap: 1rem`, so it takes the free space next
to the logo (capped, so the links don't spread across a wide screen) and
spreads its links across it. The 1rem gap keeps the row fitting at the
tightest width just above the breakpoint (~721px). Below 45rem `.header-bar` gets `flex-wrap: wrap`
and `.nav_links` `flex-basis: 100%`, so the icons always get their own
second row (without the forced basis, wider phones/small tablets fit
everything on one row).

This replaced `static/js/nav_overflow.js`, which measured whether the nav
had wrapped and toggled `.nav-compact` to swap "Ifi Home"/"Ifi Study" for
"Home"/"Study". The links now always use the short label
(`.nav_link-label`), which made the measuring, the `.nav-compact` class and
four `!important`s fighting the mobile breakpoint unnecessary.

**Do not put `overflow-x: auto` (or any non-visible overflow) on
`.nav_links`.** It forces `overflow-y` to `auto` too (CSS overflow spec),
which clips the profile dropdown panel. That clipping is what previously
forced the panel to `position: fixed` with JS positioning it on every
click/resize, plus a `z-index` and padding workarounds.

`.header-message` is one line on desktop, truncated with an ellipsis
(`white-space: nowrap; overflow: hidden; text-overflow: ellipsis` on
`.header-message p` — the rich text renders its text inside a `<p>`, so the
truncation has to sit on that block, not the wrapper). The full text is in
the wrapper's `title` attribute (`header.html`) for hover. On mobile it
wraps and is clamped to 2 lines (`-webkit-line-clamp` + `line-clamp`).
There's deliberately no character limit on `HeaderMessage.text` in Wagtail;
truncation handles long messages instead.

Width: `.ifiplatform-logo-box` is `flex: 1 1 0`, so it takes whatever
space `.nav_links` leaves; the message fills that up to
`max-width: 35rem` and truncates. The cap is there so a long message
doesn't stretch across the whole header on wide screens.
`contain: inline-size` on `.header-message` stops the text itself from
counting toward the box's size (otherwise a long message would widen the
box and squeeze the links). The h1 is `white-space: nowrap` because with a
0 flex-basis the box shrinks to its min-content — without nowrap the title
wrapped one word per line on narrow desktops. Mobile resets to
`contain: none`: there the box is centred (`align-items: center`) and the
contained message collapsed to zero width.

## Mobile (below 45rem)

The header centres: logo/message on one row, nav icons on the next. Links show
only their `.nav_link-icon` (`.nav_link-label` hidden). "Log in" has no
icon and stays text. `.nav_link-icon--page svg` is 1.6rem instead of
1.9rem because the "Your Page" document path is a narrow portrait shape
that reads taller than the other icons at the same box size.

## Profile dropdown (`profile_dropdown.css`)

Reuses `.dropdown-menu`/`.drop-content`/`.drop-option` from
`dropdownmenu.css`, but is click-only on every device: `dropdownmenu.css`
excludes `.profile-dropdown` from its `:hover` reveal, and
`dropdown_menu.js` wires it with `setupTapToggle` unconditionally. The
dropdown caret (`.link::after`) is hidden because the trigger is icon-only.

The panel is `position: absolute` (from `dropdownmenu.css`) with
`top: calc(100% + 8px); right: 0`, anchored to `.dropdown-menu`'s
`position: relative`. `z-index: 200` keeps it above the side menu
(`sidemenu.css`, `z-index: 100`). The trigger's hover colour is scoped to
`(hover: hover) and (pointer: fine)` because on touch `:hover` sticks
after a tap. On mobile the trigger drops its circular border so it matches
the plain icons beside it.

## Language picker (`select_language.css`)

Two versions in the markup: a two-button row (desktop) and a `<details>`
dropdown (`.select-language-dropdown`, mobile only) showing the current
language code and offering only the other language. Below 45rem the row
is hidden, the dropdown shown, and `.select-language` becomes
`position: absolute` in the corner (positioning context:
`.topheader-content`, `position: relative` in `page_layout.css`) so it
doesn't push the title down by its own height.
