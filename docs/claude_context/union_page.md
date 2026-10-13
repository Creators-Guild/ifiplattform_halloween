# union_page.html — layout rationale

Last updated: 2026-09-22
Covers: ifiplatform/apps/ifi_home_app/static/css/05_objects/union_layout.css, ifiplatform/apps/ifi_home_app/static/css/06_components/union/union_core.css, ifiplatform/apps/ifi_home_app/static/css/06_components/union/union_header.css, ifiplatform/apps/ifi_home_app/static/css/06_components/union/union_info_box.css, ifiplatform/apps/ifi_home_app/static/css/06_components/union/union_member_card.css, ifiplatform/apps/ifi_home_app/static/css/06_components/union/union_position_info.css, ifiplatform/apps/ifi_home_app/static/css/06_components/union/union_sections.css, ifiplatform/apps/ifi_home_app/templates/info_articles/pages/union_page.html

Covers `ifi_home_app/templates/info_articles/pages/union_page.html` and its
CSS: `ifi_home_app/static/css/05_objects/union_layout.css` and
`06_components/union/union_header.css`, `union_core.css`,
`union_sections.css`, `union_info_box.css`, `union_member_card.css`,
`union_position_info.css`.

## .union-header

Logo, title, and the open/closed badge stack vertically, centered, matching
`.union-main`'s reading-column width (`max-width: 60rem`) so the two line
up visually. Both `.union-header` and `.union-header-text` need
`flex-direction: column` — not just the outer one — because
`.union-header-text` on its own is a flex row by default, and its children
(an inline-block `h1` and the badge span) would sit side by side if there
were room, even with the outer element already stacked.

The owner flagged the `1rem` top value in `.union-header`'s
`margin: 1rem auto 1.5rem` as "don't remove".

## .union-layout / .union-main / .union-sidebar: independent layouts, not a shared row

`.union-main` and `.union-sidebar` are deliberately NOT a grid/flex row
sharing a track. That was tried twice and broke twice:

1. `max-width` directly on `.union-main` as a `minmax(0, 1fr)` grid item
   made the browser size the whole track around that max-width, pushing
   `.union-sidebar`'s fixed `16rem` column off-screen.
2. Rebuilding the row with flexbox (`flex: 1` / `flex: 0 0 16rem`) to fix
   the above broke centering again.

The working design instead makes `.union-main` a plain block, centered
against `.union-layout`'s full width with zero awareness of
`.union-sidebar`. At `min-width: 80rem`, `.union-sidebar` is taken out of
flow (`position: absolute`, anchored via `position: relative` on
`.union-layout`) so it truly cannot feed back into `.union-main`'s
centering math. Below `80rem` it sits in normal flow with
`max-width: 60rem; margin: 0 auto 1.5rem` to match `.union-main`'s column
— it comes *before* `.union-main` in `union_page.html` specifically so the
stacked order puts it above "Purpose", instead of landing after every
section.

### Where the 80rem breakpoint came from

Mathematically, avoiding overlap with pure full-page centering needs
roughly `2 * (.union-main half-width + .union-sidebar width + gap)` of
`.union-layout` width to break even: `60rem / 2 + 16rem + 2rem gap ≈ 96rem`.
A previous version of this page used `115rem` (that derived minimum plus
a deliberate buffer). This time the number was tuned live in the browser
instead of computed up front — deliberately started too small (`60rem`,
guaranteed overlap) and raised in steps (`70rem` → `80rem`) until the
overlap was gone, landing below the ~96rem derived minimum. That gap
between "tuned" and "derived" is exactly what the push zone below exists
to cover.

## The 80rem–104rem push zone

Between `80rem` (where `.union-sidebar` starts floating) and the ~96rem
derived break-even point above, pure full-page centering isn't reliably
safe yet. Rather than let `.union-main`/`.union-header` overlap
`.union-sidebar` in that range, `.union-page` (their shared parent —
*not* `.union-layout`) gets `padding-right: 18rem` there, so both
re-center within the same narrower remainder and stay lined up with each
other — the same `margin: auto` centering they already had, just now
solving against a narrower canvas.

That padding doesn't move `.union-sidebar` on its own — `right: 0`
(set in the `min-width: 80rem` block) resolves against `.union-layout`'s
own padding box, which `.union-page`'s padding doesn't touch directly.
But `.union-layout` itself, as a plain block filling `.union-page`'s
content box, physically shrinks by that same `18rem` — which would drag
`.union-sidebar`'s anchor `18rem` left of `.union-page`'s true right edge
along with it. `right: -18rem` in this same breakpoint block compensates,
pushing back out by exactly the space `.union-page` reserved, landing
`.union-sidebar` back at the true right edge — same visual position as
outside this range. **Keep the `18rem` padding-right and the `-18rem`
right-offset equal if either one changes.**

104rem is just past where the derived ~96rem minimum clears with a small
buffer — above it, `.union-page` drops the padding and full-page centering
is safe on its own again.

## Multiple .union-main sections

`union_page.html` renders several sibling top-level `.union-main` elements
(union-core with Purpose/Activities/Bylaws, Sitting Members, Open
Positions, calendar+events), each managing its own width. Spacing between
them is `.union-main + .union-main { margin-top: 2rem }` — adjacent-sibling
rather than a flat margin on every section, so whichever section renders
first (sections are conditional) gets no extra top gap.

`.union-main--wide` (`max-width: 68rem`) is on the Sitting Members / Open
Positions sections: member cards, especially Open Positions with inline
responsibilities text, read better wider than the 60rem prose column. It's
a separate `.union-main` section rather than a wider `.union-member-grid`
because a child can't exceed its parent's box without a breakout hack.
68rem and not wider: the 80rem–104rem push zone above was tuned around a
60rem `.union-main`; 68rem is close enough to stay clear without
re-deriving it. If you widen it further, re-check overlap with the
floating sidebar in that range.

`.union-calendar-section` uses `padding-top`, not `margin-top`, because a
margin would collapse into its h2's own margin-top instead of adding to it.

## .union-sidebar-row

Contact and Members boxes (`.union-info-box`, `flex: 1 1 12rem;
min-width: 0`) sit side by side and wrap on their own (no extra
breakpoint) once there's no room for both — relevant above `80rem` where
`.union-sidebar` is only `16rem` wide, not below it where `.union-sidebar`
matches `.union-main`'s `60rem` column width.

## union_info_box.css: `.union-info-box--links`

`.union-sidebar`'s flex column would otherwise stretch this box to the
sidebar's full width (up to 60rem when stacked), rendering one or two links
as a giant edge-to-edge button. It uses `width: min(24rem, 100%)`, not
`max-width`: the box's content is far narrower than 24rem, so a max-width
alone constrains nothing — `width` forces 24rem while `min(..., 100%)`
still shrinks on narrow screens. Centered with `margin-left/right: auto`.

## union_core.css

- `.union-core p { font-size: inherit }` is required: the global
  `p { font-size: 1.05rem }` in `elements.css` is set directly on the tag,
  which always beats inheriting `.union-core`'s `1.3rem` (inheritance never
  overrides a value set on the element itself). Same fix as
  `category_header.css`'s `.intro p` and `article_header.css`.
- `.union-core`'s `padding: 2rem 8rem` / `font-size: 1.3rem` are sized for
  the desktop column; the 45rem query drops them to `2rem 1rem` / `1rem`.
- `.union-bylaws-link` uses `display: flex; width: fit-content;
  margin: ... auto` (not `inline-flex`) to center just the link while
  `.union-core` stays `text-align: left`. An inline-level box's auto margins
  can't center it; a text-align on an ancestor would center the Bylaws prose
  too.

## union_sections.css: collapsible sections

Every section heading (Purpose/Activities/Bylaws inside `.union-core`,
Sitting Members, Open Positions) is a `<details class="union-section" open>`
with a `<summary class="union-section-summary"><h2>`. On desktop it's
always open with no toggle affordance (`pointer-events: none;
cursor: default` on the summary). Only inside `@media (max-width: 45rem)`
does it become tap-to-collapse (`pointer-events: auto`, caret shown), and
`union_core_sections.js` closes the sections by default there on load.
Real `<details>` rather than a custom widget so content degrades to always
visible with no JS/CSS.

- `.union-section-summary { display: block }`: browsers default `<summary>`
  to `display: list-item`, which reserves marker space on the left even with
  the marker hidden, skewing the centered h2 left. Same fix as
  `.lang-dropdown-trigger` in `select_language.css`. `list-style: none`
  hides the marker in Firefox; `::-webkit-details-marker { display: none }`
  hides it in Chrome/Safari — both are needed.
- `.union-main .union-section-summary h2 { margin-top: 0 }`: every h2 is now
  `:first-child` of its summary, so `.union-main h2:first-child` alone would
  zero them all anyway; spacing between sections comes from
  `.union-section + .union-section { margin-top: 2rem }` instead
  (adjacent-sibling, same idiom as `.union-main + .union-main`).
- Mobile: `.union-section-summary h2` is left-aligned so the caret sits by
  the title's first letter. The caret is `h2::before` (not on the summary)
  so its `em` sizing matches the h2's font-size; same border-triangle
  technique as `.dropdown-menu .link::after` in `dropdownmenu.css`, but
  `::before` + `margin-right` to sit before the title. Rotates 180° when
  `.union-section[open]`.

## union_member_card.css

- `.union-member-card { position: relative }` anchors
  `.position-info-widget` (the info icon) in its top-right corner.
- `.union-member-card--open` (`flex-basis: 18rem`, left-aligned): Open
  Positions cards show responsibilities inline (`union_position_card.html`),
  so they're wider than Sitting Members cards; narrower just made them
  taller.
- `.union-position-responsibilities` renders one `<li>` per
  `member.responsibilities` item; the item is richtext limited to
  bold/italic (`article/unions.py`), so each `<li>` contains a `<p>`. It's
  shared by the inline Open Positions card and the Sitting Members info
  popover.
- `.union-position-responsibilities p { font-size: inherit; margin: 0;
  display: inline }`: `inherit` for the same global-`p` reason as
  `.union-core p`; `margin: 0` removes the default paragraph margin inside
  the li; `display: inline` because `list-style-position: inside` puts the
  bullet as the li's first inline box, and a block `<p>` pushed the text
  onto the line below the bullet. Safe only because this richtext can't
  contain more than inline content.
- The base `.union-position-responsibilities h3, h4` and `ul` rules
  intentionally set no font-size: h3 appears only under
  `.union-member-card--open` and h4 only under `.position-info-panel`
  (see `union_position_card.html` for the h3/h4 split), and each context
  sets its own more-specific size — `.union-member-card--open ...` rules
  here, `.position-info-panel ...` rules in `union_position_info.css`. Those
  two-class selectors outweigh the one-class base rules regardless of
  stylesheet order. The two contexts deliberately mirror the same
  bigger-text / li+li divider-line treatment.
- `.union-position-held-by { margin-top: auto }`: the flex row stretches
  every card to the tallest, and `.union-member-card` is a column flexbox,
  so auto margin pins "held by" to the card bottom.

## union_position_info.css: position info popover

Same icon-button-toggles-a-panel pattern as `.toc-open-button`/
`.toc-overlay-panel` (`article_toc_overlay.css`), driven by
`union_position_info.js`. Several properties come from
`06_components/shared/popover_base.css`, not this file — don't re-add them
here or assume they're missing: `.position-info-panel`'s
background-color/border, `.position-info-header`'s
display/align-items/justify-content/gap, `.position-info-title`'s
margin/font-weight, `.position-info-close`'s flex/cursor.

Mobile (`max-width: 45rem`): like the nav dropdown (`dropdownmenu.css`),
the panel is anchored to a small icon whose position varies per card, so it
could run into the sidemenu or off-screen. The icon stays put; only the
panel switches to `position: fixed`. Its `top` is set inline by
`union_position_info.js` (just under the icon, pushed up if it would run off
the bottom). `left: calc(60px + 0.75rem)` clears the sidemenu's collapsed
rail (60px desktop-collapsed / 56px mobile-collapsed, `sidemenu.css`) plus
a gutter matching the page's mobile side padding (`home_layout.css`).
