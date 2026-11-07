"""slugify(text, sep="-"): ASCII, lower-case, one separator between words, none at the ends.

Letters with accents lose them. Letters that have no ASCII decomposition are spelled out:
Æ/æ -> ae, Ø/ø -> o, ß -> ss.
"""
import unittest

from textkit.slug import slugify

CASES = [
    ("Hello, World!", {}, "hello-world"),
    ("  multiple   spaces  ", {}, "multiple-spaces"),
    ("Crème brûlée", {}, "creme-brulee"),
    ("Ærøskøbing", {}, "aeroskobing"),
    ("Straße", {}, "strasse"),
    ("a--b__c", {}, "a-b-c"),
    ("Hello World", {"sep": "_"}, "hello_world"),
    ("", {}, ""),
    ("!!!", {}, ""),
    ("Ünïcödé 2024", {}, "unicode-2024"),
]


class SlugSpec(unittest.TestCase):
    pass


def _case(text, kwargs, expected):
    def test(self):
        self.assertEqual(slugify(text, **kwargs), expected, f"slugify({text!r}, **{kwargs})")
    return test


for _i, (_text, _kwargs, _expected) in enumerate(CASES, 1):
    setattr(SlugSpec, f"test_{_i:02d}", _case(_text, _kwargs, _expected))
