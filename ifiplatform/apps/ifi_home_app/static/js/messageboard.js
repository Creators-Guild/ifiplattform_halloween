document.addEventListener("DOMContentLoaded", () => {
  const setupScrollbar = (slide) => {
    const body = slide.querySelector(".messageboard-body");
    const track = slide.querySelector(".messageboard-scrollbar");
    const thumb = slide.querySelector(".messageboard-scrollbar-thumb");
    if (!body || !track || !thumb) {
      return () => {};
    }

    const update = () => {
      const { scrollHeight, clientHeight, scrollTop } = body;
      if (scrollHeight <= clientHeight) {
        thumb.style.display = "none";
        return;
      }
      const trackHeight = track.clientHeight;
      const thumbHeight = Math.max((clientHeight / scrollHeight) * trackHeight, 24);
      const maxThumbTop = trackHeight - thumbHeight;
      const scrollRatio = scrollTop / (scrollHeight - clientHeight);
      thumb.style.display = "block";
      thumb.style.height = `${thumbHeight}px`;
      thumb.style.top = `${scrollRatio * maxThumbTop}px`;
    };

    body.addEventListener("scroll", update);
    if (window.ResizeObserver) {
      new ResizeObserver(update).observe(body);
    }

    let dragStartY = 0;
    let dragStartScrollTop = 0;

    const onDragMove = (event) => {
      const { scrollHeight, clientHeight } = body;
      const trackHeight = track.clientHeight;
      const thumbHeight = thumb.clientHeight;
      const maxThumbTop = trackHeight - thumbHeight;
      if (maxThumbTop <= 0) {
        return;
      }
      const deltaY = event.clientY - dragStartY;
      const scrollableHeight = scrollHeight - clientHeight;
      body.scrollTop = dragStartScrollTop + (deltaY / maxThumbTop) * scrollableHeight;
    };

    const onDragEnd = () => {
      thumb.removeEventListener("pointermove", onDragMove);
      thumb.removeEventListener("pointerup", onDragEnd);
      thumb.removeEventListener("pointercancel", onDragEnd);
    };

    // Pointer Events (not mouse-only) so the thumb is actually draggable on
    // touch, not just mouse -- previously mousedown/mousemove/mouseup never
    // fire from a finger, leaving this an inert decoration on mobile and
    // forcing users to grab the bare, small message text box directly.
    // setPointerCapture keeps move/up events targeted at the thumb even as
    // a finger drifts off it mid-drag, which listening on the thumb alone
    // wouldn't otherwise give us.
    thumb.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      dragStartY = event.clientY;
      dragStartScrollTop = body.scrollTop;
      thumb.setPointerCapture(event.pointerId);
      thumb.addEventListener("pointermove", onDragMove);
      thumb.addEventListener("pointerup", onDragEnd);
      thumb.addEventListener("pointercancel", onDragEnd);
    });

    track.addEventListener("pointerdown", (event) => {
      if (event.target === thumb) {
        return;
      }
      const trackRect = track.getBoundingClientRect();
      const clickRatio = (event.clientY - trackRect.top) / trackRect.height;
      body.scrollTop = clickRatio * (body.scrollHeight - body.clientHeight);
    });

    update();
    return update;
  };

  // 1152px = 72rem, messageboard.css's own compact-mobile-layout breakpoint
  // (kept in sync by eye -- see that media query's own comment for why it's
  // 72rem and not a narrower phone-only width). Reveals "View full message"
  // only once the clamp has actually truncated the text, so a short message
  // that already fits in full doesn't get an offer to view more of nothing.
  // scrollHeight still measures the full (unclamped) content height even
  // with -webkit-line-clamp applied, so comparing it to clientHeight
  // remains a reliable truncation check.
  const MOBILE_QUERY = window.matchMedia("(max-width: 1152px)");

  const setupExpand = (slide) => {
    const body = slide.querySelector(".messageboard-body");
    const expandButton = slide.querySelector(".messageboard-expand");
    if (!body || !expandButton) {
      return () => {};
    }

    const update = () => {
      if (!MOBILE_QUERY.matches) {
        expandButton.classList.remove("is-visible");
        return;
      }
      const truncated = body.scrollHeight > body.clientHeight + 1;
      expandButton.classList.toggle("is-visible", truncated);
    };

    if (window.ResizeObserver) {
      new ResizeObserver(update).observe(body);
    }
    MOBILE_QUERY.addEventListener("change", update);

    update();
    return update;
  };

  document.querySelectorAll(".messageboard-slide").forEach((slide) => {
    setupScrollbar(slide);
    setupExpand(slide);
  });

  // Single shared dialog (same pattern as tool_preview_lightbox.js) --
  // populated from whichever slide's "View full message" was tapped,
  // rather than one modal per message.
  const modal = document.querySelector(".messageboard-modal");
  if (modal) {
    // the scrolling element -- .messageboard-modal-panel itself no longer
    // scrolls (see docs/claude_context/messageboard.md), only this
    // inner wrapper does.
    const modalScroll = modal.querySelector(".messageboard-modal-scroll");
    const modalTitle = modal.querySelector(".messageboard-modal-title");
    const modalDate = modal.querySelector(".messageboard-modal-date");
    const modalBody = modal.querySelector(".messageboard-modal-body");
    const modalSignature = modal.querySelector(".messageboard-modal-signature");
    const modalFade = modal.querySelector(".messageboard-modal-fade");
    const closeButton = modal.querySelector(".messageboard-modal-close");

    // Re-checked on scroll too (not just once on open) -- content that
    // exactly fits after opening might not once the browser's real
    // scrollbar (or a mobile keyboard, etc.) changes the scroll area's
    // own clientHeight, and this keeps the fade from lingering once
    // you've actually scrolled down past it.
    //
    // "near bottom" is judged against the fade's own height, not just the
    // last pixel -- with only a 1px margin, the fade stayed visible right
    // up until the literal last scroll position, which meant it spent its
    // last stretch overlapping/dimming real content (e.g. the sender's
    // signature) instead of blank space, reading as if that content were
    // being hidden rather than just "there's more below". Hiding it as
    // soon as the remaining scroll distance drops below the fade's own
    // height means it clears before ever sitting on top of that last bit.
    //
    // getComputedStyle, not offsetHeight -- .messageboard-modal-fade is
    // display:none until it's first toggled visible, and offsetHeight is
    // always 0 for a display:none element (no box has actually been laid
    // out to measure). That made this very first check, right when the
    // modal opens, use a height of 0 -- the same broken "only the literal
    // last pixel counts" behavior this was meant to fix, on exactly the
    // open-and-immediately-see-the-tail-end case the report was about.
    // getComputedStyle still reports the CSS-cascaded height regardless of
    // display, since it doesn't require an actual rendered box.
    const updateFade = () => {
      if (!modalScroll || !modalFade) {
        return;
      }
      const fadeHeight = parseFloat(getComputedStyle(modalFade).height) || 0;
      const nearBottom =
        modalScroll.scrollTop + modalScroll.clientHeight >= modalScroll.scrollHeight - fadeHeight;
      const overflowing = modalScroll.scrollHeight > modalScroll.clientHeight + 1;
      modalFade.classList.toggle("is-visible", overflowing && !nearBottom);
    };

    if (modalScroll) {
      modalScroll.addEventListener("scroll", updateFade);
    }
    // .messageboard-modal-panel's height is 85dvh (messageboard.css) --
    // dvh tracks the mobile browser's address bar showing/hiding, which
    // changes the modal's actual available height without ever firing a
    // "scroll" event on modalScroll. Without also listening here, the
    // fade's visibility could go stale relative to whatever the panel's
    // real current size actually is right after the browser chrome
    // settles. visualViewport (where available) reports the real
    // interactive viewport more reliably than the bare window resize
    // event for this specific case.
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", updateFade);
    } else {
      window.addEventListener("resize", updateFade);
    }

    const openModal = (slide) => {
      const title = slide.querySelector("h2");
      const date = slide.querySelector(".messageboard-date");
      const body = slide.querySelector(".messageboard-body");
      const signature = slide.querySelector(".messageboard-signature");

      modalTitle.textContent = title ? title.textContent : "";
      modalDate.textContent = date ? date.textContent : "";
      // .messageboard-body's content is already server-rendered/sanitized
      // richtext (see messageboard/slide.html), not raw user input being
      // re-injected here -- just relocating already-safe markup into the
      // modal, same as it already rendered in the card.
      modalBody.innerHTML = body ? body.innerHTML : "";
      if (signature) {
        modalSignature.innerHTML = signature.innerHTML;
        modalSignature.hidden = false;
      } else {
        modalSignature.innerHTML = "";
        modalSignature.hidden = true;
      }

      modal.hidden = false;
      document.body.classList.add("messageboard-modal-open");
      if (modalScroll) {
        modalScroll.scrollTop = 0;
      }
      updateFade();
      closeButton.focus();
    };

    const closeModal = () => {
      modal.hidden = true;
      document.body.classList.remove("messageboard-modal-open");
    };

    document.querySelectorAll(".messageboard-expand").forEach((button) => {
      button.addEventListener("click", () => {
        const slide = button.closest(".messageboard-slide");
        if (slide) {
          openModal(slide);
        }
      });
    });

    closeButton.addEventListener("click", closeModal);

    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        closeModal();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !modal.hidden) {
        closeModal();
      }
    });
  }

  document.querySelectorAll(".messageboard").forEach((board) => {
    const slides = Array.from(board.querySelectorAll(".messageboard-slide"));
    const dots = Array.from(board.querySelectorAll(".messageboard-dot"));
    const prevButton = board.querySelector(".messageboard-prev");
    const nextButton = board.querySelector(".messageboard-next");
    if (slides.length < 2) {
      return;
    }

    let currentIndex = slides.findIndex((slide) => slide.classList.contains("active"));
    if (currentIndex < 0) {
      currentIndex = 0;
    }
    if (dots[currentIndex]) {
      dots[currentIndex].classList.add("seen");
    }
    let rafId = null;

    const showSlide = (index) => {
      currentIndex = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => slide.classList.toggle("active", i === currentIndex));
      dots.forEach((dot, i) => {
        dot.classList.toggle("active", i === currentIndex);
        if (i === currentIndex) {
          dot.classList.add("seen");
        } else if (dot.classList.contains("seen")) {
          dot.style.setProperty("--progress", 100);
        }
      });
    };

    const restartAutoRotate = () => {
      if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
      }
      if (!board.dataset.autorotate) {
        return;
      }
      const durationSeconds = parseFloat(slides[currentIndex].dataset.duration);
      const interval = durationSeconds > 0 ? durationSeconds * 1000 : 8000;
      const activeDot = dots[currentIndex];
      if (activeDot) {
        activeDot.style.setProperty("--progress", 0);
      }
      const startTime = performance.now();

      const tick = (now) => {
        const elapsed = now - startTime;
        const percent = Math.min((elapsed / interval) * 100, 100);
        if (activeDot) {
          activeDot.style.setProperty("--progress", percent);
        }
        if (elapsed >= interval) {
          showSlide(currentIndex + 1);
          restartAutoRotate();
        } else {
          rafId = requestAnimationFrame(tick);
        }
      };
      rafId = requestAnimationFrame(tick);
    };

    if (prevButton) {
      prevButton.addEventListener("click", () => {
        showSlide(currentIndex - 1);
        restartAutoRotate();
      });
    }

    if (nextButton) {
      nextButton.addEventListener("click", () => {
        showSlide(currentIndex + 1);
        restartAutoRotate();
      });
    }

    dots.forEach((dot, i) => {
      dot.addEventListener("click", () => {
        showSlide(i);
        restartAutoRotate();
      });
    });

    restartAutoRotate();
  });
});
