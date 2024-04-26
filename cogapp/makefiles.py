"""Dictionary-to-filetree functions, to create test files for testing."""

import os.path

from .whiteutils import reindent_block


def make_files(d, basedir="."):
    """Create files from the dictionary `d` in the directory named by `basedir`."""
    for name, contents in d.items():
        child = os.path.join(basedir, name)
        if isinstance(contents, (bytes, str)):
            mode = "w"
            if isinstance(contents, bytes):
                mode += "b"
            with open(child, mode) as f:
                f.write(reindent_block(contents))
        else:
            if not os.path.exists(child):
                os.mkdir(child)
            make_files(contents, child)


def remove_files(d, basedir="."):
    """Remove the files created by `makeFiles`.

    Directories are removed if they are empty.

    """
    for name, contents in d.items():
        child = os.path.join(basedir, name)
        if isinstance(contents, (bytes, str)):
            os.remove(child)
        else:
            remove_files(contents, child)
            if not os.listdir(child):
                os.rmdir(child)
