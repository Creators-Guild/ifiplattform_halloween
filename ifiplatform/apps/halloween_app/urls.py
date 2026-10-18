# pylint: disable=C0114
from django.urls import path

from .views import (
    bat_snake,
    board,
    costume,
    countdown,
    fortune,
    graveyard,
    hub,
    ics,
    memory,
    potion,
    preview_404,
    pumpkin_carver,
    quiz,
    sliding_puzzle,
    spooky_name,
    story,
    whack_a_bat,
    zombie_typing,
)

urlpatterns = [
    path("", hub.hub_view, name="halloween_hub"),
    path("board/", board.board_view, name="halloween_board"),
    path("fortune/", fortune.fortune_view, name="halloween_fortune"),
    path("spooky-name/", spooky_name.spooky_name_view, name="halloween_spooky_name"),
    path("potion/", potion.potion_view, name="halloween_potion"),
    path("whack-a-bat/", whack_a_bat.whack_a_bat_view, name="halloween_whack_a_bat"),
    path("memory/", memory.memory_view, name="halloween_memory"),
    path("zombie-typing/", zombie_typing.zombie_typing_view, name="halloween_zombie_typing"),
    path("moon-puzzle/", sliding_puzzle.sliding_puzzle_view, name="halloween_sliding_puzzle"),
    path("bat-snake/", bat_snake.bat_snake_view, name="halloween_bat_snake"),
    path("costume/", costume.costume_view, name="halloween_costume"),
    path("story/", story.story_view, name="halloween_story"),
    path("quiz/", quiz.quiz_view, name="halloween_quiz"),
    path("graveyard/", graveyard.graveyard_view, name="halloween_graveyard"),
    path("countdown/", countdown.countdown_view, name="halloween_countdown"),
    path("pumpkin-carver/", pumpkin_carver.pumpkin_carver_view, name="halloween_pumpkin_carver"),
    path("event/<int:page_id>/calendar.ics", ics.event_ics_view, name="halloween_event_ics"),
    # Shows templates/404.html while DEBUG is on, when Django shows its own 404 page instead.
    path("404-preview/", preview_404.preview_404_view, name="halloween_404_preview"),
]
