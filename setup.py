#!/usr/bin/python
""" Setup.py for Cog
    http://nedbatchelder.com/code/cog

    Copyright 2004-2008, Ned Batchelder.
"""

from distutils.core import setup
setup(
    name = 'cog',
    version = '2.2',
    url = 'http://nedbatchelder.com/code/cog',
    author = 'Ned Batchelder',
    author_email = 'ned@nedbatchelder.com',
    description = 
        'A code generator for executing Python snippets in source files.',

    packages = [
        'cogapp',
        ],

    scripts = [
        'scripts/cog.py',
        'scripts/test_cog.py',
        ],
    )
