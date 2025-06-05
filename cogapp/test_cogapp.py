"""Test cogapp."""

import io
import os
import os.path
import random
import re
import shutil
import stat
import sys
import tempfile
import threading
from unittest import TestCase

from .cogapp import Cog, CogOptions, CogGenerator
from .cogapp import CogError, CogUsageError, CogGeneratedError, CogUserException
from .cogapp import usage, __version__, main
from .hashhandler import HashHandler
from .makefiles import make_files
from .whiteutils import reindent_block


class CogTestsInMemory(TestCase):
    """Test cases for cogapp.Cog()"""

    def test_no_cog(self):
        strings = [
            "",
            " ",
            " \t \t \tx",
            "hello",
            "the cat\nin the\nhat.",
            "Horton\n\tHears A\n\t\tWho",
        ]
        for s in strings:
            self.assertEqual(Cog().process_string(s), s)

    def test_simple(self):
        infile = """\
            Some text.
            //[[[cog
            import cog
            cog.outl("This is line one\\n")
            cog.outl("This is line two")
            //]]]
            gobbledegook.
            //[[[end]]]
            epilogue.
            """

        outfile = """\
            Some text.
            //[[[cog
            import cog
            cog.outl("This is line one\\n")
            cog.outl("This is line two")
            //]]]
            This is line one

            This is line two
            //[[[end]]]
            epilogue.
            """

        self.assertEqual(Cog().process_string(infile), outfile)

    def test_empty_cog(self):
        # The cog clause can be totally empty.  Not sure why you'd want it,
        # but it works.
        infile = """\
            hello
            //[[[cog
            //]]]
            //[[[end]]]
            goodbye
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_multiple_cogs(self):
        # One file can have many cog chunks, even abutting each other.
        infile = """\
            //[[[cog
            cog.out("chunk1")
            //]]]
            chunk1
            //[[[end]]]
            //[[[cog
            cog.out("chunk2")
            //]]]
            chunk2
            //[[[end]]]
            between chunks
            //[[[cog
            cog.out("chunk3")
            //]]]
            chunk3
            //[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_trim_blank_lines(self):
        infile = """\
            //[[[cog
            cog.out("This is line one\\n", trimblanklines=True)
            cog.out('''
                This is line two
            ''', dedent=True, trimblanklines=True)
            cog.outl("This is line three", trimblanklines=True)
            //]]]
            This is line one
            This is line two
            This is line three
            //[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_trim_empty_blank_lines(self):
        infile = """\
            //[[[cog
            cog.out("This is line one\\n", trimblanklines=True)
            cog.out('''
                This is line two
            ''', dedent=True, trimblanklines=True)
            cog.out('', dedent=True, trimblanklines=True)
            cog.outl("This is line three", trimblanklines=True)
            //]]]
            This is line one
            This is line two
            This is line three
            //[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_trim_blank_lines_with_last_partial(self):
        infile = """\
            //[[[cog
            cog.out("This is line one\\n", trimblanklines=True)
            cog.out("\\nLine two\\nLine three", trimblanklines=True)
            //]]]
            This is line one
            Line two
            Line three
            //[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_cog_out_dedent(self):
        infile = """\
            //[[[cog
            cog.out("This is the first line\\n")
            cog.out('''
                This is dedent=True 1
                 This is dedent=True 2
            ''', dedent=True, trimblanklines=True)
            cog.out('''
                This is dedent=False 1
                 This is dedent=False 2
            ''', dedent=False, trimblanklines=True)
            cog.out('''
                This is dedent=default 1
                 This is dedent=default 2
            ''', trimblanklines=True)
            cog.out("This is the last line\\n")
            //]]]
            This is the first line
            This is dedent=True 1
             This is dedent=True 2
                This is dedent=False 1
                 This is dedent=False 2
                This is dedent=default 1
                 This is dedent=default 2
            This is the last line
            //[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test22_end_of_line(self):
        # In Python 2.2, this cog file was not parsing because the
        # last line is indented but didn't end with a newline.
        infile = """\
            //[[[cog
            import cog
            for i in range(3):
                cog.out("%d\\n" % i)
            //]]]
            0
            1
            2
            //[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_indented_code(self):
        infile = """\
            first line
                [[[cog
                import cog
                for i in range(3):
                    cog.out("xx%d\\n" % i)
                ]]]
                xx0
                xx1
                xx2
                [[[end]]]
            last line
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_prefixed_code(self):
        infile = """\
            --[[[cog
            --import cog
            --for i in range(3):
            --    cog.out("xx%d\\n" % i)
            --]]]
            xx0
            xx1
            xx2
            --[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_prefixed_indented_code(self):
        infile = """\
            prologue
            --[[[cog
            --   import cog
            --   for i in range(3):
            --       cog.out("xy%d\\n" % i)
            --]]]
            xy0
            xy1
            xy2
            --[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_bogus_prefix_match(self):
        infile = """\
            prologue
            #[[[cog
                import cog
                # This comment should not be clobbered by removing the pound sign.
                for i in range(3):
                    cog.out("xy%d\\n" % i)
            #]]]
            xy0
            xy1
            xy2
            #[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_no_final_newline(self):
        # If the cog'ed output has no final newline,
        # it shouldn't eat up the cog terminator.
        infile = """\
            prologue
            [[[cog
                import cog
                for i in range(3):
                    cog.out("%d" % i)
            ]]]
            012
            [[[end]]]
            epilogue
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_no_output_at_all(self):
        # If there is absolutely no cog output, that's ok.
        infile = """\
            prologue
            [[[cog
                i = 1
            ]]]
            [[[end]]]
            epilogue
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_purely_blank_line(self):
        # If there is a blank line in the cog code with no whitespace
        # prefix, that should be OK.

        infile = """\
            prologue
                [[[cog
                    import sys
                    cog.out("Hello")
            $
                    cog.out("There")
                ]]]
                HelloThere
                [[[end]]]
            epilogue
            """

        infile = reindent_block(infile.replace("$", ""))
        self.assertEqual(Cog().process_string(infile), infile)

    def test_empty_outl(self):
        # Alexander Belchenko suggested the string argument to outl should
        # be optional.  Does it work?

        infile = """\
            prologue
            [[[cog
                cog.outl("x")
                cog.outl()
                cog.outl("y")
                cog.out()   # Also optional, a complete no-op.
                cog.outl(trimblanklines=True)
                cog.outl("z")
            ]]]
            x

            y

            z
            [[[end]]]
            epilogue
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_first_line_num(self):
        infile = """\
            fooey
            [[[cog
                cog.outl("started at line number %d" % cog.firstLineNum)
            ]]]
            started at line number 2
            [[[end]]]
            blah blah
            [[[cog
                cog.outl("and again at line %d" % cog.firstLineNum)
            ]]]
            and again at line 8
            [[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)

    def test_compact_one_line_code(self):
        infile = """\
            first line
            hey: [[[cog cog.outl("hello %d" % (3*3*3*3)) ]]] looky!
            get rid of this!
            [[[end]]]
            last line
            """

        outfile = """\
            first line
            hey: [[[cog cog.outl("hello %d" % (3*3*3*3)) ]]] looky!
            hello 81
            [[[end]]]
            last line
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), reindent_block(outfile))

    def test_inside_out_compact(self):
        infile = """\
            first line
            hey?: ]]] what is this? [[[cog strange!
            get rid of this!
            [[[end]]]
            last line
            """
        with self.assertRaisesRegex(
            CogError, r"^infile.txt\(2\): Cog code markers inverted$"
        ):
            Cog().process_string(reindent_block(infile), "infile.txt")

    def test_sharing_globals(self):
        infile = """\
            first line
            hey: [[[cog s="hey there" ]]] looky!
            [[[end]]]
            more literal junk.
            [[[cog cog.outl(s) ]]]
            [[[end]]]
            last line
            """

        outfile = """\
            first line
            hey: [[[cog s="hey there" ]]] looky!
            [[[end]]]
            more literal junk.
            [[[cog cog.outl(s) ]]]
            hey there
            [[[end]]]
            last line
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), reindent_block(outfile))

    def test_assert_in_cog_code(self):
        # Check that we can test assertions in cog code in the test framework.
        infile = """\
            [[[cog
            assert 1 == 2, "Oops"
            ]]]
            [[[end]]]
            """
        infile = reindent_block(infile)
        with self.assertRaisesRegex(CogUserException, "AssertionError: Oops"):
            Cog().process_string(infile)

    def test_cog_previous(self):
        # Check that we can access the previous run's output.
        infile = """\
            [[[cog
            assert cog.previous == "Hello there!\\n", "WTF??"
            cog.out(cog.previous)
            cog.outl("Ran again!")
            ]]]
            Hello there!
            [[[end]]]
            """

        outfile = """\
            [[[cog
            assert cog.previous == "Hello there!\\n", "WTF??"
            cog.out(cog.previous)
            cog.outl("Ran again!")
            ]]]
            Hello there!
            Ran again!
            [[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), reindent_block(outfile))


class CogOptionsTests(TestCase):
    """Test the CogOptions class."""

    def test_equality(self):
        o = CogOptions()
        p = CogOptions()
        self.assertEqual(o, p)
        o.parse_args(["-r"])
        self.assertNotEqual(o, p)
        p.parse_args(["-r"])
        self.assertEqual(o, p)

    def test_cloning(self):
        o = CogOptions()
        o.parse_args(["-I", "fooey", "-I", "booey", "-s", " /*x*/"])
        p = o.clone()
        self.assertEqual(o, p)
        p.parse_args(["-I", "huey", "-D", "foo=quux"])
        self.assertNotEqual(o, p)
        q = CogOptions()
        q.parse_args(
            [
                "-I",
                "fooey",
                "-I",
                "booey",
                "-s",
                " /*x*/",
                "-I",
                "huey",
                "-D",
                "foo=quux",
            ]
        )
        self.assertEqual(p, q)

    def test_combining_flags(self):
        # Single-character flags can be combined.
        o = CogOptions()
        o.parse_args(["-e", "-r", "-z"])
        p = CogOptions()
        p.parse_args(["-erz"])
        self.assertEqual(o, p)

    def test_markers(self):
        o = CogOptions()
        o._parse_markers("a b c")
        self.assertEqual("a", o.begin_spec)
        self.assertEqual("b", o.end_spec)
        self.assertEqual("c", o.end_output)

    def test_markers_switch(self):
        o = CogOptions()
        o.parse_args(["--markers", "a b c"])
        self.assertEqual("a", o.begin_spec)
        self.assertEqual("b", o.end_spec)
        self.assertEqual("c", o.end_output)


class FileStructureTests(TestCase):
    """Test that we're properly strict about the structure of files."""

    def is_bad(self, infile, msg=None):
        infile = reindent_block(infile)
        with self.assertRaisesRegex(CogError, "^" + re.escape(msg) + "$"):
            Cog().process_string(infile, "infile.txt")

    def test_begin_no_end(self):
        infile = """\
            Fooey
            #[[[cog
                cog.outl('hello')
            """
        self.is_bad(infile, "infile.txt(2): Cog block begun but never ended.")

    def test_no_eoo(self):
        infile = """\
            Fooey
            #[[[cog
                cog.outl('hello')
            #]]]
            """
        self.is_bad(infile, "infile.txt(4): Missing '[[[end]]]' before end of file.")

        infile2 = """\
            Fooey
            #[[[cog
                cog.outl('hello')
            #]]]
            #[[[cog
                cog.outl('goodbye')
            #]]]
            """
        self.is_bad(infile2, "infile.txt(5): Unexpected '[[[cog'")

    def test_start_with_end(self):
        infile = """\
            #]]]
            """
        self.is_bad(infile, "infile.txt(1): Unexpected ']]]'")

        infile2 = """\
            #[[[cog
                cog.outl('hello')
            #]]]
            #[[[end]]]
            #]]]
            """
        self.is_bad(infile2, "infile.txt(5): Unexpected ']]]'")

    def test_start_with_eoo(self):
        infile = """\
            #[[[end]]]
            """
        self.is_bad(infile, "infile.txt(1): Unexpected '[[[end]]]'")

        infile2 = """\
            #[[[cog
                cog.outl('hello')
            #]]]
            #[[[end]]]
            #[[[end]]]
            """
        self.is_bad(infile2, "infile.txt(5): Unexpected '[[[end]]]'")

    def test_no_end(self):
        infile = """\
            #[[[cog
                cog.outl("hello")
            #[[[end]]]
            """
        self.is_bad(infile, "infile.txt(3): Unexpected '[[[end]]]'")

        infile2 = """\
            #[[[cog
                cog.outl('hello')
            #]]]
            #[[[end]]]
            #[[[cog
                cog.outl("hello")
            #[[[end]]]
            """
        self.is_bad(infile2, "infile.txt(7): Unexpected '[[[end]]]'")

    def test_two_begins(self):
        infile = """\
            #[[[cog
            #[[[cog
                cog.outl("hello")
            #]]]
            #[[[end]]]
            """
        self.is_bad(infile, "infile.txt(2): Unexpected '[[[cog'")

        infile2 = """\
            #[[[cog
                cog.outl("hello")
            #]]]
            #[[[end]]]
            #[[[cog
            #[[[cog
                cog.outl("hello")
            #]]]
            #[[[end]]]
            """
        self.is_bad(infile2, "infile.txt(6): Unexpected '[[[cog'")

    def test_two_ends(self):
        infile = """\
            #[[[cog
                cog.outl("hello")
            #]]]
            #]]]
            #[[[end]]]
            """
        self.is_bad(infile, "infile.txt(4): Unexpected ']]]'")

        infile2 = """\
            #[[[cog
                cog.outl("hello")
            #]]]
            #[[[end]]]
            #[[[cog
                cog.outl("hello")
            #]]]
            #]]]
            #[[[end]]]
            """
        self.is_bad(infile2, "infile.txt(8): Unexpected ']]]'")


class CogErrorTests(TestCase):
    """Test cases for cog.error()."""

    def test_error_msg(self):
        infile = """\
            [[[cog cog.error("This ain't right!")]]]
            [[[end]]]
            """

        infile = reindent_block(infile)
        with self.assertRaisesRegex(CogGeneratedError, "^This ain't right!$"):
            Cog().process_string(infile)

    def test_error_no_msg(self):
        infile = """\
            [[[cog cog.error()]]]
            [[[end]]]
            """

        infile = reindent_block(infile)
        with self.assertRaisesRegex(
            CogGeneratedError, "^Error raised by cog generator.$"
        ):
            Cog().process_string(infile)

    def test_no_error_if_error_not_called(self):
        infile = """\
            --[[[cog
            --import cog
            --for i in range(3):
            --    if i > 10:
            --        cog.error("Something is amiss!")
            --    cog.out("xx%d\\n" % i)
            --]]]
            xx0
            xx1
            xx2
            --[[[end]]]
            """

        infile = reindent_block(infile)
        self.assertEqual(Cog().process_string(infile), infile)


class CogGeneratorGetCodeTests(TestCase):
    """Tests for CogGenerator.getCode()."""

    def setUp(self):
        # All tests get a generator to use, and short same-length names for
        # the functions we're going to use.
        self.gen = CogGenerator()
        self.m = self.gen.parse_marker
        self.parse_line = self.gen.parse_line

    def test_empty(self):
        self.m("// [[[cog")
        self.m("// ]]]")
        self.assertEqual(self.gen.get_code(), "")

    def test_simple(self):
        self.m("// [[[cog")
        self.parse_line('  print "hello"')
        self.parse_line('  print "bye"')
        self.m("// ]]]")
        self.assertEqual(self.gen.get_code(), 'print "hello"\nprint "bye"')

    def test_compressed1(self):
        # For a while, I supported compressed code blocks, but no longer.
        self.m('// [[[cog: print """')
        self.parse_line("// hello")
        self.parse_line("// bye")
        self.m('// """)]]]')
        self.assertEqual(self.gen.get_code(), "hello\nbye")

    def test_compressed2(self):
        # For a while, I supported compressed code blocks, but no longer.
        self.m('// [[[cog: print """')
        self.parse_line("hello")
        self.parse_line("bye")
        self.m('// """)]]]')
        self.assertEqual(self.gen.get_code(), "hello\nbye")

    def test_compressed3(self):
        # For a while, I supported compressed code blocks, but no longer.
        self.m("// [[[cog")
        self.parse_line('print """hello')
        self.parse_line("bye")
        self.m('// """)]]]')
        self.assertEqual(self.gen.get_code(), 'print """hello\nbye')

    def test_compressed4(self):
        # For a while, I supported compressed code blocks, but no longer.
        self.m('// [[[cog: print """')
        self.parse_line("hello")
        self.parse_line('bye""")')
        self.m("// ]]]")
        self.assertEqual(self.gen.get_code(), 'hello\nbye""")')

    def test_no_common_prefix_for_markers(self):
        # It's important to be able to use #if 0 to hide lines from a
        # C++ compiler.
        self.m("#if 0 //[[[cog")
        self.parse_line("\timport cog, sys")
        self.parse_line("")
        self.parse_line("\tprint sys.argv")
        self.m("#endif //]]]")
        self.assertEqual(self.gen.get_code(), "import cog, sys\n\nprint sys.argv")


class TestCaseWithTempDir(TestCase):
    def new_cog(self):
        """Initialize the cog members for another run."""
        # Create a cog engine, and catch its output.
        self.cog = Cog()
        self.output = io.StringIO()
        self.cog.set_output(stdout=self.output, stderr=self.output)

    def setUp(self):
        # Create a temporary directory.
        self.tempdir = os.path.join(
            tempfile.gettempdir(), "testcog_tempdir_" + str(random.random())[2:]
        )
        os.mkdir(self.tempdir)
        self.olddir = os.getcwd()
        os.chdir(self.tempdir)
        self.new_cog()

    def tearDown(self):
        os.chdir(self.olddir)
        # Get rid of the temporary directory.
        shutil.rmtree(self.tempdir)

    def assertFilesSame(self, file_name1, file_name2):
        with open(os.path.join(self.tempdir, file_name1), "rb") as f1:
            text1 = f1.read()
        with open(os.path.join(self.tempdir, file_name2), "rb") as f2:
            text2 = f2.read()
        self.assertEqual(text1, text2)

    def assertFileContent(self, fname, content):
        absname = os.path.join(self.tempdir, fname)
        with open(absname, "rb") as f:
            file_content = f.read()
        self.assertEqual(file_content, content.encode("utf-8"))


class ArgumentHandlingTests(TestCaseWithTempDir):
    def test_argument_failure(self):
        # Return value 2 means usage problem.
        self.assertEqual(self.cog.main(["argv0", "-j"]), 2)
        output = self.output.getvalue()
        self.assertIn("option -j not recognized", output)
        with self.assertRaisesRegex(CogUsageError, r"^No files to process$"):
            self.cog.callable_main(["argv0"])
        with self.assertRaisesRegex(CogUsageError, r"^option -j not recognized$"):
            self.cog.callable_main(["argv0", "-j"])

    def test_no_dash_o_and_at_file(self):
        make_files({"cogfiles.txt": "# Please run cog"})
        with self.assertRaisesRegex(CogUsageError, r"^Can't use -o with @file$"):
            self.cog.callable_main(["argv0", "-o", "foo", "@cogfiles.txt"])

    def test_no_dash_o_and_amp_file(self):
        make_files({"cogfiles.txt": "# Please run cog"})
        with self.assertRaisesRegex(CogUsageError, r"^Can't use -o with &file$"):
            self.cog.callable_main(["argv0", "-o", "foo", "&cogfiles.txt"])

    def test_no_diff_without_check(self):
        with self.assertRaisesRegex(
            CogUsageError, r"^Can't use --diff without --check$"
        ):
            self.cog.callable_main(["argv0", "--diff"])

    def test_dash_v(self):
        self.assertEqual(self.cog.main(["argv0", "-v"]), 0)
        output = self.output.getvalue()
        self.assertEqual("Cog version %s\n" % __version__, output)

    def produces_help(self, args):
        self.new_cog()
        argv = ["argv0"] + args.split()
        self.assertEqual(self.cog.main(argv), 0)
        self.assertEqual(usage, self.output.getvalue())

    def test_dash_h(self):
        # -h, --help, or -? anywhere on the command line should just print help.
        self.produces_help("-h")
        self.produces_help("--help")
        self.produces_help("-?")
        self.produces_help("fooey.txt -h")
        self.produces_help("fooey.txt --help")
        self.produces_help("-o -r @fooey.txt -? @booey.txt")

    def test_dash_o_and_dash_r(self):
        d = {
            "cogfile.txt": """\
                # Please run cog
                """
        }

        make_files(d)
        with self.assertRaisesRegex(
            CogUsageError, r"^Can't use -o with -r \(they are opposites\)$"
        ):
            self.cog.callable_main(["argv0", "-o", "foo", "-r", "cogfile.txt"])

    def test_dash_z(self):
        d = {
            "test.cog": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                """,
            "test.out": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                void DoSomething();
                void DoAnotherThing();
                void DoLastThing();
                """,
        }

        make_files(d)
        with self.assertRaisesRegex(
            CogError, r"^test.cog\(6\): Missing '\[\[\[end\]\]\]' before end of file.$"
        ):
            self.cog.callable_main(["argv0", "-r", "test.cog"])
        self.new_cog()
        self.cog.callable_main(["argv0", "-r", "-z", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")

    def test_bad_dash_d(self):
        with self.assertRaisesRegex(CogUsageError, r"^-D takes a name=value argument$"):
            self.cog.callable_main(["argv0", "-Dfooey", "cog.txt"])
        with self.assertRaisesRegex(CogUsageError, r"^-D takes a name=value argument$"):
            self.cog.callable_main(["argv0", "-D", "fooey", "cog.txt"])

    def test_bad_markers(self):
        with self.assertRaisesRegex(
            CogUsageError,
            r"^--markers requires 3 values separated by spaces, could not parse 'X'$",
        ):
            self.cog.callable_main(["argv0", "--markers=X"])
        with self.assertRaisesRegex(
            CogUsageError,
            r"^--markers requires 3 values separated by spaces, could not parse 'A B C D'$",
        ):
            self.cog.callable_main(["argv0", "--markers=A B C D"])


class TestMain(TestCaseWithTempDir):
    def setUp(self):
        super().setUp()
        self.old_argv = sys.argv[:]
        self.old_stderr = sys.stderr
        sys.stderr = io.StringIO()

    def tearDown(self):
        sys.stderr = self.old_stderr
        sys.argv = self.old_argv
        sys.modules.pop("mycode", None)
        super().tearDown()

    def test_main_function(self):
        sys.argv = ["argv0", "-Z"]
        ret = main()
        self.assertEqual(ret, 2)
        stderr = sys.stderr.getvalue()
        self.assertEqual(stderr, "option -Z not recognized\n(for help use --help)\n")

    files = {
        "test.cog": """\
            //[[[cog
            def func():
                import mycode
                mycode.boom()
            //]]]
            //[[[end]]]
            -----
            //[[[cog
            func()
            //]]]
            //[[[end]]]
            """,
        "mycode.py": """\
            def boom():
                [][0]
            """,
    }

    def test_error_report(self):
        self.check_error_report()

    def test_error_report_with_prologue(self):
        self.check_error_report("-p", "#1\n#2")

    def check_error_report(self, *args):
        """Check that the error report is right."""
        make_files(self.files)
        sys.argv = ["argv0"] + list(args) + ["-r", "test.cog"]
        main()
        expected = reindent_block("""\
            Traceback (most recent call last):
              File "test.cog", line 9, in <module>
                func()
              File "test.cog", line 4, in func
                mycode.boom()
              File "MYCODE", line 2, in boom
                [][0]
            IndexError: list index out of range
            """)
        expected = expected.replace("MYCODE", os.path.abspath("mycode.py"))
        assert expected == sys.stderr.getvalue()

    def test_error_in_prologue(self):
        make_files(self.files)
        sys.argv = ["argv0", "-p", "import mycode; mycode.boom()", "-r", "test.cog"]
        main()
        expected = reindent_block("""\
            Traceback (most recent call last):
              File "<prologue>", line 1, in <module>
                import mycode; mycode.boom()
              File "MYCODE", line 2, in boom
                [][0]
            IndexError: list index out of range
            """)
        expected = expected.replace("MYCODE", os.path.abspath("mycode.py"))
        assert expected == sys.stderr.getvalue()


class TestFileHandling(TestCaseWithTempDir):
    def test_simple(self):
        d = {
            "test.cog": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                //[[[end]]]
                """,
            "test.out": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                void DoSomething();
                void DoAnotherThing();
                void DoLastThing();
                //[[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)

    def test_print_output(self):
        d = {
            "test.cog": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    print("void %s();" % fn)
                //]]]
                //[[[end]]]
                """,
            "test.out": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    print("void %s();" % fn)
                //]]]
                void DoSomething();
                void DoAnotherThing();
                void DoLastThing();
                //[[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-rP", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)

    def test_wildcards(self):
        d = {
            "test.cog": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                //[[[end]]]
                """,
            "test2.cog": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                //[[[end]]]
                """,
            "test.out": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                void DoSomething();
                void DoAnotherThing();
                void DoLastThing();
                //[[[end]]]
                """,
            "not_this_one.cog": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                //[[[end]]]
                """,
            "not_this_one.out": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                //[[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "t*.cog"])
        self.assertFilesSame("test.cog", "test.out")
        self.assertFilesSame("test2.cog", "test.out")
        self.assertFilesSame("not_this_one.cog", "not_this_one.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)

    def test_output_file(self):
        # -o sets the output file.
        d = {
            "test.cog": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                //[[[end]]]
                """,
            "test.out": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                void DoSomething();
                void DoAnotherThing();
                void DoLastThing();
                //[[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-o", "in/a/dir/test.cogged", "test.cog"])
        self.assertFilesSame("in/a/dir/test.cogged", "test.out")

    def test_at_file(self):
        d = {
            "one.cog": """\
                //[[[cog
                cog.outl("hello world")
                //]]]
                //[[[end]]]
                """,
            "one.out": """\
                //[[[cog
                cog.outl("hello world")
                //]]]
                hello world
                //[[[end]]]
                """,
            "two.cog": """\
                //[[[cog
                cog.outl("goodbye cruel world")
                //]]]
                //[[[end]]]
                """,
            "two.out": """\
                //[[[cog
                cog.outl("goodbye cruel world")
                //]]]
                goodbye cruel world
                //[[[end]]]
                """,
            "cogfiles.txt": """\
                # Please run cog
                one.cog

                two.cog
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "@cogfiles.txt"])
        self.assertFilesSame("one.cog", "one.out")
        self.assertFilesSame("two.cog", "two.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)

    def test_nested_at_file(self):
        d = {
            "one.cog": """\
                //[[[cog
                cog.outl("hello world")
                //]]]
                //[[[end]]]
                """,
            "one.out": """\
                //[[[cog
                cog.outl("hello world")
                //]]]
                hello world
                //[[[end]]]
                """,
            "two.cog": """\
                //[[[cog
                cog.outl("goodbye cruel world")
                //]]]
                //[[[end]]]
                """,
            "two.out": """\
                //[[[cog
                cog.outl("goodbye cruel world")
                //]]]
                goodbye cruel world
                //[[[end]]]
                """,
            "cogfiles.txt": """\
                # Please run cog
                one.cog
                @cogfiles2.txt
                """,
            "cogfiles2.txt": """\
                # This one too, please.
                two.cog
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "@cogfiles.txt"])
        self.assertFilesSame("one.cog", "one.out")
        self.assertFilesSame("two.cog", "two.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)

    def test_at_file_with_args(self):
        d = {
            "both.cog": """\
                //[[[cog
                cog.outl("one: %s" % ('one' in globals()))
                cog.outl("two: %s" % ('two' in globals()))
                //]]]
                //[[[end]]]
                """,
            "one.out": """\
                //[[[cog
                cog.outl("one: %s" % ('one' in globals()))
                cog.outl("two: %s" % ('two' in globals()))
                //]]]
                one: True // ONE
                two: False // ONE
                //[[[end]]]
                """,
            "two.out": """\
                //[[[cog
                cog.outl("one: %s" % ('one' in globals()))
                cog.outl("two: %s" % ('two' in globals()))
                //]]]
                one: False // TWO
                two: True // TWO
                //[[[end]]]
                """,
            "cogfiles.txt": """\
                # Please run cog
                both.cog -o in/a/dir/both.one -s ' // ONE' -D one=x
                both.cog -o in/a/dir/both.two -s ' // TWO' -D two=x
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "@cogfiles.txt"])
        self.assertFilesSame("in/a/dir/both.one", "one.out")
        self.assertFilesSame("in/a/dir/both.two", "two.out")

    def test_at_file_with_bad_arg_combo(self):
        d = {
            "both.cog": """\
                //[[[cog
                cog.outl("one: %s" % ('one' in globals()))
                cog.outl("two: %s" % ('two' in globals()))
                //]]]
                //[[[end]]]
                """,
            "cogfiles.txt": """\
                # Please run cog
                both.cog
                both.cog -d # This is bad: -r and -d
                """,
        }

        make_files(d)
        with self.assertRaisesRegex(
            CogUsageError,
            r"^Can't use -d with -r \(or you would delete all your source!\)$",
        ):
            self.cog.callable_main(["argv0", "-r", "@cogfiles.txt"])

    def test_at_file_with_tricky_filenames(self):
        def fix_backslashes(files_txt):
            """Make the contents of a files.txt sensitive to the platform."""
            if sys.platform != "win32":
                files_txt = files_txt.replace("\\", "/")
            return files_txt

        d = {
            "one 1.cog": """\
                //[[[cog cog.outl("hello world") ]]]
                """,
            "one.out": """\
                //[[[cog cog.outl("hello world") ]]]
                hello world //xxx
                """,
            "subdir": {
                "subback.cog": """\
                    //[[[cog cog.outl("down deep with backslashes") ]]]
                    """,
                "subfwd.cog": """\
                    //[[[cog cog.outl("down deep with slashes") ]]]
                    """,
            },
            "subback.out": """\
                //[[[cog cog.outl("down deep with backslashes") ]]]
                down deep with backslashes //yyy
                """,
            "subfwd.out": """\
                //[[[cog cog.outl("down deep with slashes") ]]]
                down deep with slashes //zzz
                """,
            "cogfiles.txt": fix_backslashes("""\
                # Please run cog
                'one 1.cog' -s ' //xxx'
                subdir\\subback.cog -s ' //yyy'
                subdir/subfwd.cog -s ' //zzz'
                """),
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-z", "-r", "@cogfiles.txt"])
        self.assertFilesSame("one 1.cog", "one.out")
        self.assertFilesSame("subdir/subback.cog", "subback.out")
        self.assertFilesSame("subdir/subfwd.cog", "subfwd.out")

    def test_amp_file(self):
        d = {
            "code": {
                "files_to_cog": """\
                    # A locally resolved file name.
                    test.cog
                    """,
                "test.cog": """\
                    //[[[cog
                        import myampsubmodule
                    //]]]
                    //[[[end]]]
                    """,
                "test.out": """\
                    //[[[cog
                        import myampsubmodule
                    //]]]
                    Hello from myampsubmodule
                    //[[[end]]]
                    """,
                "myampsubmodule.py": """\
                    import cog
                    cog.outl("Hello from myampsubmodule")
                    """,
            }
        }

        make_files(d)
        print(os.path.abspath("code/test.out"))
        self.cog.callable_main(["argv0", "-r", "&code/files_to_cog"])
        self.assertFilesSame("code/test.cog", "code/test.out")

    def run_with_verbosity(self, verbosity):
        d = {
            "unchanged.cog": """\
                //[[[cog
                cog.outl("hello world")
                //]]]
                hello world
                //[[[end]]]
                """,
            "changed.cog": """\
                //[[[cog
                cog.outl("goodbye cruel world")
                //]]]
                //[[[end]]]
                """,
            "cogfiles.txt": """\
                unchanged.cog
                changed.cog
                """,
        }

        make_files(d)
        self.cog.callable_main(
            ["argv0", "-r", "--verbosity=" + verbosity, "@cogfiles.txt"]
        )
        output = self.output.getvalue()
        return output

    def test_verbosity0(self):
        output = self.run_with_verbosity("0")
        self.assertEqual(output, "")

    def test_verbosity1(self):
        output = self.run_with_verbosity("1")
        self.assertEqual(output, "Cogging changed.cog  (changed)\n")

    def test_verbosity2(self):
        output = self.run_with_verbosity("2")
        self.assertEqual(
            output, "Cogging unchanged.cog\nCogging changed.cog  (changed)\n"
        )

    def test_change_dir(self):
        # The code can change directories, cog will move us back.
        d = {
            "sub": {
                "data.txt": "Hello!",
            },
            "test.cog": """\
                //[[[cog
                import os
                os.chdir("sub")
                cog.outl(open("data.txt").read())
                //]]]
                //[[[end]]]
                """,
            "test.out": """\
                //[[[cog
                import os
                os.chdir("sub")
                cog.outl(open("data.txt").read())
                //]]]
                Hello!
                //[[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)


class CogTestLineEndings(TestCaseWithTempDir):
    """Tests for -U option (force LF line-endings in output)."""

    lines_in = [
        "Some text.",
        "//[[[cog",
        'cog.outl("Cog text")',
        "//]]]",
        "gobbledegook.",
        "//[[[end]]]",
        "epilogue.",
        "",
    ]

    lines_out = [
        "Some text.",
        "//[[[cog",
        'cog.outl("Cog text")',
        "//]]]",
        "Cog text",
        "//[[[end]]]",
        "epilogue.",
        "",
    ]

    def test_output_native_eol(self):
        make_files({"infile": "\n".join(self.lines_in)})
        self.cog.callable_main(["argv0", "-o", "outfile", "infile"])
        self.assertFileContent("outfile", os.linesep.join(self.lines_out))

    def test_output_lf_eol(self):
        make_files({"infile": "\n".join(self.lines_in)})
        self.cog.callable_main(["argv0", "-U", "-o", "outfile", "infile"])
        self.assertFileContent("outfile", "\n".join(self.lines_out))

    def test_replace_native_eol(self):
        make_files({"test.cog": "\n".join(self.lines_in)})
        self.cog.callable_main(["argv0", "-r", "test.cog"])
        self.assertFileContent("test.cog", os.linesep.join(self.lines_out))

    def test_replace_lf_eol(self):
        make_files({"test.cog": "\n".join(self.lines_in)})
        self.cog.callable_main(["argv0", "-U", "-r", "test.cog"])
        self.assertFileContent("test.cog", "\n".join(self.lines_out))


class CogTestCharacterEncoding(TestCaseWithTempDir):
    def test_simple(self):
        d = {
            "test.cog": b"""\
                // This is my C++ file.
                //[[[cog
                cog.outl("// Unicode: \xe1\x88\xb4 (U+1234)")
                //]]]
                //[[[end]]]
                """,
            "test.out": b"""\
                // This is my C++ file.
                //[[[cog
                cog.outl("// Unicode: \xe1\x88\xb4 (U+1234)")
                //]]]
                // Unicode: \xe1\x88\xb4 (U+1234)
                //[[[end]]]
                """.replace(b"\n", os.linesep.encode()),
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)

    def test_file_encoding_option(self):
        d = {
            "test.cog": b"""\
                // \xca\xee\xe4\xe8\xf0\xe2\xea\xe0 Windows
                //[[[cog
                cog.outl("\xd1\xfa\xe5\xf8\xfc \xe5\xf9\xb8 \xfd\xf2\xe8\xf5 \xec\xff\xe3\xea\xe8\xf5 \xf4\xf0\xe0\xed\xf6\xf3\xe7\xf1\xea\xe8\xf5 \xe1\xf3\xeb\xee\xea \xe4\xe0 \xe2\xfb\xef\xe5\xe9 \xf7\xe0\xfe")
                //]]]
                //[[[end]]]
                """,
            "test.out": b"""\
                // \xca\xee\xe4\xe8\xf0\xe2\xea\xe0 Windows
                //[[[cog
                cog.outl("\xd1\xfa\xe5\xf8\xfc \xe5\xf9\xb8 \xfd\xf2\xe8\xf5 \xec\xff\xe3\xea\xe8\xf5 \xf4\xf0\xe0\xed\xf6\xf3\xe7\xf1\xea\xe8\xf5 \xe1\xf3\xeb\xee\xea \xe4\xe0 \xe2\xfb\xef\xe5\xe9 \xf7\xe0\xfe")
                //]]]
                \xd1\xfa\xe5\xf8\xfc \xe5\xf9\xb8 \xfd\xf2\xe8\xf5 \xec\xff\xe3\xea\xe8\xf5 \xf4\xf0\xe0\xed\xf6\xf3\xe7\xf1\xea\xe8\xf5 \xe1\xf3\xeb\xee\xea \xe4\xe0 \xe2\xfb\xef\xe5\xe9 \xf7\xe0\xfe
                //[[[end]]]
                """.replace(b"\n", os.linesep.encode()),
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-n", "cp1251", "-r", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)


class TestCaseWithImports(TestCaseWithTempDir):
    """Automatic resetting of sys.modules for tests that import modules.

    When running tests which import modules, the sys.modules list
    leaks from one test to the next.  This test case class scrubs
    the list after each run to keep the tests isolated from each other.

    """

    def setUp(self):
        super().setUp()
        self.sysmodulekeys = list(sys.modules)

    def tearDown(self):
        modstoscrub = [
            modname for modname in sys.modules if modname not in self.sysmodulekeys
        ]
        for modname in modstoscrub:
            del sys.modules[modname]
        super().tearDown()


class CogIncludeTests(TestCaseWithImports):
    dincludes = {
        "test.cog": """\
            //[[[cog
                import mymodule
            //]]]
            //[[[end]]]
            """,
        "test.out": """\
            //[[[cog
                import mymodule
            //]]]
            Hello from mymodule
            //[[[end]]]
            """,
        "test2.out": """\
            //[[[cog
                import mymodule
            //]]]
            Hello from mymodule in inc2
            //[[[end]]]
            """,
        "include": {
            "mymodule.py": """\
                import cog
                cog.outl("Hello from mymodule")
                """
        },
        "inc2": {
            "mymodule.py": """\
                import cog
                cog.outl("Hello from mymodule in inc2")
                """
        },
        "inc3": {
            "someothermodule.py": """\
                import cog
                cog.outl("This is some other module.")
                """
        },
    }

    def test_need_include_path(self):
        # Try it without the -I, to see that an ImportError happens.
        make_files(self.dincludes)
        msg = "(ImportError|ModuleNotFoundError): No module named '?mymodule'?"
        with self.assertRaisesRegex(CogUserException, msg):
            self.cog.callable_main(["argv0", "-r", "test.cog"])

    def test_include_path(self):
        # Test that -I adds include directories properly.
        make_files(self.dincludes)
        self.cog.callable_main(["argv0", "-r", "-I", "include", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")

    def test_two_include_paths(self):
        # Test that two -I's add include directories properly.
        make_files(self.dincludes)
        self.cog.callable_main(
            ["argv0", "-r", "-I", "include", "-I", "inc2", "test.cog"]
        )
        self.assertFilesSame("test.cog", "test.out")

    def test_two_include_paths2(self):
        # Test that two -I's add include directories properly.
        make_files(self.dincludes)
        self.cog.callable_main(
            ["argv0", "-r", "-I", "inc2", "-I", "include", "test.cog"]
        )
        self.assertFilesSame("test.cog", "test2.out")

    def test_useless_include_path(self):
        # Test that the search will continue past the first directory.
        make_files(self.dincludes)
        self.cog.callable_main(
            ["argv0", "-r", "-I", "inc3", "-I", "include", "test.cog"]
        )
        self.assertFilesSame("test.cog", "test.out")

    def test_sys_path_is_unchanged(self):
        d = {
            "bad.cog": """\
                //[[[cog cog.error("Oh no!") ]]]
                //[[[end]]]
                """,
            "good.cog": """\
                //[[[cog cog.outl("Oh yes!") ]]]
                //[[[end]]]
                """,
        }

        make_files(d)
        # Is it unchanged just by creating a cog engine?
        oldsyspath = sys.path[:]
        self.new_cog()
        self.assertEqual(oldsyspath, sys.path)
        # Is it unchanged for a successful run?
        self.new_cog()
        self.cog.callable_main(["argv0", "-r", "good.cog"])
        self.assertEqual(oldsyspath, sys.path)
        # Is it unchanged for a successful run with includes?
        self.new_cog()
        self.cog.callable_main(["argv0", "-r", "-I", "xyzzy", "good.cog"])
        self.assertEqual(oldsyspath, sys.path)
        # Is it unchanged for a successful run with two includes?
        self.new_cog()
        self.cog.callable_main(["argv0", "-r", "-I", "xyzzy", "-I", "quux", "good.cog"])
        self.assertEqual(oldsyspath, sys.path)
        # Is it unchanged for a failed run?
        self.new_cog()
        with self.assertRaisesRegex(CogError, r"^Oh no!$"):
            self.cog.callable_main(["argv0", "-r", "bad.cog"])
        self.assertEqual(oldsyspath, sys.path)
        # Is it unchanged for a failed run with includes?
        self.new_cog()
        with self.assertRaisesRegex(CogError, r"^Oh no!$"):
            self.cog.callable_main(["argv0", "-r", "-I", "xyzzy", "bad.cog"])
        self.assertEqual(oldsyspath, sys.path)
        # Is it unchanged for a failed run with two includes?
        self.new_cog()
        with self.assertRaisesRegex(CogError, r"^Oh no!$"):
            self.cog.callable_main(
                ["argv0", "-r", "-I", "xyzzy", "-I", "quux", "bad.cog"]
            )
        self.assertEqual(oldsyspath, sys.path)

    def test_sub_directories(self):
        # Test that relative paths on the command line work, with includes.

        d = {
            "code": {
                "test.cog": """\
                    //[[[cog
                        import mysubmodule
                    //]]]
                    //[[[end]]]
                    """,
                "test.out": """\
                    //[[[cog
                        import mysubmodule
                    //]]]
                    Hello from mysubmodule
                    //[[[end]]]
                    """,
                "mysubmodule.py": """\
                    import cog
                    cog.outl("Hello from mysubmodule")
                    """,
            }
        }

        make_files(d)
        # We should be able to invoke cog without the -I switch, and it will
        # auto-include the current directory
        self.cog.callable_main(["argv0", "-r", "code/test.cog"])
        self.assertFilesSame("code/test.cog", "code/test.out")


class CogTestsInFiles(TestCaseWithTempDir):
    def test_warn_if_no_cog_code(self):
        # Test that the -e switch warns if there is no Cog code.
        d = {
            "with.cog": """\
                //[[[cog
                cog.outl("hello world")
                //]]]
                hello world
                //[[[end]]]
                """,
            "without.cog": """\
                There's no cog
                code in this file.
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-e", "with.cog"])
        output = self.output.getvalue()
        self.assertNotIn("Warning", output)
        self.new_cog()
        self.cog.callable_main(["argv0", "-e", "without.cog"])
        output = self.output.getvalue()
        self.assertIn("Warning: no cog code found in without.cog", output)
        self.new_cog()
        self.cog.callable_main(["argv0", "without.cog"])
        output = self.output.getvalue()
        self.assertNotIn("Warning", output)

    def test_file_name_props(self):
        d = {
            "cog1.txt": """\
                //[[[cog
                cog.outl("This is %s in, %s out" % (cog.inFile, cog.outFile))
                //]]]
                this is cog1.txt in, cog1.txt out
                [[[end]]]
                """,
            "cog1.out": """\
                //[[[cog
                cog.outl("This is %s in, %s out" % (cog.inFile, cog.outFile))
                //]]]
                This is cog1.txt in, cog1.txt out
                [[[end]]]
                """,
            "cog1out.out": """\
                //[[[cog
                cog.outl("This is %s in, %s out" % (cog.inFile, cog.outFile))
                //]]]
                This is cog1.txt in, cog1out.txt out
                [[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "cog1.txt"])
        self.assertFilesSame("cog1.txt", "cog1.out")
        self.new_cog()
        self.cog.callable_main(["argv0", "-o", "cog1out.txt", "cog1.txt"])
        self.assertFilesSame("cog1out.txt", "cog1out.out")

    def test_globals_dont_cross_files(self):
        # Make sure that global values don't get shared between files.
        d = {
            "one.cog": """\
                //[[[cog s = "This was set in one.cog" ]]]
                //[[[end]]]
                //[[[cog cog.outl(s) ]]]
                //[[[end]]]
                """,
            "one.out": """\
                //[[[cog s = "This was set in one.cog" ]]]
                //[[[end]]]
                //[[[cog cog.outl(s) ]]]
                This was set in one.cog
                //[[[end]]]
                """,
            "two.cog": """\
                //[[[cog
                try:
                    cog.outl(s)
                except NameError:
                    cog.outl("s isn't set!")
                //]]]
                //[[[end]]]
                """,
            "two.out": """\
                //[[[cog
                try:
                    cog.outl(s)
                except NameError:
                    cog.outl("s isn't set!")
                //]]]
                s isn't set!
                //[[[end]]]
                """,
            "cogfiles.txt": """\
                # Please run cog
                one.cog

                two.cog
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "@cogfiles.txt"])
        self.assertFilesSame("one.cog", "one.out")
        self.assertFilesSame("two.cog", "two.out")
        output = self.output.getvalue()
        self.assertIn("(changed)", output)

    def test_remove_generated_output(self):
        d = {
            "cog1.txt": """\
                //[[[cog
                cog.outl("This line was generated.")
                //]]]
                This line was generated.
                //[[[end]]]
                This line was not.
                """,
            "cog1.out": """\
                //[[[cog
                cog.outl("This line was generated.")
                //]]]
                //[[[end]]]
                This line was not.
                """,
            "cog1.out2": """\
                //[[[cog
                cog.outl("This line was generated.")
                //]]]
                This line was generated.
                //[[[end]]]
                This line was not.
                """,
        }

        make_files(d)
        # Remove generated output.
        self.cog.callable_main(["argv0", "-r", "-x", "cog1.txt"])
        self.assertFilesSame("cog1.txt", "cog1.out")
        self.new_cog()
        # Regenerate the generated output.
        self.cog.callable_main(["argv0", "-r", "cog1.txt"])
        self.assertFilesSame("cog1.txt", "cog1.out2")
        self.new_cog()
        # Remove the generated output again.
        self.cog.callable_main(["argv0", "-r", "-x", "cog1.txt"])
        self.assertFilesSame("cog1.txt", "cog1.out")

    def test_msg_call(self):
        infile = """\
            #[[[cog
                cog.msg("Hello there!")
            #]]]
            #[[[end]]]
            """
        infile = reindent_block(infile)
        self.assertEqual(self.cog.process_string(infile), infile)
        output = self.output.getvalue()
        self.assertEqual(output, "Message: Hello there!\n")

    def test_error_message_has_no_traceback(self):
        # Test that a Cog error is printed to stderr with no traceback.

        d = {
            "cog1.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                Xhis line was newly
                generated by cog
                blah blah.
                //[[[end]]] (sum: qFQJguWta5)
                """,
        }

        make_files(d)
        stderr = io.StringIO()
        self.cog.set_output(stderr=stderr)
        self.cog.main(["argv0", "-c", "-r", "cog1.txt"])
        self.assertEqual(self.output.getvalue(), "Cogging cog1.txt\n")
        self.assertEqual(
            stderr.getvalue(),
            "cog1.txt(9): Output has been edited! Delete old checksum to unprotect.\n",
        )

    def test_dash_d(self):
        d = {
            "test.cog": """\
                --[[[cog cog.outl("Defined fooey as " + fooey) ]]]
                --[[[end]]]
                """,
            "test.kablooey": """\
                --[[[cog cog.outl("Defined fooey as " + fooey) ]]]
                Defined fooey as kablooey
                --[[[end]]]
                """,
            "test.einstein": """\
                --[[[cog cog.outl("Defined fooey as " + fooey) ]]]
                Defined fooey as e=mc2
                --[[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-D", "fooey=kablooey", "test.cog"])
        self.assertFilesSame("test.cog", "test.kablooey")
        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-Dfooey=kablooey", "test.cog"])
        self.assertFilesSame("test.cog", "test.kablooey")
        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-Dfooey=e=mc2", "test.cog"])
        self.assertFilesSame("test.cog", "test.einstein")
        make_files(d)
        self.cog.callable_main(
            ["argv0", "-r", "-Dbar=quux", "-Dfooey=kablooey", "test.cog"]
        )
        self.assertFilesSame("test.cog", "test.kablooey")
        make_files(d)
        self.cog.callable_main(
            ["argv0", "-r", "-Dfooey=kablooey", "-Dbar=quux", "test.cog"]
        )
        self.assertFilesSame("test.cog", "test.kablooey")
        make_files(d)
        self.cog.callable_main(
            ["argv0", "-r", "-Dfooey=gooey", "-Dfooey=kablooey", "test.cog"]
        )
        self.assertFilesSame("test.cog", "test.kablooey")

    def test_output_to_stdout(self):
        d = {
            "test.cog": """\
                --[[[cog cog.outl('Hey there!') ]]]
                --[[[end]]]
                """
        }

        make_files(d)
        stderr = io.StringIO()
        self.cog.set_output(stderr=stderr)
        self.cog.callable_main(["argv0", "test.cog"])
        output = self.output.getvalue()
        outerr = stderr.getvalue()
        self.assertEqual(
            output, "--[[[cog cog.outl('Hey there!') ]]]\nHey there!\n--[[[end]]]\n"
        )
        self.assertEqual(outerr, "")

    def test_read_from_stdin(self):
        stdin = io.StringIO("--[[[cog cog.outl('Wow') ]]]\n--[[[end]]]\n")

        def restore_stdin(old_stdin):
            sys.stdin = old_stdin

        self.addCleanup(restore_stdin, sys.stdin)
        sys.stdin = stdin

        stderr = io.StringIO()
        self.cog.set_output(stderr=stderr)
        self.cog.callable_main(["argv0", "-"])
        output = self.output.getvalue()
        outerr = stderr.getvalue()
        self.assertEqual(output, "--[[[cog cog.outl('Wow') ]]]\nWow\n--[[[end]]]\n")
        self.assertEqual(outerr, "")

    def test_suffix_output_lines(self):
        d = {
            "test.cog": """\
                Hey there.
                ;[[[cog cog.outl('a\\nb\\n   \\nc') ]]]
                ;[[[end]]]
                Good bye.
                """,
            "test.out": """\
                Hey there.
                ;[[[cog cog.outl('a\\nb\\n   \\nc') ]]]
                a (foo)
                b (foo)
                   """  # These three trailing spaces are important.
            # The suffix is not applied to completely blank lines.
            """
                c (foo)
                ;[[[end]]]
                Good bye.
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-s", " (foo)", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")

    def test_empty_suffix(self):
        d = {
            "test.cog": """\
                ;[[[cog cog.outl('a\\nb\\nc') ]]]
                ;[[[end]]]
                """,
            "test.out": """\
                ;[[[cog cog.outl('a\\nb\\nc') ]]]
                a
                b
                c
                ;[[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-s", "", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")

    def test_hellish_suffix(self):
        d = {
            "test.cog": """\
                ;[[[cog cog.outl('a\\n\\nb') ]]]
                """,
            "test.out": """\
                ;[[[cog cog.outl('a\\n\\nb') ]]]
                a /\\n*+([)]><

                b /\\n*+([)]><
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-z", "-r", "-s", r" /\n*+([)]><", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")

    def test_prologue(self):
        d = {
            "test.cog": """\
                Some text.
                //[[[cog cog.outl(str(math.sqrt(2))[:12])]]]
                //[[[end]]]
                epilogue.
                """,
            "test.out": """\
                Some text.
                //[[[cog cog.outl(str(math.sqrt(2))[:12])]]]
                1.4142135623
                //[[[end]]]
                epilogue.
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-p", "import math", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")

    def test_threads(self):
        # Test that the implicitly imported cog module is actually different for
        # different threads.
        numthreads = 20

        d = {}
        for i in range(numthreads):
            d[f"f{i}.cog"] = (
                "x\n" * i
                + "[[[cog\n"
                + f"assert cog.firstLineNum == int(FIRST) == {i + 1}\n"
                + "]]]\n"
                + "[[[end]]]\n"
            )
        make_files(d)

        results = []

        def thread_main(num):
            try:
                ret = Cog().main(
                    ["cog.py", "-r", "-D", f"FIRST={num + 1}", f"f{num}.cog"]
                )
                assert ret == 0
            except Exception as exc:  # pragma: no cover (only happens on test failure)
                results.append(exc)
            else:
                results.append(None)

        ts = [
            threading.Thread(target=thread_main, args=(i,)) for i in range(numthreads)
        ]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        assert results == [None] * numthreads


class CheckTests(TestCaseWithTempDir):
    def run_check(self, args, status=0):
        actual_status = self.cog.main(["argv0", "--check"] + args)
        print(self.output.getvalue())
        self.assertEqual(status, actual_status)

    def assert_made_files_unchanged(self, d):
        for name, content in d.items():
            content = reindent_block(content)
            if os.name == "nt":
                content = content.replace("\n", "\r\n")
            self.assertFileContent(name, content)

    def test_check_no_cog(self):
        d = {
            "hello.txt": """\
                Hello.
                """,
        }
        make_files(d)
        self.run_check(["hello.txt"], status=0)
        self.assertEqual(self.output.getvalue(), "Checking hello.txt\n")
        self.assert_made_files_unchanged(d)

    def test_check_good(self):
        d = {
            "unchanged.cog": """\
                //[[[cog
                cog.outl("hello world")
                //]]]
                hello world
                //[[[end]]]
                """,
        }
        make_files(d)
        self.run_check(["unchanged.cog"], status=0)
        self.assertEqual(self.output.getvalue(), "Checking unchanged.cog\n")
        self.assert_made_files_unchanged(d)

    def test_check_bad(self):
        d = {
            "changed.cog": """\
                //[[[cog
                cog.outl("goodbye world")
                //]]]
                hello world
                //[[[end]]]
                """,
        }
        make_files(d)
        self.run_check(["changed.cog"], status=5)
        self.assertEqual(
            self.output.getvalue(), "Checking changed.cog  (changed)\nCheck failed\n"
        )
        self.assert_made_files_unchanged(d)

    def test_check_bad_with_diff(self):
        d = {
            "skittering.cog": """\
                //[[[cog
                for i in range(5): cog.outl(f"number {i}")
                cog.outl("goodbye world")
                //]]]
                number 0
                number 1
                number 2
                number 3
                number 4
                hello world
                //[[[end]]]
                """,
        }
        make_files(d)
        self.run_check(["--diff", "skittering.cog"], status=5)
        output = """\
            Checking skittering.cog  (changed)
            --- current skittering.cog
            +++ changed skittering.cog
            @@ -7,5 +7,5 @@
             number 2
             number 3
             number 4
            -hello world
            +goodbye world
             //[[[end]]]
            Check failed
            """
        self.assertEqual(self.output.getvalue(), reindent_block(output))
        self.assert_made_files_unchanged(d)

    def test_check_mixed(self):
        d = {
            "unchanged.cog": """\
                //[[[cog
                cog.outl("hello world")
                //]]]
                hello world
                //[[[end]]]
                """,
            "changed.cog": """\
                //[[[cog
                cog.outl("goodbye world")
                //]]]
                hello world
                //[[[end]]]
                """,
        }
        make_files(d)
        for verbosity, output in [
            ("0", "Check failed\n"),
            ("1", "Checking changed.cog  (changed)\nCheck failed\n"),
            (
                "2",
                "Checking unchanged.cog\nChecking changed.cog  (changed)\nCheck failed\n",
            ),
        ]:
            self.new_cog()
            self.run_check(
                ["--verbosity=%s" % verbosity, "unchanged.cog", "changed.cog"], status=5
            )
            self.assertEqual(self.output.getvalue(), output)
            self.assert_made_files_unchanged(d)

    def test_check_with_good_checksum(self):
        d = {
            "good.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah.
                //[[[end]]] (checksum: a8540982e5ad6b95c9e9a184b26f4346)
                """,
        }
        make_files(d)
        # Have to use -c with --check if there are checksums in the file.
        self.run_check(["-c", "good.txt"], status=0)
        self.assertEqual(self.output.getvalue(), "Checking good.txt\n")
        self.assert_made_files_unchanged(d)

    def test_check_with_bad_checksum(self):
        d = {
            "bad.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah.
                //[[[end]]] (checksum: a9999999e5ad6b95c9e9a184b26f4346)
                """,
        }
        make_files(d)
        # Have to use -c with --check if there are checksums in the file.
        self.run_check(["-c", "bad.txt"], status=1)
        self.assertEqual(
            self.output.getvalue(),
            "Checking bad.txt\nbad.txt(9): Output has been edited! Delete old checksum to unprotect.\n",
        )
        self.assert_made_files_unchanged(d)

    def test_check_with_good_sum(self):
        d = {
            "good.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah.
                //[[[end]]] (sum: qFQJguWta5)
                """,
        }
        make_files(d)
        # Have to use -c with --check if there are checksums in the file.
        self.run_check(["-c", "good.txt"], status=0)
        self.assertEqual(self.output.getvalue(), "Checking good.txt\n")
        self.assert_made_files_unchanged(d)

    def test_check_with_bad_sum(self):
        d = {
            "bad.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah.
                //[[[end]]] (sum: qZmZmeWta5)
                """,
        }
        make_files(d)
        # Have to use -c with --check if there are checksums in the file.
        self.run_check(["-c", "bad.txt"], status=1)
        self.assertEqual(
            self.output.getvalue(),
            "Checking bad.txt\nbad.txt(9): Output has been edited! Delete old checksum to unprotect.\n",
        )
        self.assert_made_files_unchanged(d)


class WritabilityTests(TestCaseWithTempDir):
    d = {
        "test.cog": """\
            //[[[cog
            for fn in ['DoSomething', 'DoAnotherThing', 'DoLastThing']:
                cog.outl("void %s();" % fn)
            //]]]
            //[[[end]]]
            """,
        "test.out": """\
            //[[[cog
            for fn in ['DoSomething', 'DoAnotherThing', 'DoLastThing']:
                cog.outl("void %s();" % fn)
            //]]]
            void DoSomething();
            void DoAnotherThing();
            void DoLastThing();
            //[[[end]]]
            """,
    }

    if os.name == "nt":
        # for Windows
        cmd_w_args = "attrib -R %s"
        cmd_w_asterisk = "attrib -R *"
    else:
        # for unix-like
        cmd_w_args = "chmod +w %s"
        cmd_w_asterisk = "chmod +w *"

    def setUp(self):
        super().setUp()
        make_files(self.d)
        self.testcog = os.path.join(self.tempdir, "test.cog")
        os.chmod(self.testcog, stat.S_IREAD)  # Make the file readonly.
        assert not os.access(self.testcog, os.W_OK)

    def tearDown(self):
        os.chmod(self.testcog, stat.S_IWRITE)  # Make the file writable again.
        super().tearDown()

    def test_readonly_no_command(self):
        with self.assertRaisesRegex(CogError, "^Can't overwrite test.cog$"):
            self.cog.callable_main(["argv0", "-r", "test.cog"])
        assert not os.access(self.testcog, os.W_OK)

    def test_readonly_with_command(self):
        self.cog.callable_main(["argv0", "-r", "-w", self.cmd_w_args, "test.cog"])
        self.assertFilesSame("test.cog", "test.out")
        assert os.access(self.testcog, os.W_OK)

    def test_readonly_with_command_with_no_slot(self):
        self.cog.callable_main(["argv0", "-r", "-w", self.cmd_w_asterisk, "test.cog"])
        self.assertFilesSame("test.cog", "test.out")
        assert os.access(self.testcog, os.W_OK)

    def test_readonly_with_ineffectual_command(self):
        with self.assertRaisesRegex(CogError, "^Couldn't make test.cog writable$"):
            self.cog.callable_main(["argv0", "-r", "-w", "echo %s", "test.cog"])
        assert not os.access(self.testcog, os.W_OK)


class ChecksumTests(TestCaseWithTempDir):
    def test_create_checksum_output(self):
        d = {
            "cog1.txt": """\
                //[[[cog
                cog.outl("This line was generated.")
                //]]]
                This line was generated.
                //[[[end]]] what
                This line was not.
                """,
            "cog1.out": """\
                //[[[cog
                cog.outl("This line was generated.")
                //]]]
                This line was generated.
                //[[[end]]] (sum: itsT+1m5lq) what
                This line was not.
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-c", "cog1.txt"])
        self.assertFilesSame("cog1.txt", "cog1.out")

    def test_check_checksum_output(self):
        d = {
            "cog1.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was generated.
                //[[[end]]] (sum: itsT+1m5lq) end
                """,
            "cog1.out": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah.
                //[[[end]]] (sum: qFQJguWta5) end
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-c", "cog1.txt"])
        self.assertFilesSame("cog1.txt", "cog1.out")

    def test_check_old_checksum_format(self):
        # Test that old checksum format can still be read
        d = {
            "cog1.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was generated.
                //[[[end]]] (checksum: 8adb13fb59b996a1c7f0065ea9f3d893) end
                """,
            "cog1.out": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah.
                //[[[end]]] (sum: qFQJguWta5) end
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "-c", "cog1.txt"])
        self.assertFilesSame("cog1.txt", "cog1.out")

    def test_remove_checksum_output(self):
        d = {
            "cog1.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was generated.
                //[[[end]]] (sum: itsT+1m5lq) fooey
                """,
            "cog1.out": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah.
                //[[[end]]] fooey
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "cog1.txt"])
        self.assertFilesSame("cog1.txt", "cog1.out")

    def test_tampered_checksum_output(self):
        d = {
            "cog1.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                Xhis line was newly
                generated by cog
                blah blah.
                //[[[end]]] (sum: qFQJguWta5)
                """,
            "cog2.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah!
                //[[[end]]] (sum: qFQJguWta5)
                """,
            "cog3.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]

                This line was newly
                generated by cog
                blah blah.
                //[[[end]]] (sum: qFQJguWta5)
                """,
            "cog4.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah..
                //[[[end]]] (sum: qFQJguWta5)
                """,
            "cog5.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                This line was newly
                generated by cog
                blah blah.
                extra
                //[[[end]]] (sum: qFQJguWta5)
                """,
            "cog6.txt": """\
                //[[[cog
                cog.outl("This line was newly")
                cog.outl("generated by cog")
                cog.outl("blah blah.")
                //]]]
                //[[[end]]] (sum: qFQJguWta5)
                """,
        }

        make_files(d)
        with self.assertRaisesRegex(
            CogError,
            r"^cog1.txt\(9\): Output has been edited! Delete old checksum to unprotect.$",
        ):
            self.cog.callable_main(["argv0", "-c", "cog1.txt"])
        with self.assertRaisesRegex(
            CogError,
            r"^cog2.txt\(9\): Output has been edited! Delete old checksum to unprotect.$",
        ):
            self.cog.callable_main(["argv0", "-c", "cog2.txt"])
        with self.assertRaisesRegex(
            CogError,
            r"^cog3.txt\(10\): Output has been edited! Delete old checksum to unprotect.$",
        ):
            self.cog.callable_main(["argv0", "-c", "cog3.txt"])
        with self.assertRaisesRegex(
            CogError,
            r"^cog4.txt\(9\): Output has been edited! Delete old checksum to unprotect.$",
        ):
            self.cog.callable_main(["argv0", "-c", "cog4.txt"])
        with self.assertRaisesRegex(
            CogError,
            r"^cog5.txt\(10\): Output has been edited! Delete old checksum to unprotect.$",
        ):
            self.cog.callable_main(["argv0", "-c", "cog5.txt"])
        with self.assertRaisesRegex(
            CogError,
            r"^cog6.txt\(6\): Output has been edited! Delete old checksum to unprotect.$",
        ):
            self.cog.callable_main(["argv0", "-c", "cog6.txt"])

    def test_argv_isnt_modified(self):
        argv = ["argv0", "-v"]
        orig_argv = argv[:]
        self.cog.callable_main(argv)
        self.assertEqual(argv, orig_argv)


class CustomMarkerTests(TestCaseWithTempDir):
    def test_customer_markers(self):
        d = {
            "test.cog": """\
                //{{
                cog.outl("void %s();" % "MyFunction")
                //}}
                //{{end}}
                """,
            "test.out": """\
                //{{
                cog.outl("void %s();" % "MyFunction")
                //}}
                void MyFunction();
                //{{end}}
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-r", "--markers={{ }} {{end}}", "test.cog"])
        self.assertFilesSame("test.cog", "test.out")

    def test_truly_wacky_markers(self):
        # Make sure the markers are properly re-escaped.
        d = {
            "test.cog": """\
                //**(
                cog.outl("void %s();" % "MyFunction")
                //**)
                //**(end)**
                """,
            "test.out": """\
                //**(
                cog.outl("void %s();" % "MyFunction")
                //**)
                void MyFunction();
                //**(end)**
                """,
        }

        make_files(d)
        self.cog.callable_main(
            ["argv0", "-r", "--markers=**( **) **(end)**", "test.cog"]
        )
        self.assertFilesSame("test.cog", "test.out")

    def test_change_just_one_marker(self):
        d = {
            "test.cog": """\
                //**(
                cog.outl("void %s();" % "MyFunction")
                //]]]
                //[[[end]]]
                """,
            "test.out": """\
                //**(
                cog.outl("void %s();" % "MyFunction")
                //]]]
                void MyFunction();
                //[[[end]]]
                """,
        }

        make_files(d)
        self.cog.callable_main(
            ["argv0", "-r", "--markers=**( ]]] [[[end]]]", "test.cog"]
        )
        self.assertFilesSame("test.cog", "test.out")


class BlakeTests(TestCaseWithTempDir):
    # Blake Winton's contributions.
    def test_delete_code(self):
        # -o sets the output file.
        d = {
            "test.cog": """\
                // This is my C++ file.
                //[[[cog
                fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                Some Sample Code Here
                //[[[end]]]Data Data
                And Some More
                """,
            "test.out": """\
                // This is my C++ file.
                void DoSomething();
                void DoAnotherThing();
                void DoLastThing();
                And Some More
                """,
        }

        make_files(d)
        self.cog.callable_main(["argv0", "-d", "-o", "test.cogged", "test.cog"])
        self.assertFilesSame("test.cogged", "test.out")

    def test_delete_code_with_dash_r_fails(self):
        d = {
            "test.cog": """\
                // This is my C++ file.
                """
        }

        make_files(d)
        with self.assertRaisesRegex(
            CogUsageError,
            r"^Can't use -d with -r \(or you would delete all your source!\)$",
        ):
            self.cog.callable_main(["argv0", "-r", "-d", "test.cog"])

    def test_setting_globals(self):
        # Blake Winton contributed a way to set the globals that will be used in
        # processFile().
        d = {
            "test.cog": """\
                // This is my C++ file.
                //[[[cog
                for fn in fnames:
                    cog.outl("void %s();" % fn)
                //]]]
                Some Sample Code Here
                //[[[end]]]""",
            "test.out": """\
                // This is my C++ file.
                void DoBlake();
                void DoWinton();
                void DoContribution();
                """,
        }

        make_files(d)
        globals = {}
        globals["fnames"] = ["DoBlake", "DoWinton", "DoContribution"]
        self.cog.options.delete_code = True
        self.cog.process_file("test.cog", "test.cogged", globals=globals)
        self.assertFilesSame("test.cogged", "test.out")


class ErrorCallTests(TestCaseWithTempDir):
    def test_error_call_has_no_traceback(self):
        # Test that cog.error() doesn't show a traceback.
        d = {
            "error.cog": """\
                //[[[cog
                cog.error("Something Bad!")
                //]]]
                //[[[end]]]
                """,
        }

        make_files(d)
        self.cog.main(["argv0", "-r", "error.cog"])
        output = self.output.getvalue()
        self.assertEqual(output, "Cogging error.cog\nError: Something Bad!\n")

    def test_real_error_has_traceback(self):
        # Test that a genuine error does show a traceback.
        d = {
            "error.cog": """\
                //[[[cog
                raise RuntimeError("Hey!")
                //]]]
                //[[[end]]]
                """,
        }

        make_files(d)
        self.cog.main(["argv0", "-r", "error.cog"])
        output = self.output.getvalue()
        msg = "Actual output:\n" + output
        self.assertTrue(
            output.startswith("Cogging error.cog\nTraceback (most recent"), msg
        )
        self.assertIn("RuntimeError: Hey!", output)


class HashHandlerTests(TestCase):
    """Test cases for HashHandler functionality."""

    def setUp(self):
        self.handler = HashHandler("[[[end]]]")

    def test_validate_hash_with_base64_mismatch(self):
        # Test the base64 validation branch with a mismatch
        line = "//[[[end]]] (sum: wronghas12)"  # 10 chars to match regex
        expected_hash = "a8540982e5ad6b95c9e9a184b26f4346"

        with self.assertRaises(ValueError) as cm:
            self.handler.validate_hash(line, expected_hash)
        self.assertEqual(
            str(cm.exception),
            "Output has been edited! Delete old checksum to unprotect.",
        )

    def test_validate_hash_with_base64_match(self):
        # Test the base64 validation branch with a match
        line = "//[[[end]]] (sum: qFQJguWta5)"
        expected_hash = "a8540982e5ad6b95c9e9a184b26f4346"

        # Should not raise an exception
        result = self.handler.validate_hash(line, expected_hash)
        self.assertTrue(result)


# Things not yet tested:
# - A bad -w command (currently fails silently).
