"""Test the cogapp.whiteutils module."""

import pytest

from .whiteutils import common_prefix, reindent_block, white_prefix


@pytest.mark.parametrize(
    "lines, expected",
    [
        # single line
        ([""], ""),
        ([" "], ""),
        (["x"], ""),
        ([" x"], " "),
        (["\tx"], "\t"),
        (["  x"], "  "),
        ([" \t \tx   "], " \t \t"),
        # multi line
        (["  x", "  x", "  x"], "  "),
        (["   y", "  y", " y"], " "),
        ([" y", "  y", "   y"], " "),
        # blank lines are ignored
        (["  x", "  x", "", "  x"], "  "),
        (["", "  x", "  x", "  x"], "  "),
        (["  x", "  x", "  x", ""], "  "),
        (["  x", "  x", "          ", "  x"], "  "),
        # tab characters
        (["\timport sys", "", "\tprint sys.argv"], "\t"),
        # decreasing lengths
        (["   x", "  x", " x"], " "),
        (["     x", " x", " x"], " "),
    ],
)
def test_white_prefix(lines, expected):
    assert white_prefix(lines) == expected


@pytest.mark.parametrize(
    "text, indent, expected",
    [
        # non-terminated line
        ("", "", ""),
        ("x", "", "x"),
        (" x", "", "x"),
        ("  x", "", "x"),
        ("\tx", "", "x"),
        ("x", " ", " x"),
        ("x", "\t", "\tx"),
        (" x", " ", " x"),
        (" x", "\t", "\tx"),
        (" x", "  ", "  x"),
        # single line
        ("\n", "", "\n"),
        ("x\n", "", "x\n"),
        (" x\n", "", "x\n"),
        ("  x\n", "", "x\n"),
        ("\tx\n", "", "x\n"),
        ("x\n", " ", " x\n"),
        ("x\n", "\t", "\tx\n"),
        (" x\n", " ", " x\n"),
        (" x\n", "\t", "\tx\n"),
        (" x\n", "  ", "  x\n"),
        # real block
        (
            "\timport sys\n\n\tprint sys.argv\n",
            "",
            "import sys\n\nprint sys.argv\n",
        ),
    ],
)
def test_reindent_block(text, indent, expected):
    assert reindent_block(text, indent) == expected


@pytest.mark.parametrize(
    "strings, expected",
    [
        # degenerate cases
        ([], ""),
        ([""], ""),
        (["", "", "", "", ""], ""),
        (["cat in the hat"], "cat in the hat"),
        # no common prefix
        (["a", "b"], ""),
        (["a", "b", "c", "d", "e", "f"], ""),
        (["a", "a", "a", "a", "a", "x"], ""),
        # usual cases
        (["ab", "ac"], "a"),
        (["aab", "aac"], "aa"),
        (["aab", "aab", "aab", "aac"], "aa"),
        # blank line
        (["abc", "abx", "", "aby"], ""),
        # decreasing lengths
        (["abcd", "abc", "ab"], "ab"),
    ],
)
def test_common_prefix(strings, expected):
    assert common_prefix(strings) == expected
