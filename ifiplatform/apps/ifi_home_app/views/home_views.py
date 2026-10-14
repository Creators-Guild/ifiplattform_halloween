"""Views for IFI home page."""

from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone
from ifi_home_app.models.article_models import ArticlePage, get_section_index
from ifi_home_app.models.event.dates import group_events_by_day
from ifi_home_app.models.event.pages import EventIndexPage, EventPage

from ..dummydata import (
    dummy_news_objects,
    dummy_studentunions_objects,
    dummy_tools_objects,
)
from ..models.home_models import HomeBoardMessage, IfiTool, NewsItem, StudentUnion


def main_view(request):
    """Display the main IFI home page with news, unions and tools."""
    # (development) if no news in database, use dummydata
    if not NewsItem.objects.exists():
        dummy_news_objects.create(fresh_on_page_load=True)
    if not StudentUnion.objects.exists():
        dummy_studentunions_objects.create(fresh_on_page_load=True)
    if not IfiTool.objects.exists():
        dummy_tools_objects.create(fresh_on_page_load=True)

    # create context
    news_items = NewsItem.objects.order_by("-created_at")[:4]
    news_index_page = get_section_index("news")
    news_articles = (
        ArticlePage.objects.descendant_of(news_index_page)
        .live()
        .filter(show_on_homepage=True)
        .order_by("-published_date")[:12]
        if news_index_page
        else ArticlePage.objects.none()
    )

    unions = StudentUnion.objects.all()
    tools = IfiTool.objects.all()
    board_messages = HomeBoardMessage.objects.filter(is_active=True)

    today = timezone.localdate()
    event_index = EventIndexPage.objects.live().first()
    upcoming_events = (
        EventPage.objects.child_of(event_index)
        .live()
        .filter(show_on_homepage=True, is_archived=False)
        .filter(
            Q(end_date__gte=today) | Q(end_date__isnull=True, event_date__gte=today)
        )
        .order_by("event_date", "event_time")[:6]
        if event_index
        else EventPage.objects.none()
    )

    context = {
        "news_items": news_items,
        "news_articles": news_articles,
        "unions": unions,
        "tools": tools,
        "board_messages": board_messages,
        "show_board_controls": len(board_messages) > 1,
        "upcoming_events": upcoming_events,
        "upcoming_event_days": group_events_by_day(upcoming_events),
    }

    return render(
        request=request,
        template_name="home/home_index.html",
        context=context,
    )
