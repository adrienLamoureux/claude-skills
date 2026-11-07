import re

_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


def parse_duration(text):
    """'90s' -> 90, '2h' -> 7200. Raises ValueError on anything else."""
    match = re.fullmatch(r"(\d+)([dhms])", text)
    if not match:
        raise ValueError(f"invalid duration: {text!r}")
    return int(match.group(1)) * _UNITS[match.group(2)]


def format_duration(seconds):
    """Seconds -> human text."""
    return f"{int(seconds)}s"
