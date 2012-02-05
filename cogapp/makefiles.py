""" Dictionary-to-filetree functions, to create test files for testing.
    http://nedbatchelder.com/code/cog
    
    Copyright 2004-2009, Ned Batchelder.
"""

from __future__ import absolute_import
import os.path
from .whiteutils import reindentBlock
from .backward import string_types, to_bytes

__version__ = '1.0.20040126'
__all__ = ['makeFiles', 'removeFiles']

def makeFiles(d, basedir='.', raw=False):
    """ Create files from the dictionary `d`, in the directory named by `basedir`.
    """
    for name, contents in d.items():
        child = os.path.join(basedir, name)
        if isinstance(contents, string_types):
            mode = 'w'
            if raw:
                mode = 'wb'
            f = open(child, mode)
            if not raw:
                contents = reindentBlock(contents)
            f.write(to_bytes(contents))
            f.close()
        else:
            if not os.path.exists(child):
                os.mkdir(child)
            makeFiles(contents, child, raw=raw)

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

if __name__ == '__main__':      #pragma: no cover
    # Try it a little.
    d = {
        'test_makefiles': {
            'hey.txt': """\
                        This is hey.txt.
                        It's very simple.
                        """,
            'subdir': {
                'fooey': """\
                            # Fooey
                                Kablooey
                            Ew.
                            """
            }
        }
    }
    makeFiles(d)
