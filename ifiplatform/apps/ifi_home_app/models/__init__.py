"""Models module for IFI home app."""

__all__ = [
    "StudentUnion",
    "ArticlePage",
    "ArticleIndexPage",
    "HeaderMessage",
    "HomeBoardMessage",
    "EventIndexPage",
    "EventPage",
    "GlossarySyncState",
    "Menu",
    "MenuGroup",
    "MenuGroupLink",
    "MenuSlot",
]

from .home_models import *
from .article_models import ArticlePage, ArticleIndexPage
from .site_models import HeaderMessage
from .event.pages import EventIndexPage, EventPage
from .event import peoply  # noqa: F401 -- imported so Django registers its models
from .glossary_models import GlossarySyncState
from .menus import Menu, MenuGroup, MenuGroupLink, MenuSlot
