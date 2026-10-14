"""Dummy data for populating IfiTool objects during development."""

from ifi_home_app.models.home_models import IfiTool


def create(fresh_on_page_load: bool = False):
    """Create dummy IfiTool entries, optionally clearing existing ones first."""
    if fresh_on_page_load:
        IfiTool.objects.all().delete()

    IfiTool.objects.bulk_create(
        [
            IfiTool(
                title="Peoply",
                creators="MAPS",
                description="App for studentarrangementer på Ifi",
                short_description="Eventcalender",
                image_name="PeoplyLogo.png",
                link="https://peoply.app/",
            ),
            IfiTool(
                title="IFI-Rom",
                creators="Carl-Magnus Lein?",
                description="Romoversikt over Ole Johan Dahls Hus",
                short_description="Map",
                image_name="IfiRomLogo.png",
                link="https://ifirom.no/",
            ),
            IfiTool(
                title="Cliffi",
                creators="students",
                description="App for når Ifi Studenter klatrer",
                short_description="Klatre App",
                image_name="CliffiLogo.png",
                link="https://cliffi.app/",
            ),
        ]
    )
