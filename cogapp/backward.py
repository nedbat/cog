"""Compatibility between Py2 and Py3."""

import sys
import unittest

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = (str,bytes)
    bytes_types = (bytes,)
    def to_bytes(s):
        return s.encode('utf8')
else:
    string_types = (basestring,)
    bytes_types = (str,)
    def to_bytes(s):
        return s

# Pythons 2 and 3 differ on where to get StringIO
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


def unittest_has(method):
    """Does `unittest.TestCase` have `method` defined?"""
    return hasattr(unittest.TestCase, method)


class TestCase(unittest.TestCase):
    """Just like unittest.TestCase, but with assert methods added.

    Designed to be compatible with 3.1 unittest.  Methods are only defined if
    `unittest` doesn't have them.

    """
    # pylint: disable=missing-docstring

    if not unittest_has('assertRaisesRegex'):
        def assertRaisesRegex(self, *args, **kwargs):
            return self.assertRaisesRegexp(*args, **kwargs)
