"""{% costume_of_the_day as costume %}: today's costume, (emoji, text)."""

from datetime import datetime
from zoneinfo import ZoneInfo

from django import template

from ..costume_of_the_day import costume_of_the_day as pick

register = template.Library()


@register.simple_tag
def costume_of_the_day():
    return pick(datetime.now(ZoneInfo("Europe/Oslo")).date())
