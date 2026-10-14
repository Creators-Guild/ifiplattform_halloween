document.addEventListener("DOMContentLoaded", () => {
  const panel = document.getElementById("banner-style-panel");
  const banner = document.querySelector(".title-banner");
  // the page's own plain (bannerless) title -- always rendered alongside
  // .title-banner now, whichever one is currently [hidden] is decided by
  // show_banner (see article_category_page.html/article_index_page.html/
  // studentunion_category_page.html), so toggling the checkbox can flip
  // between them live instead of needing a save+reload to see anything.
  const plainTitle = document.getElementById("page-title-plain");
  if (!panel) {
    return;
  }

  const showBannerInput = document.getElementById("banner-style-show-banner");
  const sectionsWrapper = document.getElementById("banner-style-sections");
  const colorInput = document.getElementById("banner-style-color");
  const colorPicker = document.getElementById("banner-style-color-picker");
  const dotColorInput = document.getElementById("banner-style-dot-color");
  const dotColorPicker = document.getElementById("banner-style-dot-color-picker");
  const textColorInput = document.getElementById("banner-style-text-color");
  const textColorPicker = document.getElementById("banner-style-text-color-picker");
  const widthInput = document.getElementById("banner-style-width");
  const widthValue = document.getElementById("banner-style-width-value");
  const heightInput = document.getElementById("banner-style-height");
  const heightValue = document.getElementById("banner-style-height-value");
  const fontSizeInput = document.getElementById("banner-style-font-size");
  const fontSizeValue = document.getElementById("banner-style-font-size-value");
  const statusEl = document.getElementById("banner-style-status");
  const minimizeButton = document.getElementById("banner-style-minimize");
  const MINIMIZED_KEY = "ifiBannerStyleMinimized";

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

  // Colors/Size & Text collapsible sections -- same generic [data-controls]
  // wiring as article_quick_style.js's own Publish/Style sections (see
  // that file's comment for why this is one generic loop rather than
  // per-section JS).
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

  // fills the text input itself with the color it holds (same convention
  // as article_block_style.js's own custom hex swatches) -- otherwise
  // there's nothing here to show what "#1c6fc1" actually looks like
  // besides the tiny picker swatch next to it.
  const fillSwatch = (input, hex) => {
    if (hex) {
      input.style.backgroundColor = hex;
      input.style.color = contrastTextColor(hex);
    } else {
      input.style.backgroundColor = "";
      input.style.color = "";
    }
  };

  // no banner rendered at all yet (show_banner was already false on page
  // load, see article_category_page.html/article_index_page.html) --
  // live preview has nothing to update, but the panel itself (show/hide
  // toggle, save) still works.
  const applyBannerColors = () => {
    if (!banner) {
      return;
    }
    if (colorInput.value) {
      banner.style.background = colorInput.value;
    }
    if (dotColorInput.value) {
      banner.style.setProperty("--dot-color", dotColorInput.value);
    }
    const h1 = banner.querySelector("h1");
    if (h1 && textColorInput.value) {
      h1.style.color = textColorInput.value;
    }
  };
  applyBannerColors();

  const applyBannerSize = () => {
    if (!banner) {
      return;
    }
    banner.style.width = `${widthInput.value}rem`;
    banner.style.maxWidth = "100%";
    banner.style.height = `${heightInput.value}rem`;
    const h1 = banner.querySelector("h1");
    if (h1) {
      h1.style.fontSize = `${fontSizeInput.value}rem`;
    }
  };
  applyBannerSize();

  // pairs a hex text input with its native color-picker sibling, same
  // "typing a valid hex updates the picker, picking updates the text"
  // convention as article_block_style.js's own custom swatches.
  const swatchPairs = [
    [colorInput, colorPicker],
    [dotColorInput, dotColorPicker],
    [textColorInput, textColorPicker],
  ];
  swatchPairs.forEach(([textInput, pickerInput]) => {
    fillSwatch(textInput, normalizeHex(textInput.value));
    textInput.addEventListener("input", () => {
      const hex = normalizeHex(textInput.value);
      if (!hex) {
        return;
      }
      pickerInput.value = hex;
      fillSwatch(textInput, hex);
      applyBannerColors();
      window.ifiUnsavedChanges.markDirty("bannerStyle");
    });
    pickerInput.addEventListener("input", () => {
      textInput.value = pickerInput.value;
      fillSwatch(textInput, pickerInput.value);
      applyBannerColors();
      window.ifiUnsavedChanges.markDirty("bannerStyle");
    });
  });

  widthInput.addEventListener("input", () => {
    widthValue.textContent = widthInput.value;
    applyBannerSize();
    window.ifiUnsavedChanges.markDirty("bannerStyle");
  });
  heightInput.addEventListener("input", () => {
    heightValue.textContent = heightInput.value;
    applyBannerSize();
    window.ifiUnsavedChanges.markDirty("bannerStyle");
  });
  fontSizeInput.addEventListener("input", () => {
    fontSizeValue.textContent = fontSizeInput.value;
    applyBannerSize();
    window.ifiUnsavedChanges.markDirty("bannerStyle");
  });

  showBannerInput.addEventListener("change", () => {
    const show = showBannerInput.checked;
    sectionsWrapper.hidden = !show;
    // the actual point of this fix -- flip which one is visible right
    // now, not just after a save+reload.
    if (banner) {
      banner.hidden = !show;
    }
    if (plainTitle) {
      plainTitle.hidden = show;
    }
    window.ifiUnsavedChanges.markDirty("bannerStyle");
  });

  const resetButton = document.getElementById("banner-style-reset");
  resetButton.addEventListener("click", () => {
    if (!window.confirm("Reset the banner style to its default values? Unsaved changes will be lost.")) {
      return;
    }
    showBannerInput.checked = false;
    showBannerInput.dispatchEvent(new Event("change"));
    [
      [colorInput, colorPicker, panel.dataset.defaultBannerColor],
      [dotColorInput, dotColorPicker, panel.dataset.defaultDotColor],
      [textColorInput, textColorPicker, panel.dataset.defaultTextColor],
    ].forEach(([textInput, pickerInput, defaultHex]) => {
      textInput.value = "";
      pickerInput.value = defaultHex;
      fillSwatch(textInput, null);
    });
    applyBannerColors();

    widthInput.value = panel.dataset.defaultWidth;
    widthInput.dispatchEvent(new Event("input"));
    heightInput.value = panel.dataset.defaultHeight;
    heightInput.dispatchEvent(new Event("input"));
    fontSizeInput.value = panel.dataset.defaultFontSize;
    fontSizeInput.dispatchEvent(new Event("input"));
  });

  // returns a Promise<{ok, error}> -- see article_quick_style.js's save()
  // for the full reasoning (no Save button of its own, registered below
  // for the global floating save bar to trigger).
  const save = () => {
    statusEl.textContent = "Saving...";
    statusEl.classList.remove("is-error");

    const csrfToken = panel.querySelector("[name=csrfmiddlewaretoken]").value;

    return fetch(panel.dataset.bannerStyleUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({
        show_banner: showBannerInput.checked,
        banner_color: colorInput.value,
        banner_dot_color: dotColorInput.value,
        banner_text_color: textColorInput.value,
        banner_width_rem: widthInput.value,
        banner_height_rem: heightInput.value,
        banner_font_size: fontSizeInput.value,
      }),
    })
      .then((response) => response.json().then((data) => ({ ok: response.ok, data })))
      .then(({ ok, data }) => {
        if (ok) {
          statusEl.textContent = "Saved";
          window.ifiUnsavedChanges.markClean("bannerStyle");
          // no reload needed -- .title-banner (and its dots) are always
          // in the DOM now, just [hidden] when show_banner is off (see
          // showBannerInput's own change handler above), so the live
          // preview already matches what a fresh page load would show.
          return { ok: true };
        }
        const error = data.error || "Failed to save banner style.";
        statusEl.textContent = error;
        statusEl.classList.add("is-error");
        return { ok: false, error };
      })
      .catch(() => {
        const error = "Failed to save banner style (network error).";
        statusEl.textContent = error;
        statusEl.classList.add("is-error");
        return { ok: false, error };
      });
  };

  window.ifiUnsavedChanges.registerSaveHandler(save);
});
