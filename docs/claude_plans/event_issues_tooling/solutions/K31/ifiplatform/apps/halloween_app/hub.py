"""The order of the cards on the Halloween corner's front page: the haunted
board first, then every other page from A to Z by its title."""

from .pages import PAGES


def hub_pages():
    """PAGES in the order the hub shows them."""
    board = [page for page in PAGES if page[0] == "board"]
    rest = [page for page in PAGES if page[0] != "board"]
    return board + sorted(rest, key=lambda page: page[2])
