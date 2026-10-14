"""Menu seeding: the MenuGroups and the three Menus (sidemenu, home
dropmenus, homepage shortcuts) -- same layout migration 0152_menus builds
for existing databases. Each group's title and link labels get stored
English (_store_english)."""

from ifi_home_app.models import ArticleIndexPage, EventIndexPage
from ifi_home_app.models.article_models import (
    CategoryPage,
    StudentUnionCategoryPage,
    UnionPage,
)
from ifi_home_app.models.menus import Menu, MenuGroup, MenuGroupLink, MenuSlot

from .constants import CATEGORY_SPECS, LONG_UNION_NAME

LISTINGS_AT = ("Annonser hos", "Listings at")


class MenuSeedMixin:
    def _seed_menus(self, nb_locale):
        if Menu.objects.exists():
            self.skipped_count += 1
            return

        def nb_page(model, **filters):
            return model.objects.live().filter(locale=nb_locale, **filters).first()

        def children(parent):
            return list(parent.get_children().live()) if parent else []

        info_index = nb_page(ArticleIndexPage, section="info_articles")
        news_index = nb_page(ArticleIndexPage, section="news")
        event_index = nb_page(EventIndexPage)
        unions_category = nb_page(StudentUnionCategoryPage, slug="studentforeninger")
        tools_category = nb_page(CategoryPage, slug="ifi-verktøy")
        new_student_category = nb_page(CategoryPage, slug="ny-ifi-student")
        top_categories = [
            nb_page(CategoryPage, title=title, depth=info_index.depth + 1)
            for title, _color in CATEGORY_SPECS
        ]

        def group(titles, link_page=None, links=(), short_titles=("", ""), icon=""):
            nb_group = MenuGroup(
                locale=nb_locale,
                title=titles[0],
                short_title=short_titles[0],
                link_page=link_page,
                icon=icon,
            )
            for order, link in enumerate(links):
                nb_group.links.add(
                    MenuGroupLink(
                        sort_order=order,
                        page=link.get("page"),
                        url=link.get("url", ""),
                        label=link.get("label", ("", ""))[0],
                        label_prefix=link.get("prefix", ("", ""))[0],
                        description=link.get("description", ""),
                    )
                )
            nb_group.save()

            self._store_english(
                nb_group, {"title": titles[1], "short_title": short_titles[1]}
            )
            for nb_link, link in zip(nb_group.links.all(), links):
                self._store_english(
                    nb_link,
                    {
                        "label": link.get("label", ("", ""))[1],
                        "label_prefix": link.get("prefix", ("", ""))[1],
                        # names (Peoply, Navet), the same in English
                        "description": link.get("description", ""),
                    },
                )

            self.created_count += 1
            self.stdout.write(f"  created MenuGroup: {titles[0]}")
            return nb_group

        def pages(page_list):
            return [{"page": page} for page in page_list if page is not None]

        def menu(key, slots):
            menu_obj = Menu(key=key)
            for order, (menu_group, column, hide_on_mobile) in enumerate(slots):
                menu_obj.slots.add(
                    MenuSlot(
                        sort_order=order,
                        group=menu_group,
                        column=column,
                        hide_on_mobile=hide_on_mobile,
                    )
                )
            menu_obj.save()
            self.created_count += 1
            self.stdout.write(f"  created Menu: {key}")

        info = group(
            ("Infoartikkler", "Info Articles"),
            info_index,
            pages(top_categories),
            icon="info",
        )
        news = group(
            ("Nyheter", "News"), news_index, pages(children(news_index)), icon="news"
        )
        events = group(("Arrangementer", "Events"), event_index, icon="events")
        help_group = group(("hJELP", "hELP"), nb_page(CategoryPage, slug="hjelp"))
        unions = group(
            ("Studentforeninger", "Student Unions"),
            unions_category,
            pages(
                [
                    nb_page(UnionPage, title="Navet"),
                    nb_page(UnionPage, title=LONG_UNION_NAME),
                ]
            ),
            short_titles=("Foreninger", "Unions"),
            icon="unions",
        )
        tools = group(
            ("Verktøy", "Tools"),
            tools_category,
            pages(children(tools_category)),
            icon="tools",
        )
        new_student = group(
            ("Ny Student?", "New Student?"),
            new_student_category,
            pages(children(new_student_category)),
        )

        shortcut_info = group(
            ("Info", "Info"), info_index, pages(top_categories[:4]), icon="info"
        )
        shortcut_unions = group(
            ("Foreninger", "Unions"), unions_category, icon="unions"
        )
        shortcut_events = group(
            ("Arrangementer", "Events"),
            event_index,
            [
                {"page": event_index, "label": ("Alle", "All")},
                {
                    "url": "https://peoply.app/",
                    "label": ("Foreningsarrangementer", "Union Events"),
                    "description": "Peoply",
                },
                {
                    "url": "https://ifinavet.no/events",
                    "label": ("Bedriftspresentasjoner", "Company Presentations"),
                    "description": "Navet",
                },
                {
                    "url": "https://dagenatifi.no/program/",
                    "label": ("Karrieredag", "Career Day"),
                    "description": "dagen@ifi",
                },
            ],
            icon="events",
        )
        jobs = group(
            ("Stillingsannonser", "Job Listings"),
            None,
            [
                {
                    "url": "https://dagenatifi.no/stillingsannonser/",
                    "label": ("dagen@ifi", "dagen@ifi"),
                    "prefix": LISTINGS_AT,
                },
                {
                    "url": "https://ifinavet.no/job-listings",
                    "label": ("Navet", "Navet"),
                    "prefix": LISTINGS_AT,
                },
            ],
            icon="jobs",
        )

        menu(
            "sidemenu",
            [
                (info, 1, False),
                (news, 1, False),
                (events, 1, False),
                (help_group, 1, False),
            ],
        )
        menu(
            "home_dropmenu",
            [
                (news, 1, True),
                (info, 1, True),
                (unions, 1, False),
                (tools, 1, False),
                (new_student, 1, False),
            ],
        )
        menu(
            "shortcuts",
            [
                (shortcut_info, 1, False),
                (shortcut_unions, 1, False),
                (news, 2, False),
                (shortcut_events, 2, False),
                (jobs, 3, False),
                (tools, 3, False),
            ],
        )
