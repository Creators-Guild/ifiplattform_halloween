"""Template filters for rendering article body blocks."""

from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """dictionary[key] for templates -- Django's built-in dot lookup only
    works for a literal key written in the template, not a variable, which
    is what looking a block up in block_styles by block.id needs."""
    if dictionary is None:
        return None
    return dictionary.get(str(key))


@register.filter
def index(sequence, position):
    """sequence[position] for templates -- same reasoning as lookup() above,
    but for a list (a multi_column block's per-column weight, indexed by
    each column's own loop position)."""
    if sequence is None:
        return None
    try:
        return sequence[position]
    except IndexError:
        return None
