"""Test the cogapp.makefiles modules"""

import shutil
import os
import random
import tempfile
from unittest import TestCase

from . import makefiles


class SimpleTests(TestCase):
    def setUp(self):
        # Create a temporary directory.
        my_dir = "testmakefiles_tempdir_" + str(random.random())[2:]
        self.tempdir = os.path.join(tempfile.gettempdir(), my_dir)
        os.mkdir(self.tempdir)

    def tearDown(self):
        # Get rid of the temporary directory.
        shutil.rmtree(self.tempdir)

    def exists(self, dname, fname):
        return os.path.exists(os.path.join(dname, fname))

    def check_files_exist(self, d, dname):
        for fname in d.keys():
            assert self.exists(dname, fname)
            if isinstance(d[fname], dict):
                self.check_files_exist(d[fname], os.path.join(dname, fname))

    def check_files_dont_exist(self, d, dname):
        for fname in d.keys():
            assert not self.exists(dname, fname)

    def test_one_file(self):
        fname = "foo.txt"
        notfname = "not_here.txt"
        d = {fname: "howdy"}
        assert not self.exists(self.tempdir, fname)
        assert not self.exists(self.tempdir, notfname)

        makefiles.make_files(d, self.tempdir)
        assert self.exists(self.tempdir, fname)
        assert not self.exists(self.tempdir, notfname)

        makefiles.remove_files(d, self.tempdir)
        assert not self.exists(self.tempdir, fname)
        assert not self.exists(self.tempdir, notfname)

    def test_many_files(self):
        d = {
            "top1.txt": "howdy",
            "top2.txt": "hello",
            "sub": {
                "sub1.txt": "inside",
                "sub2.txt": "inside2",
            },
        }

        self.check_files_dont_exist(d, self.tempdir)
        makefiles.make_files(d, self.tempdir)
        self.check_files_exist(d, self.tempdir)
        makefiles.remove_files(d, self.tempdir)
        self.check_files_dont_exist(d, self.tempdir)

    def test_overlapping(self):
        d1 = {
            "top1.txt": "howdy",
            "sub": {
                "sub1.txt": "inside",
            },
        }

        d2 = {
            "top2.txt": "hello",
            "sub": {
                "sub2.txt": "inside2",
            },
        }

        self.check_files_dont_exist(d1, self.tempdir)
        self.check_files_dont_exist(d2, self.tempdir)
        makefiles.make_files(d1, self.tempdir)
        makefiles.make_files(d2, self.tempdir)
        self.check_files_exist(d1, self.tempdir)
        self.check_files_exist(d2, self.tempdir)
        makefiles.remove_files(d1, self.tempdir)
        makefiles.remove_files(d2, self.tempdir)
        self.check_files_dont_exist(d1, self.tempdir)
        self.check_files_dont_exist(d2, self.tempdir)

    def test_contents(self):
        fname = "bar.txt"
        cont0 = "I am bar.txt"
        d = {fname: cont0}
        makefiles.make_files(d, self.tempdir)
        with open(os.path.join(self.tempdir, fname)) as fcont1:
            assert fcont1.read() == cont0

    def test_dedent(self):
        fname = "dedent.txt"
        d = {
            fname: """\
                This is dedent.txt
                \tTabbed in.
                  spaced in.
                OK.
                """,
        }
        makefiles.make_files(d, self.tempdir)
        with open(os.path.join(self.tempdir, fname)) as fcont:
            assert (
                fcont.read() == "This is dedent.txt\n\tTabbed in.\n  spaced in.\nOK.\n"
            )
