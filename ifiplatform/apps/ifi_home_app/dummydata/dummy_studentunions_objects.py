"""Dummy data for populating StudentUnion objects during development."""

from ifi_home_app.models.home_models import StudentUnion


def create(fresh_on_page_load: bool = False):
    """Create dummy StudentUnion entries, optionally clearing existing ones first."""
    if fresh_on_page_load:
        StudentUnion.objects.all().delete()

    StudentUnion.objects.bulk_create(
        [
            StudentUnion(
                title="ProgSys():",
                description="Linjeforening for PROSA",
                image_name="ProgSysLogo.webp",
                programme_union=True,
                homepage="https://progsys.no/",
            ),
            StudentUnion(
                title="PiTCH",
                description="Linjeforening for entrepreneur",
                image_name="PitchLogo.jpg",
                programme_union=True,
                homepage="https://www.instagram.com/pitch_ifi_uio/",
            ),
            StudentUnion(
                title="IFI Rastløs",
                description="Forening for å fremme fysisk aktivitet og fellesskap",
                image_name="IFIRastløsLogo.jpg",
                programme_union=False,
                homepage="https://www.instagram.com/ifirastlos/",
            ),
            StudentUnion(
                title="Ifi Pitbulls",
                description="Forening for å fremme Pitbull og stemning",
                image_name="IfiPitbullsLogo.jpg",
                programme_union=False,
                homepage="https://www.instagram.com/ifipitbulls/?hl=tr",
            ),
        ]
    )
