"""URL configuration for study app."""

from django.conf import settings
from django.urls import path
from django.utils.translation import gettext_lazy as _
from core_app.under_development import under_development_urlpatterns
from .views import flashcard_views
from .views import multiplechoice_views
from .views import mix_studyset_views
from .views import core_views

study_urlpatterns = [
    path("", core_views.main_view, name="study_home"),
]

flashcard_urlpatterns = [
    path("flashcard/", flashcard_views.flashcard_menu, name="flashcard_menu"),
    # <int:pk> is a parameter for the decks ID in database
    path(
        "flashcard/deck/<int:deck_pk>/", flashcard_views.deck_detail, name="deck_detail"
    ),
    path(
        "flashcard/deck/<int:deck_pk>/review/<int:index>",
        flashcard_views.review,
        name="review",
    ),
    path("flashcard/deck/new/", flashcard_views.deck_create, name="deck_create"),
    path(
        "flashcard/deck/delete/<int:deck_pk>",
        flashcard_views.deck_delete,
        name="deck_delete",
    ),
    path(
        "flashcard/deck/<int:deck_pk>/card/new/",
        flashcard_views.card_create,
        name="card_create",
    ),
    path(
        "flashcard/deck/<int:deck_pk>/card/delete/",
        flashcard_views.card_delete,
        name="card_delete",
    ),
]

multiplechoice_urlpatterns = [
    path("multiplechoice/", multiplechoice_views.menu_view, name="multiplechoice_menu")
]

mix_studyset_urlpatterns = [
    path("mixstudyset/", mix_studyset_views.menu_view, name="mix_studyset_menu")
]

studygames_urlpatterns = [
    path("studygames/", mix_studyset_views.menu_view, name="studygames_menu")
]

if settings.APPS_UNDER_DEVELOPMENT.get("study_app"):
    urlpatterns = under_development_urlpatterns("study_home", _("Study"))
else:
    urlpatterns = (
        study_urlpatterns
        + flashcard_urlpatterns
        + multiplechoice_urlpatterns
        + mix_studyset_urlpatterns
        + studygames_urlpatterns
    )
