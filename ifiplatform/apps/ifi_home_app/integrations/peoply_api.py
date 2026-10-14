"""Thin client for Peoply's public API (api.peoply.app) -- fetches a
student union's upcoming events, and Peoply's full organization roster,
both paginated. See sync_peoply_events and check_peoply_union_matches for
what consumes this."""

import requests

url = "https://api.peoply.app"


def get_events(union_id, after_date):
    events = []  # peoply API only gives all events or nothing, everything just filters

    # use skip/offset and take for safety. Take caps at 500(though I doubt there will ever more than 500)
    offset = 0  # starts at 0 to get from
    # think of this as getting pages (max 500 event on each). If full page, means you have to chekc next page
    while True:
        response = requests.get(
            url + "/events",
            params={
                "organizationId": union_id,
                "afterDate": after_date.isoformat(),  # safetycall to make sure right formatting
                "orderBy": "startDate",
                "orderDirection": "asc",  # ascending
                "skip": offset,
                "take": 500,
            },
            timeout=10,  # don't wait forever(ex. server down)
        )
        response.raise_for_status()  # fail loudly on an outage/bad request instead of choking on .json() below

        page = response.json()
        events += page
        take = len(page)  # to check actual count
        if take < 500:  # not a full page, means no more pages after
            break

        offset += take  # used to figure out next pagenr

    return events


def get_organizations():
    """Every organization registered on Peoply (not just IFI's own unions --
    Peoply is shared across student orgs), paginated the same skip/take way
    as get_events. Unlike get_events, nothing in this project called the
    unfiltered form of this endpoint before check_peoply_union_matches --
    link_peoply_organizations only ever used ?name=<title> per union, which
    Peoply happens to page internally too (confirmed by hand against the
    live API), so the same skip/take loop applies here."""
    organizations = []

    offset = 0
    while True:
        response = requests.get(
            url + "/organizations",
            params={"skip": offset, "take": 500},
            timeout=10,
        )
        response.raise_for_status()

        page = response.json()
        organizations += page
        take = len(page)
        if take < 500:
            break

        offset += take

    return organizations


def find_exact_match(title, candidates):
    """title against each candidate org's name or urlId (Peoply's own
    shorthand, e.g. "cyb" for "Cybernetisk Selskab"), case-insensitive --
    shared by link_peoply_organizations and check_peoply_union_matches, both
    of which need Peoply's own name-search to only ever count as a match
    when it's exact (see link_peoply_organizations's docstring for why: its
    search is substring-based, e.g. "FU" matches "FUI")."""
    title_lower = title.lower()
    for org in candidates:
        url_id = org["urlId"]
        if org["name"].lower() == title_lower or (
            url_id and url_id.lower() == title_lower
        ):
            return org
    return None


def apply_peoply_match(union, org):
    """Writes org["id"] as union's peoply_organization_id. Uses
    queryset.update(), not save_revision().publish():
    peoply_organization_id isn't editor-facing draft/live content that
    needs a Wagtail revision."""
    from ifi_home_app.models.article.unions import UnionPage

    UnionPage.objects.filter(pk=union.pk).update(peoply_organization_id=org["id"])
