// Shared "have any on-page style edits (quick-style panel or block-style
// mini panel) been made since the last successful save" state, the styled
// in-site "you have unsaved changes" modal that reads it, and the native
// beforeunload fallback for whatever that modal can't cover.
window.ifiUnsavedChanges = (() => {
  // a Set of source names, not a single boolean -- the quick-style panel
  // and the block-style panel (which can itself have several different
  // *blocks* mid-edit at once, see its own pendingEdits map) are
  // independent; one of them finishing its own save shouldn't be able to
  // wipe out the fact that another is still dirty.
  const dirtySources = new Set();
  const saveHandlers = [];
  // called after every dirty/clean transition with the new isDirty() value
  // -- lets the floating save bar (article_save_bar.html) show/hide itself
  // reactively instead of polling.
  const changeListeners = [];
  const notify = () => {
    const dirty = dirtySources.size > 0;
    changeListeners.forEach((fn) => fn(dirty));
  };

  // Separate from dirtySources above -- a source can be dirty (something
  // changed) without saving it being destructive (e.g. padding/font-size/
  // background just live-preview). This tracks specifically "Save will also
  // bulk-apply something beyond what's already previewed on screen" (today
  // just the quick-style panel's Alignment field, see article_quick_style.js's
  // own comment on apply_alignment_to_blocks) so the save buttons can relabel
  // themselves "Save and Apply" as a heads-up, instead of a plain "Save" that
  // undersells what pressing it is about to do.
  const applySources = new Set();
  const applyChangeListeners = [];
  const notifyApply = () => {
    const pending = applySources.size > 0;
    applyChangeListeners.forEach((fn) => fn(pending));
  };

  // A real page unload -- closing the tab, an actual reload, typing a new
  // URL, back/forward -- can't be intercepted with custom UI. Browsers
  // hard-code their own generic "leave site?" wording here regardless of
  // what's put in event.returnValue (a long-standing anti-phishing
  // measure), so this is only a safety net for those cases. In-site link
  // clicks are handled below instead, where a real styled prompt is
  // possible.
  window.addEventListener("beforeunload", (event) => {
    if (dirtySources.size === 0) {
      return;
    }
    event.preventDefault();
    event.returnValue = "";
  });

  return {
    markDirty: (source) => {
      dirtySources.add(source);
      notify();
    },
    markClean: (source) => {
      dirtySources.delete(source);
      notify();
    },
    // discarding throws away every pending edit, everywhere, regardless of
    // which panel/block it came from -- unlike markClean, which only ever
    // speaks for the one source that called it.
    markAllClean: () => {
      dirtySources.clear();
      applySources.clear();
      notify();
      notifyApply();
    },
    isDirty: () => dirtySources.size > 0,
    onChange: (fn) => {
      changeListeners.push(fn);
    },
    markApplyPending: (source) => {
      applySources.add(source);
      notifyApply();
    },
    clearApplyPending: (source) => {
      applySources.delete(source);
      notifyApply();
    },
    hasApplyPending: () => applySources.size > 0,
    onApplyChange: (fn) => {
      applyChangeListeners.push(fn);
    },
    // each editor panel (quick-style, block-style) registers its own save
    // function here -- () => Promise<{ok, error}> -- so the modal's "Save
    // changes" button can trigger every panel's save, and show *why* if one
    // fails, without this file needing to know how any of them actually work.
    registerSaveHandler: (fn) => {
      saveHandlers.push(fn);
    },
    // runs handlers one at a time, not Promise.all -- the dev DB is SQLite,
    // which locks up ("database is locked") if two of these POSTs land as
    // overlapping write transactions, so save requests can't fire
    // concurrently.
    saveAll: () =>
      saveHandlers
        .reduce(
          (chain, fn) =>
            chain.then((results) => fn().then((result) => [...results, result])),
          Promise.resolve([])
        )
        .then((results) => ({
          ok: results.every((r) => r.ok),
          errors: results.filter((r) => !r.ok).map((r) => r.error),
        })),
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("unsaved-changes-modal");
  if (!modal) {
    return;
  }

  wireUnsavedChangesModal(modal);
  wireSaveBar();
});

function wireUnsavedChangesModal(modal) {
  const backdrop = document.getElementById("unsaved-changes-backdrop");
  const saveButton = document.getElementById("unsaved-changes-save");
  const discardButton = document.getElementById("unsaved-changes-discard");
  const cancelButton = document.getElementById("unsaved-changes-cancel");
  const statusEl = document.getElementById("unsaved-changes-status");

  // Same "Save and Apply" heads-up as the floating save bar below -- see
  // ifiUnsavedChanges' own comment on applySources for what this means.
  const saveLabel = saveButton.textContent;
  const applySaveLabel = "Save and Apply changes";
  window.ifiUnsavedChanges.onApplyChange((pending) => {
    saveButton.textContent = pending ? applySaveLabel : saveLabel;
  });

  // the link the user actually tried to follow -- navigated to for real
  // once they've saved or chosen to discard.
  let pendingHref = null;

  const openModal = (href) => {
    pendingHref = href;
    statusEl.textContent = "";
    modal.hidden = false;
  };

  const closeModal = () => {
    pendingHref = null;
    modal.hidden = true;
  };

  // only in-site, same-tab, real navigations -- #anchors, mailto:/tel:,
  // new-tab links, and JS-driven buttons (which aren't <a> tags at all,
  // e.g. this panel's own Save/Discard/Cancel) are all left alone.
  document.addEventListener("click", (event) => {
    if (!window.ifiUnsavedChanges.isDirty()) {
      return;
    }
    const link = event.target.closest("a[href]");
    if (!link || link.target === "_blank") {
      return;
    }
    const href = link.getAttribute("href");
    if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:")) {
      return;
    }
    event.preventDefault();
    openModal(link.href);
  });

  backdrop.addEventListener("click", closeModal);
  cancelButton.addEventListener("click", closeModal);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });

  discardButton.addEventListener("click", () => {
    window.ifiUnsavedChanges.markAllClean();
    const href = pendingHref;
    closeModal();
    if (href) {
      window.location.href = href;
    }
  });

  saveButton.addEventListener("click", () => {
    saveButton.disabled = true;
    discardButton.disabled = true;
    statusEl.textContent = "Saving...";
    statusEl.classList.remove("is-error");

    window.ifiUnsavedChanges.saveAll().then(({ ok, errors }) => {
      saveButton.disabled = false;
      discardButton.disabled = false;

      if (!ok) {
        statusEl.textContent = errors.join(" ") || "Couldn't save everything.";
        statusEl.classList.add("is-error");
        return;
      }

      const href = pendingHref;
      closeModal();
      if (href) {
        window.location.href = href;
      }
    });
  });
}

// Persistent floating "unsaved changes" bar, bottom-center of the viewport
// (see article_save_bar.html) -- shown whenever ifiUnsavedChanges' dirty
// state is non-empty, hidden otherwise, via onChange() rather than polling.
// Same save/discard machinery as the modal above, just always reachable
// instead of only appearing when you try to navigate away.
function wireSaveBar() {
  const bar = document.getElementById("save-bar");
  if (!bar) {
    return;
  }

  const saveButton = document.getElementById("save-bar-save");
  const discardButton = document.getElementById("save-bar-discard");
  const statusEl = document.getElementById("save-bar-status");

  // Same "Save and Apply" heads-up as the unsaved-changes modal above --
  // see ifiUnsavedChanges' own comment on applySources for what this means.
  const saveLabel = saveButton.textContent;
  const applySaveLabel = "Save and Apply";
  window.ifiUnsavedChanges.onApplyChange((pending) => {
    saveButton.textContent = pending ? applySaveLabel : saveLabel;
  });

  window.ifiUnsavedChanges.onChange((isDirty) => {
    bar.hidden = !isDirty;
    if (isDirty) {
      statusEl.textContent = "";
      statusEl.classList.remove("is-error");
    }
  });
  bar.hidden = !window.ifiUnsavedChanges.isDirty();

  saveButton.addEventListener("click", () => {
    saveButton.disabled = true;
    discardButton.disabled = true;
    statusEl.textContent = "Saving...";
    statusEl.classList.remove("is-error");

    window.ifiUnsavedChanges.saveAll().then(({ ok, errors }) => {
      saveButton.disabled = false;
      discardButton.disabled = false;

      if (!ok) {
        statusEl.textContent = errors.join(" ") || "Couldn't save everything.";
        statusEl.classList.add("is-error");
        return;
      }
      statusEl.textContent = "Saved";
      // onChange() above already hides the bar once dirty flips to false --
      // nothing else to do here.
    });
  });

  discardButton.addEventListener("click", () => {
    if (!window.confirm("Discard all unsaved changes? This can't be undone.")) {
      return;
    }
    window.ifiUnsavedChanges.markAllClean();
    // there's no per-field "undo" -- every panel already applied its edits
    // straight to the live page, so the only way back to the actual saved
    // state is to reload it from the server.
    window.location.reload();
  });
}
