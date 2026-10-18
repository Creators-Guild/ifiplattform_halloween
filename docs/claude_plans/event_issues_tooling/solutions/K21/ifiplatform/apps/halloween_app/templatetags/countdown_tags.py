"""{% days_to_halloween %}: how many days until the next 31 October."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from django import template

register = template.Library()


@register.simple_tag
def days_to_halloween():
    """0 on Halloween itself, otherwise the days until the next one."""
    today = datetime.now(ZoneInfo("Europe/Oslo")).date()
    halloween = date(today.year, 10, 31)
    if halloween < today:
        halloween = date(today.year + 1, 10, 31)
    return (halloween - today).days
