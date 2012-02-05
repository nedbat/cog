#!/usr/bin/python
""" Test the Cog distribution.
    http://nedbatchelder.com/code/cog

    Copyright 2004-2012, Ned Batchelder.
"""

import unittest, sys

bCoverage = ('-cover' in sys.argv or '--cover' in sys.argv)

if bCoverage:
    import coverage
    coverage.use_cache(0)
    coverage.exclude("#pragma: no cover")
    coverage.exclude("raise CogInternalError\(")
    coverage.start()

testmodules = [
    'cogapp.test_makefiles',
    'cogapp.test_whiteutils',
    'cogapp.test_cogapp',
    ]

# We don't need to import these modules to run the tests.  But loadTestsFromNames
# doesn't show import errors.  These imports do.
exec("import " + ("\nimport ".join(testmodules)))

suite = unittest.TestSuite()

for t in testmodules:
    try:
        # If the module defines a suite() function, call it to get the suite.
        mod = __import__(t, globals(), locals(), ['suite'])
        suitefn = getattr(mod, 'suite')
        suite.addTest(suitefn())
    except (ImportError, AttributeError):
        # else, just load all the test cases from the module.
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(t))


unittest.TextTestRunner().run(suite)


modnames = [
    "cogapp.cogapp",
    "cogapp.makefiles",
    "cogapp.whiteutils",
    "cogapp.test_cogapp",
    "cogapp.test_makefiles",
    "cogapp.test_whiteutils",
]

if bCoverage:
    coverage.stop()
    mods = [ sys.modules[n] for n in modnames ]
    coverage.report(mods)
