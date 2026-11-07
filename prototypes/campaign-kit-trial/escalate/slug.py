import re
import unicodedata

_SPELLED = {"æ": "ae", "Æ": "ae", "ø": "o", "Ø": "o", "ß": "ss"}


def slugify(text, sep="-"):
    """Lower-case ASCII URL slug: runs of anything but a-z and 0-9 become one separator."""
    text = "".join(_SPELLED.get(ch, ch) for ch in text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", sep, text.lower()).strip(sep)
