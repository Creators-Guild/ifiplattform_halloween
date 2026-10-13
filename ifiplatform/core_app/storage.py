"""Static file storage backends.

ManifestStaticFilesStorage's manifest_strict flag isn't something Django
accepts as a constructor kwarg via STORAGES' OPTIONS -- it's a class
attribute, so overriding it means subclassing. Only matters when
DEBUG=False (production) -- see settings.py's own STORAGES comment for
what manifest_strict=False actually changes."""

from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class LenientManifestStaticFilesStorage(ManifestStaticFilesStorage):
    manifest_strict = False
