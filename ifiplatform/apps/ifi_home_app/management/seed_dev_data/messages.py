"""HeaderMessage/HomeBoardMessage seeding -- the site-wide banner text and
the homepage's rotating board messages."""

from django.utils import timezone
from wagtail.rich_text import RichText

from ifi_home_app.models import HeaderMessage, HomeBoardMessage

from .constants import BANNER_TEXT, BOARD_MESSAGE_SPECS


class MessageSeedMixin:
    def _seed_header_message(self, nb_locale):
        text = f"<p>{BANNER_TEXT}</p>"
        message = HeaderMessage.objects.filter(text=text, locale=nb_locale).first()
        if message is None:
            message = HeaderMessage.objects.create(
                text=RichText(text),
                is_active=True,
                locale=nb_locale,
            )
            self.created_count += 1
            self.stdout.write(f"  created HeaderMessage: {BANNER_TEXT}")
        else:
            self.skipped_count += 1

        self._translate_page(message)

    def _seed_home_board_message(self, nb_locale):
        for i, spec in enumerate(BOARD_MESSAGE_SPECS):
            title = spec["title"]
            message = HomeBoardMessage.objects.filter(
                title=title, locale=nb_locale
            ).first()
            if message is None:
                message = HomeBoardMessage(
                    title=title,
                    date=timezone.now().date(),
                    body=RichText(spec["body"]),
                    sender_name=spec["sender_name"],
                    sender_role="Seed script",
                    order=i,
                    display_seconds=spec["display_seconds"],
                    locale=nb_locale,
                )
                message.save()
                self.created_count += 1
                self.stdout.write(f"  created HomeBoardMessage: {title}")
            else:
                self.skipped_count += 1

            self._translate_page(message)
