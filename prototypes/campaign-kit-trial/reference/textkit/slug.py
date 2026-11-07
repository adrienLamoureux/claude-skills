import re
import unicodedata

_SPELLED = {"æ": "ae", "Æ": "ae", "ø": "o", "Ø": "o", "ß": "ss", "ł": "l", "Ł": "l",
            "œ": "oe", "Œ": "oe", "đ": "d", "Đ": "d", "ð": "d", "Ð": "d", "þ": "th", "Þ": "th"}


def slugify(text, sep="-"):
    text = "".join(_SPELLED.get(ch, ch) for ch in text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", sep, text.lower()).strip(sep)
