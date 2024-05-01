"""Test the cogapp.whiteutils module."""

from unittest import TestCase

from .whiteutils import common_prefix, reindent_block, white_prefix


class WhitePrefixTests(TestCase):
    """Test cases for cogapp.whiteutils."""

    def test_single_line(self):
        self.assertEqual(white_prefix([""]), "")
        self.assertEqual(white_prefix([" "]), "")
        self.assertEqual(white_prefix(["x"]), "")
        self.assertEqual(white_prefix([" x"]), " ")
        self.assertEqual(white_prefix(["\tx"]), "\t")
        self.assertEqual(white_prefix(["  x"]), "  ")
        self.assertEqual(white_prefix([" \t \tx   "]), " \t \t")

    def test_multi_line(self):
        self.assertEqual(white_prefix(["  x", "  x", "  x"]), "  ")
        self.assertEqual(white_prefix(["   y", "  y", " y"]), " ")
        self.assertEqual(white_prefix([" y", "  y", "   y"]), " ")

    def test_blank_lines_are_ignored(self):
        self.assertEqual(white_prefix(["  x", "  x", "", "  x"]), "  ")
        self.assertEqual(white_prefix(["", "  x", "  x", "  x"]), "  ")
        self.assertEqual(white_prefix(["  x", "  x", "  x", ""]), "  ")
        self.assertEqual(white_prefix(["  x", "  x", "          ", "  x"]), "  ")

    def test_tab_characters(self):
        self.assertEqual(white_prefix(["\timport sys", "", "\tprint sys.argv"]), "\t")

    def test_decreasing_lengths(self):
        self.assertEqual(white_prefix(["   x", "  x", " x"]), " ")
        self.assertEqual(white_prefix(["     x", " x", " x"]), " ")


class ReindentBlockTests(TestCase):
    """Test cases for cogapp.reindentBlock."""

    def test_non_term_line(self):
        self.assertEqual(reindent_block(""), "")
        self.assertEqual(reindent_block("x"), "x")
        self.assertEqual(reindent_block(" x"), "x")
        self.assertEqual(reindent_block("  x"), "x")
        self.assertEqual(reindent_block("\tx"), "x")
        self.assertEqual(reindent_block("x", " "), " x")
        self.assertEqual(reindent_block("x", "\t"), "\tx")
        self.assertEqual(reindent_block(" x", " "), " x")
        self.assertEqual(reindent_block(" x", "\t"), "\tx")
        self.assertEqual(reindent_block(" x", "  "), "  x")

    def test_single_line(self):
        self.assertEqual(reindent_block("\n"), "\n")
        self.assertEqual(reindent_block("x\n"), "x\n")
        self.assertEqual(reindent_block(" x\n"), "x\n")
        self.assertEqual(reindent_block("  x\n"), "x\n")
        self.assertEqual(reindent_block("\tx\n"), "x\n")
        self.assertEqual(reindent_block("x\n", " "), " x\n")
        self.assertEqual(reindent_block("x\n", "\t"), "\tx\n")
        self.assertEqual(reindent_block(" x\n", " "), " x\n")
        self.assertEqual(reindent_block(" x\n", "\t"), "\tx\n")
        self.assertEqual(reindent_block(" x\n", "  "), "  x\n")

    def test_real_block(self):
        self.assertEqual(
            reindent_block("\timport sys\n\n\tprint sys.argv\n"),
            "import sys\n\nprint sys.argv\n",
        )


class CommonPrefixTests(TestCase):
    """Test cases for cogapp.commonPrefix."""

    def test_degenerate_cases(self):
        self.assertEqual(common_prefix([]), "")
        self.assertEqual(common_prefix([""]), "")
        self.assertEqual(common_prefix(["", "", "", "", ""]), "")
        self.assertEqual(common_prefix(["cat in the hat"]), "cat in the hat")

    def test_no_common_prefix(self):
        self.assertEqual(common_prefix(["a", "b"]), "")
        self.assertEqual(common_prefix(["a", "b", "c", "d", "e", "f"]), "")
        self.assertEqual(common_prefix(["a", "a", "a", "a", "a", "x"]), "")

    def test_usual_cases(self):
        self.assertEqual(common_prefix(["ab", "ac"]), "a")
        self.assertEqual(common_prefix(["aab", "aac"]), "aa")
        self.assertEqual(common_prefix(["aab", "aab", "aab", "aac"]), "aa")

    def test_blank_line(self):
        self.assertEqual(common_prefix(["abc", "abx", "", "aby"]), "")

    def test_decreasing_lengths(self):
        self.assertEqual(common_prefix(["abcd", "abc", "ab"]), "ab")
