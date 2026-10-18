"""Helper notes for the pilot issues, shown with the solution on the site
(load_event_solutions). Phase 1 notes come from build_phase1_solutions.py."""

NOTE_ISSUE = (
    "Correct: one new .txt file with exactly the name from the issue. Line 1 "
    "is the title, then the text, and an optional last line starting with "
    "'-- ' as the signature. Any kind, funny text is fine.\n\n"
    "Check: the note shows on http://localhost:8000/halloween/board/.\n\n"
    "Common mistakes: a different file name (then it can clash with another "
    "note issue: rename it), a .txt.txt name from Windows, the file in the "
    "wrong folder, or a normal dash instead of '— ' for the signature (then "
    "the signature just shows as text: fine)."
)

NOTES = {
    "P4": NOTE_ISSUE,
    "C34": NOTE_ISSUE,
    "C35": NOTE_ISSUE,
    "C36": NOTE_ISSUE,
    "K1": (
        "Correct: cobweb.svg in static/images/halloween/, and body gets "
        "background-image with the path ../../images/halloween/cobweb.svg, "
        "no-repeat, top left. background-image doesn't clash with the dark home "
        "page (that one sets background-color).\n\n"
        "Check: a faint web in the top-left corner of every page. Not showing? "
        "Open http://localhost:8000/static/images/halloween/cobweb.svg: if "
        "that fails, the file is in the wrong place; if it works, the CSS path "
        "is wrong.\n\n"
        "Common mistakes: the path written from the repo root instead of from "
        "the CSS file, the web on html (body's own background covers it), "
        "background-attachment: fixed (it then vanishes when you scroll), "
        "a stroke colour that vanishes on the dark home page or the light pages."
    ),
    "C1": (
        "Correct: :root:has(#home-shortcuts) and its body get a dark "
        "background-color, and the news heading and the menu links above the "
        "shortcuts get a light color. Any dark colour is fine.\n\n"
        "Check: the home page is dark all the way down (scroll to the "
        "bottom), all text on it is readable, and an article page is still "
        "light.\n\n"
        "Common mistakes: plain html, body (darkens every page, and the "
        "article and study text becomes unreadable), only body (the page "
        "turns light again below the first screen), forgetting the light "
        "text colours."
    ),
    "K3": (
        "Correct: a .ghost rule with animation: ghost-float <time> <timing> "
        "infinite, and some opacity. Don't touch scaffold.css.\n\n"
        "Check: wait 20 seconds on any page. The ghost floats from left to "
        "right and disappears.\n\n"
        "Common mistakes: the animation name doesn't match the @keyframes "
        "name, a missing 's' after the time (20 instead of 20s), editing "
        "scaffold.css."
    ),
    "K5": (
        "Correct: account_icon.html still starts with the same <svg "
        "class=\"profile-icon\" ...> line, and inside is a skull: an outline "
        "path plus eyes, nose and teeth.\n\n"
        "Check: log in, look at the top right of the header, and click the "
        "skull: the account menu must still open.\n\n"
        "Common mistakes: deleting the <svg> line or its class (the icon "
        "then has no size), shapes without fill (invisible)."
    ),
    "K14": (
        "Correct: at least four rules, all starting with .article-page or "
        ".article-meta-item, so only article pages change.\n\n"
        "Check: an article looks Halloween; the home page doesn't change.\n\n"
        "Common mistakes: plain h1 or a selectors (they change every page), "
        "text that's hard to read on the new background."
    ),
    "K15": (
        "Correct: at least four rules on .event-page, .event-meta, "
        ".event-type-badge or .event-signup-link.\n\n"
        "Check: open an event from 'Happening at Ifi'; other pages don't "
        "change.\n\n"
        "Common mistakes: .event-type-badge is also used on the home page "
        "events box, so a change there shows on the home page too. Fine if "
        "it's on purpose."
    ),
    "K16": (
        "Correct: at least four rules on .auth-card, .auth-links and things "
        "inside them.\n\n"
        "Check: log out, then open /account/login and /account/signin.\n\n"
        "Borders: one plain black border all round (border: 2px solid #000) "
        "also replaces the site's thick pink top edge. A focused field needs "
        "border-color as well as outline, or it shows turquoise and orange.\n\n"
        "Common mistakes: styling plain input or .btn (that changes every "
        "form and button on the site), editing the templates' text (another "
        "file)."
    ),
    "K17": (
        "Correct: at least four rules on .under-development and the classes "
        "inside it (h1, -status, -joke, a). On this site /study/ is the "
        "'Ahaha, nei' joke page, not a real study home.\n\n"
        "Check: http://localhost:8000/study/ (reload for a new excuse).\n\n"
        "Common mistakes: plain h1 or a (changes every page), styling "
        ".study_layout or .studytools-btn (that page isn't shown on this site)."
    ),
    "K19": (
        "Correct: a loop that prints a pumpkin width characters wide, with "
        "eyes and a mouth; --size changes it. Any shape is fine.\n\n"
        "Check: python manage.py carve_pumpkin, then --size 1 and --size 6.\n\n"
        "Common mistakes: the file not in management/commands/ (\"Unknown "
        "command\"), a single backslash in a Python string (\\ is needed), "
        "print() instead of self.stdout.write (works, but not in tests)."
    ),
    "K28": (
        "Correct: inside @media (prefers-reduced-motion: reduce), .ghost "
        "gets animation: none.\n\n"
        "Check: DevTools → Rendering → emulate prefers-reduced-motion: "
        "reduce. The ghost must stop.\n\n"
        "Common mistakes: the rule outside the media query (the ghost then "
        "stops for everyone), display: none on body by accident."
    ),
    "K30": (
        "The planted bug: the English form's hidden input has "
        "value=\"/\" instead of value=\"{{ en_next }}\".\n\n"
        "Check: on an article, press English: same article, in English.\n\n"
        "If they're stuck: compare the two forms line by line."
    ),
    "Q1": (
        "Correct: at least 8 FORTUNES, pick_fortune uses clean_name, a "
        "number from the letters and % len(FORTUNES). test_fortune.py with "
        "the last test filled in. Styled fortune.css.\n\n"
        "Check: the same name gives the same fortune, with spaces or "
        "capitals; ifi test passes.\n\n"
        "Common mistakes: random.choice (a different fortune every reload), "
        "testing with æøå names (that's the separate 👻 issue), changing "
        "fortune_names.py (belongs to the bug issue)."
    ),
    "Q2": (
        "Correct: 6+ words in each list; spooky_name picks one of each from "
        "the name and returns f\"{first} {name} {last}\"; tests filled in.\n\n"
        "Check: Kari gets the same spooky name every time; ifi test passes.\n\n"
        "Common mistakes: random (not stable), an IndexError from forgetting "
        "% len(...)."
    ),
    "Q3": (
        "Correct: nothing → 'Just water. Spooky.', 4+ special combinations, "
        "a general sentence with the count; tests filled in.\n\n"
        "Check: tick bat wing + coffee and Brew, then other mixes.\n\n"
        "Common mistakes: comparing lists instead of sets (then the order "
        "matters and the order test fails)."
    ),
    "Q28": (
        "Correct: clean_name swaps æ/ø/å, then unicodedata.normalize('NFKD') "
        "and .encode('ascii', 'ignore'); never crashes. test_fortune_names.py "
        "with 3+ tests.\n\n"
        "Check: /halloween/fortune/?name=Åse, Bjørn and René don't crash.\n\n"
        "Common mistakes: only .encode('ascii', 'ignore') (Åse becomes 'se', "
        "and the test wants 'ase'), changing views/fortune.py (another "
        "issue's file)."
    ),
    "Q5": (
        "Correct: showBat puts one 🦇 in a random hole, a click on a bat "
        "scores, the timer moves the bat every second and ends the game at 0. "
        "A 3×3 grid in the CSS.\n\n"
        "Check: play a round on /halloween/whack-a-bat/.\n\n"
        "Common mistakes: forgetting clearInterval (Start twice → double "
        "speed), comparing textContent with a different emoji than the one "
        "put in."
    ),
    "Q7": (
        "Correct: the cards shuffle, a turned card shows its symbol, two "
        "turned cards count a try, pairs stay found, others turn back after "
        "~800 ms, and no third card turns meanwhile. A 4-column grid.\n\n"
        "Check: play a game on /halloween/memory/; click fast to test the "
        "'no third card' rule.\n\n"
        "Common mistakes: clicking the same card twice counts as a pair "
        "(check open.includes(card))."
    ),
    "Q15": (
        "Correct: 404.html still extends home_base and keeps the link home "
        "with {% url 'ifi_home' %}; texts in {% trans %}; page_404.css rules "
        "all start with .page-404; motion off under reduced motion.\n\n"
        "Check: /halloween/404-preview/ (not a random URL: with DEBUG on "
        "Django shows its own page there).\n\n"
        "Common mistakes: plain h1/p rules in page_404.css (that file loads "
        "on every page, so it would restyle the whole site)."
    ),
    "Q22": (
        "Correct: spooky_counts counts only SPOOKY_WORDS; handle adds up "
        "title + strip_tags(intro) of live articles, prints most_common and "
        "the spookiest article; tests include running on an empty database.\n\n"
        "Check: python manage.py halloween_stats, and ifi test.\n\n"
        "Common mistakes: forgetting strip_tags (HTML tags count as words), "
        "crashing when no article matches (spookiest is None)."
    ),
    "Q23": (
        "Correct: mascot.svg (under ~20 KB) and mascot.html with an <img> "
        "using {% static %} and a real alt text.\n\n"
        "Check: /halloween/ shows the mascot under the heading.\n\n"
        "Common mistakes: a missing {% load static %} (TemplateSyntaxError), "
        "a huge SVG export with embedded bitmaps, alt=\"\" or alt=\"image\"."
    ),
    "Q29": (
        "Correct: pointer events move notes with the translate property (the "
        "tilt in transform stays), spots saved in localStorage by title "
        "inside try/catch, a 'Tidy the board' button made in JS.\n\n"
        "Check: drag a note, reload, it stays; Tidy puts everything back; a "
        "private window still lets you drag.\n\n"
        "Common mistakes: setting style.transform (kills the tilt), "
        "forgetting touch-action: none (dragging scrolls on phones)."
    ),
    "SET-moon": "The parent of the three moon issues. It earns nothing itself; close it when all three are merged.",
    "SET-pages": "The parent of the four page restyles. It earns nothing itself; close it when all four are merged.",
    "SET-fortune": "The parent of the fortune booth pages. It earns nothing itself; close it when all four are merged.",
    "SET-arcade": "The parent of the five games. It earns nothing itself; close it when all five are merged.",
    "SET-spider": "The parent of the four spider issues. It earns nothing itself; close it when all four are merged.",
    "SET-right": "The parent of the Instagram and >OUTPUT issues. It earns nothing itself; close it when all three are merged.",
}

NOTES.update({
    "C2": (
        "Correct: .ifiplatform-logo gets an orange color and font-family: "
        "var(--font-spooky). Any colour and size is fine.\n\n"
        "Check: the site name top left, on any page; it stays on one line.\n\n"
        "Common mistakes: a typo in var(--font-spooky) (the font silently "
        "falls back), a font-size so big the name wraps."
    ),
    "C3": (
        "Correct: .header-tagline gets an orange colour and the spooky font.\n\n"
        "Check: 'Trick or Treat?' under the site name.\n\n"
        "Common mistakes: styling 'button' instead of .header-tagline (that "
        "restyles every button on the site)."
    ),
    "C4": (
        "Correct: .nav_link purple and spooky, a text-shadow glow on :hover "
        "and on .nav_link.active.\n\n"
        "Check: hover the header links; the current page's link glows.\n\n"
        "Common mistakes: box-shadow instead of text-shadow (a glowing box), "
        "a hover rule without the colon (.nav_link hover)."
    ),
    "C5": (
        "Correct: .lang-btn orange text and border; .lang-btn.active and "
        ":hover filled orange with dark text.\n\n"
        "Check: both buttons top right; switching language still works.\n\n"
        "Common mistakes: forgetting border-color (a turquoise frame stays)."
    ),
    "C6": (
        "Correct: one rule on .home-navbar .link .drop-option: small, "
        "underline, uppercase.\n\n"
        "Check: the row above the shortcut cards on the home page; hover one: "
        "the dropdown's own links must keep their normal look.\n\n"
        "Common mistakes: plain .drop-option (also changes the dropdown "
        "contents and the side menu), a white colour (unreadable before the "
        "dark home page issue is merged; that issue sets the colour)."
    ),
    "C7": (
        "Correct: .sidemenu_container and .sidemenu both get the same dark "
        "teal background.\n\n"
        "Check: the strip on the left, all the way down; hover it to open.\n\n"
        "Common mistakes: only one of the two selectors (two shades of "
        "turquoise), a colour so dark the black ☰ icon vanishes."
    ),
    "C8": (
        "Correct: #home-shortcuts .shortcut-card grey with border: 2px solid "
        "#000, plus a hover/focus rule with a lighter grey.\n\n"
        "Check: hover a card (it must not turn turquoise), and Tab to one.\n\n"
        "Common mistakes: leaving out the hover rule (cards flash turquoise), "
        "a border colour other than black."
    ),
    "C9": (
        "Correct: #home-shortcuts .shortcut-title gets font-family: "
        "var(--font-spooky).\n\n"
        "Check: the six card titles; make the window narrow: long titles "
        "switch to their short version (shortcut_fit.js), that's expected.\n\n"
        "Common mistakes: styling .shortcut-main (also changes the icons' "
        "box)."
    ),
    "C10": (
        "Correct: a @keyframes with rotate, played on the card's :hover / "
        ":has(:focus-visible), and switched off in a "
        "prefers-reduced-motion: reduce block.\n\n"
        "Check: hover a card: one short wiggle.\n\n"
        "Common mistakes: transform: rotate in the keyframes is fine too; "
        "a keyframes name that doesn't match the animation name."
    ),
    "C17": (
        "Correct: .messageboard grey, box-shadow: none, and no border (the "
        "message board stays borderless).\n\n"
        "Check: the 'Velkommen!' box on the home page.\n\n"
        "Common mistakes: adding a border (the design keeps this box without "
        "one)."
    ),
    "C18": (
        "Correct: .newsbar-heading--news gets the spooky font, a bigger "
        "size, centred. No colour (the dark home page issue sets it).\n\n"
        "Check: 'Siste nyheter' on the home page.\n\n"
        "Common mistakes: color: white (invisible on the light page until "
        "the dark home page issue is merged)."
    ),
    "C20": (
        "Correct: .eventsbox_container grey with border: 2px solid #000 and "
        "box-shadow: none; its h2 without underline.\n\n"
        "Check: 'Happening at Ifi' in the right column.\n\n"
        "Common mistakes: a coloured or thicker border, styling .side-box "
        "(that changes the other boxes too, which belong to other issues)."
    ),
    "C22": (
        "Correct: smaller .home-eventsbox-day-heading and "
        ".home-eventsbox-time, extra bold .home-eventsbox-title.\n\n"
        "Check: the events box; all text still readable.\n\n"
        "Common mistakes: a font-size so small it's unreadable (below "
        "about 0.75rem)."
    ),
    "C23": (
        "Correct: .output-box grey with border: 2px solid #000, centred.\n\n"
        "Check: the >OUTPUT box at the bottom of the right column.\n\n"
        "Common mistakes: styling .side-box (changes the opening hours box "
        "too)."
    ),
    "C27": (
        "Correct: .spider gets a size; .spider__thread a 1px line; "
        ".spider__body a red oval with its head in ::before. Don't touch "
        "scaffold.css.\n\n"
        "Check: top left of any page; links under the spider still click "
        "(scaffold.css gives it pointer-events: none).\n\n"
        "Common mistakes: forgetting position: absolute on the parts (they "
        "pile up at the top), content: \"\" missing on ::before (no head)."
    ),
    "C28": (
        "Correct: spider_legs.svg in static/images/halloween/, and "
        ".spider__legs with the legs as background: "
        "url(\"../../images/halloween/spider_legs.svg\").\n\n"
        "Check: legs at the top left. Not showing? Open "
        "http://localhost:8000/static/images/halloween/spider_legs.svg: if "
        "that fails the file is in the wrong place, otherwise the CSS path "
        "is wrong.\n\n"
        "Common mistakes: the path written from the repo root, a .svg.txt "
        "file name on Windows."
    ),
    "C29": (
        "Correct: @keyframes spider-swing with rotate, and .spider with "
        "transform-origin: 50% 0 and the animation.\n\n"
        "Check: the spider swings (needs C27/C28 merged to see anything).\n\n"
        "Common mistakes: no transform-origin (the spider spins around its "
        "middle instead of swinging from the thread)."
    ),
    "C30": (
        "Correct: inside @media (prefers-reduced-motion: reduce), .spider "
        "gets animation: none.\n\n"
        "Check: DevTools → Rendering → prefers-reduced-motion: reduce.\n\n"
        "Common mistakes: the rule outside the media query (stops the swing "
        "for everyone)."
    ),
    "C31": (
        "The planted bug: in eventsbox.html the {% trans %} texts for "
        "\"today\" and \"tomorrow\" are swapped.\n\n"
        "Check: the day headings in 'Happening at Ifi' (only visible if "
        "there are events today or tomorrow in the database; otherwise read "
        "the two lines).\n\n"
        "Common mistakes: swapping the time_tag values instead of the texts "
        "(works too), breaking the {% if %} / {% elif %} chain."
    ),
    "C33": (
        "Correct: the hero image's alt is just {{ article.hero_image_alt }} "
        "(no default), and the placeholder image has alt=\"\".\n\n"
        "Check: the cards look the same; Inspect an image: alt is empty or "
        "a real description.\n\n"
        "Common mistakes: removing the alt attribute completely (screen "
        "readers then read the file name: worse)."
    ),
    "K2": (
        "Correct: trees.svg with at least four <use href=\"#tree\"> copies, "
        "and .treeline with a height and the SVG as background (center "
        "bottom / cover, no-repeat).\n\n"
        "Check: scroll to the bottom of any page, wide and narrow window.\n\n"
        "Common mistakes: trees floating above the ground (the translate "
        "doesn't match the scale), the CSS path from the repo root."
    ),
    "K4": (
        "Correct: the given CSS, and JS that adds spider--startled on click "
        "and removes it after ~1.5 s with setTimeout (clearTimeout on a new "
        "click).\n\n"
        "Check: click the spider's body (needs the spider set merged).\n\n"
        "Common mistakes: listening on document instead of the spider, "
        "toggle instead of add (a second click sends it down early)."
    ),
    "K6": (
        "Correct: the long .home-layout .maincontent .suggestions-row "
        ".newsbar-layout selector, grey, no shadow, no border, "
        "repeat(4, minmax(0, 1fr)); two columns under 45rem.\n\n"
        "Check: the news on the home page, wide and narrow.\n\n"
        "Common mistakes: a shorter selector that loses to the site's own "
        "CSS (nothing changes), a border on the news box."
    ),
    "K7": (
        "Correct: .hours-box grey with a black 2px border, lines between "
        ".hours-place, pill-shaped .hours-status in dark green and dark "
        "red.\n\n"
        "Check: the 'Open now?' box; both badges readable.\n\n"
        "Common mistakes: light green/red with white text (low contrast), "
        "styling .side-box (changes the other boxes)."
    ),
    "K8": (
        "Correct: 3+ real places with seven entries each, Monday first, and "
        "the source pages and date in the docstring. Any real places are "
        "fine; hours change by semester.\n\n"
        "Check: the box shows today's hours. Compare one place with its web "
        "page.\n\n"
        "Common mistakes: six or eight entries (an IndexError or the wrong "
        "day), Sunday first, times like \"9:00\" without the leading zero "
        "(then the text comparison in is_open breaks: \"9:00\" > \"10:00\")."
    ),
    "K9": (
        "Correct: grey .insta-box without border, five columns, tiles with "
        "position: relative and the caption absolute at the bottom on a "
        "dark gradient, zoom on hover.\n\n"
        "Check: the Instagram row under the news.\n\n"
        "Common mistakes: no position: relative on .insta-tile (all captions "
        "end up at the bottom of the box), a border on the box."
    ),
    "K10": (
        "Correct: five new 160×200 SVGs and, in instagram.html, a real alt "
        "and caption per tile, still in {% trans %}, classes and paths "
        "unchanged.\n\n"
        "Check: the row shows five different pictures.\n\n"
        "Common mistakes: alt = the caption (alt says what's in the "
        "picture), huge exported SVGs with embedded bitmaps."
    ),
    "K11": (
        "Correct: output_cover.svg redrawn, 300×400, title readable, 4+ "
        "shapes and a cover line.\n\n"
        "Check: the >OUTPUT box at the bottom of the right column.\n\n"
        "Common mistakes: drawing over the title, a missing xmlns (the "
        "picture doesn't show)."
    ),
    "K12": (
        "Correct: a click listener on .header-tagline that shows a random "
        "trick or treat, and puts the original text back after ~4 s "
        "(clearTimeout on a new click). aria-live set.\n\n"
        "Check: click 'Trick or Treat?' a few times.\n\n"
        "Common mistakes: hard-coding \"Trick or Treat?\" to put back (wrong "
        "on the Norwegian site: save the original text), an index from "
        "Math.random() without Math.floor."
    ),
    "K13": (
        "Correct: a keydown listener that ignores inputs, keeps the last 3 "
        "keys, and spins .page-layout with element.animate on \"boo\", "
        "skipped with prefers-reduced-motion.\n\n"
        "Check: click on the page (not a field), type b o o.\n\n"
        "Common mistakes: comparing event.key without toLowerCase (caps "
        "lock), spinning document.body (the fixed decorations jump)."
    ),
    "K20": (
        "Correct: templatetags/spooky.py with a filter that alternates the "
        "case of letters only, and adds '... 👻'; spooky_demo.html loads it "
        "and shows the translated welcome text through it.\n\n"
        "Check: /halloween/ (restart runserver after adding templatetags/).\n\n"
        "Common mistakes: counting spaces in the alternation (doesn't match "
        "the example, but fine), a TemplateSyntaxError because the server "
        "wasn't restarted."
    ),
    "K21": (
        "Correct: countdown_tags.py returns the days to this year's or next "
        "year's 31 October (0 on the day); the partial shows it with "
        "blocktrans count.\n\n"
        "Check: /nb/arrangementer/ (restart runserver after adding "
        "templatetags/).\n\n"
        "Common mistakes: a negative number after Halloween, date.today() "
        "(server time, UTC) instead of Oslo time: off by one late at night."
    ),
    "K22": (
        "Correct: 5+ words per list, make_costume with random.choice from "
        "each list, the {% if costume %} card in the template, and the "
        "styled card.\n\n"
        "Check: /halloween/costume/, press the button a few times.\n\n"
        "Common mistakes: random.choice on the whole sentence list, the "
        "card shown without {% if %} (an empty card before the first press)."
    ),
    "K27": (
        "Correct: darker colours (4.5:1 on #b4b4b8 and on white) for "
        ".articlecard-meta, .messageboard-date, .home-eventsbox-time, the "
        "sub-event text, and .home-eventsbox-view-all.\n\n"
        "Check: DevTools colour picker shows the contrast ratio with a ✓.\n\n"
        "Common mistakes: making the boxes lighter instead (those are other "
        "issues' files), a colour that only works on grey."
    ),
    "K29": (
        "The planted bug: event_page.html shows {% now \"l\" %} (today's "
        "weekday) before the event date. Fix: {{ page.event_date|date:\"l\" }}.\n\n"
        "Check: Halloweenfest (31 Oct 2026) says lørdag/Saturday.\n\n"
        "If they're stuck: what does {% now %} show, and what's the "
        "event's own date variable?"
    ),
    "K31": (
        "The planted bug: hub.py sorts by page[1] (the emoji) instead of "
        "page[2] (the title).\n\n"
        "Check: /halloween/ shows the board, then Bat snake, Costume "
        "generator, Countdown...; ifi test passes "
        "(test_hub_shows_every_page_once_board_first).\n\n"
        "If they're stuck: print one item of PAGES and count the positions "
        "from 0."
    ),
    "K34": (
        "Correct: the given keyframes, an animation on .bat-flock span, "
        "--fly-x/--fly-y per nth-child, delays, and animation: none under "
        "prefers-reduced-motion.\n\n"
        "Check: watch the moon for ~10 s on any page.\n\n"
        "Common mistakes: forgetting the delays (all three fly as one), "
        "editing scaffold.css."
    ),
    "Q4": (
        "Correct: tell_story returns None if any word is empty, otherwise 3+ "
        "paragraphs using every word; test_story.py with the last test "
        "filled in; styled story.css.\n\n"
        "Check: /halloween/story/ with all six words, then with one empty.\n\n"
        "Common mistakes: building the story with + and forgetting a word, "
        "returning one long string (the template loops over paragraphs: a "
        "string shows one letter per paragraph)."
    ),
    "Q6": (
        "Correct: spawnZombie makes a .zt-zombie with a random word at a "
        "random height; moveZombies moves them left, removes biters and "
        "loses lives; typing a word removes that zombie and scores. Styled "
        "field and zombies.\n\n"
        "Check: play a round on /halloween/zombie-typing/.\n\n"
        "Common mistakes: no position: relative on .zt-field (zombies fly "
        "off over the page), removing the element but not the entry in "
        "zombies (lives keep dropping)."
    ),
    "Q8": (
        "Correct: isNextToEmpty uses rows and columns, move swaps and checks "
        "for SOLVED, shuffle makes ~200 allowed moves; the moon picture via "
        "background-size 300% and --col/--row.\n\n"
        "Check: Shuffle, then solve a few moves; spot 2 must not swap with "
        "spot 3.\n\n"
        "Common mistakes: Math.abs(spot - empty) === 1 alone (wraps around "
        "rows), shuffling the array directly (can be unsolvable)."
    ),
    "Q9": (
        "Correct: placeCandy avoids the snake, step moves the head, grows on "
        "candy, pops the tail otherwise, and ends on walls or itself. A "
        "15-column grid.\n\n"
        "Check: play on /halloween/bat-snake/; eat a candy, hit a wall.\n\n"
        "Common mistakes: checking the crash after unshift (the head always "
        "'hits' itself), an infinite loop in placeCandy if the check is wrong."
    ),
    "Q10": (
        "Correct: 10 questions with unique keys and answers among the "
        "options, score counts matches, verdict differs for low/middle/full; "
        "test_quiz.py with the last test filled in; styled quiz.css.\n\n"
        "Check: answer everything right → 10/10.\n\n"
        "Common mistakes: an answer with a typo (never matches), duplicate "
        "keys (one question's radio buttons control another)."
    ),
    "Q11": (
        "Correct: 6+ graves for features really removed (from git log "
        "--diff-filter=D), styled tombstones.\n\n"
        "Check: /halloween/graveyard/; ask where one of the dead came from.\n\n"
        "Common mistakes: made-up features, editing the template (it already "
        "shows every grave; not this issue's file)."
    ),
    "Q12": (
        "Correct: next_halloween handles before/on/after 31 Oct; tick() "
        "splits the seconds left into d/h/m/s, never negative; tests with the "
        "last one filled in; styled tiles.\n\n"
        "Check: /halloween/countdown/ ticks every second.\n\n"
        "Common mistakes: date.today() in the view (fine, but the scaffold "
        "uses Oslo time), hours as total hours instead of hours % 24."
    ),
    "Q13": (
        "Correct: clicks toggle carver-cell--carved and aria-pressed, the "
        "light button toggles carver-pumpkin--lit and its text, Start over "
        "clears; styled pumpkin.\n\n"
        "Check: carve, light, Tab + Enter on a cell.\n\n"
        "Common mistakes: one listener per cell is fine but heavier; "
        "forgetting aria-pressed."
    ),
    "Q16": (
        "Correct: phase() from KNOWN_NEW_MOON with % SYNODIC_MONTH, "
        "shadow_offset 0 → -100 → 100 → 0, a moon_shadow tag, the decor's "
        "first line changed to include the shadow, tests filled in, the "
        "given CSS.\n\n"
        "Check: compare the moon with timeanddate.com for Oslo today.\n\n"
        "Common mistakes: changing more than the first line of "
        "halloween_decor.html (other decorations live there), forgetting "
        "{% load moon_tags %}, not restarting runserver."
    ),
    "Q17": (
        "The planted bug: is_open compares opens <= time < closes, which is "
        "never true when closes is after midnight, and ignores yesterday's "
        "late hours. Correct: handle closes <= opens, and check yesterday "
        "((weekday - 1) % 7) after midnight; tests for the night.\n\n"
        "Check: ifi test.\n\n"
        "Common mistakes: forgetting the after-midnight case (Friday night "
        "into Saturday), weekday - 1 without % 7 (Monday gives -1: that "
        "happens to work in Python, but by accident)."
    ),
    "Q18": (
        "Correct: no ghost without a fine pointer or with reduced motion; a "
        ".ghost-follower made in JS, eased towards the pointer with "
        "requestAnimationFrame via style.translate; hidden on pointerleave; "
        "pointer-events: none.\n\n"
        "Check: move the mouse around any page and click links.\n\n"
        "Common mistakes: no pointer-events: none (the ghost eats clicks), "
        "moving the existing .ghost (that's another issue's)."
    ),
    "Q19": (
        "Correct: the last 10 keys compared with the Konami code, ~40 "
        "fixed spans animated with element.animate and removed on finish; "
        "a role=status message with reduced motion.\n\n"
        "Check: ↑↑↓↓←→←→BA on any page.\n\n"
        "Common mistakes: never removing the spans (the page fills up), "
        "case-sensitive 'B'."
    ),
    "Q20": (
        "Correct: a toggle button and a .flashlight overlay made in JS, "
        "aria-pressed kept in sync, --x/--y set on pointermove, Esc turns "
        "it off; the given CSS plus the button style.\n\n"
        "Check: turn it on, move around, click a link through the dark.\n\n"
        "Common mistakes: no pointer-events: none on the overlay (nothing "
        "can be clicked), the button under the overlay (can't turn it off)."
    ),
    "Q21": (
        "Correct: ics_text with CRLF lines, TZID times or all-day dates "
        "(DTEND the next day), escaped text; event_ics_view finds the live "
        "EventPage or 404s and sends text/calendar as an attachment; the "
        "link in add_to_calendar.html; tests.\n\n"
        "Check: download from an event page and open it in a calendar app.\n\n"
        "Common mistakes: \\n instead of \\r\\n (most apps cope, the spec "
        "doesn't), DTEND on the same day for all-day events (zero length)."
    ),
    "Q24": (
        "Correct: six different faces, 120×120, on the blank pumpkin, small "
        "files.\n\n"
        "Check: 'Need ideas?' under the pumpkin carver.\n\n"
        "Common mistakes: big exports with embedded bitmaps, a missing "
        "xmlns (the picture doesn't show)."
    ),
    "Q26": (
        "Correct: readable badge colours for all four types, the side menu's "
        ".icon-text visually hidden at rest and shown when the menu opens, "
        "and an orange :focus-visible outline in .topheader-content.\n\n"
        "Check: Lighthouse/axe on the home page; Tab through the header; "
        "hover the side menu ('Menu' still shows).\n\n"
        "Common mistakes: display: none / visibility: hidden for the menu "
        "text (screen readers skip both), the outline on all :focus (also "
        "shows on mouse clicks)."
    ),
    "Q27": (
        "Correct: a <nav aria-labelledby> with an 'All pages' h2 around the "
        "list, aria-label = title and aria-describedby = the description "
        "per link, the h1's emoji in aria-hidden, a skip link. Includes and "
        "classes unchanged.\n\n"
        "Check: DevTools → Accessibility tab on a card link; ifi test.\n\n"
        "Common mistakes: removing an {% include %} (another issue's partial "
        "disappears), duplicate ids (use the slug)."
    ),
    "Q30": (
        "Correct: hub.css with the spooky h1, dark cards with a hard shadow "
        "that lift on hover and focus, an orange focus outline, the board's "
        "card brown, no transition with reduced motion.\n\n"
        "Check: /halloween/, hover and Tab through the cards.\n\n"
        "Common mistakes: removing the black border, styling plain a (also "
        "the back link and the skip link)."
    ),
    "Q31": (
        "Correct: COSTUMES with 8+ pairs, costume_of_the_day(day) with "
        "random.Random(day.toordinal()), a tag using Oslo's date, the given "
        "partial, tests.\n\n"
        "Check: /halloween/ shows the same costume on every reload "
        "(restart runserver after adding templatetags/).\n\n"
        "Common mistakes: random.choice without a seed (changes every "
        "reload), a tag and an import with the same name (recursion)."
    ),
})

JOKE_ISSUE = (
    "Correct: one new .txt file with exactly the name from the issue, holding "
    "one short joke as plain text (no heading, no quotes). English or "
    "Norwegian, any kind joke is fine.\n\n"
    "Check: http://localhost:8000/study/?joke=NN (the number from the file "
    "name) shows it.\n\n"
    "Common mistakes: a different file name (it can clash with another joke "
    "issue: rename it), a .txt.txt name from Windows, the file in the wrong "
    "folder. If the joke-file tests are merged, a joke over 200 characters or "
    "with a blank line fails ifi test: shorten it."
)

NOTES.update({f"C{48 + n}": JOKE_ISSUE for n in range(1, 11)})
NOTES.update({
    "SET-study": "The parent of the three study page issues. It earns nothing itself; close it when all three are merged.",
    "K36": (
        "Correct: 👍/👎 buttons made in JS inside #study-joke-tools, with "
        "aria-label and aria-pressed; votes in localStorage by joke text, "
        "inside try/catch; a second click takes the vote back; styled pills.\n\n"
        "Check: vote, reload until the same excuse shows (or use ?joke=NN for "
        "a file joke): the vote is still there. A private window still works.\n\n"
        "Common mistakes: reading the joke text once at load (wrong after the "
        "no-reload issue swaps the joke), localStorage without try/catch."
    ),
    "K37": (
        "Correct: a .joke-copy button made in JS in #study-joke-tools, "
        "navigator.clipboard.writeText with await in try/catch, 'Copied!' for "
        "~2 s, an error message on failure; styled button.\n\n"
        "Check: click, then paste somewhere.\n\n"
        "Common mistakes: await without async (SyntaxError), copying the text "
        "read at page load."
    ),
    "K38": (
        "Correct: study_app/test_joke_files.py with tests for the names, "
        "UTF-8 and not empty, at most 200 characters, no blank line, and no "
        "duplicates (including STUDY_JOKES).\n\n"
        "Check: ifi test passes; ask them to show one test failing with a "
        "broken joke_99.txt, and that the file is gone from the PR.\n\n"
        "Common mistakes: a leftover joke_99.txt in the PR (it shows as an "
        "extra file in the Files check), comparing lazy STUDY_JOKES without "
        "str()."
    ),
    "Q32": (
        "Correct: excuse_api_view returns JsonResponse with a random joke "
        "(str() of all_jokes()), leaving out ?not=; study_excuse.js prevents "
        "the reload, fetches link.dataset.api with the encoded current joke, "
        "swaps the text, and falls back to the link on any error; tests.\n\n"
        "Check: click 'Give me another excuse' a few times: no reload, never "
        "the same twice. /study/api/excuse/ shows JSON.\n\n"
        "Common mistakes: JsonResponse with lazy strings (TypeError: not JSON "
        "serializable), a hard-coded /study/api/excuse/ in the JS (breaks with "
        "the /nb/ and /en/ prefixes: use data-api), no fallback."
    ),
})
