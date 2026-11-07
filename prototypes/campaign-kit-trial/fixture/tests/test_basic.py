import unittest

from textkit.cells import escape_cell
from textkit.durations import format_duration, parse_duration
from textkit.slug import slugify


class Basic(unittest.TestCase):
    def test_slug_words(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_slug_already(self):
        self.assertEqual(slugify("Already-a-slug"), "already-a-slug")

    def test_parse_seconds(self):
        self.assertEqual(parse_duration("90s"), 90)

    def test_parse_hours(self):
        self.assertEqual(parse_duration("2h"), 7200)

    def test_format_seconds(self):
        self.assertEqual(format_duration(45), "45s")

    def test_cell_plain(self):
        self.assertEqual(escape_cell("plain"), "plain")

    def test_cell_formula(self):
        self.assertEqual(escape_cell("=cmd"), "'=cmd")
