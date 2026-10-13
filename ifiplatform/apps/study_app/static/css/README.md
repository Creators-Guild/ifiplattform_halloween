# study_app CSS structure

The sitewide CSS architecture (ITCSS layers, how stylesheets are loaded,
BEM) is described in [docs/architecture/frontend.md](../../../../../docs/architecture/frontend.md).
This file only covers what is specific to this app's CSS.

Scaled down to this app's actual size -- no per-concern subfolders needed
yet, just the two tiers, so this tree starts at 05:

```
05_objects/     -- study_layout.css (page shell)
06_components/  -- box.css, studytools_btn.css, flashcards.css,
                   mutiplechoice.css, studygames.css
study_base.css
```

`study_base.css` is the entry point, linked from every study-app
template. It bundles `05_objects/study_layout.css`,
`06_components/studytools_btn.css`, and `06_components/box.css` via
`@import`. `flashcards.css`, `mutiplechoice.css`, and `studygames.css`
are each linked separately, only on the specific study-tool page that
uses them.

This app has not adopted the block-per-tier loading described in
[docs/architecture/frontend.md](../../../../../docs/architecture/frontend.md) yet -- its templates
still each link `study_base.css` themselves, and it has no base template
of its own. That works and causes no flash of unstyled content (the links
sit in `extra_head`, so they are render-blocking), it is just more
repetition than it needs.

Note (pre-existing, not a doc-scope fix): several templates under
`templates/{flashcards,studygames,multiplechoice,mix_studyset}/` link a
`styles/neon_style/ifi_study/*.css` path that has never corresponded to a
real file -- worth fixing separately, left alone here.
