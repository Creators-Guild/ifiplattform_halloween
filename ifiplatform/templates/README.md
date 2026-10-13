# Global templates

The sitewide template structure (base templates, blocks, partials) is
described in [docs/architecture/frontend.md](../../docs/architecture/frontend.md#html-templates).
This file only covers what is specific to this folder.

This is the global template folder: the site shell and the pieces every
page shares. Each app's own templates live in that app's `templates/`.

```
global_base.html         -- the base every page extends, directly or
                            through an app base like home_base.html
under_development.html   -- placeholder page for sections not built yet
partials/                -- included by global_base.html on every page:
                            deploy_notice, beta_notice, select_language,
                            header, footer.
                            sidemenu/ is sitewide too, but pulled in per
                            page through the `sidemenu` block rather than
                            by global_base.html.
                            account_minimenu.html is not included
                            anywhere at the moment
css_links/global.html    -- the global CSS tier, linked on every page
```
