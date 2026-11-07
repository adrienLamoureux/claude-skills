import re

_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def escape_cell(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value)
    if text.startswith(_TRIGGERS) and not _NUMBER.fullmatch(text):
        return "'" + text
    return text
