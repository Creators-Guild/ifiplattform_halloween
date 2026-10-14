# pylint: disable=C0114,C0115,C0116
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import translation

from ifi_home_app.admin_dashboard import ShortcutsPanel


class ShortcutsPanelTests(TestCase):
    def labels(self, user):
        request = RequestFactory().get("/")
        request.user = user
        context = ShortcutsPanel(request).get_context_data()
        return (
            [label for label, _url, _icon in context["shortcuts"]],
            [label for label, _url in context["settings"]],
        )

    def test_superuser_sees_everything(self):
        admin = get_user_model().objects.create_superuser("kari", "k@test.com", "pw")
        shortcuts, settings = self.labels(admin)
        self.assertEqual(shortcuts, ["Pages", "Snippets", "Images"])
        self.assertEqual(
            settings,
            ["Translation settings", "Users", "Redirects", "Sites", "Stored English"],
        )

    def test_editor_sees_only_what_they_may_open(self):
        editor = get_user_model().objects.create_user("ola", "o@test.com", "pw")
        editor.groups.add(Group.objects.get(name="Editors"))
        editor.user_permissions.add(
            Permission.objects.get(codename="change_translationsettings")
        )
        shortcuts, settings = self.labels(editor)
        self.assertEqual(shortcuts, ["Pages", "Snippets", "Images"])
        self.assertEqual(settings, ["Translation settings"])

    def test_dashboard_panel_order(self):
        admin = get_user_model().objects.create_superuser("kari", "k@test.com", "pw")
        self.client.force_login(admin)
        html = self.client.get(reverse("wagtailadmin_home")).content.decode()
        self.assertIn("How this site works", html)
        self.assertIn('<details class="dashboard-guide">', html)  # starts closed
        self.assertLess(html.index('id="guide'), html.index('id="shortcuts'))
        self.assertLess(
            html.index('id="shortcuts'), html.index('id="translations-needed')
        )


class AdminLanguageTests(TestCase):
    def setUp(self):
        admin = get_user_model().objects.create_superuser("kari", "k@test.com", "pw")
        self.client.force_login(admin)

    def tearDown(self):
        # LocaleMiddleware leaves /en/'s language active in this thread;
        # later tests would run in English.
        translation.activate(settings.LANGUAGE_CODE)

    def test_admin_speaks_the_language_of_its_address(self):
        nb_html = self.client.get("/nb/wagtail-admin/").content.decode()
        en_html = self.client.get("/en/wagtail-admin/").content.decode()
        self.assertIn("Dokumenter", nb_html)
        self.assertNotIn("Dokumenter", en_html)
        self.assertIn("Documents", en_html)

    def test_switch_links_to_the_same_page_in_the_other_language(self):
        nb_html = self.client.get("/nb/wagtail-admin/images/?p=2").content.decode()
        self.assertIn("/en/wagtail-admin/images/?p=2", nb_html)
        en_html = self.client.get("/en/wagtail-admin/images/").content.decode()
        self.assertIn("/nb/wagtail-admin/images/", en_html)
        self.assertIn("Norsk", en_html)
