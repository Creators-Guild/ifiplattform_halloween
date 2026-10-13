"""Dev superuser seeding -- the admin/admin login contributors use to reach
django-admin and wagtail-admin on a fresh local database."""

from django.conf import settings
from django.contrib.auth import get_user_model

DEV_ADMIN_USERNAME = "admin"
DEV_ADMIN_PASSWORD = "admin"
DEV_ADMIN_EMAIL = "admin@example.invalid"


class UserSeedMixin:
    def _seed_dev_superuser(self):
        """Creates the admin/admin superuser if no user by that name exists.

        Unlike the rest of the seed data this is skipped whenever DEBUG is
        off, even under --force: a published username/password pair on a
        reachable database is a different class of mistake from a dummy
        article, and --force exists for seeding content into a real local
        Postgres.
        """
        if not settings.DEBUG:
            self.stdout.write("  skipped superuser: DEBUG is off")
            return

        user_model = get_user_model()
        if user_model.objects.filter(username=DEV_ADMIN_USERNAME).exists():
            self.skipped_count += 1
            return

        user_model.objects.create_superuser(
            username=DEV_ADMIN_USERNAME,
            email=DEV_ADMIN_EMAIL,
            password=DEV_ADMIN_PASSWORD,
        )
        self.created_count += 1
        self.stdout.write(
            self.style.WARNING(
                f"  created superuser {DEV_ADMIN_USERNAME}/{DEV_ADMIN_PASSWORD} "
                "-- local development only, never deploy this"
            )
        )
