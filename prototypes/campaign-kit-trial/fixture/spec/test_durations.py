"""parse_duration(text) -> int seconds; format_duration(seconds) -> str.

parse: units d, h, m, s, case-insensitive, combined largest first ("1d2h", "1h 30m"), spaces
allowed between parts, decimals allowed ("1.5h"), a bare number means seconds. Each unit at
most once. Anything else (empty, a unit with no number, unknown units, signs) -> ValueError.

format: round to the nearest second, halves round up (2.5 -> 3), then "1d 1h 1m 1s" with
zero parts left out; 0 -> "0s"; negative -> ValueError.
"""
import unittest

from textkit.durations import format_duration, parse_duration

PARSE = [
    ("90s", 90), ("1h30m", 5400), ("2h", 7200), ("1h 30m", 5400),
    ("1d2h", 93600), ("45", 45), ("1H", 3600), ("1.5h", 5400),
]
PARSE_INVALID = ["", "h", "1x", "1h-30m", "-5m", "1m1m"]
FORMAT = [
    (0, "0s"), (59, "59s"), (60, "1m"), (3600, "1h"), (3661, "1h 1m 1s"),
    (90061, "1d 1h 1m 1s"), (59.6, "1m"), (2.5, "3s"), (0.4, "0s"),
]
FORMAT_INVALID = [-1]


class DurationSpec(unittest.TestCase):
    pass


def _parse(text, expected):
    def test(self):
        self.assertEqual(parse_duration(text), expected, f"parse_duration({text!r})")
    return test


def _parse_invalid(text):
    def test(self):
        with self.assertRaises(ValueError, msg=f"parse_duration({text!r})"):
            parse_duration(text)
    return test


def _format(seconds, expected):
    def test(self):
        self.assertEqual(format_duration(seconds), expected, f"format_duration({seconds!r})")
    return test


def _format_invalid(seconds):
    def test(self):
        with self.assertRaises(ValueError, msg=f"format_duration({seconds!r})"):
            format_duration(seconds)
    return test


for _i, (_t, _e) in enumerate(PARSE, 1):
    setattr(DurationSpec, f"test_parse_{_i:02d}", _parse(_t, _e))
for _i, _t in enumerate(PARSE_INVALID, 1):
    setattr(DurationSpec, f"test_parse_invalid_{_i:02d}", _parse_invalid(_t))
for _i, (_s, _e) in enumerate(FORMAT, 1):
    setattr(DurationSpec, f"test_format_{_i:02d}", _format(_s, _e))
for _i, _s in enumerate(FORMAT_INVALID, 1):
    setattr(DurationSpec, f"test_format_invalid_{_i:02d}", _format_invalid(_s))
