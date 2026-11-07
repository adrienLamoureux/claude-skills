"""escape_cell(value) -> str, safe for a CSV cell a spreadsheet will open.

Text starting with =, +, -, @, a tab or a carriage return gets a leading apostrophe, unless the
whole text is a plain number ("-5", "+3.25"). Numbers (int, float) are written as str(value).
None -> "".
"""
import unittest

from textkit.cells import escape_cell

CASES = [
    ("hello", "hello"), ("=1+1", "'=1+1"), ("+SUM(A1)", "'+SUM(A1)"), ("-2+3", "'-2+3"),
    ("@SUM(A1)", "'@SUM(A1)"), ("-5", "-5"), ("+3.25", "+3.25"), (-5, "-5"), (2.5, "2.5"),
    (None, ""), ("\t=1", "'\t=1"), ("\rcmd", "'\rcmd"), ("'=1", "'=1"), ("a=b", "a=b"),
]


class CellSpec(unittest.TestCase):
    pass


def _case(value, expected):
    def test(self):
        self.assertEqual(escape_cell(value), expected, f"escape_cell({value!r})")
    return test


for _i, (_v, _e) in enumerate(CASES, 1):
    setattr(CellSpec, f"test_{_i:02d}", _case(_v, _e))
