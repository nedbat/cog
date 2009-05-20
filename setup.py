#!/usr/bin/python
""" Setup.py for Cog
    http://nedbatchelder.com/code/cog

    Copyright 2004-2008, Ned Batchelder.
"""

# $Id: setup.py 138 2008-05-21 13:24:40Z nedbat $

from distutils.core import setup
setup(
    name = 'cog',
    version = '2.1',
    url = 'http://nedbatchelder.com/code/cog',
    author = 'Ned Batchelder',
    author_email = 'ned@nedbatchelder.com',
    description = 
        'A code generator for executing Python snippets in source files.',

    packages = [
        'cogapp',
        'handyxml',
        ],

    scripts = [
        'scripts/cog.py',
        'scripts/test_cog.py',
        ],
    )
