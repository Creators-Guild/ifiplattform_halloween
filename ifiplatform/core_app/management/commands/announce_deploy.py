"""Sets the shared "a deploy is imminent" flag that core_app.deploy_notice
(the context processor powering partials/deploy_notice.html, included in
every page via global_base.html) reads to show a site-wide countdown banner.

Meant to be run by the deploy script (deploy/deploy.sh)
*before* the actual git reset/migrate/restart steps, against whatever code
is currently on disk from the previous deploy -- it's the currently-running
gunicorn workers that need to render the banner for the full warning
window, not the incoming new code (which isn't live yet). See that
workflow's own comments for the one-time bootstrapping caveat: the first
deploy that ships this command can't announce itself.

Uses the project's existing cache framework (FileBasedCache, see
settings.py's own comment on why -- shared across gunicorn worker
processes) rather than a bespoke file format, since that's exactly the
"multiple processes need to see one shared flag" problem this also has.

--clear removes the flag immediately -- run this once the actual restart
has completed (after `sudo systemctl restart gunicorn` in deploy/deploy.sh),
against the newly-deployed code. Without it, the flag would just sit there
until its own timeout eventually expires (up to a minute after the target),
during which a visitor's post-restart page reload (see deploy_notice.js's
own auto-reload once its countdown hits zero) would still show the banner
even though the restart already finished."""

import time

from django.core.cache import cache
from django.core.management.base import BaseCommand

from core_app.deploy_notice import DEPLOY_NOTICE_CACHE_KEY


class Command(BaseCommand):
    help = (
        "Sets the shared deploy-imminent flag (a target timestamp) that the "
        "site-wide countdown banner reads. Run this before restarting the "
        "server, not after."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=10,
            help="Minutes from now the server is expected to restart (default: 10).",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove the flag immediately (run after the restart completes), ignores --minutes.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            cache.delete(DEPLOY_NOTICE_CACHE_KEY)
            self.stdout.write(self.style.SUCCESS("Deploy notice cleared."))
            return

        minutes = options["minutes"]
        target = int(time.time()) + minutes * 60
        # small buffer past the target so the flag doesn't expire a few
        # seconds early due to script timing drift -- it's meant to
        # disappear once the new server is up anyway, not at this exact
        # second.
        cache.set(DEPLOY_NOTICE_CACHE_KEY, target, timeout=minutes * 60 + 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"Deploy notice set: restart expected in {minutes} minute(s)."
            )
        )
