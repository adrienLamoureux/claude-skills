import re


def slugify(text, sep="-"):
    """Lower-case URL slug: runs of anything but a-z and 0-9 become one separator."""
    return re.sub(r"[^a-z0-9]+", sep, text.lower()).strip(sep)
