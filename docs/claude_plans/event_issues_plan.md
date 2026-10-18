# Commit for Candy: issue plan (shared copy)

Plan for the event issues of Commit for Candy (19 October 2026), copied
into the project on 2026-10-18 so another session can pick it up. Read
**Current state** first: it overrides the plan below wherever they differ.
Delete this file once the event issues are on GitHub.

## Current state (2026-10-18)

**Built and tested** (uncommitted on branch `task/create-issues`):
- The two currencies (🪙 coins for the drink, 🏆 points for the top 3) in
  `ifiplatform/apps/commits_app/`, with tests.
- The Files check (`.github/workflows/files_check.yml`): warns about extra
  files, fails on a missing `Closes #N` and on browser edits (web-flow).
- The pilot scaffold: `ifiplatform/static/css/07_halloween/`, the decor
  partial, `ifiplatform/apps/halloween_app/` (hub, haunted board, page
  slots with TODOs), `templates/404.html`, planted bugs.

**The pilot: 37 issues to claim (16 🍬, 11 🍫, 10 🎃) + 4 sets.** Every
issue's full text, with a screenshot of the finished result, is in
one doc per size: [🍬 candy](event_issues_candy.md),
[🍫 chocolate](event_issues_chocolate.md) and
[🎃 pumpkin](event_issues_pumpkin.md). All 37 solutions merge
together without conflicts, each changes exactly its listed files, and the
quick tests pass with all of them merged.

**Phase 2, designed 2026-10-18: 69 more issues, so 106 in all (46 🍬, 30 🍫,
30 🎃) + 7 sets.** Built like the pilot: scaffold, issue text, solution,
helper note, screenshot. All 106 solutions merge without conflicts, each
changes exactly its listed files, and the quick tests pass with all merged
(376 tests) and on the bare scaffold (322). Every Python/template solution
also passes on its own. The review doc covers all 106.
- **No doc issues** (user's call, 2026-10-18: writing docs is boring). K26
  (pilot), K25, K35 and Q25 were dropped. In their place:
  - 🍬 C49–C58, **write a study joke**: one new file each,
    `apps/study_app/joke_files/joke_NN.txt`. The page reads the folder on
    every visit, and `/study/?joke=NN` shows a given file, so people find
    their own. An elastic 🍬 pool: more can be posted during the event
    (joke_11, ...), no code needed.
  - 🍫 set **The study page**: K36 rate 👍/👎 (localStorage), K37 copy
    the excuse, K38 tests that keep the joke files tidy.
  - 🎃 Q32 another excuse without reloading (JSON view, fetch, tests).
  - Scaffold for these: `jokes.py` (`file_jokes`, `file_joke`,
    `all_jokes`), `views/joke_page.py` replacing the generic
    under-development view for /study/, the stub
    `/study/api/excuse/` before the catch-all, and empty JS/CSS files plus
    `#study-joke-tools` in the template.
- **New issues:**
  - 🍬 C2–C10, C17, C18, C20, C22, C23, C31 (👻 Today/Tomorrow swapped),
    C33 (alt text), and the set **Spider** (C27–C30).
  - 🍫 K2, K4, K6, K7, K8 (real opening hours, checked on the web
    18 Oct), K12, K13, K20, K21, K22, K27 (contrast on the grey
    boxes), K29 (👻 weekday), K31 (👻 hub order), the set **Right column**
    (K9–K11), and **K34** bats fly out of the moon (not in the catalogue).
  - 🎃 every catalogue Q except Q14 (the soundboard: its audio files need
    licensing) and Q25 (a doc). Q4 joined the set **Fortune booth**; Q6, Q8 and Q9 joined
    **Halloween arcade**.
- **Left out on purpose:** the board-note issues (C37–C48) and the board
  styles (K23, K24, K32, K33). The user isn't happy with the board-note
  design yet: wait for them before designing these. Also left for later:
  the shortcut icons set (C11–C16), the footer set (C24–C26, it would
  split `footer.html`, which P5 edits), C19, C21, K18 (there are no
  flashcards on this site), Q14.
- **Phase 2 scaffold** (in the working tree, like the pilot's):
  - `07_halloween/`: an empty CSS file per new issue, linked from
    `css_links/halloween.html` in cascade order; `scaffold.css` adds
    `--font-spooky` (Grenze Gotisch, loaded from Google Fonts in the same
    include), parks the bat flock and the spider, resets the tagline
    button, and lays out the right column.
  - `static/js/halloween/`: an empty, deferred script per JS issue.
  - Decor: the spider, the bat flock, and an empty `.treeline` above the
    footer (in `global_base.html`, inside `.bottombar-content`).
  - Header: `partials/header_tagline.html` ("Trick or Treat?", a button).
  - Home page: `.right-column` (opening hours, the events box, >OUTPUT)
    and the Instagram row under the news; `opening_hours_data.py`,
    `opening_hours.py` (`is_open` has the planted overnight bug, Q17), the
    tag `get_opening_hours`; placeholder SVGs for Instagram, the cover and
    the carver's faces.
  - Events: empty `halloween_countdown.html` (events index) and
    `add_to_calendar.html` (event page) includes, and the stub URL
    `/halloween/event/<id>/calendar.ics`.
  - Halloween corner: nine new page slots with starter code and TODOs
    (zombie_typing, sliding_puzzle, bat_snake, costume, story, quiz,
    graveyard, countdown, pumpkin_carver), `hub.py` (with the planted
    sort bug, K31), `templatetags/`, and two empty hub partials.
  - Planted bugs: Today/Tomorrow swapped in `eventsbox.html` (C31),
    `{% now "l" %}` as the weekday in `event_page.html` (K29).
- **Findings for the a11y issues came from an axe run** on the merged
  home page: grey text on the grey boxes (K27), the event badges' contrast,
  the side menu's unnamed button and the dark focus ring in the header
  (Q26).

**Changes since the plan below was written:**
- **C1 "Make the home page dark" joined the pilot** (🍬). Only the home
  page goes dark (`:root:has(#home-shortcuts)`): other pages have no
  background of their own, so dark text would end up on dark grey.
- **K1 cobweb:** a `background-image` on `body`, scrolling with the page.
  Not on `html` (body's own background covers it), not `fixed`.
- **K17** restyles the study *joke* page (`.under-development`): on this
  site `/study/` shows "Studie? Ahaha, nei.", not the study home.
- **Scaffold fixes:**
  - `global_base.html` includes the Halloween CSS **after**
    `{% block extra_head %}`, because the account pages load their CSS
    there.
  - The hub has no back link to itself.
  - Hub cards have black borders.
  - Board signatures accept `--` (and `-` or `—`).
- **Design rules (internal):** every border is plain black, one colour,
  the same thickness all round (`2px solid #000`), and existing coloured
  edges are overridden, like the log-in card's pink top. The message
  board, news box, news cards and Instagram box have no border. Focus
  outlines may stay coloured.
- **Issue text conventions** (all applied by the generator):
  - every issue starts with "Reward", "Time" and "Good to know first"
    (🍬: "nothing, everything is explained")
  - the explanation after solution code sits under
    "#### Explanation (optional)"
  - design-heavy issues (K14–K17, Q1–Q3, Q5, Q7, Q15, and most new
    CSS-heavy 🍫/🎃) have a "Design to build" section, so people can
    build without designing; "Make it yours" holds alternative designs
  - colour suggestions come with a colour-picker tip
  - the how-to block explains reloading with Ctrl+Shift+R
  - the board-note explanation: first line → heading, the lines after →
    text, a last line starting with `--` → signature
- **Open question:** move the cobweb SVG's settings (`fill`, `stroke`)
  from the outer `<svg>` onto a `<g>`, because SVG-Edit drops them on
  import.

"Producing it" below planned one data file, `event_issues.py`. Instead, each
issue is its own Markdown file in `event_issues_tooling/issues/`.

**Where the tooling is:** [event_issues_tooling/](event_issues_tooling/), with a
README covering how to:
- edit issues
- rebuild and test the throwaway repo (`build_pilot_repo.sh`)
- regenerate the texts
- take screenshots
- post the issues to GitHub

---

# Commit for Candy: the full issue set (phase 1 + phase 2)

## Context
The Halloween mockup is approved ([preview artifact](https://claude.ai/artifact/2QAkACJMf1Ntp5Emu5Fyd7), "Final" tab). Now we design every issue for the event on 19 October. Requirements from the user:
- **At least 30 issues per difficulty** (🍬 1 point, 🍫 2, 🎃 3). The 12 phase 1 issues count.
- **🎃 issues are bigger standalone tasks.** Every difficulty also has some **sets**: a parent issue with sub-issues of that size. A set only groups issues. Points are only for the issues a person claimed and finished, and the parent earns nothing. Drinks still come from points (`DRINK_TICKET_POINTS`).
- **The whole mock site is in scope**, plus a new scaffolded **Halloween corner** (`/halloween/`) for the 🎃 pages.
- **No merge conflicts:** every issue lists its exact files, and no other issue touches them. The Files check workflow warns about extra files.
- **Easy issues give the full solution** plus "Make it yours". Bigger ones give starter code and steps.
- **Design rules (internal only, for writing the solutions and mockups; never stated in issue texts):**
  - Boxes with a border get a **black** one: shortcut cards, opening hours, events box, >OUTPUT.
  - The message board, news box, news cards and Instagram box have **no border**.
  - No blue outline on the header.

## Step 1 (now): the pilot, at least 10 per difficulty
The user tests this set first, and grows it towards the full catalogue below once they're happy. The pilot uses the issues that need the **least scaffold**, still covers **every category**, and has **at least one set per size**. The IDs refer to the catalogue below, so they keep their place when it grows.

**🍬 Candy (15):**
- the 12 phase 1 issues, with P4 now "pin obituary_01" on the board, and the set **Moon**
- plus 3 more board notes, one per new type, to test the note flow:
  - C34 = new `ifiplatform/apps/halloween_app/board_notes/warning_01.txt`
  - C35 = new `ifiplatform/apps/halloween_app/board_notes/rule_01.txt`
  - C36 = new `ifiplatform/apps/halloween_app/board_notes/missing_01.txt`

**🍫 Chocolate (10):**
- K1 cobweb 🖼️
- K3 floating ghost 🦇
- K5 skull account icon 🖼️
- K19 `carve_pumpkin` 🧪
- K26 Halloween decor doc 📚
- K28 reduced motion ♿
- K30 👻 language switch
- **set "Pages go Halloween"**: K14 article page, K15 event page, K16 login and sign-up, K17 study home 🎨

**🎃 Pumpkin (10):**
- **set "Fortune booth"**: Q1 fortune teller, Q2 spooky name, Q3 potion mixer 🧪
- Q28 👻 æøå crash
- **set "Halloween arcade"**: Q5 whack-a-bat, Q7 memory pairs 🦇
- Q15 Halloween 404 🎨
- Q22 `halloween_stats` 🧪
- Q23 mascot drawing 🖼️
- Q29 drag notes on the board 🦇

**Pilot scaffold** (on top of the phase 1 scaffold that's already built):
00. **The Files check browser-edit rule** (section "How participants work").
0. **The two-currency change** in commits_app (section below). It comes first, because issue texts and the dry run depend on it.
1. **CSS files:** empty `07_halloween/` files for cobweb, ghost, reduced_motion, article_page, event_page, auth_pages, study_home and page_404. Link them in `halloween.html`.
2. **Decor and splits:**
   - the `<div class="ghost">` goes in `halloween_decor.html`
   - the account icon is split into `partials/icons/account_icon.html`
   - plant the language-switch bug in `select_language.html`
3. **`halloween_app` with only the pilot's slots:**
   - app registration, URLs and the hub (with the `mascot.html` include)
   - `management/commands/__init__.py`
   - page slots `fortune`, `spooky_name`, `potion`, `whack_a_bat`, `memory`
   - `fortune_names.py`, with the planted æøå bug
   - `templates/404.html`, plus the `/halloween/404-preview/` URL
4. **The haunted board, complete:** the loader, the page, the base CSS, the empty type CSS files, `board_drag.js`, and `board_notes/` with its README and example notes.

**Pilot verification:**
- **No shared files:** the check script passes.
- **Conflict test:** all 35 solution branches merge cleanly on the scaffold.
- **Tests and renders:** `ifi test` passes, and the hub, board, 404 preview and home page all render.
- **Preview:** the preview artifact gets a "Pilot" tab.
- **Then the user's dry run:** a few people claim, PR, merge and get points.

## Motivation and point economy
- **Everyone's goal is one drink:** 5 🪙, for example 5 🍬, or 🍫 + 🍫 + 🍬, or 🎃 + 🍫.
- **Extra drink tickets for places 1, 2 and 3**, decided by 🏆 points, which only 🍫 and 🎃 give. That's the reason to move up after the first drink.
- **Enough points for everyone:** about 30 participants × 5 = 150 points just for everyone's first drink. Available: 60 🍬 (60 points) + 33 🍫 (66) + 31 🎃 (93) = **219 points**. There's room, but the **🍬 pool is the risk**: beginners need 🍬, and fast people also grab it early.
- **Mitigations:**
  - **Notes are an elastic 🍬 pool:** organisers can add more "Pin a note" issues at any time during the event (`obituary_05.txt`, …), each with a new file name, without any code or conflicts. Prepare 20 extra note issues as drafts, and post them if 🍬 runs low.
  - **Mention in the event intro and on the issue board:** "Once you have your drink, move up to 🍫 and 🎃: that's where the top 3 is decided." This leaves 🍬 for the beginners. It's a social rule, so there's no new code in commits_app this close to the event.
  - **The 2-claims-at-a-time limit** already stops hoarding.
- **Points only for the issue you claimed and finished.** Sets just group issues, and their parent earns nothing.

## Two currencies: 🪙 coins and 🏆 points (site change, needed for the pilot)
**Why:** the drink is everyone's goal, and the top 3 is the contest. If 🍬 counts for the contest, fast people farm 🍬, beginners run out, and easy issues pay best. With two currencies, 🍬 helps you get your drink but **never** helps you climb the leaderboard.

| Size | 🪙 coins (drink) | 🏆 points (contest) |
| --- | --- | --- |
| 🍬 candy | 1 | 0 |
| 🍫 chocolate | 2 | 2 |
| 🎃 pumpkin | 3 | 3 |

- **Drink ticket at 5 🪙** (setting renamed `DRINK_TICKET_POINTS` → `DRINK_TICKET_COINS`, still 5).
- **The leaderboard shows everyone**, sorted by 🏆, then 🪙, then who got there first. The podium (top 3) is by 🏆. People with only coins are listed further down with 0 🏆.

**Changes in `ifiplatform/apps/commits_app/`** (no model fields and no migration: `EventIssue.points` becomes the 🏆 points, and coins come from the size):
- `labels.py`:
  - `SIZE_LABELS` becomes label → `(name, coins, points)`
  - new `coins_for(size)`
  - `size_label()` and `difficulty_choices()` unpack three values and sort by coins
- `models.py`: `EventIssue.coins` property, from `coins_for(self.size)`.
- `github_sync.py` (line ~190): unpack `(size, coins, points)` and store the 🏆 points.
- `scoring.py`:
  - `Score.coins`
  - `drink_earned` uses coins ≥ `DRINK_TICKET_COINS`
  - `leaderboard()` sorts by (-points, -coins, reached_at)
- `views/board_views.py` (`_difficulty_key`, `_difficulty_heading`): group and label difficulty by **size and coins**, not points. Otherwise 🍬 (0 🏆) would merge with issues that have no size.
- `views/common.py` (line ~89), `views/core_views.py` (`drink_points` → `drink_coins`) and `management/commands/seed_fake_points.py`: three-value unpacking.
- **Templates:**
  - `difficulty_badge.html`, `issue_row.html` and `issue_panel.html`: "1 🪙" or "2 🪙 + 2 🏆"
  - `my_points.html`: "3 🪙 · 4 🏆"
  - `commits_main.html`: a coins tile with the drink progress (x/5 🍹), plus a points tile
  - `leaderboard.html`: the podium by 🏆, and table columns 🏆 and 🪙
  - `drink_cell.html` stays as it is, since it already uses `drink_earned`
- **Settings:** `ifiplatform_project/settings.py` gets `DRINK_TICKET_COINS = 5`.
- **Tests** (`commits_app/tests.py`):
  - update the existing point tests
  - new tests: 🍬 gives 1 🪙 and 0 🏆; the drink comes from coins; the leaderboard sorts by 🏆, then 🪙; 🍬 stays its own difficulty group, separate from issues without a size
- **Translations:** organisers run `makemessages`/`compilemessages` for the new strings, as part of this change, before the event.
- **Docs:**
  - the README "Collect points" bullet explains 🪙 vs 🏆
  - `docs/operations/docker_server.md` (lines ~222 and ~273)
  - any commits_app architecture doc, if one exists (check `docs/` for one)
- **Issue texts:** each issue shows its reward ("Reward: 1 🪙", "Reward: 2 🪙 + 2 🏆"), and the "How it works" intro explains the two.

**Checks:**
- `python manage.py test commits_app` passes.
- `seed_fake_points` shows a sensible leaderboard and issue board locally.
- Look at the leaderboard, Your Page and the issue board.

The time estimates below are now in 🪙 for the drink. The design targets stay the same.

## Time to a drink (rough estimate, used as a design target)
**Fixed cost per issue, about 4 minutes once set up** (one-time setup not counted; that's done before the first claim):
- claim on the site
- `ifi fix-issue`
- check at localhost, `ifi test`, commit
- `ifi pull-request`, open the link

In the browser (💻) it's about 5 minutes. Waiting for the merge doesn't block anyone, because people can hold 2 claims and start the next one.

**With the full solutions as currently written, a skilled person would be fastest with 🍬.** That's the problem: easy issues pay best per minute.

| Size | Work (skilled) | + fixed cost | Per issue | Minutes per point | Drink (5 points) |
| --- | --- | --- | --- | --- | --- |
| 🍬 paste-and-tweak | ~2 min | 4 | ~6 min | **~6** | 5 × 🍬 ≈ **30 min** |
| 🍫 today (more to read and write) | ~12–15 min | 4 | ~18 min | ~9 | 🍫🍫🍬 ≈ 42 min |
| 🎃 today (games and pages from scratch) | ~40–60 min | 4 | ~50 min | ~17 | 🎃🍫 ≈ 70 min |

**Targets:**
- 🍬 stays a little *slower per point* than the bigger sizes.
- Every size reaches a drink in about **30 minutes at most**, for the person that size is meant for.

| Size | Target per issue (for whom) | Minutes per point | Drink |
| --- | --- | --- | --- |
| 🍬 | ~6 min (beginner using the given solution; a skilled person gains nothing by picking it) | ~6 | 5 × 🍬 ≈ 30 min |
| 🍫 | **~10–11 min** (someone with some code) | ~5–5.5 | 🍫🍫🍬 ≈ 28 min |
| 🎃 | **~15 min** (skilled) | ~5 | 🎃🍫 ≈ 26 min, or 🎃🎃 ≈ 30 min for 6 points |

**How the issues meet the targets:**
- **🍬:** don't make them faster. Keep one change per issue, and never bundle two tiny changes into one issue. The fixed cost already makes them ~6 min.
- **🍫:** the issue gives most of the solution, and the participant adds one real decision or piece of logic. For example, K19 `carve_pumpkin` gives the command skeleton, and they write the pumpkin-printing loop. K14–K17 give the selectors and they pick the values. Target ≤ 11 min. Anything bigger becomes 🎃.
- **🎃:** the scaffold does the "half feature". Every 🎃 slot comes with **starter code with 2–4 `TODO` checkpoints**: the view and form are wired up, the template shows the result, and for Python 🎃 the test file is prewritten with one test left as a TODO. JS games get the board markup and a game loop with TODOs (spawn, hit, score). The participant fills in the core logic. Target ~15 min for a skilled person.
- **Every issue text says how long it takes:** "About 5 min" (🍬), "About 10 min" (🍫), "About 15–20 min if you know Python/JS" (🎃). That helps people choose, and pushes skilled people upward.
- **Pilot check:** in the dry run, time 2–3 issues of each size. If 🍬 turns out faster per point than 🍫, trim 🍫/🎃 starter tasks (more prefilled) rather than slowing 🍬.

**Pilot estimates** (skilled person, including the fixed cost):

| Size | Issues |
| --- | --- |
| 🍬 | all ~5–7 min |
| 🍫 | K1 cobweb ~12, K3 ghost ~10, K5 skull ~10, K19 carve_pumpkin ~10, K26 doc ~12, K28 reduced motion ~8, K30 bug ~8, K14–K17 page restyles ~10 each |
| 🎃 | Q1–Q3 fortune booth ~15–18 each (with starter and TODOs), Q28 æøå bug ~12, Q5 whack-a-bat ~20, Q7 memory ~20, Q15 404 ~15, Q22 halloween_stats ~15, Q23 mascot ~20, Q29 drag notes ~18 |

The two games and the mascot are the slowest. Give them the most starter code, or accept them as "big 🎃" for people chasing the top 3.

## How participants work (by skill level)
**Setting up the project locally is part of the point of the event.** So **every issue is done locally**: Docker (or the setup without Docker), then `ifi fix-issue` → change → check at localhost → `ifi test` → commit → `ifi pull-request`. There's no browser path and no admin-only content. Issue texts only describe the local flow.

**Enforcement** (detect and redirect, nothing hard-blocked):
- **Files check flags browser edits:** `.github/workflows/files_check.yml` gets one more check. If any commit in the PR has the committer `web-flow` (made on github.com) or the branch is named `patch-N`, the check **fails** with "Made in the browser: please set up the project and do it locally (`ifi fix-issue <nr>`)". This one is red, not a warning, because it's an event rule. The extra-files case stays a warning.
- **Points need a merged PR:** a closed issue only counts when it's closed as completed, and only helpers and organisers close issues. A solution pasted into a comment earns nothing. Helpers never close an issue without a merged PR.
- **The helper note says:** "Red Files check about the browser? Help them set up instead of merging."

**Setup time is the real bottleneck.** The first Docker build takes minutes, longer on slow laptops. So:
- The event announcement asks people to **set up at home beforehand** (README "Get started").
- The first half hour at the event is a **setup session** with helpers walking the room.
- While the build runs, people browse the issue board, claim their first 🍬, and read its text. That's also when the "Make it yours" choices get made.

**Personas and their path:**
1. **Total beginner:** sets up with a helper, then pins a note on the haunted board (one new text file, 1–3 sentences), then 🍬 from a set (moon, icons, spider) by copying the solution and tweaking "Make it yours". Goal: 5 🪙 for a drink.
2. **Some HTML/CSS, new to Git:** 🍬 and 🍫 restyles, art, a11y, 👻, using `ifi`.
3. **Comfortable coder:** after the drink, 🍫 Python and JS, then 🎃 for 🏆.
4. **Experienced:** 🎃 games and features with tests, in sets. They can pair with a beginner on the same set, each claiming their own sub-issue.

**What this changes in the issue design:**
- No ✏️/🌐 ways and no `🌐 no setup` label. Every issue ends with the same `ifi` block.
- Board notes stay tiny (one new file) but are done locally like everything else, which makes them a perfect first PR after setup.
- The Halloween 404 issue (Q15) previews at the scaffolded `/halloween/404-preview/` locally.
- **Claim time limits:** 🍬 30 min, 🍫 60 min, 🎃 90 min. These cover the work, but **not a first-time setup**. Tell people to set up *before* claiming, or to press **Keep**.
- **Merges come in bursts:** each merge triggers CI and a deploy, one after another, so "live in a few minutes" can stretch at peaks. Issue texts say "it may take a while to show up live", and helpers can batch merges.

## Rules every issue states
- Only change the listed files.
- Never run `makemessages` or `makemigrations`. New English `{% trans %}` text is fine; organisers translate after the event.
- No model fields and no migrations. Python issues use plain Python, template tags or management commands.

## Scaffold (organisers, before the event; built on phase 1's)
1. **CSS layer:** `static/css/07_halloween/` gets one **empty** file per site CSS issue, all linked from `css_links/halloween.html`. `scaffold.css` (`body { isolation: isolate }`) stays first. Plus tokens in `tokens.css`: `--color-night`, `--color-card-grey`, `--color-card-border: #000`, `--color-pumpkin`, `--color-ghost`, `--color-poison` and `--font-spooky` (Grenze Gotisch from Google Fonts).
2. **JS layer:** an empty `static/js/halloween/*.js` per JS issue, linked with `defer` from `halloween.html`.
3. **Decor markup** in `partials/halloween_decor.html`:
   - the moon, already there
   - the spider (`__thread`, `__body`, `__legs`)
   - the ghost
   - plus an empty `<div class="treeline">` at the end of `<main>`
4. **Split shared files:**
   - the shortcut icons, into `shortcuts/icons/<name>.html`
   - the account icon, into `partials/icons/account_icon.html`
   - `header_tagline.html`
   - the footer, into `footer_left.html` and `footer_right.html`
   - the news and events headings, into their own partials
5. **Home page right column:**
   - one stack (`grid-template-columns: minmax(0,1fr)`), with the events box reset to `grid-area: auto`
   - the partials `opening_hours.html`, `instagram.html` and `output_magazine.html`
   - `opening_hours_data.py` and `opening_hours.py` (`is_open` returns `None`), plus the tag `get_opening_hours`
6. **Halloween corner app** (`apps/halloween_app/`, no models):
   - **Registration:** add the app to `INSTALLED_APPS`, and include its URLs at `/halloween/`.
   - **Hub page:** `/halloween/` lists the pages from a scaffold-owned `PAGES` list in `pages.py`.
   - **One slot per page:**
     - `views/<slug>.py`, a stub that renders the template
     - `templates/halloween/<slug>.html`, which extends `home_base` and says "Coming soon"
     - an empty `static/css/halloween_pages/<slug>.css`, already linked from that template
     - an empty `static/js/halloween_pages/<slug>.js` where the page needs JS
   - **Header link:** a "🎃 Halloween" nav link in the header.
   - **404 page:** an empty `templates/404.html` that extends `global_base`.
7. **Event page slots:** empty includes for the countdown (on the events index) and "Add to calendar" (on the event page), with their URL already registered and a stub view.
8. **Haunted notice board** (`/halloween/board/`). It's fully built by organisers, so it works on day one:
   - **Note loader:** `HC/board.py` reads every `.txt` file in `HC/board_notes/`. The note's type comes from the filename prefix (`obituary_`, `warning_`, `rule_`, `missing_`). In the file, line 1 is the title, the rest is the text, and an optional last line starting with `— ` is the signature.
   - **Page:** `HC/views/board.py` and `HC/templates/halloween/board.html` show the notes as pinned paper notes with a slight random tilt (seeded by filename, so it's stable).
   - **Base style:** `HC/static/css/halloween_pages/board.css`, owned by the scaffold.
   - **Type styles:** one empty CSS file per note type (`board_obituary.css`, `board_warning.css`, `board_rule.css`, `board_missing.css`) and an empty `board_drag.js`, all already linked.
   - **The folder:** `HC/board_notes/README.md` explains the format, plus one example note per type, written by the organisers.
   - **Phase 1:** P4 becomes a board note, so the **board is part of the phase 1 scaffold**.
9. **Planted 👻 bugs**, each in a file no other issue touches (listed below).
10. **Solutions:** one solution branch per issue, then the conflict test (see Verification).

## Full catalogue (grow into this after the pilot)
**Every issue lists every file it touches, with the full path from the repo root, marked edit or new:**
- **edit:** the file already exists. It may be an empty scaffold file.
- **new:** the participant creates exactly this file, with this name.

Nothing else may change. Files a scaffold step makes (empty CSS, JS and partials; `__init__.py`; URL routes; template includes) are already on `main` before the event.

Shorthand used **only in this plan** (the issue texts always spell out full paths):
- `CSS/` = `ifiplatform/static/css/07_halloween/`
- `JS/` = `ifiplatform/static/js/halloween/`
- `IMG/` = `ifiplatform/static/images/halloween/`
- `HOME/` = `ifiplatform/apps/ifi_home_app/`
- `HC/` = `ifiplatform/apps/halloween_app/`
- `TPL/` = `ifiplatform/templates/`

### 🍬 Candy (60 = 12 in phase 1 + 48 new)
**Phase 1** (files as in the phase 1 issue texts):
- P1: edit `CSS/header_bar.css`
- P2: edit `CSS/bat_cursor.css`, new `IMG/bat.svg`
- P3: edit `HOME/views/home_views.py`
- P4: pin the first obituary, new `HC/board_notes/obituary_01.txt` (💻)
- P5: edit `TPL/partials/footer.html` (before the footer split)
- P6: edit `ifiplatform/static/images/favicon.svg`
- P7: edit `ifiplatform/static/css/README.md`
- P8: edit `HOME/templates/home/partials/messageboard/slide.html`
- P9: edit `CSS/shortcut_focus.css`
- Set "Moon": P10a edit `CSS/moon.css`, P10b edit `CSS/moon_craters.css`, P10c edit `CSS/moon_glow.css`

| # | Issue | Cat | Way | Files |
| --- | --- | --- | --- | --- |
| C1 | Page background dark grey | 🎨 | 💻 | edit `CSS/page_background.css` |
| C2 | Logo: orange, spooky font | 🎨 | 💻 | edit `CSS/logo.css` |
| C3 | "Trick or Treat?" tagline style | 🎨 | 💻 | edit `CSS/tagline.css` |
| C4 | Nav links purple, glow on hover | 🎨 | 💻 | edit `CSS/nav_links.css` |
| C5 | Language buttons orange | 🎨 | 💻 | edit `CSS/language_buttons.css` |
| C6 | Sub-menu links: small, white, underlined | 🎨 | 💻 | edit `CSS/subnav.css` |
| C7 | Side menu teal | 🎨 | 💻 | edit `CSS/sidemenu.css` |
| C8 | Shortcut cards grey, with a black border | 🎨 | 💻 | edit `CSS/shortcut_cards.css` |
| C9 | Shortcut titles in the spooky font | 🎨 | 💻 | edit `CSS/shortcut_titles.css` |
| C10 | Shortcut hover wiggle | 🎨 | 💻 | edit `CSS/shortcut_hover.css` |
| C11 | Set "Shortcut icons": Info, a ghost with an "i" | 🖼️ | 💻 | edit `HOME/templates/home/partials/shortcuts/icons/info.html` |
| C12 | … Nyheter: a newspaper with a bat | 🖼️ | 💻 | edit `HOME/templates/home/partials/shortcuts/icons/news.html` |
| C13 | … Jobber: a pumpkin briefcase | 🖼️ | 💻 | edit `HOME/templates/home/partials/shortcuts/icons/jobs.html` |
| C14 | … Foreninger: three ghosts | 🖼️ | 💻 | edit `HOME/templates/home/partials/shortcuts/icons/unions.html` |
| C15 | … Events: a pumpkin calendar | 🖼️ | 💻 | edit `HOME/templates/home/partials/shortcuts/icons/events.html` |
| C16 | … Verktøy: crossed axes | 🖼️ | 💻 | edit `HOME/templates/home/partials/shortcuts/icons/tools.html` |
| C17 | Message board grey, no border | 🎨 | 💻 | edit `CSS/messageboard.css` |
| C18 | "Latest" heading style | 🎨 | 💻 | edit `CSS/news_heading.css` |
| C19 | "News this month – {% now 'F Y' %}" | 🔤 | 💻 | edit `HOME/templates/home/partials/news_heading.html` |
| C20 | Events box: grey, black border | 🎨 | 💻 | edit `CSS/eventsbox_box.css` |
| C21 | "This month – {% now 'F' %}" heading | 🔤 | 💻 | edit `HOME/templates/home/partials/eventsbox/heading.html` |
| C22 | Event rows: small text, bold titles | 🎨 | 💻 | edit `CSS/eventsbox_items.css` |
| C23 | >OUTPUT box: grey, black border | 🎨 | 💻 | edit `CSS/output_box.css` |
| C24 | Set "Footer": dark footer | 🎨 | 💻 | edit `CSS/footer.css` |
| C25 | … new footer text | 🔤 | 💻 | edit `TPL/partials/footer_left.html` |
| C26 | … pink Guild badge | 🎨 | 💻 | edit `CSS/footer_badge.css` |
| C27 | Set "Spider": thread and body | 🖼️ | 💻 | edit `CSS/spider_body.css` |
| C28 | … jointed legs | 🖼️ | 💻 | edit `CSS/spider_legs.css`, new `IMG/spider_legs.svg` |
| C29 | … swing | 🦇 | 💻 | edit `CSS/spider_swing.css` |
| C30 | … no swing with reduced motion | ♿ | 💻 | edit `CSS/spider_reduced_motion.css` |
| C31 | 👻 "Today" and "Tomorrow" swapped (planted) | 👻 | 💻 | edit `HOME/templates/home/partials/eventsbox/eventsbox.html` |
| C32 | 👻 "Report a bug" and "Request a feature" go nowhere (a real bug) | 👻 | 💻 | edit `TPL/partials/footer_right.html` |
| C33 | Alt text on article card images | ♿ | 💻 | edit `HOME/templates/info_articles/partials/article_card.html` |
| C34–C48 | **Pin a note on the haunted board** (15 issues, each with a fixed file name). Obituaries for things that died ("Here lies printf debugging"), warnings ("Do NOT open the 3rd-floor fridge"), rules ("Rule 7: never deploy on Friday the 13th"), missing posters ("Missing: my semicolon"). Each issue gives 3 example ideas and the format. 1–3 sentences is plenty. | ✍️ | 💻 | new `HC/board_notes/obituary_02.txt` … `obituary_04.txt`, `warning_01.txt` … `warning_04.txt`, `rule_01.txt` … `rule_04.txt`, `missing_01.txt` … `missing_04.txt`: **exactly one file per issue** |

### 🍫 Chocolate (33)
| # | Issue | Cat | Way | Files |
| --- | --- | --- | --- | --- |
| K1 | Cobweb, top left only | 🖼️ | 💻 | edit `CSS/cobweb.css`, new `IMG/cobweb.svg` |
| K2 | Scary trees above the footer | 🖼️ | 💻 | edit `CSS/treeline.css`, new `IMG/trees.svg` |
| K3 | A ghost floats past | 🦇 | 💻 | edit `CSS/ghost.css` |
| K4 | Click the spider: it climbs away and comes back | 🦇 | 💻 | edit `JS/spider_click.js`, edit `CSS/spider_startled.css` |
| K5 | Account icon becomes a skull | 🖼️ | 💻 | edit `TPL/partials/icons/account_icon.html` |
| K6 | News: no white inner card, 4 per row | 🎨 | 💻 | edit `CSS/news_cards.css` |
| K7 | Opening hours box and badges | 🎨 | 💻 | edit `CSS/opening_hours.css` |
| K8 | Fill in the real opening hours (4 places) | 🧪 | 💻 | edit `HOME/opening_hours_data.py` |
| K9 | Set "Right column extras": Instagram box style | 🎨 | 💻 | edit `CSS/instagram.css` |
| K10 | … Instagram pictures and links (replace the 5 scaffold pictures) | ✍️ | 💻 | edit `HOME/templates/home/partials/right_column/instagram.html`, edit `IMG/instagram/tile1.svg` … `tile5.svg` |
| K11 | … >OUTPUT cover drawing (replace the scaffold picture) | 🖼️ | 💻 | edit `IMG/output_cover.svg` |
| K12 | Clicking "Trick or Treat?" shows a random trick or treat | 🦇 | 💻 | edit `JS/trick_or_treat.js` |
| K13 | Secret code makes the page spin | 🦇 | 💻 | edit `JS/spooky_code.js` |
| K14 | Set "Pages go Halloween": article page | 🎨 | 💻 | edit `CSS/article_page.css` |
| K15 | … event page | 🎨 | 💻 | edit `CSS/event_page.css` |
| K16 | … login and sign-up pages | 🎨 | 💻 | edit `CSS/auth_pages.css` |
| K17 | … study home | 🎨 | 💻 | edit `CSS/study_home.css` |
| K18 | Spooky flashcard flip | 🎨 | 💻 | edit `CSS/flashcards.css` |
| K19 | `python manage.py carve_pumpkin` prints an ASCII pumpkin | 🧪 | 💻 | new `HC/management/commands/carve_pumpkin.py` |
| K20 | Template filter `spooky`, shown on the hub | 🧪 | 💻 | new `HC/templatetags/spooky.py`, edit `HC/templates/halloween/partials/spooky_demo.html` |
| K21 | "X days to Halloween" on the events page | 🧪 | 💻 | new `HC/templatetags/countdown_tags.py`, edit `HOME/templates/events/partials/halloween_countdown.html` |
| K22 | Costume generator page | 🦇 | 💻 | edit `HC/views/costume.py`, edit `HC/templates/halloween/costume.html`, edit `HC/static/css/halloween_pages/costume.css` |
| K23 | Set "Board styles": obituaries look like a death notice (black frame, cross, serif) | 🎨 | 💻 | edit `HC/static/css/halloween_pages/board_obituary.css` |
| K24 | … warnings: yellow and black hazard tape | 🎨 | 💻 | edit `HC/static/css/halloween_pages/board_warning.css` |
| K32 | … rules: a cracked stone tablet | 🎨 | 💻 | edit `HC/static/css/halloween_pages/board_rule.css` |
| K33 | … missing posters: a torn paper "MISSING" poster | 🎨 | 💻 | edit `HC/static/css/halloween_pages/board_missing.css` |
| K25 | Doc: how opening hours work | 📚 | 💻 | new `docs/architecture/ifi_home_app/opening_hours.md` |
| K26 | Doc: how the Halloween decor and layers work | 📚 | 💻 | new `docs/architecture/halloween_decor.md` |
| K27 | Readable orange: fix low-contrast text | ♿ | 💻 | edit `CSS/contrast.css` |
| K28 | Reduced motion for the ghost, the trick and the spin | ♿ | 💻 | edit `CSS/reduced_motion.css` |
| K29 | 👻 The event page shows the wrong weekday (planted) | 👻 | 💻 | edit `HOME/templates/events/event_page.html` |
| K30 | 👻 The language switch sends you to the home page (planted) | 👻 | 💻 | edit `TPL/partials/select_language.html` |
| K31 | 👻 The hub lists the pages in the wrong order (planted, Python) | 👻 | 💻 | edit `HC/hub.py` |

### 🎃 Pumpkin (31), all 💻
A Halloween corner page `<slug>` always means these three scaffold files, all **edit**:
- `HC/views/<slug>.py`
- `HC/templates/halloween/<slug>.html`
- `HC/static/css/halloween_pages/<slug>.css`

The issue text spells them out in full. The table lists them in short form, plus every extra file.

| # | Issue | Cat | Files |
| --- | --- | --- | --- |
| Q1 | Set "Fortune booth": fortune teller (name → the same fortune every time) | 🧪 | page `fortune`; new `HC/tests/test_fortune.py` (it uses `HC/fortune_names.py` but doesn't change it) |
| Q2 | … spooky name generator | 🧪 | page `spooky_name`; new `HC/tests/test_spooky_name.py` |
| Q3 | … potion mixer (ingredients → result rules) | 🧪 | page `potion`; new `HC/tests/test_potion.py` |
| Q4 | … haunted story (fill in the blanks) | 🦇 | page `story` |
| Q5 | Set "Halloween arcade": whack-a-bat | 🦇 | page `whack_a_bat`; edit `HC/static/js/halloween_pages/whack_a_bat.js` |
| Q6 | … zombie typing game | 🦇 | page `zombie_typing`; edit `HC/static/js/halloween_pages/zombie_typing.js` |
| Q7 | … memory pairs | 🦇 | page `memory`; edit `HC/static/js/halloween_pages/memory.js` |
| Q8 | … sliding moon puzzle | 🦇 | page `sliding_puzzle`; edit `HC/static/js/halloween_pages/sliding_puzzle.js` |
| Q9 | … bat snake | 🦇 | page `bat_snake`; edit `HC/static/js/halloween_pages/bat_snake.js` |
| Q10 | Ifi Halloween quiz: 10 questions, with a score | 🧪 | page `quiz`; new `HC/tests/test_quiz.py` |
| Q11 | Graveyard of retired features | 🦇 | page `graveyard` |
| Q12 | Live countdown page | 🧪 | page `countdown`; edit `HC/static/js/halloween_pages/countdown.js`; new `HC/tests/test_countdown.py` |
| Q13 | Pumpkin carver | 🦇 | page `pumpkin_carver`; edit `HC/static/js/halloween_pages/pumpkin_carver.js` |
| Q14 | Spooky soundboard | 🦇 | page `soundboard`; edit `HC/static/js/halloween_pages/soundboard.js`; new `ifiplatform/static/audio/halloween/howl.mp3`, `creak.mp3`, `thunder.mp3`, `scream.mp3` (CC0) |
| Q15 | Halloween 404 page (preview at the scaffolded `/halloween/404-preview/`) | 🎨 | edit `TPL/404.html`; edit `CSS/page_404.css` |
| Q16 | Real moon phase on the moon | 🧪 | new `HC/moon_phase.py`; new `HC/templatetags/moon_tags.py`; new `HC/tests/test_moon_phase.py`; edit `TPL/partials/halloween_decor.html` (only the moon line); edit `CSS/moon_phase.css` |
| Q17 | `is_open()` with overnight hours, with tests | 🧪 | edit `HOME/opening_hours.py`; new `HOME/tests/test_opening_hours.py` |
| Q18 | A ghost follows the cursor | 🦇 | edit `JS/ghost_follow.js`; edit `CSS/ghost_follow.css` |
| Q19 | Candy rain with the Konami code | 🦇 | edit `JS/candy_rain.js` |
| Q20 | Flashlight mode | 🦇 | edit `JS/flashlight.js`; edit `CSS/flashlight.css` |
| Q21 | "Add to calendar" (.ics) for events | 🧪 | edit `HC/views/ics.py`; new `HC/tests/test_ics.py`; edit `HOME/templates/events/partials/add_to_calendar.html` |
| Q22 | `python manage.py halloween_stats` | 🧪 | new `HC/management/commands/halloween_stats.py`; new `HC/tests/test_halloween_stats.py` |
| Q23 | Draw the Halloween corner mascot | 🖼️ | new `IMG/mascot.svg`; edit `HC/templates/halloween/partials/mascot.html` |
| Q24 | Draw 6 pumpkin faces for the carver presets | 🖼️ | new `IMG/faces/face1.svg` … `face6.svg` |
| Q25 | Write "How to add a Halloween corner page" | 📚 | new `docs/contributing/halloween_corner.md` |
| Q26 | Home page accessibility check: fix 3 CSS findings | ♿ | edit `CSS/a11y_fixes.css` |
| Q27 | Accessible hub page: landmarks, heading order, focus order (don't change the `{% include %}` lines) | ♿ | edit `HC/templates/halloween/hub.html` |
| Q28 | 👻 The fortune teller crashes on names with æøå (planted) | 👻 | edit `HC/fortune_names.py` |
| Q29 | Drag notes around the haunted board (positions remembered in your browser with localStorage) | 🦇 | edit `HC/static/js/halloween_pages/board_drag.js` |
| Q30 | Halloween hub page design | 🎨 | edit `HC/static/css/halloween_pages/hub.css` |
| Q31 | Costume of the day (seeded by date), with tests | 🧪 | new `HC/costume_of_the_day.py`; new `HC/templatetags/costume_tags.py`; new `HC/tests/test_costume_of_the_day.py`; edit `HC/templates/halloween/partials/costume_of_the_day.html` |

**Totals: 60 🍬, 33 🍫, 31 🎃.** There are no admin-only content issues. Sets:
- 🍬: Moon, Shortcut icons, Footer, Spider
- 🍫: Right column extras, Pages go Halloween, Board styles
- 🎃: Fortune booth, Halloween arcade

**The scaffold must create** every file marked **edit** above that doesn't exist yet:
- **Empty:** the CSS, JS, partials, `__init__.py` files and the view stubs.
- **Placeholders:** `IMG/output_cover.svg` and `IMG/instagram/tile1–5.svg`.
- **Hub includes:** `spooky_demo.html`, `mascot.html` and `costume_of_the_day.html` are already included in `hub.html`.
- **Event includes:** `halloween_countdown.html` and `add_to_calendar.html` are already included in the event templates.
- **Wiring:** every URL, plus the CSS and JS links.

Before the event, a script checks that **no file appears in two issues' lists**.

Overlaps to watch:
- K7 (badge CSS) and Q17 (`is_open`) use different files. Without Q17 the badges just don't show.
- Q16 only changes the moon line of `halloween_decor.html`. No other issue edits that file.
- Q28 and Q1: the planted bug lives in `fortune_names.py`. Q1 only imports it.

## Producing it
1. **One data file** in the scratchpad, `event_issues.py`. Each issue has: id, title, size, category, type, reward (🪙/🏆), estimated minutes, set, files, what, solution or starter, make-it-yours, done-when, and the helper note. Every issue ends with the same local `ifi` block.
2. **A generator** builds from it:
   - the issue bodies, in the phase 1 style, with the shared "How to work on it" block
   - `solutions.json` for `load_event_solutions` (with a "Files:" line)
   - a `gh` script that creates the labels, issues, types and sub-issues, then fills in the real numbers
3. **Build order:**
   - the scaffold first, because everything depends on it
   - then all 🍬 issues, since most people start there
   - then 🍫, then 🎃
4. **Each solution:** written on its own branch in the throwaway repo. Updating the preview's Final tab is optional.

The event is in 3 days. If time runs short, cut 🎃 Halloween corner pages first, keeping at least 30 🎃.

## Verification
- **No shared files:** a script reads every issue's file list from the data file and fails if any path appears in two issues.
- **Conflict test:** every solution branch, merged together on the scaffold, merges cleanly. Then `python manage.py test --exclude-tag=slow` passes, and the home page renders.
- **File lists:** for each issue, `git diff --name-only scaffold...branch` equals its "Files to change" list. The Files check regex extracts the same list from each generated body.
- **Each solution alone:** it passes the quick tests and renders its page.
- **Before creating issues on GitHub:** the user reviews the generated issue texts.
