import math
import re

_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}
_PART = re.compile(r"(\d+(?:\.\d+)?)([dhms])")


def _whole(seconds):
    return int(math.floor(seconds + 0.5))


def parse_duration(text):
    if not isinstance(text, str):
        raise ValueError("duration must be a string")
    s = text.strip().lower()
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return _whole(float(s))
    compact = s.replace(" ", "")
    pos, total, seen = 0, 0.0, set()
    for match in _PART.finditer(compact):
        unit = match.group(2)
        if match.start() != pos or unit in seen:
            raise ValueError(f"invalid duration: {text!r}")
        seen.add(unit)
        total += float(match.group(1)) * _UNITS[unit]
        pos = match.end()
    if not seen or pos != len(compact):
        raise ValueError(f"invalid duration: {text!r}")
    return _whole(total)


def format_duration(seconds):
    if seconds < 0:
        raise ValueError("negative duration")
    total = _whole(seconds)
    if total == 0:
        return "0s"
    parts = []
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        count, total = divmod(total, size)
        if count:
            parts.append(f"{count}{unit}")
    return " ".join(parts)
