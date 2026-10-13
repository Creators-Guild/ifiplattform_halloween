"""Views module for study app."""

from .....IfiPlatform.ifiplatform.apps.study_app.views import flashcard_views
from .....IfiPlatform.ifiplatform.apps.study_app.views import core_views
from .....IfiPlatform.ifiplatform.apps.study_app.views import mix_studyset_views
from .....IfiPlatform.ifiplatform.apps.study_app.views import multiplechoice_views
from .....IfiPlatform.ifiplatform.apps.study_app.views import studygames_views

__all__ = [
    "flashcard_views",
    "core_views",
    "mix_studyset_views",
    "multiplechoice_views",
    "studygames_views",
]
