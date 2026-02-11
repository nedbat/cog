"""Cog content generation tool."""

import difflib
import glob
import io
import linecache
import os
import re
import shlex
import sys
import traceback
import types

from .errors import (
    CogCheckFailed,
    CogError,
    CogGeneratedError,
    CogUsageError,
    CogUserException,
)
from .options import CogOptions
from .whiteutils import common_prefix, reindent_block, white_prefix
from .utils import NumberedFileReader, Redirectable, change_dir, md5
from .hashhandler import HashHandler

__version__ = "3.6.0"


class CogGenerator(Redirectable):
    """A generator pulled from a source file."""

    def __init__(self, options=None):
        super().__init__()
        self.markers = []
        self.lines = []
        self.options = options or CogOptions()

    def parse_marker(self, line):
        self.markers.append(line)

    def parse_line(self, line):
        self.lines.append(line.strip("\n"))

    def get_code(self):
        """Extract the executable Python code from the generator."""
        # If the markers and lines all have the same prefix
        # (end-of-line comment chars, for example),
        # then remove it from all the lines.
        for idx, marker in enumerate(self.markers):
            self.markers[idx] = marker.replace(self.options.begin_spec, "").replace(
                self.options.end_spec, ""
            )
        pref_in = common_prefix(self.markers + self.lines)
        if pref_in:
            self.markers = [line.replace(pref_in, "", 1) for line in self.markers]
            self.lines = [line.replace(pref_in, "", 1) for line in self.lines]

        return reindent_block(self.lines, "")

    def evaluate(self, cog, globals, fname):
        # figure out the right whitespace prefix for the output
        pref_out = white_prefix(self.markers)

        intext = self.get_code()
        if not intext:
            return ""

        prologue = "import " + cog.cogmodulename + " as cog\n"
        if self.options.prologue:
            prologue += self.options.prologue + "\n"
        code = compile(prologue + intext, str(fname), "exec")

        # Make sure the "cog" module has our state.
        cog.cogmodule.msg = self.msg
        cog.cogmodule.out = self.out
        cog.cogmodule.outl = self.outl
        cog.cogmodule.error = self.error

        real_stdout = sys.stdout
        if self.options.print_output:
            sys.stdout = captured_stdout = io.StringIO()

        self.outstring = ""
        try:
            eval(code, globals)
        except CogError:
            raise
        except:  # noqa: E722 (we're just wrapping in CogUserException and rethrowing)
            typ, err, tb = sys.exc_info()
            frames = (tuple(fr) for fr in traceback.extract_tb(tb.tb_next))
            frames = find_cog_source(frames, prologue)
            msg = "".join(traceback.format_list(frames))
            msg += f"{typ.__name__}: {err}"
            raise CogUserException(msg)
        finally:
            sys.stdout = real_stdout

        if self.options.print_output:
            self.outstring = captured_stdout.getvalue()

        # We need to make sure that the last line in the output
        # ends with a newline, or it will be joined to the
        # end-output line, ruining cog's idempotency.
        if self.outstring and self.outstring[-1] != "\n":
            self.outstring += "\n"

        return reindent_block(self.outstring, pref_out)

    def msg(self, s):
        self.prout("Message: " + s)

    def out(self, sOut="", dedent=False, trimblanklines=False):
        """The cog.out function."""
        if trimblanklines and ("\n" in sOut):
            lines = sOut.split("\n")
            if lines[0].strip() == "":
                del lines[0]
            if lines and lines[-1].strip() == "":
                del lines[-1]
            sOut = "\n".join(lines) + "\n"
        if dedent:
            sOut = reindent_block(sOut)
        self.outstring += sOut

    def outl(self, sOut="", **kw):
        """The cog.outl function."""
        self.out(sOut, **kw)
        self.out("\n")

    def error(self, msg="Error raised by cog generator."):
        """The cog.error function.

        Instead of raising standard python errors, cog generators can use
        this function.  It will display the error without a scary Python
        traceback.

        """
        raise CogGeneratedError(msg)


class Cog(Redirectable):
    """The Cog engine."""

    def __init__(self):
        super().__init__()
        self.options = CogOptions()
        self.cogmodulename = "cog"
        self.create_cog_module()
        self.check_failed = False
        self.hash_handler = None
        self._fix_end_output_patterns()

    def _fix_end_output_patterns(self):
        self.hash_handler = HashHandler(self.options.end_output)

    def show_warning(self, msg):
        self.prout(f"Warning: {msg}")

    def is_begin_spec_line(self, s):
        return self.options.begin_spec in s

    def is_end_spec_line(self, s):
        return self.options.end_spec in s and not self.is_end_output_line(s)

    def is_end_output_line(self, s):
        return self.options.end_output in s

    def create_cog_module(self):
        """Make a cog "module" object.

        Imported Python modules can use "import cog" to get our state.

        """
        self.cogmodule = types.SimpleNamespace()
        self.cogmodule.path = []

    def open_output_file(self, fname):
        """Open an output file, taking all the details into account."""
        opts = {}
        mode = "w"
        opts["encoding"] = self.options.encoding
        opts["newline"] = self.options.newline
        fdir = os.path.dirname(fname)
        if os.path.dirname(fdir) and not os.path.exists(fdir):
            os.makedirs(fdir)
        return open(fname, mode, **opts)

    def open_input_file(self, fname):
        """Open an input file."""
        if fname == "-":
            return sys.stdin
        else:
            return open(fname, encoding=self.options.encoding)

    def process_file(self, file_in, file_out, fname=None, globals=None):
        """Process an input file object to an output file object.

        `fileIn` and `fileOut` can be file objects, or file names.

        """
        file_name_in = fname or ""
        file_name_out = fname or ""
        file_in_to_close = file_out_to_close = None
        # Convert filenames to files.
        if isinstance(file_in, (bytes, str)):
            # Open the input file.
            file_name_in = file_in
            file_in = file_in_to_close = self.open_input_file(file_in)
        if isinstance(file_out, (bytes, str)):
            # Open the output file.
            file_name_out = file_out
            file_out = file_out_to_close = self.open_output_file(file_out)

        start_dir = os.getcwd()

        try:
            file_in = NumberedFileReader(file_in)

            saw_cog = False

            self.cogmodule.inFile = file_name_in
            self.cogmodule.outFile = file_name_out
            self.cogmodulename = "cog_" + md5(file_name_out.encode()).hexdigest()
            sys.modules[self.cogmodulename] = self.cogmodule
            # if "import cog" explicitly done in code by user, note threading will cause clashes.
            sys.modules["cog"] = self.cogmodule

            # The globals dict we'll use for this file.
            if globals is None:
                globals = {}

            # If there are any global defines, put them in the globals.
            globals.update(self.options.defines)

            # loop over generator chunks
            line = file_in.readline()
            while line:
                # Find the next spec begin
                while line and not self.is_begin_spec_line(line):
                    if self.is_end_output_line(line):
                        raise CogError(
                            f"Unexpected {self.options.end_output!r}",
                            file=file_name_in,
                            line=file_in.linenumber(),
                        )
                    file_out.write(line)
                    line = file_in.readline()
                if not line:
                    break
                if not self.options.delete_code:
                    file_out.write(line)

                # `line` is the begin spec
                gen = CogGenerator(options=self.options)
                gen.set_output(stdout=self.stdout)
                gen.parse_marker(line)
                first_line_num = file_in.linenumber()
                self.cogmodule.firstLineNum = first_line_num

                # If the spec begin is also a spec end, then process the single
                # line of code inside.
                if self.is_end_spec_line(line):
                    beg = line.find(self.options.begin_spec)
                    end = line.find(self.options.end_spec)
                    if beg > end:
                        raise CogError(
                            "Cog code markers inverted",
                            file=file_name_in,
                            line=first_line_num,
                        )
                    else:
                        code = line[beg + len(self.options.begin_spec) : end].strip()
                        gen.parse_line(code)
                else:
                    # Deal with an ordinary code block.
                    line = file_in.readline()

                    # Get all the lines in the spec
                    while line and not self.is_end_spec_line(line):
                        if self.is_begin_spec_line(line):
                            raise CogError(
                                f"Unexpected {self.options.begin_spec!r}",
                                file=file_name_in,
                                line=file_in.linenumber(),
                            )
                        if self.is_end_output_line(line):
                            raise CogError(
                                f"Unexpected {self.options.end_output!r}",
                                file=file_name_in,
                                line=file_in.linenumber(),
                            )
                        if not self.options.delete_code:
                            file_out.write(line)
                        gen.parse_line(line)
                        line = file_in.readline()
                    if not line:
                        raise CogError(
                            "Cog block begun but never ended.",
                            file=file_name_in,
                            line=first_line_num,
                        )

                    if not self.options.delete_code:
                        file_out.write(line)
                    gen.parse_marker(line)

                line = file_in.readline()

                # Eat all the lines in the output section.  While reading past
                # them, compute the md5 hash of the old output.
                previous = []
                while line and not self.is_end_output_line(line):
                    if self.is_begin_spec_line(line):
                        raise CogError(
                            f"Unexpected {self.options.begin_spec!r}",
                            file=file_name_in,
                            line=file_in.linenumber(),
                        )
                    if self.is_end_spec_line(line):
                        raise CogError(
                            f"Unexpected {self.options.end_spec!r}",
                            file=file_name_in,
                            line=file_in.linenumber(),
                        )
                    previous.append(line)
                    line = file_in.readline()
                cur_hash = self.hash_handler.compute_lines_hash(previous)

                if not line and not self.options.eof_can_be_end:
                    # We reached end of file before we found the end output line.
                    raise CogError(
                        f"Missing {self.options.end_output!r} before end of file.",
                        file=file_name_in,
                        line=file_in.linenumber(),
                    )

                # Make the previous output available to the current code
                self.cogmodule.previous = "".join(previous)

                # Write the output of the spec to be the new output if we're
                # supposed to generate code.
                if not self.options.no_generate:
                    fname = f"<cog {file_name_in}:{first_line_num}>"
                    gen = gen.evaluate(cog=self, globals=globals, fname=fname)
                    gen = self.suffix_lines(gen)
                    new_hash = self.hash_handler.compute_hash(gen)
                    file_out.write(gen)
                else:
                    new_hash = ""

                saw_cog = True

                # Write the ending output line
                if self.options.hash_output:
                    try:
                        self.hash_handler.validate_hash(line, cur_hash)
                    except ValueError as e:
                        raise CogError(
                            str(e),
                            file=file_name_in,
                            line=file_in.linenumber(),
                        )
                    line = self.hash_handler.format_end_line_with_hash(
                        line,
                        new_hash,
                        add_hash=True,
                        preserve_format=self.options.check,
                    )
                else:
                    line = self.hash_handler.format_end_line_with_hash(
                        line, new_hash, add_hash=False
                    )

                if not self.options.delete_code:
                    file_out.write(line)
                line = file_in.readline()

            if not saw_cog and self.options.warn_empty:
                self.show_warning(f"no cog code found in {file_name_in}")
        finally:
            if file_in_to_close:
                file_in_to_close.close()
            if file_out_to_close:
                file_out_to_close.close()
            os.chdir(start_dir)

    # A regex for non-empty lines, used by suffixLines.
    re_non_empty_lines = re.compile(r"^\s*\S+.*$", re.MULTILINE)

    def suffix_lines(self, text):
        """Add suffixes to the lines in text, if our options desire it.

        `text` is many lines, as a single string.

        """
        if self.options.suffix:
            # Find all non-blank lines, and add the suffix to the end.
            repl = r"\g<0>" + self.options.suffix.replace("\\", "\\\\")
            text = self.re_non_empty_lines.sub(repl, text)
        return text

    def process_string(self, input, fname=None):
        """Process `input` as the text to cog.

        Return the cogged output as a string.

        """
        file_old = io.StringIO(input)
        file_new = io.StringIO()
        self.process_file(file_old, file_new, fname=fname)
        return file_new.getvalue()

    def replace_file(self, old_path, new_text):
        """Replace file oldPath with the contents newText"""
        if not os.access(old_path, os.W_OK):
            # Need to ensure we can write.
            if self.options.make_writable_cmd:
                # Use an external command to make the file writable.
                cmd = self.options.make_writable_cmd.replace("%s", old_path)
                with os.popen(cmd) as cmdout:
                    self.stdout.write(cmdout.read())
                if not os.access(old_path, os.W_OK):
                    raise CogError(f"Couldn't make {old_path} writable")
            else:
                # Can't write!
                raise CogError(f"Can't overwrite {old_path}")
        f = self.open_output_file(old_path)
        f.write(new_text)
        f.close()

    def save_include_path(self):
        self.saved_include = self.options.include_path[:]
        self.saved_sys_path = sys.path[:]

    def restore_include_path(self):
        self.options.include_path = self.saved_include
        self.cogmodule.path = self.options.include_path
        sys.path = self.saved_sys_path

    def add_to_include_path(self, include_path):
        self.cogmodule.path.extend(include_path)
        sys.path.extend(include_path)

    def process_one_file(self, fname):
        """Process one filename through cog."""

        self.save_include_path()
        need_newline = False

        try:
            self.add_to_include_path(self.options.include_path)
            # Since we know where the input file came from,
            # push its directory onto the include path.
            self.add_to_include_path([os.path.dirname(fname)])

            # How we process the file depends on where the output is going.
            if self.options.output_name:
                self.process_file(fname, self.options.output_name, fname)
            elif self.options.replace or self.options.check:
                # We want to replace the cog file with the output,
                # but only if they differ.
                verb = "Cogging" if self.options.replace else "Checking"
                if self.options.verbosity >= 2:
                    self.prout(f"{verb} {fname}", end="")
                    need_newline = True

                try:
                    file_old_file = self.open_input_file(fname)
                    old_text = file_old_file.read()
                    file_old_file.close()
                    new_text = self.process_string(old_text, fname=fname)
                    if old_text != new_text:
                        if self.options.verbosity >= 1:
                            if self.options.verbosity < 2:
                                self.prout(f"{verb} {fname}", end="")
                            self.prout("  (changed)")
                            need_newline = False
                        if self.options.replace:
                            self.replace_file(fname, new_text)
                        else:
                            assert self.options.check
                            self.check_failed = True
                            if self.options.diff:
                                old_lines = old_text.splitlines()
                                new_lines = new_text.splitlines()
                                diff = difflib.unified_diff(
                                    old_lines,
                                    new_lines,
                                    fromfile=f"current {fname}",
                                    tofile=f"changed {fname}",
                                    lineterm="",
                                )
                                for diff_line in diff:
                                    self.prout(diff_line)
                finally:
                    # The try-finally block is so we can print a partial line
                    # with the name of the file, and print (changed) on the
                    # same line, but also make sure to break the line before
                    # any traceback.
                    if need_newline:
                        self.prout("")
            else:
                self.process_file(fname, self.stdout, fname)
        finally:
            self.restore_include_path()

    def process_wildcards(self, fname):
        files = glob.glob(fname)
        if files:
            for matching_file in files:
                self.process_one_file(matching_file)
        else:
            self.process_one_file(fname)

    def process_file_list(self, file_name_list):
        """Process the files in a file list."""
        flist = self.open_input_file(file_name_list)
        lines = flist.readlines()
        flist.close()
        for line in lines:
            # Use shlex to parse the line like a shell.
            lex = shlex.shlex(line, posix=True)
            lex.whitespace_split = True
            lex.commenters = "#"
            # No escapes, so that backslash can be part of the path
            lex.escape = ""
            args = list(lex)
            if args:
                self.process_arguments(args)

    def process_arguments(self, args):
        """Process one command-line."""
        saved_options = self.options
        self.options = self.options.clone()

        self.options.parse_args(args[1:])

        if args[0][0] == "@":
            if self.options.output_name:
                raise CogUsageError("Can't use -o with @file")
            self.process_file_list(args[0][1:])
        elif args[0][0] == "&":
            if self.options.output_name:
                raise CogUsageError("Can't use -o with &file")
            file_list = args[0][1:]
            with change_dir(os.path.dirname(file_list)):
                self.process_file_list(os.path.basename(file_list))
        else:
            self.process_wildcards(args[0])

        self.options = saved_options

    def callable_main(self, argv):
        """All of command-line cog, but in a callable form.

        This is used by main.  `argv` is the equivalent of sys.argv.

        """
        argv = argv[1:]

        # Provide help if asked for anywhere in the command line.
        if "-?" in argv or "-h" in argv or "--help" in argv:
            self.prerr(self.options.format_help(), end="")
            return

        self.options.parse_args(argv)
        self._fix_end_output_patterns()

        if self.options.show_version:
            self.prout(f"Cog version {__version__}")
            return

        if self.options.args:
            for a in self.options.args:
                self.process_arguments([a])
        else:
            raise CogUsageError("No files to process")

        if self.check_failed:
            msg = "Check failed"
            if self.options.check_fail_msg:
                msg = f"{msg}: {self.options.check_fail_msg}"
            raise CogCheckFailed(msg)

    def main(self, argv):
        """Handle the command-line execution for cog."""

        try:
            self.callable_main(argv)
            return 0
        except CogUsageError as err:
            self.prerr(err)
            self.prerr("(for help use --help)")
            return 2
        except CogGeneratedError as err:
            self.prerr(f"Error: {err}")
            return 3
        except CogUserException as err:
            self.prerr("Traceback (most recent call last):")
            self.prerr(err.args[0])
            return 4
        except CogCheckFailed as err:
            self.prerr(err)
            return 5
        except CogError as err:
            self.prerr(err)
            return 1


def find_cog_source(frame_summary, prologue):
    """Find cog source lines in a frame summary list, for printing tracebacks.

    Arguments:
        frame_summary: a list of 4-item tuples, as returned by traceback.extract_tb.
        prologue: the text of the code prologue.

    Returns
        A list of 4-item tuples, updated to correct the cog entries.

    """
    prolines = prologue.splitlines()
    for filename, lineno, funcname, source in frame_summary:
        if not source:
            m = re.search(r"^<cog ([^:]+):(\d+)>$", filename)
            if m:
                if lineno <= len(prolines):
                    filename = "<prologue>"
                    source = prolines[lineno - 1]
                    lineno -= (
                        1  # Because "import cog" is the first line in the prologue
                    )
                else:
                    filename, coglineno = m.groups()
                    coglineno = int(coglineno)
                    lineno += coglineno - len(prolines)
                    source = linecache.getline(filename, lineno).strip()
        yield filename, lineno, funcname, source


def main():
    """Main function for entry_points to use."""
    return Cog().main(sys.argv)
