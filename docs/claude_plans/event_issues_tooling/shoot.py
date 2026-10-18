"""One screenshot per event issue, from the pilot repo with every solution
merged (served on 127.0.0.1:8011). Saves JPEGs to the folder given as argv[1].
Run with shot_env.sh sourced (local Chromium libraries and fonts)."""

import html
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8011"
OUT = Path(sys.argv[1])
REPO = Path(__file__).parent / "pilot_repo"
ARTICLE = "/nb/nyheter/siste-nytt/spkelse-observert-i-ole-johan-dahls-hus/"
EVENT = "/nb/arrangementer/gresskarskjring/"
BAT = (REPO / "ifiplatform/static/images/halloween/bat.svg").read_text()
SKULL = (REPO / "ifiplatform/templates/partials/icons/account_icon.html").read_text()


def card(page, inner, width=900, height=None):
    """A plain dark card for things a page screenshot can't show."""
    page.set_viewport_size({"width": width, "height": height or 400})
    page.set_content(
        "<body style='margin:0;background:#2b2b30;color:#f2eff6;font:16px DejaVu Sans,sans-serif'>"
        f"<div style='padding:24px'>{inner}</div></body>"
    )


def terminal(page, command, output):
    card(page, f"<pre style='margin:0;background:#111;color:#e6e6e6;padding:18px;border-radius:8px;font:15px DejaVu Sans Mono,monospace'>$ {html.escape(command)}\n{html.escape(output)}</pre>")


def manage(*args):
    return subprocess.run(
        ["python", "manage.py", *args], cwd=REPO / "ifiplatform", capture_output=True, text=True, check=True
    ).stdout


def go(page, path, width=1280, height=900):
    page.set_viewport_size({"width": width, "height": height})
    page.goto(BASE + path, wait_until="networkidle")
    page.add_style_tag(content="#beta-notice-modal, #deploy-notice-root { display: none !important; }")


def around(page, selector, pad=40):
    """A clip around an element, with some of the page around it."""
    page.locator(selector).first.scroll_into_view_if_needed()
    box = page.locator(selector).first.bounding_box()
    x, y = max(0, box["x"] - pad), max(0, box["y"] - pad)
    return {"x": x, "y": y, "width": min(1280 - x, box["width"] + 2 * pad), "height": box["height"] + 2 * pad}


def save(page, issue_id, clip=None, selector=None, full=False):
    path = OUT / f"{issue_id}.jpg"
    if selector:
        page.locator(selector).first.screenshot(path=path, type="jpeg", quality=82)
    else:
        page.screenshot(path=path, type="jpeg", quality=82, clip=clip, full_page=full)
    print("saved", path.name)


def note(page, issue_id, title):
    go(page, "/nb/halloween/board/")
    page.add_style_tag(content=".note { translate: none !important; }")
    save(page, issue_id, selector=f".note:has(.note__title:text-is('{title}'))")


def shots(page):
    go(page, "/nb/")
    save(page, "C1", clip={"x": 0, "y": 0, "width": 1280, "height": 900})
    save(page, "P1", selector=".topheader-content")
    save(page, "K1", clip={"x": 0, "y": 0, "width": 640, "height": 460})
    save(page, "P5", selector=".bot-bar")
    save(page, "P8", selector=".messageboard")
    save(page, "P3", selector=".suggestions-row")

    for _ in range(40):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.closest('#home-shortcuts') !== null"):
            break
    save(page, "P9", selector="#home-shortcuts")

    moon = {"x": 1280 - 520, "y": 40, "width": 520, "height": 470}
    go(page, "/nb/")
    page.add_style_tag(content=".moon::before, .moon::after { display: none !important; } .moon { box-shadow: none !important; }")
    save(page, "P10a", clip=moon)
    go(page, "/nb/")
    page.add_style_tag(content=".moon { box-shadow: none !important; }")
    save(page, "P10b", clip=moon)
    go(page, "/nb/")
    save(page, "P10c", clip=moon)

    go(page, "/nb/")
    page.add_style_tag(content=".ghost { animation-delay: -6s !important; animation-play-state: paused !important; }")
    save(page, "K3", clip={"x": 0, "y": 200, "width": 1280, "height": 500})

    go(page, "/nb/")
    page.evaluate(
        """svg => {
            const links = document.querySelector('.nav_links');
            const last = links.lastElementChild;
            const button = document.createElement('button');
            button.className = 'link profile-trigger';
            button.innerHTML = svg;
            last.replaceWith(button);
        }""",
        SKULL,
    )
    save(page, "K5", clip={"x": 760, "y": 0, "width": 520, "height": 120})

    go(page, "/nb/")
    page.evaluate(
        """svg => {
            const img = document.createElement('div');
            img.innerHTML = svg;
            Object.assign(img.style, {position: 'fixed', left: '640px', top: '330px', width: '40px', height: '40px', zIndex: 99});
            img.firstElementChild.setAttribute('width', '40');
            img.firstElementChild.setAttribute('height', '40');
            document.body.append(img);
        }""",
        BAT,
    )
    save(page, "P2", clip={"x": 440, "y": 200, "width": 460, "height": 300})

    favicon = (REPO / "ifiplatform/static/images/favicon.svg").read_text()
    card(page, f"""
        <div style='display:flex;gap:28px;align-items:center'>
          <div style='background:#dfe1e5;color:#202124;border-radius:10px 10px 0 0;padding:10px 16px;display:flex;gap:10px;align-items:center;width:300px'>
            <span style='width:18px;height:18px;display:inline-block'>{favicon.replace('<svg ', '<svg width="18" height="18" ', 1)}</span>
            Ifi Plattform
          </div>
          <span style='width:120px;height:120px;display:inline-block;background:#fff;border-radius:12px;padding:8px'>{favicon.replace('<svg ', '<svg width="120" height="120" ', 1)}</span>
        </div>""", height=190)
    save(page, "P6")

    readme = (REPO / "ifiplatform/static/css/README.md").read_text().split("## The Halloween layer")[1]
    card(page, "<h2 style='margin:0 0 8px'>The Halloween layer (<code>07_halloween/</code>)</h2><p style='max-width:62ch;line-height:1.5'>" + html.escape(readme.strip().split("\n", 1)[1]).replace("`", "") + "</p>", height=210)
    save(page, "P7")


    terminal(page, "python manage.py carve_pumpkin --size 3", manage("carve_pumpkin", "--size", "3"))
    save(page, "K19", selector="pre")
    terminal(page, "python manage.py halloween_stats", manage("halloween_stats"))
    save(page, "Q22", selector="pre")

    card(page, """
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:24px'>
          <div style='background:#3a3a44;border-radius:8px;padding:16px'><b>Animations on</b><p>👻 floats across the page every 20 seconds.</p></div>
          <div style='background:#3a3a44;border-radius:8px;padding:16px'><b>prefers-reduced-motion: reduce</b><p>The ghost stays hidden: nothing on the page moves.</p></div>
        </div>""", height=200)
    save(page, "K28")

    go(page, ARTICLE)
    save(page, "K14", clip={"x": 0, "y": 0, "width": 1280, "height": 760})
    page.click(".select-language-buttons button[value='en']")
    page.wait_for_load_state("networkidle")
    page.add_style_tag(content="#beta-notice-modal, #deploy-notice-root { display: none !important; }")
    url = page.url.replace(BASE, "localhost:8000")
    page.evaluate(
        """url => {
            const bar = document.createElement('div');
            bar.textContent = '🔒 ' + url;
            Object.assign(bar.style, {position: 'fixed', top: 0, left: 0, right: 0, padding: '10px 16px', background: '#dfe1e5', color: '#202124', font: '15px DejaVu Sans, sans-serif', zIndex: 999});
            document.body.append(bar);
        }""",
        url,
    )
    save(page, "K30", clip={"x": 0, "y": 0, "width": 1280, "height": 360})

    go(page, EVENT)
    save(page, "K15", clip={"x": 0, "y": 0, "width": 1280, "height": 760})
    go(page, "/nb/account/login")
    save(page, "K16", clip={"x": 0, "y": 0, "width": 1280, "height": 760})
    go(page, "/nb/study/")
    save(page, "K17", clip={"x": 0, "y": 0, "width": 1280, "height": 700})

    for issue_id, title in [
        ("P4", "Here lies the 2nd-floor coffee machine"),
        ("C34", "Do NOT make eye contact with the 3rd-floor printer"),
        ("C35", "Rule 13: commit before you leave the room"),
        ("C36", "MISSING: my motivation"),
    ]:
        note(page, issue_id, title)

    for issue_id, path in [
        ("Q1", "/nb/halloween/fortune/?name=Kari"),
        ("Q2", "/nb/halloween/spooky-name/?name=Kari"),
        ("Q3", "/nb/halloween/potion/?ingredient=bat_wing&ingredient=coffee&brew=1"),
        ("Q28", "/nb/halloween/fortune/?name=%C3%85se"),
        ("Q15", "/nb/halloween/404-preview/"),
        ("Q23", "/nb/halloween/"),
    ]:
        go(page, path)
        save(page, issue_id, clip={"x": 0, "y": 0, "width": 1280, "height": 760})

    go(page, "/nb/halloween/whack-a-bat/")
    page.click("#wab-start")
    page.wait_for_timeout(1300)
    page.locator(".wab-hole:text-is('🦇')").first.click()
    page.wait_for_timeout(1100)
    save(page, "Q5", clip={"x": 0, "y": 0, "width": 1280, "height": 760})

    go(page, "/nb/halloween/memory/")
    cards = page.locator(".memory-card")
    symbols = [cards.nth(i).get_attribute("data-symbol") for i in range(cards.count())]
    first = symbols.index("🎃")
    second = symbols.index("🎃", first + 1)
    cards.nth(first).click()
    cards.nth(second).click()
    other = next(i for i, s in enumerate(symbols) if s != "🎃")
    cards.nth(other).click()
    save(page, "Q7", clip={"x": 0, "y": 0, "width": 1280, "height": 760})

    go(page, "/nb/halloween/board/")
    note_box = page.locator(".note").first.bounding_box()
    page.mouse.move(note_box["x"] + 40, note_box["y"] + 30)
    page.mouse.down()
    page.mouse.move(note_box["x"] + 260, note_box["y"] + 140, steps=8)
    page.mouse.up()
    save(page, "Q29", clip={"x": 0, "y": 0, "width": 1280, "height": 860})


def shots_more(page):
    """The issues after the pilot."""
    hide_moving = ".ghost, .bat-flock, .ghost-follower, .flashlight-toggle { display: none !important; } .spider { animation: none !important; }"

    go(page, "/nb/")
    page.add_style_tag(content=hide_moving)
    save(page, "C2", clip={"x": 0, "y": 20, "width": 640, "height": 100})
    save(page, "C3", clip={"x": 0, "y": 20, "width": 640, "height": 130})
    save(page, "C4", selector=".nav_links")
    save(page, "C5", clip={"x": 1280 - 400, "y": 0, "width": 400, "height": 60})
    save(page, "C6", clip={"x": 0, "y": 150, "width": 900, "height": 90})
    save(page, "C7", clip={"x": 0, "y": 0, "width": 420, "height": 700})
    save(page, "C8", selector="#home-shortcuts")
    save(page, "C9", selector="#home-shortcuts .shortcut-column")
    save(page, "C17", selector=".messageboard")
    save(page, "C18", selector=".newsbar_container")
    save(page, "K6", selector=".newsbar_container")
    save(page, "C20", selector=".eventsbox_container")
    save(page, "C22", selector=".home-eventsbox-days")
    save(page, "K27", selector=".home-eventsbox-days")
    save(page, "C23", selector=".output-box")
    save(page, "K11", selector=".output-box")
    save(page, "K7", selector=".hours-box")
    save(page, "K8", selector=".hours-box")
    save(page, "K9", selector=".insta-box")
    save(page, "K10", selector=".insta-row")
    save(page, "K2", selector=".bottombar-content")
    save(page, "Q26", selector=".home-eventsbox-days")

    go(page, "/nb/")
    page.add_style_tag(content=hide_moving)
    page.hover("#home-shortcuts .shortcut-card >> nth=1")
    page.add_style_tag(content="#home-shortcuts .shortcut-card { animation-delay: -0.1s !important; animation-play-state: paused !important; }")
    save(page, "C10", selector="#home-shortcuts")

    spider = {"x": 0, "y": 0, "width": 420, "height": 330}
    for issue_id, style in [
        ("C27", ".spider__legs { display: none !important; }"),
        ("C28", ""),
        ("C29", ".spider { animation-delay: 0s !important; animation-play-state: paused !important; }"),
    ]:
        go(page, "/nb/")
        page.add_style_tag(content=".ghost, .bat-flock, .flashlight-toggle { display: none !important; } " + style)
        if issue_id != "C29":
            page.add_style_tag(content=".spider { animation: none !important; }")
        save(page, issue_id, clip=spider)
    go(page, "/nb/")
    page.add_style_tag(content=hide_moving + " .spider { transition: none !important; }")
    page.evaluate("document.querySelector('.spider').classList.add('spider--startled')")
    page.wait_for_timeout(200)
    save(page, "K4", clip=spider)
    card(page, """
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:24px'>
          <div style='background:#3a3a44;border-radius:8px;padding:16px'><b>Animations on</b><p>🕷️ swings from side to side on its thread.</p></div>
          <div style='background:#3a3a44;border-radius:8px;padding:16px'><b>prefers-reduced-motion: reduce</b><p>The spider hangs still.</p></div>
        </div>""", height=200)
    save(page, "C30")

    go(page, "/nb/")
    page.add_style_tag(content=".ghost, .flashlight-toggle { display: none !important; } .bat-flock span { animation-play-state: paused !important; } "
                       ".bat-flock span:nth-child(1) { animation-delay: -3.2s !important; } .bat-flock span:nth-child(2) { animation-delay: -2s !important; } "
                       ".bat-flock span:nth-child(3) { animation-delay: -4.5s !important; }")
    save(page, "K34", clip={"x": 1280 - 900, "y": 40, "width": 900, "height": 470})

    go(page, "/nb/")
    page.add_style_tag(content=hide_moving)
    page.add_style_tag(content=".ghost, .bat-flock, .flashlight-toggle { display: none !important; }")
    save(page, "Q16", clip={"x": 1280 - 520, "y": 40, "width": 520, "height": 470})

    go(page, "/nb/")
    page.add_style_tag(content=hide_moving)
    page.click(".header-tagline")
    save(page, "K12", clip={"x": 0, "y": 20, "width": 760, "height": 130})

    go(page, "/nb/")
    page.add_style_tag(content=hide_moving)
    page.mouse.click(700, 760)
    page.keyboard.type("boo")
    page.wait_for_timeout(600)
    save(page, "K13", clip={"x": 0, "y": 0, "width": 1280, "height": 900})

    go(page, "/nb/")
    page.add_style_tag(content=hide_moving)
    for _ in range(12):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.classList.contains('nav_link')"):
            break
    save(page, "Q26-focus", selector=".topheader-content")

    # Headless Chromium reports no mouse, so the follower would never start:
    # a separate page that says it has one.
    mouse_page = page.context.browser.new_page(device_scale_factor=1)
    mouse_page.add_init_script("""
        const realMatchMedia = window.matchMedia.bind(window);
        window.matchMedia = (query) => query.includes("pointer: fine")
            ? { matches: true, media: query, addEventListener() {}, removeEventListener() {} }
            : realMatchMedia(query);
    """)
    go(mouse_page, "/nb/")
    mouse_page.add_style_tag(content=".ghost, .bat-flock, .flashlight-toggle { display: none !important; } .spider { animation: none !important; }")
    mouse_page.mouse.move(600, 230)
    for x, y in [(700, 260), (820, 300), (880, 320)]:
        mouse_page.mouse.move(x, y, steps=10)
    mouse_page.wait_for_timeout(250)
    save(mouse_page, "Q18", clip={"x": 520, "y": 150, "width": 520, "height": 260})
    mouse_page.close()

    go(page, "/nb/")
    page.add_style_tag(content=".ghost, .bat-flock { display: none !important; } .spider { animation: none !important; }")
    page.mouse.click(700, 760)
    for key in ["ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown", "ArrowLeft", "ArrowRight", "ArrowLeft", "ArrowRight", "b", "a"]:
        page.keyboard.press(key)
    page.wait_for_timeout(2600)
    save(page, "Q19", clip={"x": 0, "y": 0, "width": 1280, "height": 900})

    go(page, "/nb/")
    page.add_style_tag(content=".ghost, .bat-flock { display: none !important; } .spider { animation: none !important; }")
    page.click(".flashlight-toggle")
    page.mouse.move(560, 460)
    page.wait_for_timeout(200)
    save(page, "Q20", clip={"x": 0, "y": 0, "width": 1280, "height": 900})

    for issue_id, lines in [
        ("C31", ['{% if day.time_tag == "today" %}{% trans "Today" %}', '{% elif day.time_tag == "tomorrow" %}{% trans "Tomorrow" %}']),
        ("C33", ['<img src="{{ article_thumb.url }}" alt="{{ article.hero_image_alt }}">', '<img src="{% static \'images/news/IfiBygg.jpg\' %}" alt="">']),
    ]:
        terminal(page, "the fixed lines", "\n".join(lines))
        save(page, issue_id, selector="pre")


    terminal(page, "python manage.py test ifi_home_app.tests.test_opening_hours -v 2",
             subprocess.run(["python", "manage.py", "test", "ifi_home_app.tests.test_opening_hours", "-v", "2"],
                            cwd=REPO / "ifiplatform", capture_output=True, text=True).stderr.split("Destroying")[0].split("System check")[-1].strip())
    save(page, "Q17", selector="pre")

    go(page, "/nb/halloween/")
    page.add_style_tag(content=hide_moving)
    save(page, "Q30", clip={"x": 0, "y": 0, "width": 1280, "height": 900})
    save(page, "K31", selector=".hc-hub")
    save(page, "K20", clip=around(page, ".hc-spooky-demo"))
    save(page, "Q31", clip=around(page, ".hc-costume-of-the-day"))
    save(page, "Q27", clip={"x": 0, "y": 150, "width": 1280, "height": 500})

    go(page, "/nb/arrangementer/")
    page.add_style_tag(content=hide_moving)
    save(page, "K21", clip={"x": 0, "y": 150, "width": 1000, "height": 320})
    go(page, EVENT)
    page.add_style_tag(content=hide_moving)
    save(page, "K29", selector=".event-page-prose")
    save(page, "Q21", selector=".event-page-prose")

    for issue_id, path in [
        ("K22", "/nb/halloween/costume/?roll=1"),
        ("Q4", "/nb/halloween/story/?name=Kari&place=the+3rd+floor&food=taco&number=13&creature=mummy&sound=BOO&tell=1"),
        ("Q10", "/nb/halloween/quiz/?q1=the+programming+language+Simula&q2=A+jack-o%27-lantern&q3=31+October&q4=6&check=1"),
        ("Q11", "/nb/halloween/graveyard/"),
        ("Q12", "/nb/halloween/countdown/"),
    ]:
        go(page, path)
        page.add_style_tag(content=hide_moving)
        page.wait_for_timeout(1100)
        save(page, issue_id, clip={"x": 0, "y": 0, "width": 1280, "height": 900})

    for n in range(1, 11):
        go(page, f"/nb/study/?joke={n:02d}")
        page.add_style_tag(content=hide_moving)
        save(page, f"C{48 + n}", selector="#study-joke")

    go(page, "/nb/study/?joke=03")
    page.add_style_tag(content=hide_moving)
    page.click(".joke-rating__button--up")
    save(page, "K36", selector=".under-development")
    page.context.grant_permissions(["clipboard-read", "clipboard-write"])
    page.click(".joke-copy")
    save(page, "K37", selector=".under-development")
    page.click("#study-another")
    page.wait_for_timeout(400)
    save(page, "Q32", selector=".under-development")
    terminal(page, "python manage.py test study_app.test_joke_files -v 2",
             subprocess.run(["python", "manage.py", "test", "study_app.test_joke_files", "-v", "2"],
                            cwd=REPO / "ifiplatform", capture_output=True, text=True).stderr.split("Destroying")[0].split("System check")[-1].strip())
    save(page, "K38", selector="pre")

    go(page, "/nb/halloween/zombie-typing/")
    page.add_style_tag(content=hide_moving)
    page.click("#zt-start")
    page.wait_for_timeout(4500)
    page.fill("#zt-input", "pum")
    save(page, "Q6", clip={"x": 0, "y": 0, "width": 1280, "height": 760})

    go(page, "/nb/halloween/moon-puzzle/")
    page.add_style_tag(content=hide_moving)
    page.click("#sp-shuffle")
    save(page, "Q8", clip={"x": 0, "y": 0, "width": 1280, "height": 760})

    go(page, "/nb/halloween/bat-snake/")
    page.add_style_tag(content=hide_moving)
    page.click("#bs-start")
    page.wait_for_timeout(500)
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(500)
    save(page, "Q9", clip={"x": 0, "y": 0, "width": 1280, "height": 860})

    go(page, "/nb/halloween/pumpkin-carver/")
    page.add_style_tag(content=hide_moving)
    face = [(3, 3), (3, 4), (2, 4), (3, 9), (3, 10), (2, 9), (5, 6), (5, 7), (7, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 8), (8, 9), (8, 10), (7, 11), (7, 6)]
    for row, col in face:
        page.locator(".carver-cell").nth(row * 14 + col).click()
    page.click("#carver-light")
    page.mouse.move(5, 5)
    save(page, "Q13", clip={"x": 0, "y": 0, "width": 1280, "height": 760})
    save(page, "Q24", selector=".carver-ideas")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        page.emulate_media(reduced_motion="no-preference")
        shots(page)
        shots_more(page)
        browser.close()


if __name__ == "__main__":
    main()
