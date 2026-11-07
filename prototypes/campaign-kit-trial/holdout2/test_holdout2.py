"""Second holdout for the black-box variant (its acceptance suite is holdout/). Same rules as
spec/; the agents never see these inputs or their results. Scored by the trial only."""
import unittest

from textkit.cells import escape_cell
from textkit.durations import format_duration, parse_duration
from textkit.slug import slugify

SLUG = [("Ðuro Šćepanović", {}, "duro-scepanovic"), ("Æble & Øl", {}, "aeble-ol"),
        ("naïve café", {}, "naive-cafe"), ("Ångström", {}, "angstrom"), ("ŒIL", {}, "oeil"),
        ("þing", {}, "thing"), ("a b", {"sep": "."}, "a.b")]
PARSE = [("3D", 259200), ("1h 0m 1s", 3601), (" 45 ", 45), ("2.5m", 150)]
PARSE_INVALID = ["1h1h", "1.h"]
FORMAT = [(0.5, "1s"), (3599.5, "1h"), (172800, "2d")]
CELLS = [("+", "'+"), ("1,000", "1,000"), ("@user", "'@user"), ("\t", "'\t"), (1.0, "1.0"),
         (-0.5, "-0.5"), ("-5e", "'-5e"), ("＝1", "＝1")]


class Holdout2(unittest.TestCase):
    pass


def _eq(fn, args, kwargs, expected):
    def test(self):
        self.assertEqual(fn(*args, **kwargs), expected, f"{fn.__name__}{args!r}")
    return test


def _raises(text):
    def test(self):
        with self.assertRaises(ValueError):
            parse_duration(text)
    return test


_n = 0
for _t, _k, _e in SLUG:
    _n += 1; setattr(Holdout2, f"test_slug_{_n:02d}", _eq(slugify, (_t,), _k, _e))
for _t, _e in PARSE:
    _n += 1; setattr(Holdout2, f"test_parse_{_n:02d}", _eq(parse_duration, (_t,), {}, _e))
for _t in PARSE_INVALID:
    _n += 1; setattr(Holdout2, f"test_parse_invalid_{_n:02d}", _raises(_t))
for _s, _e in FORMAT:
    _n += 1; setattr(Holdout2, f"test_format_{_n:02d}", _eq(format_duration, (_s,), {}, _e))
for _v, _e in CELLS:
    _n += 1; setattr(Holdout2, f"test_cells_{_n:02d}", _eq(escape_cell, (_v,), {}, _e))
