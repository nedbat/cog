#!/usr/bin/python
""" Setup.py for Cog
    http://nedbatchelder.com/code/cog

    Copyright 2004-2009, Ned Batchelder.
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

    long_description = '''\
        Code repository and issue tracker are at
        `bitbucket.org <http://bitbucket.org/ned/cog>`_.
        ''',

    classifiers = [
        "Environment :: Console",
        "Intended Audience :: Developers"
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Code Generators",
        ],

    license = 'MIT',

    packages = [
        'cogapp',
        ],

    scripts = [
        'scripts/cog.py',
        'scripts/test_cog.py',
        ],
    )
