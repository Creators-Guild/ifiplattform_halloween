"""The article/category/union/tool page tree -- everything that came out of
the original monolithic article_models.py except TranslationWarningMixin/
BannerStyleMixin/EditorModeMixin (models/page_mixins.py, shared with
models/event/ too) and the re-export shim itself (models/article_models.py,
kept at that exact path -- three migrations pin
ifi_home_app.models.article_models.TranslationWarningMixin's module path)."""
