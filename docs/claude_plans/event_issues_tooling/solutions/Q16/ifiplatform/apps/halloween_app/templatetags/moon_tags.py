"""{% moon_shadow %}: the CSS offset of the moon's shadow right now."""

from django import template
from django.utils import timezone

from ..moon_phase import phase, shadow_offset

register = template.Library()


@register.simple_tag
def moon_shadow():
    """For example "-37%", for the --moon-shadow custom property."""
    return f"{shadow_offset(phase(timezone.now()))}%"
