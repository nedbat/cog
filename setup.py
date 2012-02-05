#!/usr/bin/python
""" Setup.py for Cog
    http://nedbatchelder.com/code/cog

    Copyright 2004-2012, Ned Batchelder.
"""

from distutils.core import setup
setup(
    name = 'cogapp',    # Because there's already a Cog in pypi!  :(
    version = '2.3',
    url = 'http://nedbatchelder.com/code/cog',
    author = 'Ned Batchelder',
    author_email = 'ned@nedbatchelder.com',
    description = 
        'Cog: A code generator for executing Python snippets in source files.',

    long_description = '''\
        Docs at `http://nedbatchelder.com/code/cog <http://nedbatchelder.com/code/cog>`_.
    
        Code repository and issue tracker are at
        `bitbucket.org <http://bitbucket.org/ned/cog>`_.
        ''',

    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
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
