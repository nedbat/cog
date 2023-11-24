""" Test the cogapp.makefiles modules
"""

import shutil
import os
import random
import tempfile
from unittest import TestCase

from . import makefiles


class SimpleTests(TestCase):

    def setUp(self):
        # Create a temporary directory.
        my_dir = 'testmakefiles_tempdir_' + str(random.random())[2:]
        self.tempdir = os.path.join(tempfile.gettempdir(), my_dir)
        os.mkdir(self.tempdir)

    def tearDown(self):
        # Get rid of the temporary directory.
        shutil.rmtree(self.tempdir)

    def exists(self, dname, fname):
        return os.path.exists(os.path.join(dname, fname))

    def checkFilesExist(self, d, dname):
        for fname in d.keys():
            assert(self.exists(dname, fname))
            if type(d[fname]) == type({}):
                self.checkFilesExist(d[fname], os.path.join(dname, fname))

    def checkFilesDontExist(self, d, dname):
        for fname in d.keys():
            assert(not self.exists(dname, fname))

    def testOneFile(self):
        fname = 'foo.txt'
        notfname = 'not_here.txt'
        d = { fname: "howdy" }
        assert(not self.exists(self.tempdir, fname))
        assert(not self.exists(self.tempdir, notfname))

        makefiles.makeFiles(d, self.tempdir)
        assert(self.exists(self.tempdir, fname))
        assert(not self.exists(self.tempdir, notfname))

        makefiles.removeFiles(d, self.tempdir)
        assert(not self.exists(self.tempdir, fname))
        assert(not self.exists(self.tempdir, notfname))

    def testManyFiles(self):
        d = {
            'top1.txt': "howdy",
            'top2.txt': "hello",
            'sub': {
                 'sub1.txt': "inside",
                 'sub2.txt': "inside2",
                 },
            }

        self.checkFilesDontExist(d, self.tempdir)
        makefiles.makeFiles(d, self.tempdir)
        self.checkFilesExist(d, self.tempdir)
        makefiles.removeFiles(d, self.tempdir)
        self.checkFilesDontExist(d, self.tempdir)

    def testOverlapping(self):
        d1 = {
            'top1.txt': "howdy",
            'sub': {
                 'sub1.txt': "inside",
                 },
            }

        d2 = {
            'top2.txt': "hello",
            'sub': {
                 'sub2.txt': "inside2",
                 },
            }

        self.checkFilesDontExist(d1, self.tempdir)
        self.checkFilesDontExist(d2, self.tempdir)
        makefiles.makeFiles(d1, self.tempdir)
        makefiles.makeFiles(d2, self.tempdir)
        self.checkFilesExist(d1, self.tempdir)
        self.checkFilesExist(d2, self.tempdir)
        makefiles.removeFiles(d1, self.tempdir)
        makefiles.removeFiles(d2, self.tempdir)
        self.checkFilesDontExist(d1, self.tempdir)
        self.checkFilesDontExist(d2, self.tempdir)

    def testContents(self):
        fname = 'bar.txt'
        cont0 = "I am bar.txt"
        d = { fname: cont0 }
        makefiles.makeFiles(d, self.tempdir)
        with open(os.path.join(self.tempdir, fname)) as fcont1:
            assert(fcont1.read() == cont0)

    def testDedent(self):
        fname = 'dedent.txt'
        d = {
            fname: """\
                This is dedent.txt
                \tTabbed in.
                  spaced in.
                OK.
                """,
            }
        makefiles.makeFiles(d, self.tempdir)
        with open(os.path.join(self.tempdir, fname)) as fcont:
            assert(fcont.read() == "This is dedent.txt\n\tTabbed in.\n  spaced in.\nOK.\n")
