"""python manage.py carve_pumpkin [--size N]: prints a jack-o'-lantern."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Prints a jack-o'-lantern in the terminal."

    def add_arguments(self, parser):
        parser.add_argument("--size", type=int, default=3, help="How wide the pumpkin is (1-6).")
        parser.add_argument("--face", type=str, default="happy", choices=["happy", "scary"], help="Pumpkin expression.")

    def handle(self, *args, **options):
        size = max(1, min(options["size"], 6))
        width = 6 + size * 4
        face = options["face"]

        inner = width - 2

        # Face parts
        if face == "scary":
            eyes = "▲ ▲"
            mouth = "VVVVV"
        else:
            eyes = "^ ^"
            mouth = r"\/\/\/"

        # Build mouth string to fit neatly inside
        mouth_fill = mouth
        while len(mouth_fill) < inner - 2:
            mouth_fill += mouth
        mouth_str = mouth_fill[: inner - 2].center(inner)
        eyes_str = eyes.center(inner)

        def write_line(line):
            self.stdout.write(self.style.WARNING(line))

        # Stem
        stem = "||" if size >= 4 else "|"

        ## size + 1 for rounding up.
        for i in range((size+1)//2):
            write_line(stem.center(width))

        # Top dome
        dome_lines = size - 1
        write_line(" " * (dome_lines + 1) + "—" * (inner - dome_lines * 2 ))

        for i in range(dome_lines):
            indent = dome_lines - 1 - i
            mid = " " * (inner - 2 * indent)
            write_line(" " * indent + "/" + mid + "\\" + " " * indent)

        # Body
        body_height = size + 2
        eye_line = body_height // 3
        mouth_line = body_height * 2 // 3

        for i in range(body_height):
            if i == eye_line:
                content = eyes_str
            elif i == mouth_line:
                content = mouth_str
            else:
                content = " " * inner
            write_line("|" + content + "|")

        # Bottom dome
        for i in range(dome_lines):
            indent = i
            mid = " " * (inner - 2 * indent)
            write_line(" " * indent + "\\" + mid + "/" + " " * indent)

        write_line(" " * (dome_lines + 1) + "—" * (inner - dome_lines * 2 ))

