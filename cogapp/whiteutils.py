"""Indentation utilities for Cog."""

import re


def whitePrefix(strings):
    """Find the whitespace prefix common to non-blank lines in `strings`."""
    # Remove all blank lines from the list
    strings = [s for s in strings if s.strip() != ""]

    if not strings:
        return ""

    # Find initial whitespace chunk in the first line.
    # This is the best prefix we can hope for.
    pat = r"\s*"
    if isinstance(strings[0], bytes):
        pat = pat.encode("utf-8")
    prefix = re.match(pat, strings[0]).group(0)

    # Loop over the other strings, keeping only as much of
    # the prefix as matches each string.
    for s in strings:
        for i in range(len(prefix)):
            if prefix[i] != s[i]:
                prefix = prefix[:i]
                break
    return prefix


def reindentBlock(lines, newIndent=""):
    """Re-indent a block of text.

    Take a block of text as a string or list of lines.
    Remove any common whitespace indentation.
    Re-indent using `newIndent`, and return it as a single string.

    """
    sep, nothing = "\n", ""
    if isinstance(lines, bytes):
        sep, nothing = b"\n", b""
    if isinstance(lines, (bytes, str)):
        lines = lines.split(sep)
    oldIndent = whitePrefix(lines)
    outLines = []
    for line in lines:
        if oldIndent:
            line = line.replace(oldIndent, nothing, 1)
        if line and newIndent:
            line = newIndent + line
        outLines.append(line)
    return sep.join(outLines)


def commonPrefix(strings):
    """Find the longest string that is a prefix of all the strings."""
    if not strings:
        return ""
    prefix = strings[0]
    for s in strings:
        if len(s) < len(prefix):
            prefix = prefix[: len(s)]
        if not prefix:
            return ""
        for i in range(len(prefix)):
            if prefix[i] != s[i]:
                prefix = prefix[:i]
                break
    return prefix
