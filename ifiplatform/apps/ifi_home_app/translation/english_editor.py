"""The English text editor: one row per piece (Norwegian | English | who),
an English slug for pages, and "Machine-translate now". Works for pages and
translated snippets; a menu group also lists its links' pieces.

Design rationale: docs/claude_context/translation_overlay.md"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import translation
from modelcluster.models import get_all_child_relations
from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.widgets.button import Button
from wagtail.models import Page
from wagtail.permission_policies import ModelPermissionPolicy

from ..models.menus import Menu
from ..models.translation import SegmentTranslation

from . import auto_translate, deepl, english_urls, page_segments, stored_translations


def editor_url(page):
    content_type_id, object_id = stored_translations.object_key(page)
    return reverse("english_editor", args=[content_type_id, object_id])


def can_edit(user, page):
    if isinstance(page, Page):
        return page.permissions_for_user(user).can_edit()
    opts = page._meta
    return user.has_perm(f"{opts.app_label}.change_{opts.model_name}")


def _objects(page):
    """`page` plus its child objects that have translated fields (a menu
    group's links), in that order."""
    objects = [page]
    for relation in get_all_child_relations(page):
        if page_segments.translated_field_names(relation.related_model):
            objects += list(getattr(page, relation.get_accessor_name()).all())
    return objects


def _rows(objects):
    rows = []
    for obj in objects:
        stored = stored_translations.lookup(obj)
        content_type_id, object_id = stored_translations.object_key(obj)
        for segment in page_segments.extract_segments(obj):
            row = stored.get((segment.path, segment.norwegian_hash))
            rows.append(
                {
                    "object": f"{content_type_id}:{object_id}",
                    "label": _label(obj, segment.path),
                    "segment": segment,
                    "english": row.english_text if row and not row.has_error else "",
                    "row": row,
                    "error": "",
                }
            )
    return rows


def _label(obj, path):
    field = path.split(".")[0]
    label = obj._meta.get_field(field).verbose_name
    if obj._meta.model_name == "menugrouplink":
        return f"Link “{obj.label or obj.url or obj.page}”: {label}"
    return label.capitalize() if "." not in path else f"{label.capitalize()} (block)"


def _get(content_type_id, object_id):
    model = ContentType.objects.get_for_id(content_type_id).model_class()
    if model is None or not page_segments.translated_field_names(model):
        raise Http404
    page = model._default_manager.filter(pk=object_id).first()
    if page is None:
        raise Http404
    return page


def edit(request, content_type_id, object_id):
    page = _get(content_type_id, object_id)
    if not can_edit(request.user, page):
        raise PermissionDenied
    objects = _objects(page)
    by_key = {
        ":".join(map(str, stored_translations.object_key(obj))): obj for obj in objects
    }

    if request.method == "POST" and "machine_translate" in request.POST:
        _machine_translate(request, objects)
        return redirect(editor_url(page))

    rows = _rows(objects)
    if request.method == "POST":
        failed = _save(request, page, by_key, rows)
        if not failed:
            messages.success(request, "English saved.")
            return redirect(editor_url(page))

    return render(
        request,
        "translation/english_editor.html",
        {
            "page": page,
            "title": str(page),
            "rows": rows,
            "is_page": isinstance(page, Page),
            "english_slug": (
                (english_urls.english_slug(page) or "")
                if isinstance(page, Page)
                else ""
            ),
            "deepl_configured": deepl.is_configured(),
            "back_url": AdminURLFinder(request.user).get_edit_url(page),
            "english_page_url": _english_page_url(page),
            "subtree_url": _subtree_url(page),
        },
    )


def _save(request, page, by_key, rows):
    """Saves every changed piece against the Norwegian the editor was
    looking at (sent back with the form), never the current text. Returns
    True if any piece was refused."""
    failed = False
    for index in range(int(request.POST.get("piece_count", 0))):
        prefix = f"piece-{index}-"
        obj = by_key.get(request.POST.get(prefix + "object"))
        english = request.POST.get(prefix + "english", "").strip()
        if (
            obj is None
            or not english
            or english == request.POST.get(prefix + "original")
        ):
            continue
        segment = page_segments.Segment(
            request.POST.get(prefix + "path", ""),
            request.POST.get(prefix + "norwegian", ""),
        )
        try:
            page_segments.check_english(segment, english)
        except ValueError as error:
            failed = True
            for row in rows:
                if row["segment"] == segment:
                    row["english"], row["error"] = english, str(error)
            continue
        stored_translations.save_human(obj, segment, english, request.user)

    wanted_slug = request.POST.get("english_slug", "").strip()
    if (
        isinstance(page, Page)
        and wanted_slug
        and wanted_slug != english_urls.english_slug(page)
    ):
        saved = english_urls.set_english_slug(page, wanted_slug, "human", request.user)
        if saved != wanted_slug:
            messages.warning(
                request, f"English slug saved as “{saved}” (must be unique)."
            )
    if failed:
        messages.error(request, "Some English couldn't be saved; see the marked rows.")
    return failed


def _machine_translate(request, objects):
    if not deepl.is_configured():
        messages.error(request, "DeepL isn't set up (no DEEPL_API_KEY).")
        return
    try:
        sent = auto_translate.fill_missing_many(objects)
    except Exception as error:  # pylint: disable=broad-except
        messages.error(request, f"DeepL failed: {error}")
        return
    if sent:
        messages.success(request, f"DeepL translated {sent} piece(s).")
    else:
        messages.info(request, "Nothing was missing.")


def _english_page_url(page):
    """The live page's English address, for "View in English"."""
    if not isinstance(page, Page) or not page.live:
        return None
    with translation.override("en"):
        return page.get_url()


def _subtree_url(page):
    if not deepl.is_configured() or not isinstance(page, Page):
        return None
    if not page.get_descendants().live().exists():
        return None
    return reverse("english_machine_translate_subtree", args=[page.pk])


def machine_translate_subtree(request, page_id):
    """Confirm, then mark a page and every live page under it as waiting for
    DeepL ("asked by a person": translated even with automatic translation
    off). The every-minute run translates them; big trees take minutes, too
    long for one request."""
    page = get_object_or_404(Page, pk=page_id).specific
    if not can_edit(request.user, page):
        raise PermissionDenied
    count = page.get_descendants().live().count() + 1
    if request.method == "POST":
        if not deepl.is_configured():
            messages.error(request, "DeepL isn't set up (no DEEPL_API_KEY).")
        else:
            marked = auto_translate.request_subtree(page)
            messages.success(
                request,
                f"{marked} page(s) are waiting for DeepL; their English appears "
                "within a few minutes.",
            )
        return redirect(editor_url(page))
    return render(
        request,
        "translation/english_machine_translate.html",
        {
            "title": str(page),
            "what": f"“{page}” and the {count - 1} live page(s) under it",
            "how": "They're translated in the background, one page at a time; "
            "the English appears within a few minutes.",
            "cancel_url": editor_url(page),
        },
    )


def _menu_objects(menu):
    """A menu's groups and their links: the whole menu tree."""
    groups = [slot.group for slot in menu.slots.select_related("group")]
    links = [link for group in groups for link in group.links.all()]
    return list(dict.fromkeys(groups)) + links


def machine_translate_menu(request, menu_id):
    """Confirm, then DeepL-translate a whole menu's missing English at once
    (all its groups and links in one batch: menus are small)."""
    menu = get_object_or_404(Menu, pk=menu_id)
    if not request.user.has_perm("ifi_home_app.change_menugroup"):
        raise PermissionDenied
    back = AdminURLFinder(request.user).get_edit_url(menu) or reverse(
        "wagtailadmin_home"
    )
    if request.method == "POST":
        _machine_translate(request, _menu_objects(menu))
        return redirect(back)
    objects = _menu_objects(menu)
    return render(
        request,
        "translation/english_machine_translate.html",
        {
            "title": str(menu),
            "what": f"the menu “{menu}”: {len(objects)} groups and links",
            "how": "Only missing English is sent to DeepL; it's done right away.",
            "cancel_url": back,
        },
    )


def page_button(page, user, view_name=None, next_url=None):
    """ "English" in the page header and listing "more" menu."""
    if not page.is_root() and can_edit(user, page):
        yield Button("English", editor_url(page), icon_name="globe", priority=58)


def subtree_button(page, user, view_name=None, next_url=None):
    """ "Machine-translate subtree" in the page header and "more" menu."""
    url = _subtree_url(page)
    if url and can_edit(user, page):
        yield Button("Machine-translate subtree", url, icon_name="globe", priority=59)


def snippet_button(snippet, user, next_url=None):
    if page_segments.translated_field_names(type(snippet)) and can_edit(user, snippet):
        yield Button("English", editor_url(snippet), icon_name="globe", priority=58)
    if (
        isinstance(snippet, Menu)
        and deepl.is_configured()
        and user.has_perm("ifi_home_app.change_menugroup")
    ):
        yield Button(
            "Machine-translate menu",
            reverse("english_machine_translate_menu", args=[snippet.pk]),
            icon_name="globe",
            priority=58,
        )


class SuperusersMayLookPolicy(ModelPermissionPolicy):
    """Superusers may look; nobody may add, change or delete rows here
    (English is changed only in the English editor)."""

    def user_has_permission(self, user, action):
        return action == "view" and user.is_active and user.is_superuser

    def user_has_any_permission(self, user, actions):
        return "view" in actions and user.is_active and user.is_superuser

    def users_with_any_permission(self, actions):
        users = get_user_model().objects.filter(is_active=True, is_superuser=True)
        return users if "view" in actions else users.none()


class StoredEnglishViewSet(ModelViewSet):
    """Read-only list of every SegmentTranslation row, for debugging. The
    one place besides stored_translations.py that reads the table."""

    model = SegmentTranslation
    icon = "globe"
    menu_label = "Stored English"
    add_to_admin_menu = True
    inspect_view_enabled = True
    copy_view_enabled = False
    list_display = [
        "object_title",
        "segment_path",
        "norwegian_text",
        "english_text",
        "source",
        "translated_by",
        "has_error",
        "updated_at",
    ]
    list_filter = ["source", "has_error", "content_type"]
    search_fields = ["norwegian_text", "english_text"]
    form_fields = ["english_text"]  # never used: nobody may edit

    @property
    def permission_policy(self):
        return SuperusersMayLookPolicy(self.model)
