""" Dictionary-to-filetree functions, to create test files for testing.
    http://nedbatchelder.com/code/cog

    Copyright 2004-2019, Ned Batchelder.
"""

from __future__ import absolute_import

import os.path

from .backward import string_types, bytes_types
from .whiteutils import reindentBlock

__all__ = ['makeFiles', 'removeFiles']

def makeFiles(d, basedir='.', bytes=False):
    """ Create files from the dictionary `d`, in the directory named by `basedir`.
        If `bytes` is true, then treat bytestrings as bytes, else as text.
    """
    for name, contents in d.items():
        child = os.path.join(basedir, name)
        if isinstance(contents, string_types):
            mode = 'w'
            if bytes and isinstance(contents, bytes_types):
                mode += "b"
            f = open(child, mode)
            contents = reindentBlock(contents)
            f.write(contents)
            f.close()
        else:
            if not os.path.exists(child):
                os.mkdir(child)
            makeFiles(contents, child)

def removeFiles(d, basedir='.'):
    """ Remove the files created by makeFiles.
        Directories are removed if they are empty.
    """
    for name, contents in d.items():
        child = os.path.join(basedir, name)
        if isinstance(contents, string_types):
            os.remove(child)
        else:
            removeFiles(contents, child)
            if not os.listdir(child):
                os.rmdir(child)
