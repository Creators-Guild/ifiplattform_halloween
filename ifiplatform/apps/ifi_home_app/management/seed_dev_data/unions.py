"""Student-union seeding: the two demo unions under Sosialt, and the
Fadderuke-hosting union roster used by events.py's sub-event seeding."""

from ifi_home_app.models.article_models import StudentUnionCategoryPage, UnionPage

from .constants import (
    FADDERUKE_UNION_PEOPLY_IDS,
    FADDERUKE_UNION_SPECS,
    LONG_UNION_NAME,
)


class UnionSeedMixin:
    def _seed_student_unions(self, sosialt_category, nb_locale, seed_image):
        union_category = self._get_or_create_page(
            sosialt_category,
            StudentUnionCategoryPage,
            "Studentforeninger",
            nb_locale,
        )
        self._translate_page(union_category)

        for name in ["Testforening 1", "Testforening 2", LONG_UNION_NAME]:
            union = self._get_or_create_page(
                union_category,
                UnionPage,
                name,
                nb_locale,
                email="testforening@example.com",
                logo=seed_image,
                purpose="Test-formål generert av seed-scriptet.",
                activities="Test-aktiviteter generert av seed-scriptet.",
                union_type="general",
                website_url="https://example.com",
                social_links=[
                    (
                        "social_link",
                        {
                            "platform": "instagram",
                            "url": "https://instagram.com/example",
                        },
                    ),
                ],
                member_count_intern=0,
                sitting_members=[
                    (
                        "member",
                        {
                            "name": "Test Testesen",
                            "role": "Leder",
                            "role_nickname": "Guild Master",
                            "school_email": "test@ifi.uio.no",
                            "picture": seed_image,
                            "responsibilities": [
                                "Test-ansvar generert av seed-scriptet."
                            ],
                            "availability": "opening_soon",
                            "availability_note": "Etter neste generalforsamling",
                        },
                    ),
                    (
                        "member",
                        {
                            "name": "",
                            "role": "Nestleder",
                            "role_nickname": "",
                            "school_email": "",
                            "responsibilities": [
                                "Test-ansvar generert av seed-scriptet."
                            ],
                            "availability": "open",
                            "availability_note": "",
                        },
                    ),
                ],
            )
            self._translate_page(union)

    def _seed_fadderuke_unions(self, nb_locale, seed_image):
        """Creates the minimal UnionPage per name in FADDERUKE_UNION_SPECS
        (as children of the same Studentforeninger category Testforening
        1/2 live under), for FADDERUKE_SUB_EVENT_UNIONS to link sub-events
        to via EventPage.related_unions. Returns {title: nb UnionPage}.

        Navet alone also gets a full sitting_members spread plus fake
        contact/social data -- see docs/claude_context/article_unions.md."""
        union_category = StudentUnionCategoryPage.objects.get(
            slug="studentforeninger", locale=nb_locale
        )
        unions = {}
        for title in FADDERUKE_UNION_SPECS:
            extra_kwargs = (
                {
                    "sitting_members": self._navet_sitting_members(seed_image),
                    "email": "navet@ifi.uio.no",
                    "website_url": "https://ifinavet.no",
                    "union_links": [
                        (
                            "link",
                            {
                                "label": "Bli medlem",
                                "url": "https://ifinavet.no/bli-medlem",
                            },
                        ),
                        (
                            "link",
                            {
                                "label": "Søk verv i styret",
                                "url": "https://ifinavet.no/verv",
                            },
                        ),
                    ],
                    "social_links": [
                        (
                            "social_link",
                            {
                                "platform": "instagram",
                                "url": "https://instagram.com/ifinavet",
                            },
                        ),
                        (
                            "social_link",
                            {
                                "platform": "linkedin",
                                "url": "https://linkedin.com/company/ifinavet",
                            },
                        ),
                    ],
                    "member_count_intern": 3,
                }
                if title == "Navet"
                else {}
            )
            union = self._get_or_create_page(
                union_category,
                UnionPage,
                title,
                nb_locale,
                logo=seed_image,
                purpose="En studentforening ved Ifi generert av seed-scriptet.",
                union_type="general",
                peoply_organization_id=FADDERUKE_UNION_PEOPLY_IDS.get(title, ""),
                **extra_kwargs,
            )
            self._translate_page(union)
            unions[title] = union
        return unions

    def _navet_sitting_members(self, seed_image):
        # Every optional CharBlock below is given an explicit value (even ""
        # or []) rather than omitted -- an omitted key resolves to None here
        # (raw StreamField construction, unlike an admin form submission)
        # and crashes the English extraction (_translate_page). picture
        # (ImageChooserBlock, not a string segment) is unaffected, so it's
        # simply left out where there's no picture. responsibilities takes a
        # plain list of strings here (raw-construction input, not the
        # {"type": "item", ...} shape the field serializes to on save).
        return [
            (
                "member",
                {  # filled, opening soon, every field set
                    "name": "Kari Nordmann",
                    "role": "Leder",
                    "role_nickname": "Husets Sjel",
                    "school_email": "kari@ifi.uio.no",
                    "picture": seed_image,
                    "responsibilities": [
                        "Ansvarlig for driften av Navet og koordinering av frivillige."
                    ],
                    "availability": "opening_soon",
                    "availability_note": "Etter neste generalforsamling",
                },
            ),
            (
                "member",
                {  # filled, every optional field left blank
                    "name": "Ola Nordmann",
                    "role": "Kasserer",
                    "role_nickname": "",
                    "school_email": "",
                    "responsibilities": [],
                    "availability": "filled",
                    "availability_note": "",
                },
            ),
            (
                "member",
                {  # vacant/open, every field set
                    "name": "",
                    "role": "Aktivitetsansvarlig",
                    "role_nickname": "Festfixer",
                    "school_email": "aktivitet@navet.example",
                    "picture": seed_image,
                    "responsibilities": [
                        "Planlegger sosiale arrangementer i Navet.",
                        "Bestiller mat og drikke til arrangementer.",
                    ],
                    "availability": "open",
                    "availability_note": "Søknadsfrist 1. september",
                },
            ),
            (
                "member",
                {  # vacant/open, every optional field left blank
                    "name": "",
                    "role": "Vaktansvarlig",
                    "role_nickname": "",
                    "school_email": "",
                    "responsibilities": [],
                    "availability": "open",
                    "availability_note": "",
                },
            ),
        ]
