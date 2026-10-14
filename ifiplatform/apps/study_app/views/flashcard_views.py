"""Views for flashcard study feature."""

from typing import cast  # removes errorlines

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect

from study_app.forms import DeckForm, CardForm
from study_app.models import Deck, Card


@login_required
def flashcard_menu(request):
    """Display list of flashcard decks for the logged-in user."""
    decks = Deck.objects.filter(owner=request.user)
    return render(
        request=request,
        template_name="flashcards/core/menu.html",
        context={"decks": decks},
    )


@login_required
def deck_detail(request, deck_pk):
    """Display all cards in a specific flashcard deck."""
    deck = get_object_or_404(Deck, pk=deck_pk, owner=request.user)
    cards = deck.cards.all()
    return render(
        request,
        "flashcards/core/deck_detail.html",
        {
            "deck": deck,
            "cards": cards,
        },
    )


@login_required
def review(request, deck_pk: int, index: int):
    """Display a single card for review at the given index in the deck."""
    deck = get_object_or_404(Deck, pk=deck_pk, owner=request.user)
    cards = deck.cards.all()  # later you can randomize this order
    total = cards.count()

    # clamp index to valid range (1..total)
    if total == 0:
        current_card = None
        index = 0
    else:
        index = max(1, min(index, total))
        current_card = cards[index - 1]

    context = {
        "deck": deck,
        "card": current_card,
        "current_index": index,
        "total_cards": total,
    }
    return render(request, "flashcards/core/review.html", context)


@login_required
def deck_create(request):
    """Create a new flashcard deck for the logged-in user."""
    if request.method == "POST":
        form = DeckForm(request.POST)
        if form.is_valid():
            deck = form.save(commit=False)
            deck.owner = request.user  # tie deck to logged-in user
            try:
                deck.save()
                return redirect("flashcard_menu")
            except IntegrityError:
                form.add_error("name", "You already have a deck with this name.")
    else:
        form = DeckForm()

    return render(request, "flashcards/core/deck_form.html", {"form": form})


@login_required
def deck_delete(request, deck_pk):
    """Delete a flashcard deck and return to flashcard menu."""
    deck = cast(Deck, get_object_or_404(Deck, pk=deck_pk, owner=request.user))
    decks = Deck.objects.filter(owner=request.user)

    if request.method == "POST":
        deck.delete()

    return render(
        request=request,
        template_name="flashcards/core/flashcard_menu.html",
        context={"decks": decks},
    )


@login_required
def card_create(request, deck_pk):
    """Create a new card in a specific flashcard deck."""
    deck = get_object_or_404(Deck, pk=deck_pk, owner=request.user)

    if request.method == "POST":
        form = CardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.deck = deck
            card.save()
            return redirect("deck_detail", deck_pk=deck.pk)
    else:
        form = CardForm()

    return render(
        request,
        "flashcards/core/card_form.html",
        {
            "deck": deck,
            "form": form,
        },
    )


@login_required
def card_delete(request, deck_pk):
    """Delete a card from a flashcard deck."""
    card = get_object_or_404(Card, pk=deck_pk, deck__owner=request.user)
    deck = cast(Deck, card.deck)  # cast to remove errorline
    if request.method == "POST":
        card.delete()
    return redirect("deck_detail", deck_pk=deck.pk)
