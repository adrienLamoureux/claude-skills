def escape_cell(value):
    """Make a value safe to write into a CSV cell opened by a spreadsheet."""
    text = str(value)
    if text[:1] in ("=", "+", "-", "@"):
        return "'" + text
    return text
