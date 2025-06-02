"""Utilities for cog."""

import contextlib
import functools
import hashlib
import os
import sys


# Support FIPS mode. We don't use MD5 for security.
md5 = functools.partial(hashlib.md5, usedforsecurity=False)


class Redirectable:
    """An object with its own stdout and stderr files."""

    def __init__(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def set_output(self, stdout=None, stderr=None):
        """Assign new files for standard out and/or standard error."""
        if stdout:
            self.stdout = stdout
        if stderr:
            self.stderr = stderr

    def prout(self, s, end="\n"):
        print(s, file=self.stdout, end=end)

    def prerr(self, s, end="\n"):
        print(s, file=self.stderr, end=end)


class NumberedFileReader:
    """A decorator for files that counts the readline()'s called."""

    def __init__(self, f):
        self.f = f
        self.n = 0

    def readline(self):
        line = self.f.readline()
        if line:
            self.n += 1
        return line

    def linenumber(self):
        return self.n


@contextlib.contextmanager
def change_dir(new_dir):
    """Change directory, and then change back.

    Use as a context manager, it will return to the original
    directory at the end of the block.

    """
    old_dir = os.getcwd()
    os.chdir(str(new_dir))
    try:
        yield
    finally:
        os.chdir(old_dir)
