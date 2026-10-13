document.addEventListener("DOMContentLoaded", () => {
  const panel = document.getElementById("quick-style-panel");
  const articlePage = document.querySelector(".article-page");
  // shared site-wide wrapper (home_base.html), not article-specific --
  // background color paints this one instead of .article-page itself, so
  // it also covers the site's own left/right padding around the content
  // column (see article_page.html's maincontent_style block).
  const mainContent = document.querySelector(".maincontent");
  if (!panel || !articlePage || !mainContent) {
    return;
  }

  const paddingInput = document.getElementById("quick-style-padding");
  const paddingValue = document.getElementById("quick-style-padding-value");
  const fontSizeInput = document.getElementById("quick-style-font-size");
  const fontSizeValue = document.getElementById("quick-style-font-size-value");
  const alignmentGroup = document.getElementById("quick-style-alignment");
  const bgEnabledInput = document.getElementById("quick-style-bg-enabled");
  const bgColorField = document.getElementById("quick-style-bg-color-field");
  const bgColorGroup = document.getElementById("quick-style-bg-color");
  const bgCustomColorInput = document.getElementById("quick-style-bg-custom-color");
  const bgPickerInput = document.getElementById("quick-style-bg-picker");
  const statusEl = document.getElementById("quick-style-status");
  const minimizeButton = document.getElementById("quick-style-minimize");
  const publishButton = document.getElementById("quick-style-publish-button");
  const unpublishButton = document.getElementById("quick-style-unpublish-button");
  const syncMirroredButton = document.getElementById("quick-style-sync-mirrored-button");
  const MINIMIZED_KEY = "ifiQuickStyleMinimized";

  // Alignment is destructive to save (see save() below) -- tracked
  // separately from the rest of this panel's dirty state so save() only
  // warns/bulk-overwrites when this specific field actually changed this
  // session, not on every save of an unrelated field (padding/font-size/
  // background). Starts at the server-rendered value, updated after each
  // save that doesn't reload the page (see save()'s own comment).
  let lastSavedAlignment = alignmentGroup.dataset.value;

  // Set by the Reset button (below), same "stays pending until Save"
  // pattern as alignment above -- header_side_padding/title_font_size/
  // meta_font_size/intro_font_size are the header's own independent
  // fields (not read/written by anything else in this panel, see
  // article_layout.css/article_header.css/page_title.css calc()), so Reset can't just live-preview them the
  // way padding/font-size/background do. Cleared after a successful save.
  let resetHeaderPending = false;

  // Shared by the Publish/Unpublish buttons below -- neither is a style
  // field, so they act immediately on click rather than going through the
  // dirty-tracking/save-bar flow the rest of this panel uses (there's
  // nothing to "preview" here). Both always act on the nb ("OG") copy of
  // this article and sync the en translation to match, regardless of
  // which locale you're actually looking at (see ArticlePage.publish_
  // target/article_views.publish_page/unpublish_page) -- reloads on
  // success so the badge, save-bar dirty state, and any newly-(un)
  // published content all reflect reality rather than trying to patch
  // each of those by hand.
  const runPublishAction = (button, url, confirmMessage, busyLabel, idleLabel) => {
    button.addEventListener("click", () => {
      if (!window.confirm(confirmMessage)) {
        return;
      }
      const csrfToken = panel.querySelector("[name=csrfmiddlewaretoken]").value;
      button.disabled = true;
      button.textContent = busyLabel;
      fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
      })
        .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
          if (ok) {
            window.location.reload();
            return;
          }
          window.alert(data.error || `Failed to ${idleLabel.toLowerCase()}.`);
          button.disabled = false;
          button.textContent = idleLabel;
        })
        .catch(() => {
          window.alert(`Failed to ${idleLabel.toLowerCase()} (network error).`);
          button.disabled = false;
          button.textContent = idleLabel;
        });
    });
  };

  if (publishButton) {
    runPublishAction(
      publishButton,
      panel.dataset.publishUrl,
      "Publish the latest changes to this page? This also publishes the Norwegian version if you're editing the English translation.",
      "Publishing...",
      "Publish"
    );
  }

  if (unpublishButton) {
    runPublishAction(
      unpublishButton,
      panel.dataset.unpublishUrl,
      "Unpublish this page? This takes the Norwegian version off the live site (and the English translation along with it), regardless of which one you're editing.",
      "Unpublishing...",
      "Unpublish"
    );
  }

  if (syncMirroredButton) {
    runPublishAction(
      syncMirroredButton,
      panel.dataset.syncMirroredUrl,
      "Push this page's synchronized fields (menu visibility, status, etc.) to its English translation now?",
      "Syncing...",
      "Sync mirrored page"
    );
  }

  // Publish/Style are each their own collapsible section now -- same
  // generic [data-controls] wiring as article_block_style.js's own copy
  // (see that file's comment for why this is one generic loop rather than
  // per-section JS: data-controls points each toggle at its own fields
  // wrapper's id, so adding another section here needs no matching code).
  // Not shared/imported from that file since the two panels' DOMContent-
  // Loaded handlers are otherwise independent and this is only a few lines.
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
    });
  });

  const applyMinimized = (isMinimized) => {
    panel.classList.toggle("is-minimized", isMinimized);
    minimizeButton.setAttribute("aria-expanded", String(!isMinimized));
    minimizeButton.textContent = isMinimized ? "+" : "−";
  };

  applyMinimized(localStorage.getItem(MINIMIZED_KEY) === "true");

  minimizeButton.addEventListener("click", () => {
    const isMinimized = !panel.classList.contains("is-minimized");
    localStorage.setItem(MINIMIZED_KEY, String(isMinimized));
    applyMinimized(isMinimized);
  });

  // live preview only -- writes straight to the same CSS custom properties
  // the server-rendered inline style set on page load, no network round trip.
  paddingInput.addEventListener("input", () => {
    articlePage.style.setProperty("--content-side-padding", `${paddingInput.value}rem`);
    paddingValue.textContent = paddingInput.value;
    window.ifiUnsavedChanges.markDirty("quickStyle");
  });

  // content_font_size_multiplier -- not a CSS length any more (unlike
  // padding/alignment above), so there's no single CSS var to set. Instead,
  // rescale every font-size-bearing block currently on the page directly:
  // [data-font-size] holds each one's own RAW font size (set server-side in
  // article_body_blocks.html/article_image_block.html, and kept in sync by
  // article_block_style.js's own font-size listeners) -- multiplying that
  // by the live slider value and writing straight to style.fontSize mirrors
  // what the server does at render time (_effective_heading_style's
  // display_font_size), without a page reload. data-font-size itself is
  // never touched here, only the visible rendered size -- article_block_
  // style.js's mini panel always needs the raw value when it reopens.
  fontSizeInput.addEventListener("input", () => {
    const multiplier = parseFloat(fontSizeInput.value) || 1;
    articlePage.dataset.fontSizeMultiplier = fontSizeInput.value;
    // title/meta/intro read this directly via calc() (article_header.css/page_title.css) --
    // unlike the body blocks below, they have no per-element data-font-size
    // to rescale in JS, so the CSS var is the only thing driving them.
    articlePage.style.setProperty("--content-font-size-multiplier", fontSizeInput.value);
    document.querySelectorAll("[data-font-size]").forEach((el) => {
      const raw = parseFloat(el.dataset.fontSize);
      if (!Number.isNaN(raw)) {
        el.style.fontSize = `${raw * multiplier}rem`;
      }
    });
    fontSizeValue.textContent = fontSizeInput.value;
    window.ifiUnsavedChanges.markDirty("quickStyle");
  });

  alignmentGroup.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      const align = button.dataset.align;
      alignmentGroup.dataset.value = align;
      articlePage.style.setProperty("--content-alignment", align);
      alignmentGroup.querySelectorAll("button").forEach((b) => {
        b.classList.toggle("active", b === button);
      });
      window.ifiUnsavedChanges.markDirty("quickStyle");
      // Save will bulk-overwrite every block's own alignment once this
      // actually differs from what's saved (see save()'s own comment on
      // apply_alignment_to_blocks) -- flip back off if clicked back to the
      // originally-saved value before ever saving. Own source key (not
      // shared with resetHeaderPending below) so this can toggle off
      // without accidentally clearing that pending reset's own flag too.
      if (align !== lastSavedAlignment) {
        window.ifiUnsavedChanges.markApplyPending("quickStyleAlignment");
      } else {
        window.ifiUnsavedChanges.clearApplyPending("quickStyleAlignment");
      }
    });
  });

  // background color -- same swatch-row + hex-chip-with-picker-button
  // control as the per-block box styling panel (article_block_style.js),
  // just for the whole article body's own background. Reimplemented here
  // rather than shared, same as the alignment buttons above already are --
  // this panel edits one fixed ArticlePage's own fields directly (server-
  // rendered initial values), not whichever block a trigger last opened.
  const applyBgColor = () => {
    if (!bgEnabledInput.checked) {
      mainContent.style.backgroundColor = "";
      return;
    }
    const color = bgColorGroup.dataset.value;
    mainContent.style.backgroundColor =
      color === "custom" ? bgCustomColorInput.value || "var(--color-bg-light)" : `var(--color-${color})`;
  };

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

  const contrastTextColor = (hex) => {
    const int = parseInt(hex.slice(1), 16);
    const r = (int >> 16) & 255;
    const g = (int >> 8) & 255;
    const b = int & 255;
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.6 ? "#000000" : "#ffffff";
  };

  const setCustomSwatch = (hex) => {
    bgCustomColorInput.value = hex || "";
    if (hex) {
      bgCustomColorInput.style.backgroundColor = hex;
      bgCustomColorInput.style.color = contrastTextColor(hex);
    } else {
      bgCustomColorInput.style.backgroundColor = "";
      bgCustomColorInput.style.color = "";
    }
    bgPickerInput.value = hex || "#ffffff";
  };

  const selectBgSwatch = (swatch) => {
    bgColorGroup.dataset.value = swatch.dataset.color;
    bgColorGroup.querySelectorAll(".color-swatch").forEach((s) => {
      s.classList.toggle("active", s === swatch);
    });
    applyBgColor();
    window.ifiUnsavedChanges.markDirty("quickStyle");
  };

  bgColorGroup.querySelectorAll("button.color-swatch").forEach((button) => {
    button.addEventListener("click", () => selectBgSwatch(button));
  });

  // same "outer box is the button" first-click behavior as the per-block
  // box panel's own custom swatch -- while custom isn't the active choice,
  // the whole hex-chip+picker box just selects it on the first click
  // (reapplying whatever hex was already there) instead of immediately
  // focusing the text field or opening the picker.
  const customGroupEl = bgCustomColorInput.closest(".color-swatch-custom-group");
  customGroupEl.addEventListener("mousedown", (event) => {
    if (bgColorGroup.dataset.value === "custom") {
      return;
    }
    event.preventDefault();
  });
  customGroupEl.addEventListener("click", (event) => {
    if (bgColorGroup.dataset.value === "custom") {
      return;
    }
    event.preventDefault();
    selectBgSwatch(bgCustomColorInput);
  });

  bgCustomColorInput.addEventListener("input", () => {
    const hex = normalizeHex(bgCustomColorInput.value);
    if (!hex) {
      return;
    }
    setCustomSwatch(hex);
    selectBgSwatch(bgCustomColorInput);
  });

  bgPickerInput.addEventListener("input", () => {
    setCustomSwatch(bgPickerInput.value);
    selectBgSwatch(bgCustomColorInput);
  });

  bgEnabledInput.addEventListener("change", () => {
    bgColorField.hidden = !bgEnabledInput.checked;
    applyBgColor();
    window.ifiUnsavedChanges.markDirty("quickStyle");
  });

  // sets each field to its default and replays the same input/click each
  // one already listens for, rather than duplicating what those listeners
  // do -- same trick as article_block_style.js's own reset button.
  const resetButton = document.getElementById("quick-style-reset");
  resetButton.addEventListener("click", () => {
    if (
      !window.confirm(
        "Reset the global style to its default values? This also resets the title/meta/intro block's own side padding and font sizes. Unsaved changes will be lost."
      )
    ) {
      return;
    }

    // header_side_padding/title_font_size/meta_font_size/intro_font_size
    // stay pending until Save (see resetHeaderPending's own comment) --
    // unlike padding/font-size/background above, there's no live CSS var
    // for these to preview through here, they only take effect once
    // save_quick_style writes them and the page reloads.
    resetHeaderPending = true;
    // discard any stale header edit already queued by article_block_
    // style.js's own mini panel (see that file's own comment on this
    // function) -- otherwise its save handler, registered after this
    // panel's own, would flush right after this reset and overwrite it.
    window.ifiDiscardPendingHeaderStyleEdit?.();
    window.ifiUnsavedChanges.markDirty("quickStyle");
    // Just like alignment above, this only takes effect once actually
    // saved (there's no live CSS var to preview the header's own reset
    // font sizes/padding through) -- own source key so it isn't
    // accidentally cleared by the alignment click below if the default
    // alignment happens to match what's already saved.
    window.ifiUnsavedChanges.markApplyPending("quickStyleReset");

    paddingInput.value = panel.dataset.defaultPadding;
    paddingInput.dispatchEvent(new Event("input"));

    fontSizeInput.value = panel.dataset.defaultFontSize;
    fontSizeInput.dispatchEvent(new Event("input"));

    const defaultAlignButton = alignmentGroup.querySelector(
      `button[data-align="${panel.dataset.defaultAlignment}"]`
    );
    if (defaultAlignButton) {
      defaultAlignButton.click();
    }

    setCustomSwatch(null);
    const defaultBgButton = bgColorGroup.querySelector(
      `button[data-color="${panel.dataset.defaultBgColor}"]`
    );
    if (defaultBgButton) {
      defaultBgButton.click();
    }
    bgEnabledInput.checked = false;
    bgEnabledInput.dispatchEvent(new Event("change"));
  });

  // returns a Promise<{ok, error}> -- this panel has no Save button of its
  // own, so the only way this ever runs is via registerSaveHandler below,
  // called by the global save bar/unsaved-changes modal (article_unsaved_
  // changes.js). The error string travels with the result so those can show
  // what actually went wrong even though this panel might not be visible
  // at the time.
  const save = () => {
    // Alignment is the one destructive field here: saving a changed value
    // overwrites every alignment-capable block's own alignment throughout
    // the article (see save_quick_style's apply_alignment_to_blocks in
    // article_views.py), except any block individually locked via its own
    // exclude_from_global_alignment checkbox. Only warn/apply when it
    // actually changed this session (comparing against lastSavedAlignment,
    // not the block-level dirty flag, which also covers padding/font-size/
    // background) -- cancelling reverts just the alignment control (replaying
    // its own click handler) and aborts this whole save, same as every
    // other field stays unsaved until Save is pressed again.
    const alignmentChanged = alignmentGroup.dataset.value !== lastSavedAlignment;
    if (alignmentChanged) {
      const confirmed = window.confirm(
        "Changing the global Alignment will overwrite the alignment of every block in this article that has its own alignment (headings, paragraphs, images, image captions, column titles) -- except any block you've individually locked. Continue?"
      );
      if (!confirmed) {
        const revertButton = alignmentGroup.querySelector(`button[data-align="${lastSavedAlignment}"]`);
        if (revertButton) {
          revertButton.click();
        }
        return Promise.resolve({ ok: false, error: "Alignment change cancelled." });
      }
    }

    statusEl.textContent = "Saving...";
    statusEl.classList.remove("is-error");

    const csrfToken = panel.querySelector("[name=csrfmiddlewaretoken]").value;

    return fetch(panel.dataset.quickStyleUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({
        content_side_padding: paddingInput.value,
        content_alignment: alignmentGroup.dataset.value,
        content_font_size_multiplier: fontSizeInput.value,
        content_bg_enabled: bgEnabledInput.checked,
        content_bg_color: bgColorGroup.dataset.value,
        content_bg_custom_color: bgCustomColorInput.value,
        apply_alignment_to_blocks: alignmentChanged,
        reset_header: resetHeaderPending,
      }),
    })
      .then((response) =>
        response.json().then((data) => ({ ok: response.ok, data }))
      )
      .then(({ ok, data }) => {
        if (ok) {
          statusEl.textContent = "Saved";
          window.ifiUnsavedChanges.markClean("quickStyle");
          if (alignmentChanged || resetHeaderPending) {
            // every block's alignment class/data-alignment, and/or the
            // header's own side padding/font sizes, are now stale
            // (overwritten server-side) -- reload rather than trying to
            // replicate save_quick_style's bulk update in JS, same pattern
            // runPublishAction already uses on success.
            window.location.reload();
            return { ok: true };
          }
          lastSavedAlignment = alignmentGroup.dataset.value;
          return { ok: true };
        }
        const error = data.error || "Failed to save global style.";
        statusEl.textContent = error;
        statusEl.classList.add("is-error");
        return { ok: false, error };
      })
      .catch(() => {
        const error = "Failed to save global style (network error).";
        statusEl.textContent = error;
        statusEl.classList.add("is-error");
        return { ok: false, error };
      });
  };

  // no Save button of its own -- registered here so the global floating
  // save bar (article_save_bar.html) can trigger it instead.
  window.ifiUnsavedChanges.registerSaveHandler(save);
});
