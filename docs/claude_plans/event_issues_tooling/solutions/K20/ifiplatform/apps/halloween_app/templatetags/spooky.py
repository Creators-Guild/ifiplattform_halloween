"""{{ text|spooky }}: makes text look haunted."""

from django import template

register = template.Library()


@register.filter
def spooky(text):
    """ "Welcome to the corner" -> "WeLcOmE tO tHe CoRnEr... 👻": every other
    letter a capital, then a ghost."""
    letters = []
    upper = True
    for letter in str(text):
        if letter.isalpha():
            letters.append(letter.upper() if upper else letter.lower())
            upper = not upper
        else:
            letters.append(letter)
    return "".join(letters) + "... 👻"
