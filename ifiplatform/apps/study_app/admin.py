"""Admin configuration for study app models."""

from django.contrib import admin

from .models import Card, Deck

# Register your models here.
admin.site.register(Deck)
admin.site.register(Card)
