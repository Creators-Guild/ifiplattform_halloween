# pylint: disable=C0114
from django.urls import path

from .views import board, fortune, hub, memory, potion, preview_404, spooky_name, whack_a_bat

urlpatterns = [
    path("", hub.hub_view, name="halloween_hub"),
    path("board/", board.board_view, name="halloween_board"),
    path("fortune/", fortune.fortune_view, name="halloween_fortune"),
    path("spooky-name/", spooky_name.spooky_name_view, name="halloween_spooky_name"),
    path("potion/", potion.potion_view, name="halloween_potion"),
    path("whack-a-bat/", whack_a_bat.whack_a_bat_view, name="halloween_whack_a_bat"),
    path("memory/", memory.memory_view, name="halloween_memory"),
    # Shows templates/404.html while DEBUG is on, when Django shows its own 404 page instead.
    path("404-preview/", preview_404.preview_404_view, name="halloween_404_preview"),
]
