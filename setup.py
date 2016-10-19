#!/usr/bin/python
""" Setup.py for Cog
    http://nedbatchelder.com/code/cog

    Copyright 2004-2016, Ned Batchelder.
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

extra_options = {}
try:
    # For building on Windows, need to fix the tar file after it's made.
    # Install https://bitbucket.org/ned/fixtar, then this will work.
    from setuptools_fixtar import fixtar
except ImportError:
    pass
else:
    extra_options['cmdclass'] = {
        'fixtar': fixtar.FixtarCommand,
    }

setup(
    name = 'cogapp',    # Because there's already a Cog in pypi!  :(
    version = '2.5.1',
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
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Code Generators",
        ],

    license = 'MIT',

    packages = [
        'cogapp',
        ],

    scripts = [
        'scripts/cog.py',
        ],

    **extra_options
    )
