"""Holdout cases: same rules as spec/, inputs the agents never saw. Scored by the trial only."""
import unittest

from textkit.cells import escape_cell
from textkit.durations import format_duration, parse_duration
from textkit.slug import slugify

SLUG = [
    ("Łódź", {}, "lodz"), ("Œuvre complète", {}, "oeuvre-complete"), ("ﬁnal ﬂag", {}, "final-flag"),
    ("ＡＢＣ　１２３", {}, "abc-123"), ("Þór Đaković", {}, "thor-dakovic"),
    ("--leading and trailing--", {}, "leading-and-trailing"), ("Déjà vu", {"sep": "_"}, "deja_vu"),
]
PARSE = [("1D", 86400), ("  2m  ", 120), ("0s", 0), ("1h0m", 3600), ("1h 1m 1s", 3661),
         ("1.5m", 90), ("2h 30m", 9000)]
FORMAT = [(1.5, "2s"), (86400, "1d"), (7322, "2h 2m 2s")]
ROUND_TRIP = [1, 59, 61, 3599, 3601, 86399, 90061]
CELLS = [("=", "'="), ("@", "'@"), ("-", "'-"), ("1e5", "1e5"), ("-1.5e3", "-1.5e3"),
         ("+-1", "'+-1"), (0, "0"), ("−5", "−5"), (".5", ".5"), ("-.5", "-.5"),
         ('=HYPERLINK("http://x")', '\'=HYPERLINK("http://x")'), ("- 5", "'- 5")]


class Holdout(unittest.TestCase):
    pass


def _eq(fn, args, kwargs, expected):
    def test(self):
        self.assertEqual(fn(*args, **kwargs), expected, f"{fn.__name__}{args!r}")
    return test


def _round_trip(seconds):
    def test(self):
        self.assertEqual(parse_duration(format_duration(seconds)), seconds)
    return test


_n = 0
for _t, _k, _e in SLUG:
    _n += 1; setattr(Holdout, f"test_slug_{_n:02d}", _eq(slugify, (_t,), _k, _e))
for _t, _e in PARSE:
    _n += 1; setattr(Holdout, f"test_parse_{_n:02d}", _eq(parse_duration, (_t,), {}, _e))
for _s, _e in FORMAT:
    _n += 1; setattr(Holdout, f"test_format_{_n:02d}", _eq(format_duration, (_s,), {}, _e))
for _s in ROUND_TRIP:
    _n += 1; setattr(Holdout, f"test_round_trip_{_n:02d}", _round_trip(_s))
for _v, _e in CELLS:
    _n += 1; setattr(Holdout, f"test_cells_{_n:02d}", _eq(escape_cell, (_v,), {}, _e))
