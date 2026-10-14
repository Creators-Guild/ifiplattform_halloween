"""The Wagtail dashboard's own panels: "How this site works" (a short guide
for editors) and "Shortcuts" (links to the parts of the admin editors use
most, each shown only to users who may open it)."""

from django.urls import reverse
from wagtail.admin.ui.components import Component
from wagtail.images.permissions import permission_policy as image_permissions
from wagtail.models import Site


class GuidePanel(Component):
    name = "guide"
    order = 30  # above "Shortcuts" (40)
    template_name = "wagtailadmin/home/guide.html"


class ShortcutsPanel(Component):
    name = "shortcuts"
    order = 40  # above "Needs English translation" (50)
    template_name = "wagtailadmin/home/shortcuts.html"

    def __init__(self, request):
        self.request = request

    def get_context_data(self, parent_context=None):
        user = self.request.user
        site = Site.find_for_request(self.request)
        pages_url = (
            reverse("wagtailadmin_explore", args=[site.root_page_id])
            if site
            else reverse("wagtailadmin_explore_root")
        )
        shortcuts = [
            ("Pages", pages_url, "doc-empty-inverse"),
            ("Snippets", reverse("wagtailsnippets:index"), "snippet"),
        ]
        if image_permissions.user_has_any_permission(user, ["add", "change", "delete"]):
            shortcuts.append(("Images", reverse("wagtailimages:index"), "image"))

        settings = [
            (
                "Translation settings",
                reverse(
                    "wagtailsettings:edit", args=["ifi_home_app", "translationsettings"]
                ),
                "ifi_home_app.change_translationsettings",
            ),
            ("Users", reverse("wagtailusers_users:index"), "auth.change_user"),
            (
                "Redirects",
                reverse("wagtailredirects:index"),
                "wagtailredirects.change_redirect",
            ),
            ("Sites", reverse("wagtailsites:index"), "wagtailcore.change_site"),
        ]
        settings = [
            (label, url) for label, url, perm in settings if user.has_perm(perm)
        ]
        if user.is_superuser:
            settings.append(("Stored English", reverse("stored_english:index")))
        return {"shortcuts": shortcuts, "settings": settings}


def add_dashboard_panel(request, panels):
    panels.append(GuidePanel())
    panels.append(ShortcutsPanel(request))
