"""DeepLTranslator subclass -- see docs/claude_context/translation_views.md.

wagtail_localize's own DeepLTranslator.translate() calls response.json()
with no raise_for_status() first, so any non-2xx DeepL response (rate
limit, outage, bad auth) surfaces as an opaque JSONDecodeError/KeyError
instead of a distinguishable HTTPError. Fixed here rather than upstream,
following the same pattern as core_app.storage.LenientManifestStaticFilesStorage
(subclass a third-party class to override one specific behavior, don't fork
or patch the library)."""

from wagtail_localize.machine_translators.deepl import (
    DeepLTranslator as BaseDeepLTranslator,
)
from wagtail_localize.strings import StringValue

import requests


class DeepLTranslator(BaseDeepLTranslator):
    def translate(self, source_locale, target_locale, strings):
        response = requests.post(
            self.get_api_endpoint(),
            self.get_parameters(source_locale, target_locale, strings),
            timeout=int(self.options.get("TIMEOUT", 30)),
            headers=self.get_headers(),
        )
        response.raise_for_status()
        return {
            string: StringValue(translation["text"])
            for string, translation in zip(
                strings, response.json()["translations"], strict=True
            )
        }
