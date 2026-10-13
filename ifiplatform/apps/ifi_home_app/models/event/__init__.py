"""The Events section -- everything that came out of the former monolithic
event_models.py: constants.py, blocks.py, pages.py, peoply.py,
calendar_layout.py, dates.py and queries.py.

Deliberately imports nothing, same as models/article/__init__.py: pulling
pages.py in from here would mean any import of e.g. event.calendar_layout
also dragged in the article models it depends on, recreating the circular
import UnionPage.get_context works around. Model registration is done by
models/__init__.py instead.
"""
