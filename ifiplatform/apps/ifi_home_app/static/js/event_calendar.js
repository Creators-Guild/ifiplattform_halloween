// Mobile behavior for the week-calendar view of a parent EventPage's timed
// sub_events (event_page.html + event_calendar_grid.html, positions from
// EventPage.calendar_days):
//   1. Single-day view + prev/next paging for the INLINE grid only, gated
//      to narrow viewports (same 45rem breakpoint as the horizontal-scroll
//      CSS it replaces there).
//   2. Two-tap select-then-navigate on any .event-calendar-block (inline
//      grid AND the modal's own grid copy), gated to devices with no real
//      mouse hover (matchMedia("(hover: hover) and (pointer: fine)"), same
//      gate dropdown_menu.js uses) -- independent of the viewport gate
//      above, since a wide touch tablet still has no hover even above
//      45rem.
//   3. "View whole week" full-screen modal showing the un-paged grid,
//      horizontally scrollable with a visible scrollbar and left/right
//      edge fade hints -- mirrors messageboard.js's modal open/close and
//      updateFade() mechanics, adapted to the horizontal axis.
//   4. Horizontal swipe paging on the INLINE grid (not the modal's own
//      copy, which uses horizontal movement for its own pan-across-the-
//      week scrolling instead): swipe left for the next day, right for
//      the previous one -- the standard mobile calendar gesture. Doesn't
//      need any scroll-boundary gating the way a vertical swipe would,
//      since it's orthogonal to the page's own vertical scroll.
if (!window.__ifiEventCalendarInit) {
  window.__ifiEventCalendarInit = true;

  const MOBILE_QUERY = window.matchMedia("(max-width: 45rem)");
  const HOVER_QUERY = window.matchMedia("(hover: hover) and (pointer: fine)");

  const deselectAllBlocks = () => {
    document.querySelectorAll(".event-calendar-block.is-selected").forEach((block) => {
      block.classList.remove("is-selected");
    });
  };

  // -- Single-day paging (inline section only, mobile only) ---------------
  const SWIPE_MIN_DISTANCE = 50; // px -- below this, treat it as a tap or vertical scroll, not a day-change swipe
  const SWIPE_MAX_OFF_AXIS = 60; // px -- a swipe with more vertical drift than this is a scroll, not a page-turn

  const initDayPaging = (section) => {
    const grid = section.querySelector(".event-calendar");
    const headerDays = Array.from(section.querySelectorAll(".event-calendar-header-day"));
    const dayColumns = Array.from(section.querySelectorAll(".event-calendar-day"));
    // Two copies of the pager (event_page.html: one above the grid, one
    // below) -- both kept in sync so either can be used to page.
    const prevButtons = Array.from(section.querySelectorAll(".event-calendar-pager-prev"));
    const nextButtons = Array.from(section.querySelectorAll(".event-calendar-pager-next"));
    if (!grid || dayColumns.length === 0) {
      return;
    }

    let currentIndex = 0;

    const findInitialDayIndex = () => {
      const now = new Date();
      const todayIso = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
      const exact = dayColumns.findIndex((col) => col.dataset.dayDate === todayIso);
      if (exact >= 0) {
        return exact;
      }
      // No exact match (today falls outside this event's own date range)
      // -- land on the first still-upcoming day, or the last day if the
      // whole thing is already over.
      const upcoming = dayColumns.findIndex((col) => col.dataset.dayDate > todayIso);
      return upcoming >= 0 ? upcoming : dayColumns.length - 1;
    };

    const updatePagerState = () => {
      prevButtons.forEach((button) => { button.disabled = currentIndex <= 0; });
      nextButtons.forEach((button) => { button.disabled = currentIndex >= dayColumns.length - 1; });
    };

    const setCurrentDay = (index) => {
      currentIndex = Math.min(Math.max(index, 0), dayColumns.length - 1);
      headerDays.forEach((el, i) => {
        el.classList.toggle("event-calendar-header-day--current", i === currentIndex);
      });
      dayColumns.forEach((el, i) => {
        el.classList.toggle("event-calendar-day--current", i === currentIndex);
      });
      updatePagerState();
      deselectAllBlocks();
    };

    const syncPagedState = () => {
      grid.classList.toggle("event-calendar--paged", MOBILE_QUERY.matches);
      setCurrentDay(currentIndex);
    };

    currentIndex = findInitialDayIndex();
    MOBILE_QUERY.addEventListener("change", syncPagedState);
    syncPagedState();

    prevButtons.forEach((button) => {
      button.addEventListener("click", () => setCurrentDay(currentIndex - 1));
    });
    nextButtons.forEach((button) => {
      button.addEventListener("click", () => setCurrentDay(currentIndex + 1));
    });

    // -- Horizontal swipe paging (mobile only) -----------------------------
    let touchStart = null;

    section.addEventListener("touchstart", (event) => {
      if (!MOBILE_QUERY.matches || event.touches.length !== 1) {
        touchStart = null;
        return;
      }
      touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
    }, { passive: true });

    section.addEventListener("touchend", (event) => {
      if (touchStart === null || !MOBILE_QUERY.matches) {
        return;
      }
      const touch = event.changedTouches[0];
      const deltaX = touch.clientX - touchStart.x;
      const deltaY = touch.clientY - touchStart.y;
      touchStart = null;

      if (Math.abs(deltaX) < SWIPE_MIN_DISTANCE || Math.abs(deltaY) > SWIPE_MAX_OFF_AXIS) {
        return;
      }
      if (deltaX < 0) {
        setCurrentDay(currentIndex + 1); // swiped left -- next day
      } else {
        setCurrentDay(currentIndex - 1); // swiped right -- previous day
      }
    }, { passive: true });
  };

  // -- Two-tap select-then-navigate (no-hover devices, all grid copies) --
  const initTwoTapSelect = () => {
    if (HOVER_QUERY.matches) {
      return;
    }
    document.querySelectorAll(".event-calendar-block").forEach((block) => {
      block.addEventListener("click", (event) => {
        // event.detail is 0 for a keyboard-triggered click (Enter/Space on
        // a focused <a>), >=1 for a real pointer tap -- keyboard
        // activation always navigates immediately.
        if (event.detail === 0) {
          return;
        }
        if (!block.classList.contains("is-selected")) {
          event.preventDefault();
          deselectAllBlocks();
          block.classList.add("is-selected");
        }
      });
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest(".event-calendar-block")) {
        deselectAllBlocks();
      }
    });
  };

  // -- "View whole week" modal --------------------------------------------
  const initModal = () => {
    const modal = document.querySelector(".event-calendar-modal");
    const openButton = document.querySelector(".event-calendar-view-whole-week");
    if (!modal || !openButton) {
      return;
    }
    const modalScroll = modal.querySelector(".event-calendar-modal-scroll");
    const closeButton = modal.querySelector(".event-calendar-modal-close");
    const fadeLeft = modal.querySelector(".event-calendar-modal-fade-left");
    const fadeRight = modal.querySelector(".event-calendar-modal-fade-right");

    const updateFades = () => {
      if (!modalScroll) {
        return;
      }
      const { scrollLeft, scrollWidth, clientWidth } = modalScroll;
      if (fadeLeft) {
        fadeLeft.classList.toggle("is-visible", scrollLeft > 1);
      }
      if (fadeRight) {
        fadeRight.classList.toggle("is-visible", scrollLeft + clientWidth < scrollWidth - 1);
      }
    };

    const openModal = () => {
      modal.hidden = false;
      document.body.classList.add("event-calendar-modal-open");
      if (modalScroll) {
        modalScroll.scrollLeft = 0;
      }
      updateFades();
    };
    const closeModal = () => {
      modal.hidden = true;
      document.body.classList.remove("event-calendar-modal-open");
    };

    openButton.addEventListener("click", openModal);
    if (closeButton) {
      closeButton.addEventListener("click", closeModal);
    }
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
    if (modalScroll) {
      modalScroll.addEventListener("scroll", updateFades);
    }
    window.addEventListener("resize", updateFades);
  };

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".event-calendar-section").forEach(initDayPaging);
    initTwoTapSelect();
    initModal();
  });
}
