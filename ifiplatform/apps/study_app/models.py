"""Models for study app: Deck and Card for flashcard system."""

from typing import TYPE_CHECKING

from django.db import models
from django.conf import settings


# Create your models here.
class Deck(models.Model):
    """Flashcard deck representing a collection of study cards owned by a user."""

    # one-to-many with one user
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # if user deleted, keep deck
        null=True,
        related_name="decks",  # how to access all decks to user
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # Only ever written by account_app's delete_account_view, once `owner`
    # itself is about to go NULL there (deck kept, owner chose to be
    # credited by real name/nickname/"unknown" -- same sentinel convention
    # as ArticlePage.author_display_name). No study_app view shows this
    # today (every view here filters strictly by owner=request.user), but
    # it's ready for the shared student study-resource library the README
    # lists as a future goal, so deletion has somewhere to put the choice
    # now rather than needing another schema change once that ships.
    owner_display_name = models.CharField(max_length=150, blank=True)

    class Meta:
        # make sure that the same user can't have mutiple deck with same name
        # diffrent user can still have decks sharing the same name
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_deck_name_per_owner",
            )
        ]

    if TYPE_CHECKING:
        # This is only for Pylance / type checkers, not used at runtime
        # Just used to remove errorline when ex. 'deck.cards.all()'
        from django.db.models.manager import (  # pylint: disable=import-outside-toplevel
            RelatedManager,
        )

        cards: RelatedManager["Card"]

    def __str__(self):
        """Return deck name."""
        return self.name


class Card(models.Model):
    """Individual flashcard with question/answer pairs for studying."""

    deck = models.ForeignKey(
        Deck, on_delete=models.SET_NULL, null=True, related_name="cards"
    )
    front = models.TextField()  # question
    back = models.TextField()  # answer

    created_at = models.DateTimeField(auto_now_add=True)
    last_reviewed = models.DateTimeField(null=True, blank=True)
    times_correct = models.PositiveIntegerField(default=0)
    times_incorrect = models.PositiveIntegerField(default=0)

    def __str__(self):
        """Return first 50 characters of front side (question)."""
        return self.front[:50]
