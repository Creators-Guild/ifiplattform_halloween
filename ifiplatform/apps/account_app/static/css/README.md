# account_app CSS structure

The sitewide CSS architecture (ITCSS layers, how stylesheets are loaded,
BEM) is described in [docs/architecture/frontend.md](../../../../../docs/architecture/frontend.md).
This file only covers what is specific to this app's CSS.

Scaled down to this app's actual size -- no per-concern subfolders needed
yet, just the two tiers, so this tree starts at 05:

```
05_objects/     -- account_layout.css (page shell)
06_components/  -- account_card.css, auth_card.css, profile_dropdown.css
account_base.css
```

`account_base.css` is the entry point, linked from every account-app
template. It bundles `05_objects/account_layout.css`,
`06_components/account_card.css`, and `06_components/auth_card.css` via
`@import`. `profile_dropdown.css` is deliberately NOT in that bundle:
the shared `header.html` partial puts the profile dropdown on every
page sitewide, not just this app's, so it is linked once in
`templates/css_links/global.html` instead. It stays owned by this app
because this app owns the dropdown.

This app has not adopted the block-per-tier loading described in
[docs/architecture/frontend.md](../../../../../docs/architecture/frontend.md) yet -- its templates
still each link `account_base.css` themselves, and it has no base
template of its own. That works and causes no flash of unstyled content
(the links sit in `extra_head`, so they are render-blocking), it is just
more repetition than it needs.
