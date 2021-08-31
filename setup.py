#!/usr/bin/python
""" Setup.py for Cog
    http://nedbatchelder.com/code/cog

    Copyright 2004-2021, Ned Batchelder.
"""

from setuptools import setup

with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name = 'cogapp',    # Because there's already a Cog in pypi!  :(
    version = '3.1.0',
    url = 'http://nedbatchelder.com/code/cog',
    author = 'Ned Batchelder',
    author_email = 'ned@nedbatchelder.com',
    description =
        'Cog: A content generator for executing Python snippets in source files.',

    long_description = long_description,
    long_description_content_type = 'text/x-rst',

    project_urls={
        'Documentation': 'http://nedbatchelder.com/code/cog',
        'Code': 'http://github.com/nedbat/cog',
        'Issues': 'https://github.com/nedbat/cog/issues',
        'Funding': 'https://github.com/users/nedbat/sponsorship',
        'Twitter': 'https://twitter.com/nedbat',
    },

    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Code Generators",
        ],

    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",

    license = 'MIT',

    packages = [
        'cogapp',
        ],

    scripts = [
        'scripts/cog.py',
        ],

    entry_points={
        'console_scripts': [
            'cog = cogapp:main',
            ],
        },
    )
