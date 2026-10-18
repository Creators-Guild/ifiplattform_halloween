"""Loads the notes on the haunted notice board from board_notes/. Each note is
one .txt file, so every event issue adds its own file and two notes never
clash. The file name starts with the note's kind (obituary_03.txt), line 1
is the title, the rest is the text, and a last line starting with a dash
("-- ", "- " or "— ") is the signature. See board_notes/README.md."""

import re
import zlib
from dataclasses import dataclass
from pathlib import Path

NOTES_DIR = Path(__file__).parent / "board_notes"
KINDS = ("obituary", "warning", "rule", "missing")
# Two normal dashes are what most people type; the long dash is what it
# shows as on the board.
SIGNATURE = re.compile(r"^(--|-|—)\s+")


@dataclass
class Note:
    kind: str
    title: str
    text: str
    signature: str
    tilt: int  # degrees, -3 to 3, so the board looks hand-pinned


def _read(path):
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return None
    body = lines[1:]
    signature = ""
    if body and SIGNATURE.match(body[-1]):
        signature = SIGNATURE.sub("", body.pop()).strip()
    return Note(
        kind=path.stem.split("_")[0],
        title=lines[0].strip(),
        text="\n".join(body).strip(),
        signature=signature,
        tilt=zlib.crc32(path.name.encode()) % 7 - 3,
    )


def load_notes():
    """Every note, mixed up in a fixed order (by a hash of the file name),
    so the kinds don't come in blocks. A note that can't be read is left out
    instead of breaking the whole board."""
    paths = [p for p in NOTES_DIR.glob("*.txt") if p.stem.split("_")[0] in KINDS]
    notes = []
    for path in sorted(paths, key=lambda p: zlib.crc32(p.name.encode())):
        try:
            note = _read(path)
        except (OSError, UnicodeDecodeError):
            continue
        if note:
            notes.append(note)
    return notes
