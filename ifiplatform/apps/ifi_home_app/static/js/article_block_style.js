document.addEventListener("DOMContentLoaded", () => {
  const panel = document.getElementById("block-style-mini-panel");
  if (!panel) {
    return;
  }

  // the global font-size multiplier (see article_quick_style.js), read
  // live off .article-page's own data attribute so per-block font-size
  // edits in this panel stay visually consistent with whatever multiplier
  // is currently active (including an unsaved one still being dragged in
  // the Global editor panel) -- never written here, only read.
  const articlePageEl = document.querySelector(".article-page");
  const currentFontSizeMultiplier = () => {
    const value = parseFloat(articlePageEl && articlePageEl.dataset.fontSizeMultiplier);
    return Number.isNaN(value) ? 1 : value;
  };

  // {block_type: {field: default_value}} -- see BLOCK_STYLE_DEFAULTS in
  // article_models.py, rendered via json_script in
  // article_block_style_mini_panel.html. Powers the "Reset to default" button.
  const defaultsScript = document.getElementById("block-style-defaults-data");
  const BLOCK_STYLE_DEFAULTS = defaultsScript ? JSON.parse(defaultsScript.textContent) : {};

  // {block_type: display name} -- shown as the panel's own title (see
  // openPanelFor below) so it's clear at a glance which kind of block is
  // currently open, since this one shared panel's fields otherwise look
  // the same regardless of what's being edited.
  const BLOCK_TYPE_LABELS = {
    heading: "Heading",
    paragraph: "Paragraph",
    image: "Image",
    image_caption: "Image title/caption",
    multi_column: "Multi-column",
    column: "Column",
    article_header: "Header",
    title: "Title",
    meta: "Meta",
    intro: "Intro",
    hero_image: "Hero image",
    toc_icon: "TOC icon",
    article_card: "Article card",
    category_card: "Category card",
    union_card: "Student union card",
    tool_card: "Tool card",
  };

  // which fields apply to each block type, and (for alignment) which class
  // prefix + possible values that block's template actually uses to express
  // it -- paragraph and multi_column both have "alignment"-shaped
  // concepts in the model, but multi_column's is column_alignment (top/
  // center/bottom vertical layout, a different axis entirely), not left/
  // center/right text alignment, so it's deliberately left out here.
  const FIELDS_BY_TYPE = {
    heading: [
      "side_padding",
      "alignment",
      "exclude_from_global_alignment",
      "font_size",
      "text_color",
      "text_shadow_enabled",
      "text_shadow_strength",
      "text_shadow_color",
    ],
    paragraph: [
      "side_padding",
      "alignment",
      "exclude_from_global_alignment",
      "font_size",
      "text_color",
      "text_shadow_enabled",
      "text_shadow_strength",
      "text_shadow_color",
    ],
    image: ["alignment", "exclude_from_global_alignment", "width_rem", "side_padding"],
    // article/category/union/tool cards -- width/height (a fixed-design
    // card, not built from editable text/box parts like everything else
    // here; height 0 = auto), plus, for article_card only, list_style
    // (compact list row instead of a full card -- see .articlecard--list
    // in articlecard.css) and fixed_ratio (whether its image keeps its
    // normal 8:5 ratio or lets "Height" size it directly instead -- see
    // .articlecard--unlocked-ratio).
    article_card: ["width_rem", "height_rem", "list_style", "fixed_ratio"],
    category_card: ["width_rem", "height_rem"],
    union_card: ["width_rem", "height_rem"],
    tool_card: ["width_rem", "height_rem"],
    // an image's own title (alt_text)/caption, boxed together as one unit
    // (its own <figcaption>, see article_image_block.html) -- box plus its
    // own side padding, same shape as "column" below.
    image_caption: ["side_padding"],
    // per-column weight fields aren't listed here -- there's a variable
    // number of them (1-4, multi_column's own min/max_num), added to this
    // at runtime in openPanelFor() based on the block actually being
    // edited (data-column-count).
    multi_column: ["side_padding", "gap"],
    // a multi_column sub-column -- not a block type of its own in the
    // StreamField, just a ListBlock item id (see article_models.py's
    // _effective_block_styles()), with its own side padding plus box. Its
    // title (if it has one) shares this same trigger/panel rather than its
    // own -- alignment/font_size/text_color are added at runtime in
    // openPanelFor() when the column actually has one (data-title-block-
    // id), same pattern as multi_column's own column_weight_N fields
    // above. Saved as a second, independent request in recordPendingEdit()
    // (block_id "<column id>-title", block_type "column_title") alongside
    // the column's own side padding/box.
    column: ["side_padding"],
    // title/meta/intro (the article-header group) -- each fully styleable
    // from its own individual trigger: side padding/box/text color/the
    // "lock alignment" opt-out are ArticleBlockStyle rows (same as every
    // other alignment-capable block), while alignment/font-size are plain
    // ArticlePage fields saved via save_header_style instead (see
    // recordPendingEdit's own "article-header-style" pendingEdits entry) --
    // whichever of the three triggered a save, that request always carries
    // the *whole* title+meta+intro payload, since save_header_style only
    // ever accepts the full set at once (see headerWrapperEl() below for
    // why these fields are read from/written to the shared .article-header
    // wrapper regardless of which of the three is actually open).
    title: [
      "side_padding",
      "title_alignment",
      "title_exclude_from_global_alignment",
      "title_font_size",
      "title_text_color",
      "title_text_shadow_enabled",
      "title_text_shadow_strength",
      "title_text_shadow_color",
    ],
    meta: [
      "side_padding",
      "meta_alignment",
      "meta_exclude_from_global_alignment",
      "meta_font_size",
      "meta_text_color",
      "meta_text_shadow_enabled",
      "meta_text_shadow_strength",
      "meta_text_shadow_color",
    ],
    intro: [
      "side_padding",
      "intro_alignment",
      "intro_exclude_from_global_alignment",
      "intro_font_size",
      "intro_text_color",
      "intro_text_shadow_enabled",
      "intro_text_shadow_strength",
      "intro_text_shadow_color",
    ],
    // not a StreamField block -- the title/intro/meta group above the body,
    // wrapped together so they share one trigger for their own side
    // padding + Box (their alignment/font-size/text-color now live on
    // title/meta/intro's own individual triggers instead, see above).
    article_header: ["side_padding"],
    // alignment/width/side_padding reuse the exact same generic inputs as
    // "image" -- also not a StreamField block though (hero_image is a set
    // of ArticleStyle fields, see article_models.py), so it needs the same
    // special-cased save endpoint as article_header. boxed/box_color/
    // box_custom_color/box_border_radius have their own small dedicated
    // controls below (not the generic Box section -- that one saves to a
    // per-block ArticleBlockStyle row, these save to ArticleStyle instead,
    // same endpoint as the other three).
    hero_image: [
      "alignment",
      "width_rem",
      "side_padding",
      "boxed",
      "box_color",
      "box_custom_color",
      "box_border_radius",
      "shadow_enabled",
      "shadow_strength",
      "shadow_color",
    ],
    // not a StreamField block either -- there's only ever one
    // table-of-contents icon on the page (ArticlePage.toc_icon_size), same
    // special-cased save endpoint as article_header/hero_image.
    toc_icon: ["toc_icon_size"],
  };
  // wrapper <div> class prefix for each card block type (article_body_blocks.html/
  // article_column_content.html) -- these blocks' width/height live-preview (below)
  // sets CSS custom properties on the wrapper (--card-width/--card-height) rather
  // than a literal inline width/height, so a mobile breakpoint's own CSS can
  // override them at normal specificity instead of having to fight an inline style.
  const CARD_WRAPPER_CLASS = {
    article_card: "body-article-card",
    category_card: "body-category-card",
    union_card: "body-union-card",
    tool_card: "body-tool-card",
  };
  const CLASS_SWAP = {
    heading: { alignment: { prefix: "heading--align-", values: ["left", "center", "right"] } },
    paragraph: { alignment: { prefix: "prose--align-", values: ["left", "center", "right"] } },
    image: { alignment: { prefix: "body-image--", values: ["left", "center", "right"] } },
    hero_image: { alignment: { prefix: "hero-image--", values: ["left", "center", "right"] } },
  };


  // box styling (border/background/radius/padding/margin) is available on
  // every one of these -- appended to FIELDS_BY_TYPE at runtime (see
  // openPanelFor/buildSaveRequest below) rather than listed per type above,
  // since it's the same fixed set everywhere it applies. Deliberately not
  // offered on article_header/hero_image -- those are plain ArticlePage
  // fields, not part of the per-block override table box styling lives in.
  const BOX_CAPABLE_TYPES = new Set([
    "heading",
    "paragraph",
    "image",
    "image_caption",
    "multi_column",
    "column",
    "title",
    "meta",
    "intro",
    // the title/meta/intro group as a whole, same as multi_column's own
    // grid wrapper is boxable on top of each of its columns -- its own
    // side padding is deliberately excluded from this (see paddingInput's
    // own "input" listener and applyBoxStyle below, both special-case
    // this type to keep using --header-side-padding instead of margin-
    // left/right, since that CSS custom property's accent-underline
    // reasoning still applies regardless of whether the box itself is on).
    "article_header",
  ]);
  // box_bg_custom_color/box_border_custom_color aren't listed separately --
  // they're not their own panel field, just the value of the "Custom" hex
  // swatch inside box_bg_color/box_border_color (see the mini panel
  // template).
  const BOX_FIELD_NAMES = [
    "box_enabled",
    "box_bg_color",
    "box_border_visible",
    "box_border_width",
    "box_border_color",
    "box_radius",
    "box_padding",
    "box_margin",
    "box_shadow_enabled",
    "box_shadow_strength",
    "box_shadow_color",
  ];
  // every box field except box_enabled itself -- hidden until the box is
  // turned on (see updateBoxFieldVisibility()).
  const BOX_ONLY_FIELDS = BOX_FIELD_NAMES.slice(1);

  // Any full-width text block (.prose, headings, the title/intro/meta
  // header) sitting beside a floated image doesn't shrink its own box to
  // the narrower wrapped-text width -- only the text itself wraps, the box
  // stays full container width, running underneath the float. The
  // trigger's CSS default (top:0.25rem; right:0.25rem, anchored to that
  // full-width box) lands near the float's far edge instead of where the
  // text actually is -- for the header specifically, that's often right
  // behind/under the hero image itself, since the header sits right above
  // it. Rather than trying to measure exactly where text wraps (fragile
  // with rich text markup), find any floated image whose vertical range
  // overlaps the icon's row and place the icon right at that float's own
  // edge instead -- simpler and directly targets what we're actually
  // trying to avoid overlapping. Re-run on resize (float geometry changes)
  // and once each image finishes loading (no intrinsic height before then,
  // so float geometry isn't final yet).
  const positionTextTriggers = () => {
    const floats = Array.from(
      document.querySelectorAll(".hero-image-figure, .body-image-figure")
    ).filter((el) => ["left", "right"].includes(getComputedStyle(el).float));

    const editableTextSelectors = [
      ".prose.editable-block",
      ".article-header.editable-block",
      "h2.editable-block",
      "h3.editable-block",
      "h4.editable-block",
      "h5.editable-block",
    ].join(", ");

    document.querySelectorAll(editableTextSelectors).forEach((blockEl) => {
      const trigger = blockEl.querySelector(".block-style-trigger");
      if (!trigger) {
        return;
      }
      // a multi-column item is a flex item, which per spec establishes its
      // own formatting context -- it's never affected by a float outside
      // the grid (that's also what keeps text from spilling across
      // columns), so there's nothing to avoid in here. Without this, a
      // same-page-height float completely unrelated to this column (e.g.
      // the hero image, well above/beside the grid) could still register
      // as "overlapping" by pure Y-coordinate coincidence and shove this
      // trigger somewhere that collides with the multi-column block's own
      // trigger (top-right of the whole grid, not any one column).
      if (blockEl.closest(".multi-col-item")) {
        trigger.style.top = "";
        trigger.style.right = "";
        trigger.style.left = "";
        return;
      }
      const blockRect = blockEl.getBoundingClientRect();
      const iconRowTop = blockRect.top + 4; // roughly where the icon sits, in CSS px from the top
      const iconRowBottom = iconRowTop + 28; // icon's own height (1.75rem) plus a little slack

      const overlapping = floats.find((floatEl) => {
        const fr = floatEl.getBoundingClientRect();
        return (
          fr.top < iconRowBottom &&
          fr.bottom > iconRowTop &&
          fr.left < blockRect.right &&
          fr.right > blockRect.left
        );
      });

      if (!overlapping) {
        trigger.style.top = "";
        trigger.style.right = "";
        trigger.style.left = "";
        return;
      }

      const floatRect = overlapping.getBoundingClientRect();
      const floatSide = getComputedStyle(overlapping).float;
      trigger.style.top = "0.25rem";
      if (floatSide === "right") {
        trigger.style.right = `${Math.max(blockRect.right - floatRect.left + 8, 2)}px`;
        trigger.style.left = "auto";
      } else {
        trigger.style.left = `${Math.max(floatRect.right - blockRect.left + 8, 2)}px`;
        trigger.style.right = "auto";
      }
    });
  };

  positionTextTriggers();
  window.addEventListener("resize", positionTextTriggers);
  document.querySelectorAll(".hero-image, .body-image").forEach((img) => {
    if (img.complete) {
      return;
    }
    img.addEventListener("load", positionTextTriggers);
  });

  const targetIdInput = document.getElementById("block-style-target-id");
  const targetTypeInput = document.getElementById("block-style-target-type");
  const paddingInput = document.getElementById("block-style-padding");
  const paddingValue = document.getElementById("block-style-padding-value");
  const fontSizeInput = document.getElementById("block-style-font-size");
  const fontSizeValue = document.getElementById("block-style-font-size-value");
  const fontSizeLabel = document.getElementById("block-style-font-size-label");
  const textColorLabel = document.getElementById("block-style-text-color-label");
  const widthInput = document.getElementById("block-style-width");
  const widthValue = document.getElementById("block-style-width-value");
  const heightInput = document.getElementById("block-style-height");
  const heightValue = document.getElementById("block-style-height-value");
  const listStyleInput = document.getElementById("block-style-list-style");
  const fixedRatioInput = document.getElementById("block-style-fixed-ratio");
  // hero_image only -- see FIELDS_BY_TYPE.hero_image's own comment for why
  // these are separate from the generic Box section's box*Input refs below.
  const heroBoxedInput = document.getElementById("block-style-hero-boxed");
  const heroBoxColorGroup = document.getElementById("block-style-hero-box-color");
  const heroBoxCustomColorInput = document.getElementById("block-style-hero-box-custom-color");
  const heroBoxPickerInput = document.getElementById("block-style-hero-box-picker");
  const heroBoxRadiusInput = document.getElementById("block-style-hero-box-radius");
  const heroBoxRadiusValue = document.getElementById("block-style-hero-box-radius-value");
  const alignmentGroup = document.getElementById("block-style-alignment");
  // opts this block (or, for the merged column panel, the column's own
  // title -- see FIELDS_BY_TYPE.column) out of the Global editor's
  // Alignment "overwrite all blocks" action -- see ArticleBlockStyle.
  // exclude_from_global_alignment, save_quick_style's apply_alignment_to_
  // blocks, and article_quick_style.js's save(). CAPTION_TEXT_GROUPS below
  // each have their own separate one (excludeInput), since image_title/
  // image_caption_body are independently alignment-capable blocks of
  // their own, not the shared "Style" section this one belongs to.
  const excludeGlobalAlignmentInput = document.getElementById("block-style-exclude-global-alignment");
  const titleAlignmentGroup = document.getElementById("block-style-title-alignment");
  const introAlignmentGroup = document.getElementById("block-style-intro-alignment");
  const metaAlignmentGroup = document.getElementById("block-style-meta-alignment");
  const titleFontSizeInput = document.getElementById("block-style-title-font-size");
  const titleFontSizeValue = document.getElementById("block-style-title-font-size-value");
  const introFontSizeInput = document.getElementById("block-style-intro-font-size");
  const introFontSizeValue = document.getElementById("block-style-intro-font-size-value");
  const metaFontSizeInput = document.getElementById("block-style-meta-font-size");
  const metaFontSizeValue = document.getElementById("block-style-meta-font-size-value");
  // title/meta/intro's own "lock alignment" opt-out -- unlike alignment/
  // font-size/text-color above, this one is NOT part of the shared
  // save_header_style payload: it saves onto each one's own existing
  // ArticleBlockStyle row (block_id "article-title"/etc, same row side
  // padding/box already use), read/written directly off currentBlockEl
  // (the h1/.article-meta/.intro element itself), same as every other
  // block type's own exclude_from_global_alignment checkbox.
  const titleExcludeGlobalAlignmentInput = document.getElementById("block-style-title-exclude-global-alignment");
  const metaExcludeGlobalAlignmentInput = document.getElementById("block-style-meta-exclude-global-alignment");
  const introExcludeGlobalAlignmentInput = document.getElementById("block-style-intro-exclude-global-alignment");
  const gapInput = document.getElementById("block-style-gap");
  const gapValue = document.getElementById("block-style-gap-value");
  const tocIconSizeInput = document.getElementById("block-style-toc-icon-size");
  const tocIconSizeValue = document.getElementById("block-style-toc-icon-size-value");
  const MAX_COLUMNS = 4;
  const columnWeightInputs = Array.from({ length: MAX_COLUMNS }, (_, i) =>
    document.getElementById(`block-style-column-weight-${i}`)
  );
  const columnWeightValues = Array.from({ length: MAX_COLUMNS }, (_, i) =>
    document.getElementById(`block-style-column-weight-${i}-value`)
  );
  const statusEl = document.getElementById("block-style-mini-panel-status");
  const panelTitle = document.getElementById("block-style-mini-panel-title");

  const boxEnabledInput = document.getElementById("block-style-box-enabled");
  const boxBgColorGroup = document.getElementById("block-style-box-bg-color");
  const boxBgCustomColorInput = document.getElementById("block-style-box-bg-custom-color");
  const boxBgPickerInput = document.getElementById("block-style-box-bg-picker");
  const styleLabel = document.getElementById("block-style-style-label");
  // NOT box-scoped -- applies independent of that block's own box (see
  // applyTextColor below), so these live outside the Box section entirely
  // in the template, in their own "Style" section alongside font-size/
  // alignment.
  const textColorGroup = document.getElementById("block-style-text-color");
  const textCustomColorInput = document.getElementById("block-style-text-custom-color");
  const textPickerInput = document.getElementById("block-style-text-picker");
  // text shadow -- same "outside Box, applies independent of it" reasoning
  // as text color just above, own dedicated refs since it's a visually/
  // functionally separate control group in the template even though both
  // live in the same "Style" section.
  const textShadowEnabledInput = document.getElementById("block-style-text-shadow-enabled");
  const textShadowStrengthInput = document.getElementById("block-style-text-shadow-strength");
  const textShadowStrengthValue = document.getElementById("block-style-text-shadow-strength-value");
  const textShadowColorGroup = document.getElementById("block-style-text-shadow-color");
  const textShadowCustomColorInput = document.getElementById("block-style-text-shadow-custom-color");
  const textShadowPickerInput = document.getElementById("block-style-text-shadow-picker");
  const boxBorderVisibleInput = document.getElementById("block-style-box-border-visible");
  const boxBorderWidthInput = document.getElementById("block-style-box-border-width");
  const boxBorderWidthValue = document.getElementById("block-style-box-border-width-value");
  const boxBorderColorGroup = document.getElementById("block-style-box-border-color");
  const boxBorderCustomColorInput = document.getElementById("block-style-box-border-custom-color");
  const boxBorderPickerInput = document.getElementById("block-style-box-border-picker");
  const boxRadiusInput = document.getElementById("block-style-box-radius");
  const boxRadiusValue = document.getElementById("block-style-box-radius-value");
  const boxPaddingInput = document.getElementById("block-style-box-padding");
  const boxPaddingValue = document.getElementById("block-style-box-padding-value");
  const boxMarginInput = document.getElementById("block-style-box-margin");
  const boxMarginValue = document.getElementById("block-style-box-margin-value");
  const boxShadowEnabledInput = document.getElementById("block-style-box-shadow-enabled");
  const boxShadowStrengthInput = document.getElementById("block-style-box-shadow-strength");
  const boxShadowStrengthValue = document.getElementById("block-style-box-shadow-strength-value");
  const boxShadowColorGroup = document.getElementById("block-style-box-shadow-color");
  const boxShadowCustomColorInput = document.getElementById("block-style-box-shadow-custom-color");
  const boxShadowPickerInput = document.getElementById("block-style-box-shadow-picker");
  // hero_image's own separate box shadow -- see FIELDS_BY_TYPE.hero_image's
  // own comment for why hero_image needs its own dedicated refs/wiring
  // rather than reusing the generic box* ones above.
  const heroBoxShadowEnabledInput = document.getElementById("block-style-hero-box-shadow-enabled");
  const heroBoxShadowStrengthInput = document.getElementById("block-style-hero-box-shadow-strength");
  const heroBoxShadowStrengthValue = document.getElementById("block-style-hero-box-shadow-strength-value");
  const heroBoxShadowColorGroup = document.getElementById("block-style-hero-box-shadow-color");
  const heroBoxShadowCustomColorInput = document.getElementById("block-style-hero-box-shadow-custom-color");
  const heroBoxShadowPickerInput = document.getElementById("block-style-hero-box-shadow-picker");

  // an image_caption's own title (alt_text)/caption text -- see
  // article_image_block.html's data-title-*/data-caption-* attributes and
  // BLOCK_STYLE_DEFAULTS["image_title"]/["image_caption_body"] in
  // article_models.py. Two near-identical groups (same shape as the
  // generic alignment/font-size/side-padding/text-color fields used
  // everywhere else), each with its own dedicated panel fields since both
  // need to be visible/editable at once in this one shared panel -- driven
  // generically off this config rather than duplicating the wiring below
  // twice by hand.
  const CAPTION_TEXT_GROUPS = [
    {
      datasetPrefix: "title",
      styleFieldPrefix: "caption_title",
      blockType: "image_title",
      defaultsKey: "image_title",
      spanSelector: ":scope > .image-title",
      alignmentGroup: document.getElementById("block-style-caption-title-alignment"),
      excludeInput: document.getElementById("block-style-caption-title-exclude-global-alignment"),
      fontSizeInput: document.getElementById("block-style-caption-title-font-size"),
      fontSizeValue: document.getElementById("block-style-caption-title-font-size-value"),
      paddingInput: document.getElementById("block-style-caption-title-padding"),
      paddingValue: document.getElementById("block-style-caption-title-padding-value"),
      colorGroup: document.getElementById("block-style-caption-title-text-color"),
      customColorInput: document.getElementById("block-style-caption-title-custom-color"),
      pickerInput: document.getElementById("block-style-caption-title-picker"),
      shadowEnabledInput: document.getElementById("block-style-caption-title-shadow-enabled"),
      shadowStrengthInput: document.getElementById("block-style-caption-title-shadow-strength"),
      shadowStrengthValue: document.getElementById("block-style-caption-title-shadow-strength-value"),
      shadowColorGroup: document.getElementById("block-style-caption-title-shadow-color"),
      shadowCustomColorInput: document.getElementById("block-style-caption-title-shadow-custom-color"),
      shadowPickerInput: document.getElementById("block-style-caption-title-shadow-picker"),
    },
    {
      datasetPrefix: "caption",
      styleFieldPrefix: "caption_body",
      blockType: "image_caption_body",
      defaultsKey: "image_caption_body",
      spanSelector: ":scope > .image-caption",
      alignmentGroup: document.getElementById("block-style-caption-body-alignment"),
      excludeInput: document.getElementById("block-style-caption-body-exclude-global-alignment"),
      fontSizeInput: document.getElementById("block-style-caption-body-font-size"),
      fontSizeValue: document.getElementById("block-style-caption-body-font-size-value"),
      paddingInput: document.getElementById("block-style-caption-body-padding"),
      paddingValue: document.getElementById("block-style-caption-body-padding-value"),
      colorGroup: document.getElementById("block-style-caption-body-text-color"),
      customColorInput: document.getElementById("block-style-caption-body-custom-color"),
      pickerInput: document.getElementById("block-style-caption-body-picker"),
      shadowEnabledInput: document.getElementById("block-style-caption-body-shadow-enabled"),
      shadowStrengthInput: document.getElementById("block-style-caption-body-shadow-strength"),
      shadowStrengthValue: document.getElementById("block-style-caption-body-shadow-strength-value"),
      shadowColorGroup: document.getElementById("block-style-caption-body-shadow-color"),
      shadowCustomColorInput: document.getElementById("block-style-caption-body-shadow-custom-color"),
      shadowPickerInput: document.getElementById("block-style-caption-body-shadow-picker"),
    },
  ];

  // title/meta/intro's own text color -- edited from each one's own
  // trigger, saved as part of that same trigger's own ArticleBlockStyle
  // row (block_id "article-title"/"article-meta"/"article-intro", merged
  // into buildSaveRequest's generic per-block payload -- see its own
  // comment for why this can't be a separate pendingEdits entry).
  // targetSelector picks the live-preview target off the shared .article-
  // header wrapper (headerWrapperEl(), not currentBlockEl directly -- see
  // that function's own comment), same idea as CAPTION_TEXT_GROUPS'
  // spanSelector.
  const HEADER_TEXT_COLOR_GROUPS = [
    {
      datasetPrefix: "title",
      blockId: "article-title",
      blockType: "title",
      targetSelector: ":scope > h1",
      colorGroup: document.getElementById("block-style-title-text-color"),
      customColorInput: document.getElementById("block-style-title-text-custom-color"),
      pickerInput: document.getElementById("block-style-title-text-picker"),
      shadowEnabledInput: document.getElementById("block-style-title-shadow-enabled"),
      shadowStrengthInput: document.getElementById("block-style-title-shadow-strength"),
      shadowStrengthValue: document.getElementById("block-style-title-shadow-strength-value"),
      shadowColorGroup: document.getElementById("block-style-title-shadow-color"),
      shadowCustomColorInput: document.getElementById("block-style-title-shadow-custom-color"),
      shadowPickerInput: document.getElementById("block-style-title-shadow-picker"),
    },
    {
      datasetPrefix: "meta",
      blockId: "article-meta",
      blockType: "meta",
      targetSelector: ":scope > .article-meta",
      colorGroup: document.getElementById("block-style-meta-text-color"),
      customColorInput: document.getElementById("block-style-meta-text-custom-color"),
      pickerInput: document.getElementById("block-style-meta-text-picker"),
      shadowEnabledInput: document.getElementById("block-style-meta-shadow-enabled"),
      shadowStrengthInput: document.getElementById("block-style-meta-shadow-strength"),
      shadowStrengthValue: document.getElementById("block-style-meta-shadow-strength-value"),
      shadowColorGroup: document.getElementById("block-style-meta-shadow-color"),
      shadowCustomColorInput: document.getElementById("block-style-meta-shadow-custom-color"),
      shadowPickerInput: document.getElementById("block-style-meta-shadow-picker"),
    },
    {
      datasetPrefix: "intro",
      blockId: "article-intro",
      blockType: "intro",
      targetSelector: ":scope > .intro",
      colorGroup: document.getElementById("block-style-intro-text-color"),
      customColorInput: document.getElementById("block-style-intro-text-custom-color"),
      pickerInput: document.getElementById("block-style-intro-text-picker"),
      shadowEnabledInput: document.getElementById("block-style-intro-shadow-enabled"),
      shadowStrengthInput: document.getElementById("block-style-intro-shadow-strength"),
      shadowStrengthValue: document.getElementById("block-style-intro-shadow-strength-value"),
      shadowColorGroup: document.getElementById("block-style-intro-shadow-color"),
      shadowCustomColorInput: document.getElementById("block-style-intro-shadow-custom-color"),
      shadowPickerInput: document.getElementById("block-style-intro-shadow-picker"),
    },
  ];

  let currentBlockEl = null;
  let currentTrigger = null;

  // title/meta/intro/article_header's own alignment/font-size/text-color
  // all render onto the shared .article-header wrapper's own dataset/style
  // (see article_page.html), regardless of which of the four triggers is
  // open -- currentBlockEl is whichever one was actually clicked (the
  // wrapper itself for "article_header", or the h1/.article-meta/.intro
  // child for "title"/"meta"/"intro"). Every read/write of those specific
  // fields needs to go through this wrapper rather than currentBlockEl
  // directly, so the live-preview CSS custom properties (--title-alignment
  // etc, only consumed by rules scoped to .article-header itself/its
  // direct children in article_header.css) land on the right element, and
  // so switching triggers doesn't lose track of the other two's current
  // values before a save (see the combined save_header_style payload in
  // recordPendingEdit). Returns null if no block is open, or the block
  // open isn't part of the header group at all.
  const headerWrapperEl = () => {
    if (!currentBlockEl) {
      return null;
    }
    return currentBlockEl.classList.contains("article-header")
      ? currentBlockEl
      : currentBlockEl.closest(".article-header");
  };

  // one shared panel, but edits to *every* block touched since the last
  // save need to survive switching to a different block -- keyed by
  // block_id (a real block's UUID, or the fixed "article-header"/
  // "hero-image" strings for the two non-StreamField block types), each
  // value the exact {url, payload} save() would need to send for that one
  // block. Rebuilt in full on every field change (see recordPendingEdit()),
  // not just the one field that changed, since a save always POSTs a
  // block's whole set of relevant fields at once.
  const pendingEdits = new Map();

  // Exposed for article_quick_style.js's own Reset button: without this, a
  // stale "article-header-style" entry queued earlier in the session (from
  // touching Title/Meta/Intro's own sliders in this panel before resetting
  // globally) would flush via save() below -- registered *after* quick
  // style's own save handler (see article_page.html's <script> order) --
  // and silently overwrite the header_side_padding/title_font_size/
  // meta_font_size/intro_font_size global Reset just wrote, even though
  // alignment resets fine (it's re-applied unconditionally by save_quick_
  // style's own apply_alignment_to_blocks, not just whatever this panel's
  // pendingEdits happens to send).
  window.ifiDiscardPendingHeaderStyleEdit = () => {
    pendingEdits.delete("article-header-style");
  };

  // builds the {url, payload} save() would send for whatever block is
  // currently shown in the panel, from the panel's own current field
  // values -- reads targetTypeInput/targetIdInput/paddingInput/etc, all
  // declared above. Returns null if no block has ever been opened this
  // session (targetTypeInput.value is still "").
  const buildSaveRequest = () => {
    const blockType = targetTypeInput.value;
    if (!blockType) {
      return null;
    }

    // article_header isn't a StreamField block, but unlike hero_image/
    // toc_icon below it's box-capable and it kept one real generic-path
    // field of its own (side_padding, for its Layout section) -- so it
    // falls all the way through to the generic per-block path at the
    // bottom like every other box-capable type, rather than an early
    // return here. side_padding itself never actually lands anywhere for
    // this type (see BLOCK_STYLE_FIELDS["article_header"] in
    // article_views.py, which omits it -- header's own side padding is a
    // plain ArticlePage field, save_header_style below, not this row) --
    // the generic path sends it anyway, harmlessly ignored by the backend,
    // rather than special-casing it out here too. Its title_alignment/
    // meta_alignment/intro_alignment/header_side_padding/title_font_size/
    // meta_font_size/intro_font_size and its own box now save via two
    // separate manual pendingEdits entries instead of this function's own
    // return value -- see recordPendingEdit's "article-header-style" block
    // (this same generic path's return value already covers article_
    // header's box correctly, so no separate manual box entry is needed
    // any more either).

    // hero_image isn't a StreamField block either -- ArticleStyle fields
    // (hero_image_position/width_rem/side_padding/boxed/box_color/
    // box_custom_color/box_border_radius), same reasoning as article_header
    // above.
    if (blockType === "hero_image") {
      return {
        url: panel.dataset.heroImageSaveUrl,
        payload: {
          alignment: alignmentGroup.dataset.value,
          width_rem: widthInput.value,
          side_padding: paddingInput.value,
          boxed: heroBoxedInput.checked,
          box_color: heroBoxColorGroup.dataset.value,
          box_custom_color: heroBoxCustomColorInput.value,
          box_border_radius: heroBoxRadiusInput.value,
          shadow_enabled: heroBoxShadowEnabledInput.checked,
          shadow_strength: heroBoxShadowStrengthInput.value,
          shadow_color: heroBoxShadowColorGroup.dataset.value,
          shadow_custom_color: heroBoxShadowCustomColorInput.value,
        },
      };
    }

    // not a StreamField block either -- there's only ever one
    // table-of-contents icon on the page (ArticlePage.toc_icon_size).
    if (blockType === "toc_icon") {
      return {
        url: panel.dataset.tocIconSaveUrl,
        payload: {
          toc_icon_size: tocIconSizeInput.value,
        },
      };
    }

    const visibleFields = FIELDS_BY_TYPE[blockType] || [];
    let columnWeights = null;
    if (blockType === "multi_column") {
      // currentBlockEl can be null by the time this runs (closePanel()
      // nulls it, but a pending edit can still be flushed after that) --
      // look the block back up by id instead of relying on it.
      const blockEl =
        currentBlockEl || document.querySelector(`[data-block-id="${CSS.escape(targetIdInput.value)}"]`);
      const columnCount = parseInt(blockEl ? blockEl.dataset.columnCount : "0", 10) || 0;
      columnWeights = columnWeightInputs
        .slice(0, columnCount)
        .map((input) => parseFloat(input.value));
    }
    const boxCapable = BOX_CAPABLE_TYPES.has(blockType);
    // title/meta/intro's own "lock alignment" checkbox is a differently-
    // named field per type (title_exclude_from_global_alignment etc, see
    // FIELDS_BY_TYPE) since each needs its own dedicated input, but they
    // all save to the exact same backend column (ArticleBlockStyle.
    // exclude_from_global_alignment) as every other block type's shared
    // one -- resolve whichever one actually applies to a single payload
    // value here.
    let excludeFromGlobalAlignment = null;
    if (visibleFields.includes("exclude_from_global_alignment")) {
      excludeFromGlobalAlignment = excludeGlobalAlignmentInput.checked;
    } else if (visibleFields.includes("title_exclude_from_global_alignment")) {
      excludeFromGlobalAlignment = titleExcludeGlobalAlignmentInput.checked;
    } else if (visibleFields.includes("meta_exclude_from_global_alignment")) {
      excludeFromGlobalAlignment = metaExcludeGlobalAlignmentInput.checked;
    } else if (visibleFields.includes("intro_exclude_from_global_alignment")) {
      excludeFromGlobalAlignment = introExcludeGlobalAlignmentInput.checked;
    }
    // title/meta/intro's own text color -- same reasoning as the exclude
    // flag above (their own dedicated color picker, not the generic Style
    // section's), but merged into *this* request rather than a separate
    // pendingEdits entry: this row (block_id "article-title" etc) is the
    // exact same one side_padding/box above already save to, and a second
    // pendingEdits.set() call for that identical key would silently
    // replace this whole request in the map instead of adding to it (see
    // HEADER_TEXT_COLOR_GROUPS's own comment).
    const headerColorGroup = HEADER_TEXT_COLOR_GROUPS.find((group) => group.blockType === blockType);
    let textColor = visibleFields.includes("text_color") ? textColorGroup.dataset.value : null;
    let textCustomColor = visibleFields.includes("text_color") ? textCustomColorInput.value : null;
    let textShadowEnabled = visibleFields.includes("text_shadow_enabled") ? textShadowEnabledInput.checked : null;
    let textShadowStrength = visibleFields.includes("text_shadow_strength") ? textShadowStrengthInput.value : null;
    let textShadowColor = visibleFields.includes("text_shadow_color") ? textShadowColorGroup.dataset.value : null;
    let textShadowCustomColor = visibleFields.includes("text_shadow_color")
      ? textShadowCustomColorInput.value
      : null;
    if (headerColorGroup) {
      textColor = headerColorGroup.colorGroup.dataset.value;
      textCustomColor = headerColorGroup.customColorInput.value;
      textShadowEnabled = headerColorGroup.shadowEnabledInput.checked;
      textShadowStrength = headerColorGroup.shadowStrengthInput.value;
      textShadowColor = headerColorGroup.shadowColorGroup.dataset.value;
      textShadowCustomColor = headerColorGroup.shadowCustomColorInput.value;
    }
    return {
      url: panel.dataset.saveUrl,
      payload: {
        block_id: targetIdInput.value,
        block_type: blockType,
        side_padding: visibleFields.includes("side_padding") ? paddingInput.value : null,
        alignment: visibleFields.includes("alignment") ? alignmentGroup.dataset.value : null,
        exclude_from_global_alignment: excludeFromGlobalAlignment,
        font_size: visibleFields.includes("font_size") ? fontSizeInput.value : null,
        width_rem: visibleFields.includes("width_rem") ? widthInput.value : null,
        height_rem: visibleFields.includes("height_rem") ? heightInput.value : null,
        list_style: visibleFields.includes("list_style") ? listStyleInput.checked : null,
        fixed_ratio: visibleFields.includes("fixed_ratio") ? fixedRatioInput.checked : null,
        gap: visibleFields.includes("gap") ? gapInput.value : null,
        column_weights: columnWeights,
        text_color: textColor,
        text_custom_color: textCustomColor,
        text_shadow_enabled: textShadowEnabled,
        text_shadow_strength: textShadowStrength,
        text_shadow_color: textShadowColor,
        text_shadow_custom_color: textShadowCustomColor,
        box_enabled: boxCapable ? boxEnabledInput.checked : null,
        box_bg_color: boxCapable ? boxBgColorGroup.dataset.value : null,
        box_bg_custom_color: boxCapable ? boxBgCustomColorInput.value : null,
        box_border_visible: boxCapable ? boxBorderVisibleInput.checked : null,
        box_border_width: boxCapable ? boxBorderWidthInput.value : null,
        box_border_color: boxCapable ? boxBorderColorGroup.dataset.value : null,
        box_border_custom_color: boxCapable ? boxBorderCustomColorInput.value : null,
        box_radius: boxCapable ? boxRadiusInput.value : null,
        box_padding: boxCapable ? boxPaddingInput.value : null,
        box_margin: boxCapable ? boxMarginInput.value : null,
        box_shadow_enabled: boxCapable ? boxShadowEnabledInput.checked : null,
        box_shadow_strength: boxCapable ? boxShadowStrengthInput.value : null,
        box_shadow_color: boxCapable ? boxShadowColorGroup.dataset.value : null,
        box_shadow_custom_color: boxCapable ? boxShadowCustomColorInput.value : null,
      },
    };
  };

  // called after every live edit -- snapshots the *whole* current save
  // request for the block being edited right now, keyed by its block_id, so
  // switching to a different block afterwards doesn't lose it (see
  // pendingEdits above).
  const recordPendingEdit = () => {
    const blockId = targetIdInput.value;
    const request = buildSaveRequest();
    if (!blockId || !request) {
      return;
    }
    pendingEdits.set(blockId, request);

    // a column's title is saved as its own separate ArticleBlockStyle row
    // (block_id "<column id>-title", block_type "column_title") even
    // though it now shares the column's own trigger/panel (see
    // FIELDS_BY_TYPE.column) -- record a second, independent pending edit
    // for it alongside the column's own, keyed by its own block_id so it
    // survives switching to a different block same as any other pending
    // edit (see pendingEdits above).
    if (targetTypeInput.value === "column" && currentBlockEl && currentBlockEl.dataset.titleBlockId) {
      const titleId = currentBlockEl.dataset.titleBlockId;
      pendingEdits.set(titleId, {
        url: panel.dataset.saveUrl,
        payload: {
          block_id: titleId,
          block_type: "column_title",
          alignment: alignmentGroup.dataset.value,
          exclude_from_global_alignment: excludeGlobalAlignmentInput.checked,
          font_size: fontSizeInput.value,
          text_color: textColorGroup.dataset.value,
          text_custom_color: textCustomColorInput.value,
          text_shadow_enabled: textShadowEnabledInput.checked,
          text_shadow_strength: textShadowStrengthInput.value,
          text_shadow_color: textShadowColorGroup.dataset.value,
          text_shadow_custom_color: textShadowCustomColorInput.value,
        },
      });
    }

    // an image_caption's own title/caption text are each saved as their
    // own separate ArticleBlockStyle row too (block_id "<image id>-cap-
    // title"/"-cap-body", see CAPTION_TEXT_GROUPS above), alongside the
    // figcaption's own box -- same reasoning as column's title above.
    if (targetTypeInput.value === "image_caption" && currentBlockEl) {
      CAPTION_TEXT_GROUPS.forEach((group) => {
        const textId = currentBlockEl.dataset[`${group.datasetPrefix}TextId`];
        if (!textId) {
          return;
        }
        pendingEdits.set(textId, {
          url: panel.dataset.saveUrl,
          payload: {
            block_id: textId,
            block_type: group.blockType,
            alignment: group.alignmentGroup.dataset.value,
            exclude_from_global_alignment: group.excludeInput.checked,
            font_size: group.fontSizeInput.value,
            side_padding: group.paddingInput.value,
            text_color: group.colorGroup.dataset.value,
            text_custom_color: group.customColorInput.value,
            text_shadow_enabled: group.shadowEnabledInput.checked,
            text_shadow_strength: group.shadowStrengthInput.value,
            text_shadow_color: group.shadowColorGroup.dataset.value,
            text_shadow_custom_color: group.shadowCustomColorInput.value,
          },
        });
      });
    }

    // title/meta/intro's own text color is merged into this function's
    // primary buildSaveRequest() result above now (see its own comment) --
    // article_header's box is too, now that article_header falls through
    // to the same generic per-block path as every other box-capable type
    // (see buildSaveRequest's own article_header comment) -- so box no
    // longer needs its own separate manual pendingEdits entry here either.
    //
    // What's left, common to all four of title/meta/intro/article_header:
    // title_alignment/meta_alignment/intro_alignment/header_side_padding/
    // title_font_size/meta_font_size/intro_font_size, saved together via
    // save_header_style regardless of which of the four triggered the
    // save -- that endpoint only ever accepts the whole set at once (see
    // save_header_style in article_views.py), and headerWrapperEl()'s own
    // comment covers why these inputs stay correctly populated no matter
    // which trigger is currently open. Fixed pendingEdits key
    // ("article-header-style", not any of the four's own block_id) so
    // opening a second one of the four afterwards updates this same entry
    // in place instead of creating a duplicate.
    if (["article_header", "title", "meta", "intro"].includes(targetTypeInput.value)) {
      pendingEdits.set("article-header-style", {
        url: panel.dataset.headerSaveUrl,
        payload: {
          title_alignment: titleAlignmentGroup.dataset.value,
          intro_alignment: introAlignmentGroup.dataset.value,
          meta_alignment: metaAlignmentGroup.dataset.value,
          header_side_padding: paddingInput.value,
          title_font_size: titleFontSizeInput.value,
          intro_font_size: introFontSizeInput.value,
          meta_font_size: metaFontSizeInput.value,
        },
      });
    }

    window.ifiUnsavedChanges.markDirty("blockStyle");
  };

  const swapClass = (blockEl, blockType, field, value) => {
    const swap = (CLASS_SWAP[blockType] || {})[field];
    if (!swap) {
      return;
    }
    swap.values.forEach((v) => {
      blockEl.classList.remove(swap.prefix + v);
    });
    blockEl.classList.add(swap.prefix + value);
  };

  // alignment/font-size/text-color normally read/write directly on
  // currentBlockEl's own dataset -- but a multi_column column's title has
  // no separate trigger/panel of its own any more (see FIELDS_BY_TYPE.column
  // below): these same three fields describe the *title* instead while a
  // "column" is what's open. Both the dataset key they're stored under (so
  // reopening this same column later in the same page load picks the right
  // value back up, see openPanelFor) and the live-preview target (the
  // title, not the column) need to shift accordingly.
  const TITLE_DATASET_KEYS = {
    alignment: "titleAlignment",
    excludeFromGlobalAlignment: "titleExcludeFromGlobalAlignment",
    fontSize: "titleFontSize",
    textColor: "titleTextColor",
    textCustomColor: "titleTextCustomColor",
    textShadowEnabled: "titleTextShadowEnabled",
    textShadowStrength: "titleTextShadowStrength",
    textShadowColor: "titleTextShadowColor",
    textShadowCustomColor: "titleTextShadowCustomColor",
  };
  const styleDatasetKey = (key) =>
    targetTypeInput.value === "column" && TITLE_DATASET_KEYS[key] ? TITLE_DATASET_KEYS[key] : key;

  // alignment positions the title via its wrapping <div> -- column-title is
  // display:inline-block (so its border-bottom underline hugs just the
  // text, see article_multicolumn.css), which leaves its own text-align
  // nothing to align within its own tightly-fit box (see
  // article_body_blocks.html's own comment on .column-title-wrap). Font-
  // size/color apply directly to the title text itself instead.
  const columnTitleWrapEl = () =>
    currentBlockEl ? currentBlockEl.querySelector(":scope > .column-title-wrap") : null;
  const columnTitleEl = () =>
    currentBlockEl ? currentBlockEl.querySelector(":scope > .column-title-wrap > .column-title") : null;

  const wireButtonGroup = (group, field, dataAttr) => {
    group.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        if (!currentBlockEl) {
          return;
        }
        const value = button.dataset[dataAttr];
        group.dataset.value = value;
        currentBlockEl.dataset[styleDatasetKey(field)] = value;
        if (field === "alignment" && targetTypeInput.value === "column") {
          const wrap = columnTitleWrapEl();
          if (wrap) {
            wrap.style.textAlign = value;
          }
        } else {
          swapClass(currentBlockEl, targetTypeInput.value, field, value);
        }
        group.querySelectorAll("button").forEach((b) => {
          b.classList.toggle("active", b === button);
        });
        positionTextTriggers();
        recordPendingEdit();
      });
    });
  };

  // live-preview mirror of _block_box_style.html's own logic: while the box
  // is off, padding-left/right come from the block's own side_padding (see
  // paddingInput's own listener below) -- no visible border to offset, so
  // indenting the block just means indenting its content. While it's on,
  // side_padding switches to margin-left/right instead, so it's the box's
  // *border* (not just empty space inside it) that ends up indented --
  // box.padding becomes the space between that border and the content on
  // all four sides, box.margin the vertical space outside it, side_padding
  // the horizontal counterpart to box.margin, not to box.padding. Skipped
  // entirely for article_header -- its own side padding always goes
  // through --header-side-padding instead (paddingInput's own listener
  // special-cases this same type), regardless of whether its box is on.
  const applyBoxStyle = () => {
    if (!currentBlockEl) {
      return;
    }
    const enabled = boxEnabledInput.checked;
    const managesSidePadding = targetTypeInput.value !== "article_header";
    currentBlockEl.classList.toggle("block-box", enabled);
    if (!enabled) {
      currentBlockEl.style.padding = "";
      currentBlockEl.style.marginTop = "";
      currentBlockEl.style.marginBottom = "";
      if (managesSidePadding) {
        currentBlockEl.style.marginLeft = "";
        currentBlockEl.style.marginRight = "";
      }
      currentBlockEl.style.backgroundColor = "";
      currentBlockEl.style.borderRadius = "";
      currentBlockEl.style.boxShadow = "";
      currentBlockEl.style.border = "";
      currentBlockEl.style.display = "";
      if (managesSidePadding) {
        currentBlockEl.style.paddingLeft = `${paddingInput.value}rem`;
        currentBlockEl.style.paddingRight = `${paddingInput.value}rem`;
      }
      return;
    }
    currentBlockEl.style.padding = `${boxPaddingInput.value}rem`;
    currentBlockEl.style.marginTop = `${boxMarginInput.value}rem`;
    currentBlockEl.style.marginBottom = `${boxMarginInput.value}rem`;
    if (managesSidePadding) {
      currentBlockEl.style.marginLeft = `${paddingInput.value}rem`;
      currentBlockEl.style.marginRight = `${paddingInput.value}rem`;
    }
    // multi_column's own grid wrapper needs to stay "display: flex" (set in
    // article_multicolumn.css) for its columns to lay out side by side --
    // "flow-root" would silently replace that outright (same property,
    // same element) and collapse them into a single stacked column. Every
    // other box-capable element is a plain block box to begin with, where
    // flow-root is purely additive float containment, so only this one
    // type needs to skip it (see _block_box_style.html's keep_display,
    // same reasoning for the server-rendered version of this).
    if (targetTypeInput.value !== "multi_column") {
      currentBlockEl.style.display = "flow-root";
    }
    currentBlockEl.style.borderRadius = `${boxRadiusInput.value}rem`;
    if (boxShadowEnabledInput.checked) {
      // strength is a multiplier on the box's original fixed shadow shape
      // (offset 2px/blur 8px at strength=1), same recipe as
      // _effective_box_style()'s own shadow_offset/shadow_blur -- kept in
      // sync by hand since this is a live client-side preview, not a
      // render of that server-computed dict.
      const shadowStrength = parseFloat(boxShadowStrengthInput.value) || 0;
      const shadowColor = boxShadowColorGroup.dataset.value;
      const resolvedShadowColor = shadowColor
        ? shadowColor === "custom"
          ? boxShadowCustomColorInput.value || "var(--color-shadow)"
          : `var(--color-${shadowColor})`
        : "var(--color-shadow)";
      currentBlockEl.style.boxShadow = `0 ${shadowStrength * 2}px ${shadowStrength * 8}px ${resolvedShadowColor}`;
    } else {
      currentBlockEl.style.boxShadow = "none";
    }
    const bgColor = boxBgColorGroup.dataset.value;
    currentBlockEl.style.backgroundColor =
      bgColor === "custom"
        ? boxBgCustomColorInput.value || "var(--color-bg-light)"
        : `var(--color-${bgColor})`;
    if (boxBorderVisibleInput.checked) {
      const borderColor = boxBorderColorGroup.dataset.value;
      const resolvedBorderColor =
        borderColor === "custom"
          ? boxBorderCustomColorInput.value || "var(--color-black)"
          : `var(--color-${borderColor})`;
      currentBlockEl.style.border = `${boxBorderWidthInput.value}rem solid ${resolvedBorderColor}`;
    } else {
      currentBlockEl.style.border = "";
    }
  };

  // independent of applyBoxStyle above -- text color applies regardless of
  // whether that block's own box is on (see _effective_heading_style() in
  // article_models.py). Blank ("" -- no swatch selected) leaves the text
  // color alone, same as BLOCK_STYLE_DEFAULTS["heading"]["text_color"]'s
  // own meaning server-side.
  const applyTextColor = () => {
    if (!currentBlockEl) {
      return;
    }
    const target = targetTypeInput.value === "column" ? columnTitleEl() : currentBlockEl;
    if (!target) {
      return;
    }
    const textColor = textColorGroup.dataset.value;
    if (textColor) {
      target.style.color =
        textColor === "custom" ? textCustomColorInput.value || "inherit" : `var(--color-${textColor})`;
    } else {
      target.style.color = "";
    }
  };

  // independent of applyBoxStyle/applyTextColor above -- same "outside Box"
  // reasoning, own toggle. Unlike box's own shadow (which defaults on, to
  // preserve a prior fixed shadow -- see applyBoxStyle's own comment) this
  // one defaults off, so an unset target just gets no text-shadow at all
  // rather than an explicit "none" -- there's nothing here to override.
  // strength recipe (offset 1px/blur 2px at strength=1) matches
  // _effective_heading_style()'s own text_shadow_offset/text_shadow_blur.
  const applyTextShadow = () => {
    if (!currentBlockEl) {
      return;
    }
    const target = targetTypeInput.value === "column" ? columnTitleEl() : currentBlockEl;
    if (!target) {
      return;
    }
    if (textShadowEnabledInput.checked) {
      const shadowStrength = parseFloat(textShadowStrengthInput.value) || 0;
      const shadowColor = textShadowColorGroup.dataset.value;
      const resolvedShadowColor = shadowColor
        ? shadowColor === "custom"
          ? textShadowCustomColorInput.value || "var(--color-shadow)"
          : `var(--color-${shadowColor})`
        : "var(--color-shadow)";
      target.style.textShadow = `0 ${shadowStrength * 1}px ${shadowStrength * 2}px ${resolvedShadowColor}`;
    } else {
      target.style.textShadow = "";
    }
  };

  // hero_image only -- draws a border/box around the image, title and
  // caption. Mirrors article_page.html's own server-rendered version of
  // this exact logic (--box-bg custom property + border-radius, gated by
  // .image-figure--boxed -- see article_image.css); box-color--<color> is
  // separate from --box-bg itself, only used for text contrast when the
  // box is black (see .box-color--black .image-title in that same file),
  // so it needs stripping/re-adding as its own step, not just a plain
  // classList.toggle the way image-figure--boxed itself is.
  const applyHeroImageBox = () => {
    if (!currentBlockEl) {
      return;
    }
    Array.from(currentBlockEl.classList)
      .filter((cls) => cls.startsWith("box-color--"))
      .forEach((cls) => currentBlockEl.classList.remove(cls));
    const boxed = heroBoxedInput.checked;
    currentBlockEl.classList.toggle("image-figure--boxed", boxed);
    if (!boxed) {
      currentBlockEl.style.removeProperty("--box-bg");
      currentBlockEl.style.borderRadius = "";
      currentBlockEl.style.boxShadow = "";
      return;
    }
    const boxColor = heroBoxColorGroup.dataset.value;
    currentBlockEl.classList.add(`box-color--${boxColor}`);
    currentBlockEl.style.setProperty(
      "--box-bg",
      boxColor === "custom"
        ? heroBoxCustomColorInput.value || "var(--color-bg-light)"
        : `var(--color-${boxColor})`
    );
    currentBlockEl.style.borderRadius = `${heroBoxRadiusInput.value}rem`;
    // overrides .image-figure--boxed's own fixed box-shadow (article_image.
    // css) with the editable one, same recipe as applyBoxStyle's own
    // (offset/blur = strength * 2/8) -- blank shadow color falls back to
    // the same var(--color-shadow) token that fixed rule already used.
    if (heroBoxShadowEnabledInput.checked) {
      const shadowStrength = parseFloat(heroBoxShadowStrengthInput.value) || 0;
      const shadowColor = heroBoxShadowColorGroup.dataset.value;
      const resolvedShadowColor = shadowColor
        ? shadowColor === "custom"
          ? heroBoxShadowCustomColorInput.value || "var(--color-shadow)"
          : `var(--color-${shadowColor})`
        : "var(--color-shadow)";
      currentBlockEl.style.boxShadow = `0 ${shadowStrength * 2}px ${shadowStrength * 8}px ${resolvedShadowColor}`;
    } else {
      currentBlockEl.style.boxShadow = "none";
    }
  };

  // a collapsible section's own header (see the panel template's "block-
  // style-caption-header" divs -- Layout, Style, Column weights, Title/
  // Intro/Meta) only makes sense to show while at least one real field
  // inside its own fields wrapper (the very next sibling) is currently
  // visible -- computed by reading the DOM directly (not a static "which
  // fields does this type have" list) so it stays correct even when a
  // field's visibility changes *after* the panel opened for reasons
  // besides block type, like side_padding hiding once Box gets switched on
  // (see updateBoxFieldVisibility below) -- without this, a section whose
  // only field was side_padding would keep showing its own header with an
  // empty section underneath once Box is checked. Box's own header (data-
  // style-field="box_enabled") isn't a bare label like these, so it's
  // excluded by this selector and keeps its own boxCapable-driven
  // visibility untouched.
  const updateSectionHeaders = () => {
    panel.querySelectorAll('[data-style-field$="_label"]').forEach((header) => {
      const wrapper = header.nextElementSibling;
      if (!wrapper || !wrapper.classList.contains("block-style-box-fields")) {
        return;
      }
      const hasVisibleField = Array.from(wrapper.querySelectorAll("[data-style-field]")).some(
        (field) => !field.hidden
      );
      header.hidden = !hasVisibleField;
    });
  };

  // toggles which box-related fields are showing: everything but the
  // "Box" checkbox itself stays hidden until it's on, and the border
  // width/color only show while the border itself is visible. side_padding
  // stays visible regardless -- its own live effect is still superseded by
  // box_padding while the box is on (see applyBoxStyle/paddingInput's own
  // "input" listener), but the field itself stays put rather than
  // vanishing (and, with it, Layout as a whole for types where it's the
  // only field in that section -- see updateSectionHeaders below).
  const updateBoxFieldVisibility = () => {
    if (!BOX_CAPABLE_TYPES.has(targetTypeInput.value)) {
      return;
    }
    const enabled = boxEnabledInput.checked;
    BOX_ONLY_FIELDS.forEach((name) => {
      const field = panel.querySelector(`[data-style-field="${name}"]`);
      if (field) {
        field.hidden = !enabled;
      }
    });
    const borderWidthField = panel.querySelector('[data-style-field="box_border_width"]');
    if (borderWidthField) {
      borderWidthField.hidden = !enabled || !boxBorderVisibleInput.checked;
    }
    const borderColorField = panel.querySelector('[data-style-field="box_border_color"]');
    if (borderColorField) {
      borderColorField.hidden = !enabled || !boxBorderVisibleInput.checked;
    }
    const shadowStrengthField = panel.querySelector('[data-style-field="box_shadow_strength"]');
    if (shadowStrengthField) {
      shadowStrengthField.hidden = !enabled || !boxShadowEnabledInput.checked;
    }
    const shadowColorField = panel.querySelector('[data-style-field="box_shadow_color"]');
    if (shadowColorField) {
      shadowColorField.hidden = !enabled || !boxShadowEnabledInput.checked;
    }
    updateSectionHeaders();
    // checking "Box" (or "Show border") reveals a run of fields the same
    // way expanding a [data-controls] section does -- same reposition-on-
    // height-change reasoning as that click handler's own comment. Also
    // fires once during openPanelFor() itself (harmless -- positionPanel()
    // is cheap and idempotent, and openPanelFor calls it again anyway once
    // the panel's fully populated).
    if (currentTrigger) {
      positionPanel(currentTrigger);
    }
  };

  // #rgb -> #rrggbb, lowercased; null if `value` isn't valid hex at all.
  const normalizeHex = (value) => {
    const match = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.exec((value || "").trim());
    if (!match) {
      return null;
    }
    let hex = match[1];
    if (hex.length === 3) {
      hex = hex
        .split("")
        .map((c) => c + c)
        .join("");
    }
    return `#${hex.toLowerCase()}`;
  };

  // black or white, whichever reads better on top of `hex` -- so the hex
  // text inside the custom swatch itself (see article_block_style.css)
  // stays legible regardless of how light or dark the picked color is.
  // Standard relative-luminance threshold, not exact WCAG contrast math --
  // good enough for picking between exactly two options.
  const contrastTextColor = (hex) => {
    const int = parseInt(hex.slice(1), 16);
    const r = (int >> 16) & 255;
    const g = (int >> 8) & 255;
    const b = int & 255;
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.6 ? "#000000" : "#ffffff";
  };

  // sets the custom hex swatch's own value + live color preview together
  // (and its paired color-wheel picker button's own value, so opening it
  // starts from whatever's currently picked rather than always white) --
  // shared by openPanelFor (restoring a saved value), the reset button, and
  // the input's own live-typing handler below.
  const setCustomSwatch = (input, hex, pickerInput) => {
    input.value = hex || "";
    if (hex) {
      input.style.backgroundColor = hex;
      input.style.color = contrastTextColor(hex);
    } else {
      input.style.backgroundColor = "";
      input.style.color = "";
    }
    if (pickerInput) {
      pickerInput.value = hex || "#ffffff";
    }
  };

  // every box control below writes back to currentBlockEl.dataset (not
  // just the panel's own controls + live CSS via applyBoxStyle) -- same
  // reasoning as every other field's own handler (e.g. wireButtonGroup's
  // currentBlockEl.dataset[field] = value): without it, the *element*
  // never actually remembers the edit, only its current on-screen look
  // does, so reopening this same block's panel later in the same page
  // load (openPanelFor reads blockEl.dataset.box*) would show it as
  // unchanged even though the live preview clearly isn't.
  // shared by both the five fixed-color buttons and the "Custom" hex
  // swatch -- whichever one just changed becomes the group's active
  // choice, every other swatch in the group loses its own active state.
  // applyFn defaults to applyBoxStyle (every other color group is box-
  // scoped) -- text color passes applyTextColor instead, and skips
  // updateBoxFieldVisibility entirely, since it isn't a box field.
  const selectSwatch = (group, swatch, datasetKey, applyFn = applyBoxStyle) => {
    if (!currentBlockEl) {
      return;
    }
    group.dataset.value = swatch.dataset.color;
    currentBlockEl.dataset[styleDatasetKey(datasetKey)] = swatch.dataset.color;
    group.querySelectorAll(".color-swatch").forEach((s) => {
      s.classList.toggle("active", s === swatch);
    });
    if (applyFn === applyBoxStyle) {
      updateBoxFieldVisibility();
    }
    applyFn();
    recordPendingEdit();
  };

  const wireColorGroup = (group, datasetKey, applyFn = applyBoxStyle) => {
    group.querySelectorAll("button.color-swatch").forEach((button) => {
      button.addEventListener("click", () => selectSwatch(group, button, datasetKey, applyFn));
    });
  };
  wireColorGroup(boxBgColorGroup, "boxBgColor");
  wireColorGroup(boxBorderColorGroup, "boxBorderColor");
  wireColorGroup(boxShadowColorGroup, "boxShadowColor");
  wireColorGroup(textColorGroup, "textColor", applyTextColor);
  wireColorGroup(textShadowColorGroup, "textShadowColor", applyTextShadow);
  wireColorGroup(heroBoxColorGroup, "boxColor", applyHeroImageBox);
  wireColorGroup(heroBoxShadowColorGroup, "shadowColor", applyHeroImageBox);

  // the "Custom" swatch is a plain hex text input (see the mini panel
  // template) -- typing a valid hex both selects "custom" for the group
  // (same as clicking any other swatch) and colors the input's own
  // background/text to preview it right there, recording the actual
  // picked hex (box_bg_custom_color/box_border_custom_color) alongside the
  // group's color *choice* ("custom"). The color-wheel picker button next
  // to it (a real, visually-hidden <input type="color">, see the mini
  // panel template) feeds the exact same hex swatch -- picking a color
  // there fires "input" just like typing does, just from a different
  // source.
  [
    [boxBgCustomColorInput, boxBgPickerInput, boxBgColorGroup, "boxBgColor", "boxBgCustomColor"],
    [boxBorderCustomColorInput, boxBorderPickerInput, boxBorderColorGroup, "boxBorderColor", "boxBorderCustomColor"],
    [boxShadowCustomColorInput, boxShadowPickerInput, boxShadowColorGroup, "boxShadowColor", "boxShadowCustomColor"],
    [textCustomColorInput, textPickerInput, textColorGroup, "textColor", "textCustomColor", applyTextColor],
    [
      textShadowCustomColorInput,
      textShadowPickerInput,
      textShadowColorGroup,
      "textShadowColor",
      "textShadowCustomColor",
      applyTextShadow,
    ],
    [heroBoxCustomColorInput, heroBoxPickerInput, heroBoxColorGroup, "boxColor", "boxCustomColor", applyHeroImageBox],
    [
      heroBoxShadowCustomColorInput,
      heroBoxShadowPickerInput,
      heroBoxShadowColorGroup,
      "shadowColor",
      "shadowCustomColor",
      applyHeroImageBox,
    ],
  ].forEach(([hexInput, pickerInput, group, groupDatasetKey, customDatasetKey, applyFn = applyBoxStyle]) => {
    // custom isn't active yet -- a plain click always immediately focuses a
    // text input (or, for the picker label, forwards straight into opening
    // the native color dialog), with no "just select it" step in between
    // the way clicking any of the five fixed swatches has. So: while custom
    // isn't the group's active choice, the whole outer box (the hex chip,
    // the picker button, and the gap/border between them -- see
    // .color-swatch-custom-group in article_block_style.css) acts as one
    // big "select custom" button on its *first* click, same as clicking a
    // fixed swatch reapplies its own color, and blocks whichever default
    // action that click would otherwise have triggered. Once custom *is*
    // active, clicks go back to behaving normally -- type in the hex field,
    // or open the picker. Two listeners, not one, because a text input
    // grabs focus on mousedown (before "click" even fires), while a
    // <label>'s default forwarding to its color input happens on "click" --
    // an input's focus can only be blocked by catching the earlier event.
    const customGroupEl = hexInput.closest(".color-swatch-custom-group");
    customGroupEl.addEventListener("mousedown", (event) => {
      if (!currentBlockEl || group.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
    });
    customGroupEl.addEventListener("click", (event) => {
      if (!currentBlockEl || group.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
      selectSwatch(group, hexInput, groupDatasetKey, applyFn);
    });

    hexInput.addEventListener("input", () => {
      const hex = normalizeHex(hexInput.value);
      if (!currentBlockEl || !hex) {
        // still typing a partial/invalid value -- wait for it to resolve
        // to something valid rather than fighting the user's cursor with a
        // premature style change.
        return;
      }
      setCustomSwatch(hexInput, hex, pickerInput);
      currentBlockEl.dataset[styleDatasetKey(customDatasetKey)] = hex;
      selectSwatch(group, hexInput, groupDatasetKey, applyFn);
    });

    pickerInput.addEventListener("input", () => {
      if (!currentBlockEl) {
        return;
      }
      setCustomSwatch(hexInput, pickerInput.value, pickerInput);
      currentBlockEl.dataset[styleDatasetKey(customDatasetKey)] = pickerInput.value;
      selectSwatch(group, hexInput, groupDatasetKey, applyFn);
    });
  });

  // the element a caption-text group's fields actually preview/apply to --
  // the title/caption span itself, inside the currently-open image_caption
  // block's figcaption (see CAPTION_TEXT_GROUPS above).
  const captionTextTargetEl = (group) =>
    currentBlockEl ? currentBlockEl.querySelector(group.spanSelector) : null;

  const wireCaptionTextGroup = (group) => {
    group.alignmentGroup.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        if (!currentBlockEl) {
          return;
        }
        const value = button.dataset.align;
        group.alignmentGroup.dataset.value = value;
        currentBlockEl.dataset[`${group.datasetPrefix}Alignment`] = value;
        const target = captionTextTargetEl(group);
        if (target) {
          target.style.textAlign = value;
        }
        group.alignmentGroup.querySelectorAll("button").forEach((b) => {
          b.classList.toggle("active", b === button);
        });
        recordPendingEdit();
      });
    });

    group.excludeInput.addEventListener("change", () => {
      if (!currentBlockEl) {
        return;
      }
      currentBlockEl.dataset[`${group.datasetPrefix}ExcludeFromGlobalAlignment`] = group.excludeInput.checked
        ? "true"
        : "false";
      recordPendingEdit();
    });

    group.fontSizeInput.addEventListener("input", () => {
      if (!currentBlockEl) {
        return;
      }
      const target = captionTextTargetEl(group);
      if (target) {
        target.style.fontSize = `${group.fontSizeInput.value * currentFontSizeMultiplier()}rem`;
      }
      currentBlockEl.dataset[`${group.datasetPrefix}FontSize`] = group.fontSizeInput.value;
      group.fontSizeValue.textContent = group.fontSizeInput.value;
      recordPendingEdit();
    });

    group.paddingInput.addEventListener("input", () => {
      if (!currentBlockEl) {
        return;
      }
      const target = captionTextTargetEl(group);
      if (target) {
        target.style.paddingLeft = `${group.paddingInput.value}rem`;
        target.style.paddingRight = `${group.paddingInput.value}rem`;
      }
      currentBlockEl.dataset[`${group.datasetPrefix}SidePadding`] = group.paddingInput.value;
      group.paddingValue.textContent = group.paddingInput.value;
      recordPendingEdit();
    });

    const applyColor = () => {
      const target = captionTextTargetEl(group);
      if (!target) {
        return;
      }
      const color = group.colorGroup.dataset.value;
      if (color) {
        target.style.color =
          color === "custom" ? group.customColorInput.value || "inherit" : `var(--color-${color})`;
      } else {
        target.style.color = "";
      }
    };
    group.applyColor = applyColor;

    const colorDatasetKey = `${group.datasetPrefix}TextColor`;
    const customDatasetKey = `${group.datasetPrefix}TextCustomColor`;
    wireColorGroup(group.colorGroup, colorDatasetKey, applyColor);

    // same "click anywhere in the custom swatch's shared outer box selects
    // it" handling as the generic box/text custom swatches above, just
    // scoped to this one group's own hex input/picker.
    const customGroupEl = group.customColorInput.closest(".color-swatch-custom-group");
    customGroupEl.addEventListener("mousedown", (event) => {
      if (!currentBlockEl || group.colorGroup.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
    });
    customGroupEl.addEventListener("click", (event) => {
      if (!currentBlockEl || group.colorGroup.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
      selectSwatch(group.colorGroup, group.customColorInput, colorDatasetKey, applyColor);
    });
    group.customColorInput.addEventListener("input", () => {
      const hex = normalizeHex(group.customColorInput.value);
      if (!currentBlockEl || !hex) {
        return;
      }
      setCustomSwatch(group.customColorInput, hex, group.pickerInput);
      currentBlockEl.dataset[customDatasetKey] = hex;
      selectSwatch(group.colorGroup, group.customColorInput, colorDatasetKey, applyColor);
    });
    group.pickerInput.addEventListener("input", () => {
      if (!currentBlockEl) {
        return;
      }
      setCustomSwatch(group.customColorInput, group.pickerInput.value, group.pickerInput);
      currentBlockEl.dataset[customDatasetKey] = group.pickerInput.value;
      selectSwatch(group.colorGroup, group.customColorInput, colorDatasetKey, applyColor);
    });

    // an image title/caption's own text shadow -- currentBlockEl-based
    // throughout, same as everything else in this group (unlike
    // HEADER_TEXT_COLOR_GROUPS's own wrapper indirection), so this reuses
    // the generic wireColorGroup/selectSwatch helpers directly rather than
    // hand-rolling swatch clicks the way that one has to.
    const applyShadow = () => {
      const target = captionTextTargetEl(group);
      if (!target) {
        return;
      }
      if (group.shadowEnabledInput.checked) {
        const shadowStrength = parseFloat(group.shadowStrengthInput.value) || 0;
        const shadowColor = group.shadowColorGroup.dataset.value;
        const resolvedShadowColor = shadowColor
          ? shadowColor === "custom"
            ? group.shadowCustomColorInput.value || "var(--color-shadow)"
            : `var(--color-${shadowColor})`
          : "var(--color-shadow)";
        target.style.textShadow = `0 ${shadowStrength * 1}px ${shadowStrength * 2}px ${resolvedShadowColor}`;
      } else {
        target.style.textShadow = "";
      }
    };
    group.applyShadow = applyShadow;

    group.shadowEnabledInput.addEventListener("change", () => {
      if (!currentBlockEl) {
        return;
      }
      currentBlockEl.dataset[`${group.datasetPrefix}TextShadowEnabled`] = group.shadowEnabledInput.checked
        ? "true"
        : "false";
      applyShadow();
      recordPendingEdit();
    });
    group.shadowStrengthInput.addEventListener("input", () => {
      if (!currentBlockEl) {
        return;
      }
      currentBlockEl.dataset[`${group.datasetPrefix}TextShadowStrength`] = group.shadowStrengthInput.value;
      group.shadowStrengthValue.textContent = group.shadowStrengthInput.value;
      applyShadow();
      recordPendingEdit();
    });

    const shadowColorDatasetKey = `${group.datasetPrefix}TextShadowColor`;
    const shadowCustomDatasetKey = `${group.datasetPrefix}TextShadowCustomColor`;
    wireColorGroup(group.shadowColorGroup, shadowColorDatasetKey, applyShadow);

    const shadowCustomGroupEl = group.shadowCustomColorInput.closest(".color-swatch-custom-group");
    shadowCustomGroupEl.addEventListener("mousedown", (event) => {
      if (!currentBlockEl || group.shadowColorGroup.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
    });
    shadowCustomGroupEl.addEventListener("click", (event) => {
      if (!currentBlockEl || group.shadowColorGroup.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
      selectSwatch(group.shadowColorGroup, group.shadowCustomColorInput, shadowColorDatasetKey, applyShadow);
    });
    group.shadowCustomColorInput.addEventListener("input", () => {
      const hex = normalizeHex(group.shadowCustomColorInput.value);
      if (!currentBlockEl || !hex) {
        return;
      }
      setCustomSwatch(group.shadowCustomColorInput, hex, group.shadowPickerInput);
      currentBlockEl.dataset[shadowCustomDatasetKey] = hex;
      selectSwatch(group.shadowColorGroup, group.shadowCustomColorInput, shadowColorDatasetKey, applyShadow);
    });
    group.shadowPickerInput.addEventListener("input", () => {
      if (!currentBlockEl) {
        return;
      }
      setCustomSwatch(group.shadowCustomColorInput, group.shadowPickerInput.value, group.shadowPickerInput);
      currentBlockEl.dataset[shadowCustomDatasetKey] = group.shadowPickerInput.value;
      selectSwatch(group.shadowColorGroup, group.shadowCustomColorInput, shadowColorDatasetKey, applyShadow);
    });
  };
  CAPTION_TEXT_GROUPS.forEach(wireCaptionTextGroup);

  // title/meta/intro's own text color, edited from each one's own trigger
  // now -- color-only, so a lighter version of wireCaptionTextGroup above
  // (no alignment/font-size/padding, those still live on their own
  // dedicated title_alignment/title_font_size/etc fields elsewhere in this
  // panel). Reads/writes the shared .article-header wrapper via
  // headerWrapperEl() throughout, not currentBlockEl directly (see that
  // function's own comment) -- targetSelector (":scope > h1" etc) only
  // resolves correctly from the wrapper, and the generic wireColorGroup/
  // selectSwatch helpers used everywhere else in this file hardcode
  // currentBlockEl for their own dataset write, so the fixed-swatch clicks
  // below are hand-rolled here instead of reusing them.
  const wireHeaderTextColorGroup = (group) => {
    const applyColor = () => {
      const wrapperEl = headerWrapperEl();
      const target = wrapperEl ? wrapperEl.querySelector(group.targetSelector) : null;
      if (!target) {
        return;
      }
      const color = group.colorGroup.dataset.value;
      if (color) {
        target.style.color =
          color === "custom" ? group.customColorInput.value || "inherit" : `var(--color-${color})`;
      } else {
        target.style.color = "";
      }
    };
    group.applyColor = applyColor;

    const colorDatasetKey = `${group.datasetPrefix}TextColor`;
    const customDatasetKey = `${group.datasetPrefix}TextCustomColor`;

    const selectHeaderSwatch = (swatch) => {
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl) {
        return;
      }
      group.colorGroup.dataset.value = swatch.dataset.color;
      wrapperEl.dataset[colorDatasetKey] = swatch.dataset.color;
      group.colorGroup.querySelectorAll(".color-swatch").forEach((s) => {
        s.classList.toggle("active", s === swatch);
      });
      applyColor();
      recordPendingEdit();
    };
    group.colorGroup.querySelectorAll("button.color-swatch").forEach((button) => {
      button.addEventListener("click", () => selectHeaderSwatch(button));
    });

    const customGroupEl = group.customColorInput.closest(".color-swatch-custom-group");
    customGroupEl.addEventListener("mousedown", (event) => {
      if (!headerWrapperEl() || group.colorGroup.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
    });
    customGroupEl.addEventListener("click", (event) => {
      if (!headerWrapperEl() || group.colorGroup.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
      selectHeaderSwatch(group.customColorInput);
    });
    group.customColorInput.addEventListener("input", () => {
      const hex = normalizeHex(group.customColorInput.value);
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl || !hex) {
        return;
      }
      setCustomSwatch(group.customColorInput, hex, group.pickerInput);
      wrapperEl.dataset[customDatasetKey] = hex;
      selectHeaderSwatch(group.customColorInput);
    });
    group.pickerInput.addEventListener("input", () => {
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl) {
        return;
      }
      setCustomSwatch(group.customColorInput, group.pickerInput.value, group.pickerInput);
      wrapperEl.dataset[customDatasetKey] = group.pickerInput.value;
      selectHeaderSwatch(group.customColorInput);
    });

    // title/meta/intro's own text shadow -- same wrapper-not-currentBlockEl
    // reasoning throughout as the color wiring just above.
    const applyShadow = () => {
      const wrapperEl = headerWrapperEl();
      const target = wrapperEl ? wrapperEl.querySelector(group.targetSelector) : null;
      if (!target) {
        return;
      }
      if (group.shadowEnabledInput.checked) {
        const shadowStrength = parseFloat(group.shadowStrengthInput.value) || 0;
        const shadowColor = group.shadowColorGroup.dataset.value;
        const resolvedShadowColor = shadowColor
          ? shadowColor === "custom"
            ? group.shadowCustomColorInput.value || "var(--color-shadow)"
            : `var(--color-${shadowColor})`
          : "var(--color-shadow)";
        target.style.textShadow = `0 ${shadowStrength * 1}px ${shadowStrength * 2}px ${resolvedShadowColor}`;
      } else {
        target.style.textShadow = "";
      }
    };
    group.applyShadow = applyShadow;

    const shadowEnabledDatasetKey = `${group.datasetPrefix}TextShadowEnabled`;
    const shadowStrengthDatasetKey = `${group.datasetPrefix}TextShadowStrength`;
    const shadowColorDatasetKey = `${group.datasetPrefix}TextShadowColor`;
    const shadowCustomColorDatasetKey = `${group.datasetPrefix}TextShadowCustomColor`;

    group.shadowEnabledInput.addEventListener("change", () => {
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl) {
        return;
      }
      wrapperEl.dataset[shadowEnabledDatasetKey] = group.shadowEnabledInput.checked ? "true" : "false";
      applyShadow();
      recordPendingEdit();
    });
    group.shadowStrengthInput.addEventListener("input", () => {
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl) {
        return;
      }
      wrapperEl.dataset[shadowStrengthDatasetKey] = group.shadowStrengthInput.value;
      group.shadowStrengthValue.textContent = group.shadowStrengthInput.value;
      applyShadow();
      recordPendingEdit();
    });

    const selectHeaderShadowSwatch = (swatch) => {
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl) {
        return;
      }
      group.shadowColorGroup.dataset.value = swatch.dataset.color;
      wrapperEl.dataset[shadowColorDatasetKey] = swatch.dataset.color;
      group.shadowColorGroup.querySelectorAll(".color-swatch").forEach((s) => {
        s.classList.toggle("active", s === swatch);
      });
      applyShadow();
      recordPendingEdit();
    };
    group.shadowColorGroup.querySelectorAll("button.color-swatch").forEach((button) => {
      button.addEventListener("click", () => selectHeaderShadowSwatch(button));
    });

    const shadowCustomGroupEl = group.shadowCustomColorInput.closest(".color-swatch-custom-group");
    shadowCustomGroupEl.addEventListener("mousedown", (event) => {
      if (!headerWrapperEl() || group.shadowColorGroup.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
    });
    shadowCustomGroupEl.addEventListener("click", (event) => {
      if (!headerWrapperEl() || group.shadowColorGroup.dataset.value === "custom") {
        return;
      }
      event.preventDefault();
      selectHeaderShadowSwatch(group.shadowCustomColorInput);
    });
    group.shadowCustomColorInput.addEventListener("input", () => {
      const hex = normalizeHex(group.shadowCustomColorInput.value);
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl || !hex) {
        return;
      }
      setCustomSwatch(group.shadowCustomColorInput, hex, group.shadowPickerInput);
      wrapperEl.dataset[shadowCustomColorDatasetKey] = hex;
      selectHeaderShadowSwatch(group.shadowCustomColorInput);
    });
    group.shadowPickerInput.addEventListener("input", () => {
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl) {
        return;
      }
      setCustomSwatch(group.shadowCustomColorInput, group.shadowPickerInput.value, group.shadowPickerInput);
      wrapperEl.dataset[shadowCustomColorDatasetKey] = group.shadowPickerInput.value;
      selectHeaderShadowSwatch(group.shadowCustomColorInput);
    });
  };
  HEADER_TEXT_COLOR_GROUPS.forEach(wireHeaderTextColorGroup);

  boxEnabledInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset.boxEnabled = boxEnabledInput.checked ? "true" : "false";
    updateBoxFieldVisibility();
    applyBoxStyle();
    positionTextTriggers();
    recordPendingEdit();
  });

  // every collapsible section header in the panel (Layout, Style, Column
  // weights, Title/Intro/Meta, Image title/Image caption, Box) is wired the
  // same generic way -- purely whether that section's own fields are
  // showing right now, not (for Box) whether it's enabled. Not reset when
  // switching to a different block's panel, so collapsing one once keeps
  // it collapsed for whatever you open next too. data-controls points each
  // toggle at its own fields wrapper's id (see the panel template) --
  // there's no per-section JS beyond this one loop, so adding another
  // section there needs no matching code here.
  panel.querySelectorAll("[data-controls]").forEach((toggle) => {
    const wrapper = document.getElementById(toggle.dataset.controls);
    if (!wrapper) {
      return;
    }
    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
      wrapper.hidden = expanded;
      // expanding a section can make the panel taller than the space
      // positionPanel() originally found for it when the panel first
      // opened (that calculation only ever ran once, against whatever
      // height the panel happened to have at that moment) -- re-run it
      // now that the panel's actual height has changed, so it re-clamps
      // to the viewport (flip above the trigger, or pin to the bottom
      // edge with .block-style-mini-panel's own overflow-y:auto taking
      // over from there) instead of just growing past the bottom of the
      // screen with no way to reach Save/Reset below the fold.
      if (currentTrigger) {
        positionPanel(currentTrigger);
      }
    });
  });

  boxBorderVisibleInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset.boxBorderVisible = boxBorderVisibleInput.checked ? "true" : "false";
    updateBoxFieldVisibility();
    applyBoxStyle();
    recordPendingEdit();
  });

  boxShadowEnabledInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset.boxShadowEnabled = boxShadowEnabledInput.checked ? "true" : "false";
    updateBoxFieldVisibility();
    applyBoxStyle();
    recordPendingEdit();
  });

  [
    [boxBorderWidthInput, boxBorderWidthValue, "boxBorderWidth"],
    [boxRadiusInput, boxRadiusValue, "boxRadius"],
    [boxPaddingInput, boxPaddingValue, "boxPadding"],
    [boxMarginInput, boxMarginValue, "boxMargin"],
    [boxShadowStrengthInput, boxShadowStrengthValue, "boxShadowStrength"],
  ].forEach(([input, valueEl, datasetKey]) => {
    input.addEventListener("input", () => {
      if (!currentBlockEl) {
        return;
      }
      currentBlockEl.dataset[datasetKey] = input.value;
      valueEl.textContent = input.value;
      applyBoxStyle();
      recordPendingEdit();
    });
  });

  // article_header's three alignment groups aren't class-based (h1/.intro/
  // .article-meta each read their own CSS custom property, see
  // article_header.css) -- live preview writes straight to that property on
  // the wrapper instead of swapping a class.
  const wireHeaderAlignmentGroup = (group, cssVar, datasetKey) => {
    group.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        const wrapperEl = headerWrapperEl();
        if (!wrapperEl) {
          return;
        }
        const value = button.dataset.align;
        group.dataset.value = value;
        wrapperEl.dataset[datasetKey] = value;
        wrapperEl.style.setProperty(cssVar, value);
        group.querySelectorAll("button").forEach((b) => {
          b.classList.toggle("active", b === button);
        });
        recordPendingEdit();
      });
    });
  };

  // the panel is position:fixed, so top/left are plain viewport pixels --
  // re-run on every scroll/resize while it's open (see the listeners near
  // the bottom of this file) rather than computing them once and trusting
  // some containing-block/offsetParent math to carry the panel along on
  // its own.
  const positionPanel = (trigger) => {
    const rect = trigger.getBoundingClientRect();
    const panelWidth = panel.offsetWidth || 224;
    const panelHeight = panel.offsetHeight || 0;

    let left = rect.right - panelWidth;
    left = Math.max(8, Math.min(left, window.innerWidth - panelWidth - 8));

    // default: open below the trigger. If it wouldn't fit before hitting
    // the bottom of the viewport, flip to open above it instead -- same
    // idea as the horizontal clamp above, just on the other axis and with
    // a flip instead of a slide, since sliding vertically would put the
    // panel over the trigger itself.
    let top = rect.bottom + 8;
    if (top + panelHeight > window.innerHeight - 8) {
      const above = rect.top - 8 - panelHeight;
      top = above >= 8 ? above : Math.max(8, window.innerHeight - panelHeight - 8);
    }

    panel.style.top = `${top}px`;
    panel.style.left = `${left}px`;
  };

  const closePanel = () => {
    panel.hidden = true;
    if (currentTrigger) {
      currentTrigger.classList.remove("is-open");
    }
    if (currentBlockEl) {
      currentBlockEl.classList.remove("is-editing");
    }
    currentBlockEl = null;
    currentTrigger = null;
  };

  const openPanelFor = (trigger) => {
    const blockEl = trigger.closest(".editable-block");
    if (!blockEl) {
      return;
    }
    currentBlockEl = blockEl;
    currentTrigger = trigger;
    currentBlockEl.classList.add("is-editing");

    const blockType = blockEl.dataset.blockType;
    let visibleFields = FIELDS_BY_TYPE[blockType] || [];
    if (blockType === "multi_column") {
      const columnCount = parseInt(blockEl.dataset.columnCount, 10) || 0;
      visibleFields = visibleFields.concat(
        Array.from({ length: columnCount }, (_, i) => `column_weight_${i}`)
      );
    }
    if (blockType === "column" && blockEl.dataset.titleBlockId) {
      visibleFields = visibleFields.concat([
        "alignment",
        "exclude_from_global_alignment",
        "font_size",
        "text_color",
        "text_shadow_enabled",
        "text_shadow_strength",
        "text_shadow_color",
      ]);
    }
    if (blockType === "image_caption") {
      CAPTION_TEXT_GROUPS.forEach((group) => {
        if (blockEl.dataset[`${group.datasetPrefix}TextId`]) {
          visibleFields = visibleFields.concat([
            `${group.styleFieldPrefix}_label`,
            `${group.styleFieldPrefix}_alignment`,
            `${group.styleFieldPrefix}_exclude_from_global_alignment`,
            `${group.styleFieldPrefix}_font_size`,
            `${group.styleFieldPrefix}_side_padding`,
            `${group.styleFieldPrefix}_text_color`,
            `${group.styleFieldPrefix}_text_shadow_enabled`,
            `${group.styleFieldPrefix}_text_shadow_strength`,
            `${group.styleFieldPrefix}_text_shadow_color`,
          ]);
        }
      });
    }
    const boxCapable = BOX_CAPABLE_TYPES.has(blockType);
    if (boxCapable) {
      visibleFields = visibleFields.concat(BOX_FIELD_NAMES);
    }

    panel.querySelectorAll("[data-style-field]").forEach((field) => {
      field.hidden = !visibleFields.includes(field.dataset.styleField);
    });
    updateSectionHeaders();

    targetIdInput.value = blockEl.dataset.blockId;
    targetTypeInput.value = blockType;
    statusEl.textContent = "";
    statusEl.classList.remove("is-error");
    styleLabel.textContent =
      blockType === "column" ? styleLabel.dataset.labelTitle : styleLabel.dataset.labelDefault;
    panelTitle.textContent = BLOCK_TYPE_LABELS[blockType] || panelTitle.dataset.labelDefault;

    if (visibleFields.includes("side_padding")) {
      paddingInput.value = blockEl.dataset.sidePadding;
      paddingValue.textContent = blockEl.dataset.sidePadding;
    }
    if (boxCapable) {
      boxEnabledInput.checked = blockEl.dataset.boxEnabled === "true";
      boxBgColorGroup.dataset.value = blockEl.dataset.boxBgColor;
      boxBgColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
        b.classList.toggle("active", b.dataset.color === blockEl.dataset.boxBgColor);
      });
      setCustomSwatch(boxBgCustomColorInput, blockEl.dataset.boxBgCustomColor, boxBgPickerInput);
      boxBorderVisibleInput.checked = blockEl.dataset.boxBorderVisible === "true";
      boxBorderWidthInput.value = blockEl.dataset.boxBorderWidth;
      boxBorderWidthValue.textContent = blockEl.dataset.boxBorderWidth;
      boxBorderColorGroup.dataset.value = blockEl.dataset.boxBorderColor;
      boxBorderColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
        b.classList.toggle("active", b.dataset.color === blockEl.dataset.boxBorderColor);
      });
      setCustomSwatch(boxBorderCustomColorInput, blockEl.dataset.boxBorderCustomColor, boxBorderPickerInput);
      boxRadiusInput.value = blockEl.dataset.boxRadius;
      boxRadiusValue.textContent = blockEl.dataset.boxRadius;
      boxPaddingInput.value = blockEl.dataset.boxPadding;
      boxPaddingValue.textContent = blockEl.dataset.boxPadding;
      boxMarginInput.value = blockEl.dataset.boxMargin;
      boxMarginValue.textContent = blockEl.dataset.boxMargin;
      boxShadowEnabledInput.checked = blockEl.dataset.boxShadowEnabled === "true";
      boxShadowStrengthInput.value = blockEl.dataset.boxShadowStrength;
      boxShadowStrengthValue.textContent = blockEl.dataset.boxShadowStrength;
      boxShadowColorGroup.dataset.value = blockEl.dataset.boxShadowColor;
      boxShadowColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
        b.classList.toggle("active", b.dataset.color === blockEl.dataset.boxShadowColor);
      });
      setCustomSwatch(boxShadowCustomColorInput, blockEl.dataset.boxShadowCustomColor, boxShadowPickerInput);
      updateBoxFieldVisibility();
    }
    if (visibleFields.includes("exclude_from_global_alignment")) {
      excludeGlobalAlignmentInput.checked =
        blockEl.dataset[styleDatasetKey("excludeFromGlobalAlignment")] === "true";
    }
    // title/meta/intro's own opt-out -- unprefixed data-exclude-from-
    // global-alignment lives directly on blockEl itself (the h1/.article-
    // meta/.intro element), not the shared header wrapper -- see this
    // field's own FIELDS_BY_TYPE comment.
    [
      [titleExcludeGlobalAlignmentInput, "title_exclude_from_global_alignment"],
      [metaExcludeGlobalAlignmentInput, "meta_exclude_from_global_alignment"],
      [introExcludeGlobalAlignmentInput, "intro_exclude_from_global_alignment"],
    ].forEach(([input, field]) => {
      if (visibleFields.includes(field)) {
        input.checked = blockEl.dataset.excludeFromGlobalAlignment === "true";
      }
    });
    if (visibleFields.includes("font_size")) {
      const fontVal = blockEl.dataset[styleDatasetKey("fontSize")];
      fontSizeInput.value = fontVal;
      fontSizeValue.textContent = fontVal;
      fontSizeLabel.textContent =
        blockType === "column" ? fontSizeLabel.dataset.labelTitle : fontSizeLabel.dataset.labelDefault;
    }
    if (visibleFields.includes("text_color")) {
      const colorVal = blockEl.dataset[styleDatasetKey("textColor")] || "";
      textColorGroup.dataset.value = colorVal;
      textColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
        b.classList.toggle("active", b.dataset.color === colorVal);
      });
      setCustomSwatch(textCustomColorInput, blockEl.dataset[styleDatasetKey("textCustomColor")], textPickerInput);
      textColorLabel.textContent =
        blockType === "column" ? textColorLabel.dataset.labelTitle : textColorLabel.dataset.labelDefault;
    }
    if (visibleFields.includes("text_shadow_enabled")) {
      textShadowEnabledInput.checked = blockEl.dataset[styleDatasetKey("textShadowEnabled")] === "true";
      const shadowStrengthVal = blockEl.dataset[styleDatasetKey("textShadowStrength")];
      textShadowStrengthInput.value = shadowStrengthVal;
      textShadowStrengthValue.textContent = shadowStrengthVal;
      const shadowColorVal = blockEl.dataset[styleDatasetKey("textShadowColor")] || "";
      textShadowColorGroup.dataset.value = shadowColorVal;
      textShadowColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
        b.classList.toggle("active", b.dataset.color === shadowColorVal);
      });
      setCustomSwatch(
        textShadowCustomColorInput,
        blockEl.dataset[styleDatasetKey("textShadowCustomColor")],
        textShadowPickerInput
      );
    }
    if (blockType === "image_caption") {
      CAPTION_TEXT_GROUPS.forEach((group) => {
        if (!blockEl.dataset[`${group.datasetPrefix}TextId`]) {
          return;
        }
        const alignVal = blockEl.dataset[`${group.datasetPrefix}Alignment`];
        group.alignmentGroup.dataset.value = alignVal;
        group.alignmentGroup.querySelectorAll("button").forEach((b) => {
          b.classList.toggle("active", b.dataset.align === alignVal);
        });
        group.excludeInput.checked = blockEl.dataset[`${group.datasetPrefix}ExcludeFromGlobalAlignment`] === "true";
        const fontVal = blockEl.dataset[`${group.datasetPrefix}FontSize`];
        group.fontSizeInput.value = fontVal;
        group.fontSizeValue.textContent = fontVal;
        const paddingVal = blockEl.dataset[`${group.datasetPrefix}SidePadding`];
        group.paddingInput.value = paddingVal;
        group.paddingValue.textContent = paddingVal;
        const colorVal = blockEl.dataset[`${group.datasetPrefix}TextColor`] || "";
        group.colorGroup.dataset.value = colorVal;
        group.colorGroup.querySelectorAll(".color-swatch").forEach((b) => {
          b.classList.toggle("active", b.dataset.color === colorVal);
        });
        setCustomSwatch(
          group.customColorInput,
          blockEl.dataset[`${group.datasetPrefix}TextCustomColor`],
          group.pickerInput
        );
        group.shadowEnabledInput.checked =
          blockEl.dataset[`${group.datasetPrefix}TextShadowEnabled`] === "true";
        const shadowStrengthVal = blockEl.dataset[`${group.datasetPrefix}TextShadowStrength`];
        group.shadowStrengthInput.value = shadowStrengthVal;
        group.shadowStrengthValue.textContent = shadowStrengthVal;
        const shadowColorVal = blockEl.dataset[`${group.datasetPrefix}TextShadowColor`] || "";
        group.shadowColorGroup.dataset.value = shadowColorVal;
        group.shadowColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
          b.classList.toggle("active", b.dataset.color === shadowColorVal);
        });
        setCustomSwatch(
          group.shadowCustomColorInput,
          blockEl.dataset[`${group.datasetPrefix}TextShadowCustomColor`],
          group.shadowPickerInput
        );
      });
    }
    if (visibleFields.includes("width_rem")) {
      widthInput.value = blockEl.dataset.widthRem;
      widthValue.textContent = blockEl.dataset.widthRem;
    }
    if (visibleFields.includes("height_rem")) {
      heightInput.value = blockEl.dataset.heightRem;
      heightValue.textContent = blockEl.dataset.heightRem;
    }
    if (visibleFields.includes("list_style")) {
      listStyleInput.checked = blockEl.dataset.listStyle === "true";
    }
    if (visibleFields.includes("fixed_ratio")) {
      fixedRatioInput.checked = blockEl.dataset.fixedRatio === "true";
    }
    if (visibleFields.includes("boxed")) {
      heroBoxedInput.checked = blockEl.dataset.boxed === "true";
    }
    if (visibleFields.includes("box_color")) {
      heroBoxColorGroup.dataset.value = blockEl.dataset.boxColor;
      heroBoxColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
        b.classList.toggle("active", b.dataset.color === blockEl.dataset.boxColor);
      });
      setCustomSwatch(heroBoxCustomColorInput, blockEl.dataset.boxCustomColor, heroBoxPickerInput);
    }
    if (visibleFields.includes("box_border_radius")) {
      heroBoxRadiusInput.value = blockEl.dataset.boxBorderRadius;
      heroBoxRadiusValue.textContent = blockEl.dataset.boxBorderRadius;
    }
    if (visibleFields.includes("shadow_enabled")) {
      heroBoxShadowEnabledInput.checked = blockEl.dataset.shadowEnabled === "true";
    }
    if (visibleFields.includes("shadow_strength")) {
      heroBoxShadowStrengthInput.value = blockEl.dataset.shadowStrength;
      heroBoxShadowStrengthValue.textContent = blockEl.dataset.shadowStrength;
    }
    if (visibleFields.includes("shadow_color")) {
      heroBoxShadowColorGroup.dataset.value = blockEl.dataset.shadowColor;
      heroBoxShadowColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
        b.classList.toggle("active", b.dataset.color === blockEl.dataset.shadowColor);
      });
      setCustomSwatch(heroBoxShadowCustomColorInput, blockEl.dataset.shadowCustomColor, heroBoxShadowPickerInput);
    }
    if (visibleFields.includes("gap")) {
      gapInput.value = blockEl.dataset.gap;
      gapValue.textContent = blockEl.dataset.gap;
    }
    if (visibleFields.includes("toc_icon_size")) {
      tocIconSizeInput.value = blockEl.dataset.tocIconSize;
      tocIconSizeValue.textContent = blockEl.dataset.tocIconSize;
    }
    if (blockType === "multi_column") {
      const weights = (blockEl.dataset.columnWeights || "")
        .split(",")
        .filter((w) => w !== "")
        .map(Number);
      weights.forEach((w, i) => {
        if (!columnWeightInputs[i]) {
          return;
        }
        columnWeightInputs[i].value = w;
        columnWeightValues[i].textContent = w;
      });
    }
    if (visibleFields.includes("alignment")) {
      const alignVal = blockEl.dataset[styleDatasetKey("alignment")];
      alignmentGroup.dataset.value = alignVal;
      alignmentGroup.querySelectorAll("button").forEach((b) => {
        b.classList.toggle("active", b.dataset.align === alignVal);
      });
    }
    // title/meta/intro/article_header's own alignment/font-size/text-color
    // -- read off the shared .article-header wrapper via headerWrapperEl()
    // rather than blockEl directly (see that function's own comment), and
    // NOT gated by visibleFields.includes(...) the way every other field on
    // this panel is: these seven values all travel together in one combined
    // save_header_style request regardless of which of the four triggers
    // fires it (see recordPendingEdit), so they need to stay loaded into
    // their inputs even while only one of the three's own section is
    // actually visible, or a save from e.g. Title's own trigger would wipe
    // out Meta/Intro's current alignment/font-size with blank values.
    const headerWrapper = headerWrapperEl();
    if (headerWrapper) {
      [
        [titleAlignmentGroup, "titleAlignment"],
        [introAlignmentGroup, "introAlignment"],
        [metaAlignmentGroup, "metaAlignment"],
      ].forEach(([group, datasetKey]) => {
        group.dataset.value = headerWrapper.dataset[datasetKey];
        group.querySelectorAll("button").forEach((b) => {
          b.classList.toggle("active", b.dataset.align === headerWrapper.dataset[datasetKey]);
        });
      });
      [
        [titleFontSizeInput, titleFontSizeValue, "titleFontSize"],
        [introFontSizeInput, introFontSizeValue, "introFontSize"],
        [metaFontSizeInput, metaFontSizeValue, "metaFontSize"],
      ].forEach(([input, valueEl, datasetKey]) => {
        input.value = headerWrapper.dataset[datasetKey];
        valueEl.textContent = headerWrapper.dataset[datasetKey];
      });
      HEADER_TEXT_COLOR_GROUPS.forEach((group) => {
        const colorVal = headerWrapper.dataset[`${group.datasetPrefix}TextColor`] || "";
        group.colorGroup.dataset.value = colorVal;
        group.colorGroup.querySelectorAll(".color-swatch").forEach((b) => {
          b.classList.toggle("active", b.dataset.color === colorVal);
        });
        setCustomSwatch(
          group.customColorInput,
          headerWrapper.dataset[`${group.datasetPrefix}TextCustomColor`],
          group.pickerInput
        );
        group.shadowEnabledInput.checked =
          headerWrapper.dataset[`${group.datasetPrefix}TextShadowEnabled`] === "true";
        const shadowStrengthVal = headerWrapper.dataset[`${group.datasetPrefix}TextShadowStrength`];
        group.shadowStrengthInput.value = shadowStrengthVal;
        group.shadowStrengthValue.textContent = shadowStrengthVal;
        const shadowColorVal = headerWrapper.dataset[`${group.datasetPrefix}TextShadowColor`] || "";
        group.shadowColorGroup.dataset.value = shadowColorVal;
        group.shadowColorGroup.querySelectorAll(".color-swatch").forEach((b) => {
          b.classList.toggle("active", b.dataset.color === shadowColorVal);
        });
        setCustomSwatch(
          group.shadowCustomColorInput,
          headerWrapper.dataset[`${group.datasetPrefix}TextShadowCustomColor`],
          group.shadowPickerInput
        );
      });
    }

    panel.hidden = false;
    trigger.classList.add("is-open");
    positionPanel(trigger);
  };

  // keep the panel anchored to its trigger while open, on both scroll
  // (capture: window scroll events don't bubble) and resize.
  const repositionIfOpen = () => {
    if (!panel.hidden && currentTrigger) {
      positionPanel(currentTrigger);
    }
  };
  window.addEventListener("scroll", repositionIfOpen, { capture: true, passive: true });
  window.addEventListener("resize", repositionIfOpen);

  document.querySelectorAll(".block-style-trigger").forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      if (currentTrigger === trigger) {
        closePanel();
      } else {
        openPanelFor(trigger);
      }
    });
  });

  const closeButton = document.getElementById("block-style-close");
  closeButton.addEventListener("click", (event) => {
    event.stopPropagation();
    closePanel();
  });

  document.addEventListener("click", (event) => {
    if (!panel.hidden && !panel.contains(event.target)) {
      closePanel();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) {
      closePanel();
    }
  });

  paddingInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    // article_header expresses its side padding as margin (via
    // --header-side-padding, see article_layout.css) rather than padding --
    // its border-bottom accent underline needs to move with the indent, and
    // margin does that while padding on a width:auto block wouldn't.
    if (targetTypeInput.value === "article_header") {
      currentBlockEl.style.setProperty("--header-side-padding", `${paddingInput.value}rem`);
    } else if (BOX_CAPABLE_TYPES.has(targetTypeInput.value) && boxEnabledInput.checked) {
      // while the box is on, side_padding indents the box itself (margin)
      // instead of the space inside it (padding, which box.padding governs
      // instead) -- see applyBoxStyle/_block_box_style.html.
      currentBlockEl.style.marginLeft = `${paddingInput.value}rem`;
      currentBlockEl.style.marginRight = `${paddingInput.value}rem`;
    } else {
      currentBlockEl.style.paddingLeft = `${paddingInput.value}rem`;
      currentBlockEl.style.paddingRight = `${paddingInput.value}rem`;
    }
    currentBlockEl.dataset.sidePadding = paddingInput.value;
    paddingValue.textContent = paddingInput.value;
    positionTextTriggers();
    recordPendingEdit();
  });

  fontSizeInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    const target = targetTypeInput.value === "column" ? columnTitleEl() : currentBlockEl;
    if (target) {
      target.style.fontSize = `${fontSizeInput.value * currentFontSizeMultiplier()}rem`;
    }
    currentBlockEl.dataset[styleDatasetKey("fontSize")] = fontSizeInput.value;
    fontSizeValue.textContent = fontSizeInput.value;
    positionTextTriggers();
    recordPendingEdit();
  });

  textShadowEnabledInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset[styleDatasetKey("textShadowEnabled")] = textShadowEnabledInput.checked
      ? "true"
      : "false";
    applyTextShadow();
    recordPendingEdit();
  });

  textShadowStrengthInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset[styleDatasetKey("textShadowStrength")] = textShadowStrengthInput.value;
    textShadowStrengthValue.textContent = textShadowStrengthInput.value;
    applyTextShadow();
    recordPendingEdit();
  });

  widthInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    // Card blocks (CARD_WRAPPER_CLASS above) drive their width from a
    // --card-width custom property instead of a literal inline width --
    // everything else (just "image" today) keeps the plain inline style.
    if (CARD_WRAPPER_CLASS[currentBlockEl.dataset.blockType]) {
      currentBlockEl.style.setProperty("--card-width", `${widthInput.value}rem`);
    } else {
      currentBlockEl.style.width = `${widthInput.value}rem`;
    }
    currentBlockEl.dataset.widthRem = widthInput.value;
    widthValue.textContent = widthInput.value;
    positionTextTriggers();
    recordPendingEdit();
  });

  // card blocks only -- 0 means auto (drop the fixed-height custom property
  // and its modifier class entirely, back to the card's own natural
  // content-driven height).
  heightInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    const height = parseFloat(heightInput.value);
    const wrapperClass = CARD_WRAPPER_CLASS[currentBlockEl.dataset.blockType];
    if (wrapperClass) {
      if (height > 0) {
        currentBlockEl.style.setProperty("--card-height", `${heightInput.value}rem`);
        currentBlockEl.classList.add(`${wrapperClass}--fixed-height`);
      } else {
        currentBlockEl.style.removeProperty("--card-height");
        currentBlockEl.classList.remove(`${wrapperClass}--fixed-height`);
      }
    } else if (height > 0) {
      currentBlockEl.style.height = `${heightInput.value}rem`;
      currentBlockEl.style.overflow = "hidden";
    } else {
      currentBlockEl.style.height = "";
      currentBlockEl.style.overflow = "";
    }
    currentBlockEl.dataset.heightRem = heightInput.value;
    heightValue.textContent = heightInput.value;
    positionTextTriggers();
    recordPendingEdit();
  });

  // article_card only -- toggles .articlecard--list on the <a> itself
  // (currentBlockEl is its wrapping div, see article_body_blocks.html).
  listStyleInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    const cardEl = currentBlockEl.querySelector(".articlecard");
    if (cardEl) {
      cardEl.classList.toggle("articlecard--list", listStyleInput.checked);
    }
    currentBlockEl.dataset.listStyle = listStyleInput.checked ? "true" : "false";
    recordPendingEdit();
  });

  // article_card only -- toggles .articlecard--unlocked-ratio (dropping
  // the image's fixed 8:5 ratio in favor of "Height" above) -- unchecked
  // means unlocked, since the checkbox itself reads "Lock image ratio".
  fixedRatioInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    const cardEl = currentBlockEl.querySelector(".articlecard");
    if (cardEl) {
      cardEl.classList.toggle("articlecard--unlocked-ratio", !fixedRatioInput.checked);
    }
    currentBlockEl.dataset.fixedRatio = fixedRatioInput.checked ? "true" : "false";
    recordPendingEdit();
  });

  // heading/paragraph/image, and (via styleDatasetKey) a column's own
  // title -- see ArticleBlockStyle.exclude_from_global_alignment. Purely a
  // meta-flag, no live-preview visual to update, just the dataset marker
  // openPanelFor reads back on reopen and recordPendingEdit sends on save.
  excludeGlobalAlignmentInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset[styleDatasetKey("excludeFromGlobalAlignment")] = excludeGlobalAlignmentInput.checked
      ? "true"
      : "false";
    recordPendingEdit();
  });

  // title/meta/intro's own "lock alignment" checkboxes -- same reasoning
  // as excludeGlobalAlignmentInput above (a meta-flag, no live-preview
  // visual), but plain currentBlockEl.dataset (not styleDatasetKey, that
  // helper only ever redirects for the merged column-title panel) since
  // each of these three always corresponds 1:1 with currentBlockEl being
  // that exact h1/.article-meta/.intro element.
  [titleExcludeGlobalAlignmentInput, metaExcludeGlobalAlignmentInput, introExcludeGlobalAlignmentInput].forEach(
    (input) => {
      input.addEventListener("change", () => {
        if (!currentBlockEl) {
          return;
        }
        currentBlockEl.dataset.excludeFromGlobalAlignment = input.checked ? "true" : "false";
        recordPendingEdit();
      });
    }
  );

  // hero_image only -- see applyHeroImageBox's own comment.
  heroBoxedInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset.boxed = heroBoxedInput.checked ? "true" : "false";
    applyHeroImageBox();
    recordPendingEdit();
  });

  heroBoxRadiusInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset.boxBorderRadius = heroBoxRadiusInput.value;
    heroBoxRadiusValue.textContent = heroBoxRadiusInput.value;
    applyHeroImageBox();
    recordPendingEdit();
  });

  heroBoxShadowEnabledInput.addEventListener("change", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset.shadowEnabled = heroBoxShadowEnabledInput.checked ? "true" : "false";
    applyHeroImageBox();
    recordPendingEdit();
  });

  heroBoxShadowStrengthInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.dataset.shadowStrength = heroBoxShadowStrengthInput.value;
    heroBoxShadowStrengthValue.textContent = heroBoxShadowStrengthInput.value;
    applyHeroImageBox();
    recordPendingEdit();
  });

  gapInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    currentBlockEl.style.gap = `${gapInput.value}rem`;
    currentBlockEl.dataset.gap = gapInput.value;
    gapValue.textContent = gapInput.value;
    recordPendingEdit();
  });

  // the ToC icon and its own button circle scale together (article_toc.css's
  // .toc-open-icon/.toc-open-button/.article-page--has-toc all key off this
  // one variable) -- set on .article-page, not currentBlockEl itself, since
  // that's the wrapper around just the button+trigger, not the icon.
  tocIconSizeInput.addEventListener("input", () => {
    if (!currentBlockEl) {
      return;
    }
    const articlePage = document.querySelector(".article-page");
    if (articlePage) {
      articlePage.style.setProperty("--toc-icon-size", `${tocIconSizeInput.value}rem`);
    }
    currentBlockEl.dataset.tocIconSize = tocIconSizeInput.value;
    tocIconSizeValue.textContent = tocIconSizeInput.value;
    recordPendingEdit();
  });

  // each column weight slider only ever touches its own column's flex-grow
  // (via data-col-index, see article_body_blocks.html) -- separate
  // controls for separate columns, related only by living in the same
  // multi_column block's dataset.columnWeights.
  columnWeightInputs.forEach((input, i) => {
    if (!input) {
      return;
    }
    input.addEventListener("input", () => {
      if (!currentBlockEl) {
        return;
      }
      const item = currentBlockEl.querySelector(`.multi-col-item[data-col-index="${i}"]`);
      if (item) {
        item.style.flex = `${input.value} 1 0`;
      }
      columnWeightValues[i].textContent = input.value;
      const weights = (currentBlockEl.dataset.columnWeights || "").split(",").map(Number);
      weights[i] = parseFloat(input.value);
      currentBlockEl.dataset.columnWeights = weights.join(",");
      recordPendingEdit();
    });
  });

  // title/intro/meta font size, like the header's alignment groups, write
  // straight to a CSS custom property on the wrapper (h1/.intro/.article-meta
  // each read their own, see article_header.css/page_title.css/category_card.css) rather
  // than an inline font-size directly on the wrapper itself -- there's no
  // single element here that all three should apply to.
  const wireHeaderFontSizeInput = (input, valueEl, cssVar, datasetKey) => {
    input.addEventListener("input", () => {
      const wrapperEl = headerWrapperEl();
      if (!wrapperEl) {
        return;
      }
      wrapperEl.style.setProperty(cssVar, `${input.value}rem`);
      wrapperEl.dataset[datasetKey] = input.value;
      valueEl.textContent = input.value;
      recordPendingEdit();
    });
  };

  wireButtonGroup(alignmentGroup, "alignment", "align");
  wireHeaderAlignmentGroup(titleAlignmentGroup, "--title-alignment", "titleAlignment");
  wireHeaderAlignmentGroup(introAlignmentGroup, "--intro-alignment", "introAlignment");
  wireHeaderAlignmentGroup(metaAlignmentGroup, "--meta-alignment", "metaAlignment");
  wireHeaderFontSizeInput(titleFontSizeInput, titleFontSizeValue, "--title-font-size", "titleFontSize");
  wireHeaderFontSizeInput(introFontSizeInput, introFontSizeValue, "--intro-font-size", "introFontSize");
  wireHeaderFontSizeInput(metaFontSizeInput, metaFontSizeValue, "--meta-font-size", "metaFontSize");

  // pure network call, no statusEl/dirty side effects -- save() below
  // drives those centrally, since a single save() call can now flush
  // several of these in a row (one per pending block) and the status/dirty
  // state should reflect the whole batch, not each individual request.
  // Returns a Promise<{ok, error}>.
  const saveViaFetch = (url, payload) => {
    const csrfToken = panel.querySelector("[name=csrfmiddlewaretoken]").value;
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(payload),
    })
      .then((response) =>
        response.json().then((data) => ({ ok: response.ok, data }))
      )
      .then(({ ok, data }) =>
        ok ? { ok: true } : { ok: false, error: data.error || "Failed to save block style." }
      )
      .catch(() => ({ ok: false, error: "Failed to save block style (network error)." }));
  };

  // flushes every block in pendingEdits, one request at a time (not in
  // parallel -- see article_unsaved_changes.js's saveAll for why), so every
  // block touched since the last save gets saved, not just whichever one
  // happens to still be showing in the panel. Returns a Promise<{ok, error}>.
  // This panel has no Save button of its own -- the only way this ever runs
  // is via registerSaveHandler below, called by the global save bar/
  // unsaved-changes modal (article_unsaved_changes.js).
  const save = () => {
    const entries = Array.from(pendingEdits.entries());
    if (entries.length === 0) {
      return Promise.resolve({ ok: true });
    }

    statusEl.textContent = "Saving...";
    statusEl.classList.remove("is-error");

    return entries
      .reduce(
        (chain, [blockId, request]) =>
          chain.then((results) =>
            saveViaFetch(request.url, request.payload).then((result) => {
              if (result.ok) {
                pendingEdits.delete(blockId);
              }
              return results.concat([result]);
            })
          ),
        Promise.resolve([])
      )
      .then((results) => {
        if (pendingEdits.size === 0) {
          window.ifiUnsavedChanges.markClean("blockStyle");
        }
        const ok = results.every((r) => r.ok);
        if (!ok) {
          const error = results
            .filter((r) => !r.ok)
            .map((r) => r.error)
            .join(" ");
          statusEl.textContent = error;
          statusEl.classList.add("is-error");
          return { ok: false, error };
        }
        statusEl.textContent = "Saved";
        return { ok: true };
      });
  };

  window.ifiUnsavedChanges.registerSaveHandler(save);

  // sets each relevant field to its default and replays the same
  // input/click event each one already listens for, rather than
  // duplicating what those listeners do (live preview, dataset, class
  // swap, recordPendingEdit, all of it) a second time here.
  const resetButton = document.getElementById("block-style-reset");
  const applySlider = (input, value) => {
    if (value === undefined || !input) {
      return;
    }
    input.value = value;
    input.dispatchEvent(new Event("input"));
  };
  const applyButtonGroup = (group, value) => {
    if (value === undefined || !group) {
      return;
    }
    const button = group.querySelector(`button[data-align="${value}"]`);
    if (button) {
      button.click();
    }
  };
  const applyColorGroup = (group, value) => {
    if (value === undefined || !group) {
      return;
    }
    const button = group.querySelector(`button[data-color="${value}"]`);
    if (button) {
      button.click();
    }
  };
  // for a color group whose default is blank (text color, unlike bg/border,
  // has no fixed color of its own to click through -- see
  // BLOCK_STYLE_DEFAULTS["box"]["text_color"]) -- clears it back to "no
  // swatch selected" directly instead.
  const clearColorGroup = (group) => {
    group.dataset.value = "";
    group.querySelectorAll(".color-swatch").forEach((s) => s.classList.remove("active"));
  };
  const applyToggle = (input, value) => {
    if (value === undefined || !input) {
      return;
    }
    input.checked = value;
    input.dispatchEvent(new Event("change"));
  };
  resetButton.addEventListener("click", () => {
    const blockType = targetTypeInput.value;
    const defaults = BLOCK_STYLE_DEFAULTS[blockType];
    // column/image_caption/title/meta/intro have no BLOCK_STYLE_DEFAULTS
    // entry of their own -- side padding (see FIELDS_BY_TYPE above) always
    // defaults to plain 0 for these, handled in the fallback below rather
    // than needing a whole defaults dict just for one field.
    const boxCapable = BOX_CAPABLE_TYPES.has(blockType);
    if (!blockType || (!defaults && !boxCapable)) {
      return;
    }
    if (!window.confirm("Reset this block's style to its default values? Unsaved changes to it will be lost.")) {
      return;
    }

    if (defaults) {
      applySlider(paddingInput, defaults.side_padding);
      applyButtonGroup(alignmentGroup, defaults.alignment);
      applySlider(fontSizeInput, defaults.font_size);
      applySlider(widthInput, defaults.width_rem);
      applySlider(heightInput, defaults.height_rem);
      if (defaults.list_style !== undefined) {
        applyToggle(listStyleInput, defaults.list_style);
      }
      if (defaults.fixed_ratio !== undefined) {
        applyToggle(fixedRatioInput, defaults.fixed_ratio);
      }
      applySlider(gapInput, defaults.gap);
      applySlider(tocIconSizeInput, defaults.toc_icon_size);

      if (blockType === "multi_column" && defaults.column_weight !== undefined) {
        const blockEl =
          currentBlockEl || document.querySelector(`[data-block-id="${CSS.escape(targetIdInput.value)}"]`);
        const columnCount = parseInt(blockEl ? blockEl.dataset.columnCount : "0", 10) || 0;
        for (let i = 0; i < columnCount; i++) {
          applySlider(columnWeightInputs[i], defaults.column_weight);
        }
      }

    }

    // title/meta/intro's own alignment/font-size -- pulled from article_
    // header's own BLOCK_STYLE_DEFAULTS entry (title/meta/intro have none
    // of their own, see the fallback below) regardless of whether `defaults`
    // itself is set, since that's only ever populated for blockType
    // "article_header" -- and scoped to whichever of the three is actually
    // open, so resetting Title doesn't also silently reset Meta/Intro's
    // alignment, and resetting article_header itself (side padding + box
    // only now) doesn't reach into any of the three at all.
    const headerDefaults = BLOCK_STYLE_DEFAULTS.article_header || {};
    if (blockType === "title") {
      applyButtonGroup(titleAlignmentGroup, headerDefaults.title_alignment);
      applySlider(titleFontSizeInput, headerDefaults.title_font_size);
    }
    if (blockType === "meta") {
      applyButtonGroup(metaAlignmentGroup, headerDefaults.meta_alignment);
      applySlider(metaFontSizeInput, headerDefaults.meta_font_size);
    }
    if (blockType === "intro") {
      applyButtonGroup(introAlignmentGroup, headerDefaults.intro_alignment);
      applySlider(introFontSizeInput, headerDefaults.intro_font_size);
    }

    // title/meta/intro's own text color -- every type that offers text
    // color defaults to blank (inherit the page's normal text color), same
    // as the generic text_color field's own reset below.
    const headerColorGroup = HEADER_TEXT_COLOR_GROUPS.find((group) => group.blockType === blockType);
    if (headerColorGroup) {
      clearColorGroup(headerColorGroup.colorGroup);
      setCustomSwatch(headerColorGroup.customColorInput, "", headerColorGroup.pickerInput);
      headerColorGroup.applyColor();
      // same blank/off default as text shadow everywhere else -- no prior
      // fixed text-shadow to reproduce (see ArticleBlockStyle.text_shadow_
      // enabled's own docstring).
      applyToggle(headerColorGroup.shadowEnabledInput, false);
      applySlider(headerColorGroup.shadowStrengthInput, 1);
      clearColorGroup(headerColorGroup.shadowColorGroup);
      setCustomSwatch(headerColorGroup.shadowCustomColorInput, "", headerColorGroup.shadowPickerInput);
      headerColorGroup.applyShadow();
    }

    // column/image_caption/title/meta/intro's own side padding -- no
    // BLOCK_STYLE_DEFAULTS entry of their own (see above), always resets
    // to plain 0.
    if (!defaults && (FIELDS_BY_TYPE[blockType] || []).includes("side_padding")) {
      applySlider(paddingInput, 0);
    }

    // a column's title shares this same trigger/panel/reset button now
    // (see FIELDS_BY_TYPE.column above) -- reset it back to heading's own
    // defaults (column_title has no separate BLOCK_STYLE_DEFAULTS entry,
    // it always shared heading's -- see article_models.py) alongside the
    // column's own box, below.
    if (blockType === "column" && currentBlockEl && currentBlockEl.dataset.titleBlockId) {
      const titleDefaults = BLOCK_STYLE_DEFAULTS.heading || {};
      applyButtonGroup(alignmentGroup, titleDefaults.alignment);
      applySlider(fontSizeInput, titleDefaults.font_size);
      clearColorGroup(textColorGroup);
      setCustomSwatch(textCustomColorInput, "", textPickerInput);
      applyTextColor();
      applyToggle(textShadowEnabledInput, titleDefaults.text_shadow_enabled);
      applySlider(textShadowStrengthInput, titleDefaults.text_shadow_strength);
      clearColorGroup(textShadowColorGroup);
      setCustomSwatch(textShadowCustomColorInput, "", textShadowPickerInput);
      applyTextShadow();
    }

    // an image_caption's own title/caption text share this same trigger/
    // panel/reset button too (see CAPTION_TEXT_GROUPS above) -- reset each
    // one back to its own BLOCK_STYLE_DEFAULTS entry, independent of the
    // figcaption's own box below.
    if (blockType === "image_caption" && currentBlockEl) {
      CAPTION_TEXT_GROUPS.forEach((group) => {
        if (!currentBlockEl.dataset[`${group.datasetPrefix}TextId`]) {
          return;
        }
        const groupDefaults = BLOCK_STYLE_DEFAULTS[group.defaultsKey] || {};
        applyButtonGroup(group.alignmentGroup, groupDefaults.alignment);
        applySlider(group.fontSizeInput, groupDefaults.font_size);
        applySlider(group.paddingInput, groupDefaults.side_padding);
        clearColorGroup(group.colorGroup);
        setCustomSwatch(group.customColorInput, "", group.pickerInput);
        group.applyColor();
        applyToggle(group.shadowEnabledInput, groupDefaults.text_shadow_enabled);
        applySlider(group.shadowStrengthInput, groupDefaults.text_shadow_strength);
        clearColorGroup(group.shadowColorGroup);
        setCustomSwatch(group.shadowCustomColorInput, "", group.shadowPickerInput);
        group.applyShadow();
      });
    }

    // text color is independent of box (see FIELDS_BY_TYPE) -- every type
    // that offers it defaults to blank (inherit the page's normal text
    // color), so there's no per-type default value to look up.
    if ((FIELDS_BY_TYPE[blockType] || []).includes("text_color")) {
      clearColorGroup(textColorGroup);
      setCustomSwatch(textCustomColorInput, "", textPickerInput);
      applyTextColor();
    }

    // same blank/off default as text color just above -- see
    // ArticleBlockStyle.text_shadow_enabled's own docstring.
    if ((FIELDS_BY_TYPE[blockType] || []).includes("text_shadow_enabled")) {
      applyToggle(textShadowEnabledInput, false);
      applySlider(textShadowStrengthInput, 1);
      clearColorGroup(textShadowColorGroup);
      setCustomSwatch(textShadowCustomColorInput, "", textShadowPickerInput);
      applyTextShadow();
    }

    if (boxCapable) {
      const boxDefaults = BLOCK_STYLE_DEFAULTS.box;
      if (boxDefaults) {
        applyColorGroup(boxBgColorGroup, boxDefaults.bg_color);
        setCustomSwatch(boxBgCustomColorInput, boxDefaults.bg_custom_color, boxBgPickerInput);
        applyColorGroup(boxBorderColorGroup, boxDefaults.border_color);
        setCustomSwatch(boxBorderCustomColorInput, boxDefaults.border_custom_color, boxBorderPickerInput);
        applySlider(boxBorderWidthInput, boxDefaults.border_width);
        applySlider(boxRadiusInput, boxDefaults.radius);
        applySlider(boxPaddingInput, boxDefaults.padding);
        applySlider(boxMarginInput, boxDefaults.margin);
        applySlider(boxShadowStrengthInput, boxDefaults.shadow_strength);
        // shadow_color's default is blank (no swatch selected, same as
        // text_color's own default elsewhere), so clearColorGroup, not
        // applyColorGroup -- there's no button to click for "".
        clearColorGroup(boxShadowColorGroup);
        setCustomSwatch(boxShadowCustomColorInput, boxDefaults.shadow_custom_color, boxShadowPickerInput);
        applyToggle(boxBorderVisibleInput, boxDefaults.border_visible);
        applyToggle(boxShadowEnabledInput, boxDefaults.shadow_enabled);
        // applied last: its own change handler re-derives box field
        // visibility from every other box field's current value, so it
        // needs to run after they've all already been reset above.
        applyToggle(boxEnabledInput, boxDefaults.enabled);
      }
    }

    // hero_image's own box -- separate from the generic box mechanism
    // above (hero_image isn't in BOX_CAPABLE_TYPES, see applyHeroImageBox's
    // own comment), so it needs its own reset here.
    if (blockType === "hero_image" && defaults) {
      applyToggle(heroBoxedInput, defaults.boxed);
      applyColorGroup(heroBoxColorGroup, defaults.box_color);
      setCustomSwatch(heroBoxCustomColorInput, defaults.box_custom_color, heroBoxPickerInput);
      applySlider(heroBoxRadiusInput, defaults.box_border_radius);
      applySlider(heroBoxShadowStrengthInput, defaults.shadow_strength);
      clearColorGroup(heroBoxShadowColorGroup);
      setCustomSwatch(heroBoxShadowCustomColorInput, defaults.shadow_custom_color, heroBoxShadowPickerInput);
      applyToggle(heroBoxShadowEnabledInput, defaults.shadow_enabled);
    }
  });
});
