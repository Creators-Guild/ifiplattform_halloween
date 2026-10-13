"""Keep the Wagtail admin Norwegian-only: English pages and snippets are
hidden from listings and choosers, and reached only through translation
mirroring. Superusers can toggle English back on for debugging.

Design rationale: docs/claude_context/admin_locales.md"""

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from wagtail.admin.menu import MenuItem
from wagtail.snippets.views.chooser import (
    ChooseResultsView,
    ChooseView,
    SnippetChooserViewSet,
)
from wagtail.snippets.views.snippets import IndexView, SnippetViewSet

from .sync import SOURCE_LANGUAGE_CODE

SESSION_KEY = "show_all_locales"


def show_all_locales(request):
    return request.user.is_superuser and request.session.get(SESSION_KEY, False)


def filter_explorer_pages(parent_page, pages, request):
    """Only the parent's own locale -- nb at the tree root -- so the English
    tree is hidden, but an English page opened via "Translations" still
    lists its English children."""
    if show_all_locales(request):
        return pages
    if parent_page.is_root():
        return pages.filter(locale__language_code=SOURCE_LANGUAGE_CODE)
    return pages.filter(locale_id=parent_page.locale_id)


def filter_chooser_pages(pages, request):
    if show_all_locales(request):
        return pages
    return pages.filter(locale__language_code=SOURCE_LANGUAGE_CODE)


def toggle_all_locales(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    request.session[SESSION_KEY] = not request.session.get(SESSION_KEY, False)
    next_url = request.META.get("HTTP_REFERER")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return redirect(next_url)
    return redirect(reverse("wagtailadmin_home"))


class ToggleAllLocalesMenuItem(MenuItem):
    def __init__(self):
        super().__init__(
            "Show English pages",
            reverse_lazy("toggle_all_locales"),
            name="toggle-all-locales",
            icon_name="globe",
            order=10000,
        )

    def is_shown(self, request):
        return request.user.is_superuser

    def render_component(self, request):
        self.label = (
            "Hide English pages" if show_all_locales(request) else "Show English pages"
        )
        return super().render_component(request)


def _default_to_norwegian(request, params):
    """Snippet listings/choosers default their locale filter to "All" --
    preselect nb instead, unless a locale was picked (incl. "All")."""
    if "locale" in params or show_all_locales(request):
        return params
    params = params.copy()
    params["locale"] = SOURCE_LANGUAGE_CODE
    return params


class NorwegianFirstIndexView(IndexView):
    def get_filterset_kwargs(self):
        kwargs = super().get_filterset_kwargs()
        kwargs["data"] = _default_to_norwegian(self.request, kwargs["data"])
        return kwargs


class NorwegianFirstChooseMixin:
    def get_filter_form(self):
        return self.get_filter_form_class()(
            _default_to_norwegian(self.request, self.request.GET)
        )


class NorwegianFirstChooseView(NorwegianFirstChooseMixin, ChooseView):
    pass


class NorwegianFirstChooseResultsView(NorwegianFirstChooseMixin, ChooseResultsView):
    pass


class NorwegianFirstChooserViewSet(SnippetChooserViewSet):
    choose_view_class = NorwegianFirstChooseView
    choose_results_view_class = NorwegianFirstChooseResultsView


class NorwegianFirstSnippetViewSet(SnippetViewSet):
    """For translatable snippets: listing and chooser open on nb."""

    index_view_class = NorwegianFirstIndexView
    chooser_viewset_class = NorwegianFirstChooserViewSet
