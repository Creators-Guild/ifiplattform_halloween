"""Our DeepL client -- see docs/claude_context/translation_overlay.md.

translate_texts() sends the same request wagtail-localize's DeepLTranslator
did (NB -> EN, XML tag handling, glossary), but checks the HTTP status
first: any non-2xx answer (rate limit, quota, bad key) raises a readable
requests.HTTPError instead of an opaque JSON error."""

import requests
from django.conf import settings

# Pause between DeepL calls, so batches aren't fired back-to-back.
DEEPL_CALL_DELAY_SECONDS = 1
BATCH_SIZE = 50  # DeepL's limit of texts per request
TIMEOUT_SECONDS = 30


def is_configured():
    return bool(settings.DEEPL_API_KEY)


def _endpoint():
    if settings.DEEPL_API_KEY.endswith(":fx"):
        return "https://api-free.deepl.com/v2/translate"
    return "https://api.deepl.com/v2/translate"


def translate_texts(texts):
    """English for each Norwegian text, in order. Texts are in stored form
    (HTML with <a id="a1"> placeholders, which DeepL keeps as XML tags)."""
    english = []
    for start in range(0, len(texts), BATCH_SIZE):
        parameters = {
            "text": texts[start : start + BATCH_SIZE],
            "tag_handling": "xml",
            "source_lang": "NB",
            "target_lang": "EN",
        }
        if settings.DEEPL_GLOSSARY_ID:
            parameters["glossary_id"] = settings.DEEPL_GLOSSARY_ID
        response = requests.post(
            _endpoint(),
            parameters,
            timeout=TIMEOUT_SECONDS,
            headers={"Authorization": f"DeepL-Auth-Key {settings.DEEPL_API_KEY}"},
        )
        if not response.ok:
            raise requests.HTTPError(_error_text(response), response=response)
        english += [item["text"] for item in response.json()["translations"]]
    return english


def _error_text(response):
    """DeepL's own explanation, plus what to do for the usual causes."""
    try:
        message = response.json().get("message", "")
    except ValueError:
        message = response.text[:200]
    text = f"DeepL answered {response.status_code}: {message or response.reason}."
    if response.status_code == 404 and settings.DEEPL_GLOSSARY_ID:
        text += (
            " The glossary in DEEPL_GLOSSARY_ID doesn't exist on this DeepL "
            "account: set the current glossary's ID, or leave it empty."
        )
    elif response.status_code in (401, 403):
        text += " Check DEEPL_API_KEY."
    elif response.status_code == 456:
        text += " The DeepL character quota is used up."
    return text
