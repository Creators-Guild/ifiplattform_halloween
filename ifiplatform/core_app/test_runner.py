from django.apps import apps
from django.conf import settings
from django.test.runner import DiscoverRunner


class ProjectAppsTestRunner(DiscoverRunner):
    """With no labels, test every installed app inside the project, including those under apps/."""

    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            base = str(settings.BASE_DIR)
            test_labels = list(
                dict.fromkeys(
                    config.name
                    for config in apps.get_app_configs()
                    if config.path.startswith(base)
                    and "site-packages" not in config.path
                )
            )
        return super().build_suite(test_labels, **kwargs)
