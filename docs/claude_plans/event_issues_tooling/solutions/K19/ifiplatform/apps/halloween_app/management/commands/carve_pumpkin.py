"""python manage.py carve_pumpkin [--size N]: prints a jack-o'-lantern."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Prints a jack-o'-lantern in the terminal."

    def add_arguments(self, parser):
        parser.add_argument("--size", type=int, default=3, help="How wide the pumpkin is (1-6).")

    def handle(self, *args, **options):
        size = max(1, min(options["size"], 6))
        width = 6 + size * 4
        self.stdout.write(" " * (width // 2) + "|")
        inside = width - 2
        rows = ["", "^   ^", "", "\\/\\/\\/\\/"[: max(4, inside - 4)], ""]
        self.stdout.write("/" + "~" * inside + "\\")
        for row in rows:
            self.stdout.write(self.style.WARNING("(" + row.center(inside) + ")"))
        self.stdout.write("\\" + "_" * inside + "/")
