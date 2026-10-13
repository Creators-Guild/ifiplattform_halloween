"""Forms for the study app: Deck and Card creation/editing forms."""

from django import forms
from .models import Deck, Card


class DeckForm(forms.ModelForm):
    """ModelForm for creating and editing flashcard decks."""

    class Meta:
        """Meta options for DeckForm."""

        model = Deck
        fields = ["name", "description"]


class CardForm(forms.ModelForm):
    """ModelForm for creating and editing individual flashcards."""

    class Meta:
        """Meta options for CardForm."""

        model = Card
        fields = ["front", "back"]
