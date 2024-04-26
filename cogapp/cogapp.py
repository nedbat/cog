"""Cog content generation tool."""

import copy
import getopt
import glob
import io
import linecache
import os
import re
import shlex
import sys
import traceback
import types

from .whiteutils import commonPrefix, reindentBlock, whitePrefix
from .utils import NumberedFileReader, Redirectable, change_dir, md5

__version__ = "3.4.1"

usage = """\
cog - generate content with inlined Python code.

cog [OPTIONS] [INFILE | @FILELIST | &FILELIST] ...

INFILE is the name of an input file, '-' will read from stdin.
FILELIST is the name of a text file containing file names or
other @FILELISTs.

For @FILELIST, paths in the file list are relative to the working
directory where cog was called.  For &FILELIST, paths in the file
list are relative to the file list location.

OPTIONS:
    -c          Checksum the output to protect it against accidental change.
    -d          Delete the generator code from the output file.
    -D name=val Define a global string available to your generator code.
    -e          Warn if a file has no cog code in it.
    -I PATH     Add PATH to the list of directories for data files and modules.
    -n ENCODING Use ENCODING when reading and writing files.
    -o OUTNAME  Write the output to OUTNAME.
    -p PROLOGUE Prepend the generator source with PROLOGUE. Useful to insert an
                import line. Example: -p "import math"
    -P          Use print() instead of cog.outl() for code output.
    -r          Replace the input file with the output.
    -s STRING   Suffix all generated output lines with STRING.
    -U          Write the output with Unix newlines (only LF line-endings).
    -w CMD      Use CMD if the output file needs to be made writable.
                    A %s in the CMD will be filled with the filename.
    -x          Excise all the generated output without running the generators.
    -z          The end-output marker can be omitted, and is assumed at eof.
    -v          Print the version of cog and exit.
    --check     Check that the files would not change if run again.
    --markers='START END END-OUTPUT'
                The patterns surrounding cog inline instructions. Should
                include three values separated by spaces, the start, end,
                and end-output markers. Defaults to '[[[cog ]]] [[[end]]]'.
    --verbosity=VERBOSITY
                Control the amount of output. 2 (the default) lists all files,
                1 lists only changed files, 0 lists no files.
    -h          Print this help.
"""


class CogError(Exception):
    """Any exception raised by Cog."""

    def __init__(self, msg, file="", line=0):
        if file:
            super().__init__(f"{file}({line}): {msg}")
        else:
            super().__init__(msg)


class CogUsageError(CogError):
    """An error in usage of command-line arguments in cog."""

    pass


class CogInternalError(CogError):
    """An error in the coding of Cog. Should never happen."""

    pass


class CogGeneratedError(CogError):
    """An error raised by a user's cog generator."""

    pass


class CogUserException(CogError):
    """An exception caught when running a user's cog generator.

    The argument is the traceback message to print.

    """

    pass


class CogCheckFailed(CogError):
    """A --check failed."""

    pass


class CogGenerator(Redirectable):
    """A generator pulled from a source file."""

    def __init__(self, options=None):
        super().__init__()
        self.markers = []
        self.lines = []
        self.options = options or CogOptions()

    def parseMarker(self, line):
        self.markers.append(line)

    def parseLine(self, line):
        self.lines.append(line.strip("\n"))

    def getCode(self):
        """Extract the executable Python code from the generator."""
        # If the markers and lines all have the same prefix
        # (end-of-line comment chars, for example),
        # then remove it from all the lines.
        prefIn = commonPrefix(self.markers + self.lines)
        if prefIn:
            self.markers = [line.replace(prefIn, "", 1) for line in self.markers]
            self.lines = [line.replace(prefIn, "", 1) for line in self.lines]

        return reindentBlock(self.lines, "")

    def evaluate(self, cog, globals, fname):
        # figure out the right whitespace prefix for the output
        prefOut = whitePrefix(self.markers)

        intext = self.getCode()
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
        if self.options.printOutput:
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

        if self.options.printOutput:
            self.outstring = captured_stdout.getvalue()

        # We need to make sure that the last line in the output
        # ends with a newline, or it will be joined to the
        # end-output line, ruining cog's idempotency.
        if self.outstring and self.outstring[-1] != "\n":
            self.outstring += "\n"

        return reindentBlock(self.outstring, prefOut)

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
            sOut = reindentBlock(sOut)
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


class CogOptions:
    """Options for a run of cog."""

    def __init__(self):
        # Defaults for argument values.
        self.args = []
        self.includePath = []
        self.defines = {}
        self.showVersion = False
        self.makeWritableCmd = None
        self.replace = False
        self.noGenerate = False
        self.outputName = None
        self.warnEmpty = False
        self.hashOutput = False
        self.deleteCode = False
        self.eofCanBeEnd = False
        self.suffix = None
        self.newlines = False
        self.beginSpec = "[[[cog"
        self.endSpec = "]]]"
        self.endOutput = "[[[end]]]"
        self.encoding = "utf-8"
        self.verbosity = 2
        self.prologue = ""
        self.printOutput = False
        self.check = False

    def __eq__(self, other):
        """Comparison operator for tests to use."""
        return self.__dict__ == other.__dict__

    def clone(self):
        """Make a clone of these options, for further refinement."""
        return copy.deepcopy(self)

    def addToIncludePath(self, dirs):
        """Add directories to the include path."""
        dirs = dirs.split(os.pathsep)
        self.includePath.extend(dirs)

    def parseArgs(self, argv):
        # Parse the command line arguments.
        try:
            opts, self.args = getopt.getopt(
                argv,
                "cdD:eI:n:o:rs:p:PUvw:xz",
                [
                    "check",
                    "markers=",
                    "verbosity=",
                ],
            )
        except getopt.error as msg:
            raise CogUsageError(msg)

        # Handle the command line arguments.
        for o, a in opts:
            if o == "-c":
                self.hashOutput = True
            elif o == "-d":
                self.deleteCode = True
            elif o == "-D":
                if a.count("=") < 1:
                    raise CogUsageError("-D takes a name=value argument")
                name, value = a.split("=", 1)
                self.defines[name] = value
            elif o == "-e":
                self.warnEmpty = True
            elif o == "-I":
                self.addToIncludePath(os.path.abspath(a))
            elif o == "-n":
                self.encoding = a
            elif o == "-o":
                self.outputName = a
            elif o == "-r":
                self.replace = True
            elif o == "-s":
                self.suffix = a
            elif o == "-p":
                self.prologue = a
            elif o == "-P":
                self.printOutput = True
            elif o == "-U":
                self.newlines = True
            elif o == "-v":
                self.showVersion = True
            elif o == "-w":
                self.makeWritableCmd = a
            elif o == "-x":
                self.noGenerate = True
            elif o == "-z":
                self.eofCanBeEnd = True
            elif o == "--check":
                self.check = True
            elif o == "--markers":
                self._parse_markers(a)
            elif o == "--verbosity":
                self.verbosity = int(a)
            else:
                # Since getopt.getopt is given a list of possible flags,
                # this is an internal error.
                raise CogInternalError(f"Don't understand argument {o}")

    def _parse_markers(self, val):
        try:
            self.beginSpec, self.endSpec, self.endOutput = val.split(" ")
        except ValueError:
            raise CogUsageError(
                f"--markers requires 3 values separated by spaces, could not parse {val!r}"
            )

    def validate(self):
        """Does nothing if everything is OK, raises CogError's if it's not."""
        if self.replace and self.deleteCode:
            raise CogUsageError(
                "Can't use -d with -r (or you would delete all your source!)"
            )

        if self.replace and self.outputName:
            raise CogUsageError("Can't use -o with -r (they are opposites)")


class Cog(Redirectable):
    """The Cog engine."""

    def __init__(self):
        super().__init__()
        self.options = CogOptions()
        self._fixEndOutputPatterns()
        self.cogmodulename = "cog"
        self.createCogModule()
        self.checkFailed = False

    def _fixEndOutputPatterns(self):
        end_output = re.escape(self.options.endOutput)
        self.reEndOutput = re.compile(
            end_output + r"(?P<hashsect> *\(checksum: (?P<hash>[a-f0-9]+)\))"
        )
        self.endFormat = self.options.endOutput + " (checksum: %s)"

    def showWarning(self, msg):
        self.prout(f"Warning: {msg}")

    def isBeginSpecLine(self, s):
        return self.options.beginSpec in s

    def isEndSpecLine(self, s):
        return self.options.endSpec in s and not self.isEndOutputLine(s)

    def isEndOutputLine(self, s):
        return self.options.endOutput in s

    def createCogModule(self):
        """Make a cog "module" object.

        Imported Python modules can use "import cog" to get our state.

        """
        self.cogmodule = types.SimpleNamespace()
        self.cogmodule.path = []

    def openOutputFile(self, fname):
        """Open an output file, taking all the details into account."""
        opts = {}
        mode = "w"
        opts["encoding"] = self.options.encoding
        if self.options.newlines:
            opts["newline"] = "\n"
        fdir = os.path.dirname(fname)
        if os.path.dirname(fdir) and not os.path.exists(fdir):
            os.makedirs(fdir)
        return open(fname, mode, **opts)

    def openInputFile(self, fname):
        """Open an input file."""
        if fname == "-":
            return sys.stdin
        else:
            return open(fname, encoding=self.options.encoding)

    def processFile(self, fileIn, fileOut, fname=None, globals=None):
        """Process an input file object to an output file object.

        `fileIn` and `fileOut` can be file objects, or file names.

        """
        fileNameIn = fname or ""
        fileNameOut = fname or ""
        fileInToClose = fileOutToClose = None
        # Convert filenames to files.
        if isinstance(fileIn, (bytes, str)):
            # Open the input file.
            fileNameIn = fileIn
            fileIn = fileInToClose = self.openInputFile(fileIn)
        if isinstance(fileOut, (bytes, str)):
            # Open the output file.
            fileNameOut = fileOut
            fileOut = fileOutToClose = self.openOutputFile(fileOut)

        try:
            fileIn = NumberedFileReader(fileIn)

            sawCog = False

            self.cogmodule.inFile = fileNameIn
            self.cogmodule.outFile = fileNameOut
            self.cogmodulename = "cog_" + md5(fileNameOut.encode()).hexdigest()
            sys.modules[self.cogmodulename] = self.cogmodule
            # if "import cog" explicitly done in code by user, note threading will cause clashes.
            sys.modules["cog"] = self.cogmodule

            # The globals dict we'll use for this file.
            if globals is None:
                globals = {}

            # If there are any global defines, put them in the globals.
            globals.update(self.options.defines)

            # loop over generator chunks
            line = fileIn.readline()
            while line:
                # Find the next spec begin
                while line and not self.isBeginSpecLine(line):
                    if self.isEndSpecLine(line):
                        raise CogError(
                            f"Unexpected {self.options.endSpec!r}",
                            file=fileNameIn,
                            line=fileIn.linenumber(),
                        )
                    if self.isEndOutputLine(line):
                        raise CogError(
                            f"Unexpected {self.options.endOutput!r}",
                            file=fileNameIn,
                            line=fileIn.linenumber(),
                        )
                    fileOut.write(line)
                    line = fileIn.readline()
                if not line:
                    break
                if not self.options.deleteCode:
                    fileOut.write(line)

                # l is the begin spec
                gen = CogGenerator(options=self.options)
                gen.setOutput(stdout=self.stdout)
                gen.parseMarker(line)
                firstLineNum = fileIn.linenumber()
                self.cogmodule.firstLineNum = firstLineNum

                # If the spec begin is also a spec end, then process the single
                # line of code inside.
                if self.isEndSpecLine(line):
                    beg = line.find(self.options.beginSpec)
                    end = line.find(self.options.endSpec)
                    if beg > end:
                        raise CogError(
                            "Cog code markers inverted",
                            file=fileNameIn,
                            line=firstLineNum,
                        )
                    else:
                        code = line[beg + len(self.options.beginSpec) : end].strip()
                        gen.parseLine(code)
                else:
                    # Deal with an ordinary code block.
                    line = fileIn.readline()

                    # Get all the lines in the spec
                    while line and not self.isEndSpecLine(line):
                        if self.isBeginSpecLine(line):
                            raise CogError(
                                f"Unexpected {self.options.beginSpec!r}",
                                file=fileNameIn,
                                line=fileIn.linenumber(),
                            )
                        if self.isEndOutputLine(line):
                            raise CogError(
                                f"Unexpected {self.options.endOutput!r}",
                                file=fileNameIn,
                                line=fileIn.linenumber(),
                            )
                        if not self.options.deleteCode:
                            fileOut.write(line)
                        gen.parseLine(line)
                        line = fileIn.readline()
                    if not line:
                        raise CogError(
                            "Cog block begun but never ended.",
                            file=fileNameIn,
                            line=firstLineNum,
                        )

                    if not self.options.deleteCode:
                        fileOut.write(line)
                    gen.parseMarker(line)

                line = fileIn.readline()

                # Eat all the lines in the output section.  While reading past
                # them, compute the md5 hash of the old output.
                previous = []
                hasher = md5()
                while line and not self.isEndOutputLine(line):
                    if self.isBeginSpecLine(line):
                        raise CogError(
                            f"Unexpected {self.options.beginSpec!r}",
                            file=fileNameIn,
                            line=fileIn.linenumber(),
                        )
                    if self.isEndSpecLine(line):
                        raise CogError(
                            f"Unexpected {self.options.endSpec!r}",
                            file=fileNameIn,
                            line=fileIn.linenumber(),
                        )
                    previous.append(line)
                    hasher.update(line.encode("utf-8"))
                    line = fileIn.readline()
                curHash = hasher.hexdigest()

                if not line and not self.options.eofCanBeEnd:
                    # We reached end of file before we found the end output line.
                    raise CogError(
                        f"Missing {self.options.endOutput!r} before end of file.",
                        file=fileNameIn,
                        line=fileIn.linenumber(),
                    )

                # Make the previous output available to the current code
                self.cogmodule.previous = "".join(previous)

                # Write the output of the spec to be the new output if we're
                # supposed to generate code.
                hasher = md5()
                if not self.options.noGenerate:
                    fname = f"<cog {fileNameIn}:{firstLineNum}>"
                    gen = gen.evaluate(cog=self, globals=globals, fname=fname)
                    gen = self.suffixLines(gen)
                    hasher.update(gen.encode("utf-8"))
                    fileOut.write(gen)
                newHash = hasher.hexdigest()

                sawCog = True

                # Write the ending output line
                hashMatch = self.reEndOutput.search(line)
                if self.options.hashOutput:
                    if hashMatch:
                        oldHash = hashMatch["hash"]
                        if oldHash != curHash:
                            raise CogError(
                                "Output has been edited! Delete old checksum to unprotect.",
                                file=fileNameIn,
                                line=fileIn.linenumber(),
                            )
                        # Create a new end line with the correct hash.
                        endpieces = line.split(hashMatch.group(0), 1)
                    else:
                        # There was no old hash, but we want a new hash.
                        endpieces = line.split(self.options.endOutput, 1)
                    line = (self.endFormat % newHash).join(endpieces)
                else:
                    # We don't want hashes output, so if there was one, get rid of
                    # it.
                    if hashMatch:
                        line = line.replace(hashMatch["hashsect"], "", 1)

                if not self.options.deleteCode:
                    fileOut.write(line)
                line = fileIn.readline()

            if not sawCog and self.options.warnEmpty:
                self.showWarning(f"no cog code found in {fileNameIn}")
        finally:
            if fileInToClose:
                fileInToClose.close()
            if fileOutToClose:
                fileOutToClose.close()

    # A regex for non-empty lines, used by suffixLines.
    reNonEmptyLines = re.compile(r"^\s*\S+.*$", re.MULTILINE)

    def suffixLines(self, text):
        """Add suffixes to the lines in text, if our options desire it.

        `text` is many lines, as a single string.

        """
        if self.options.suffix:
            # Find all non-blank lines, and add the suffix to the end.
            repl = r"\g<0>" + self.options.suffix.replace("\\", "\\\\")
            text = self.reNonEmptyLines.sub(repl, text)
        return text

    def processString(self, input, fname=None):
        """Process `input` as the text to cog.

        Return the cogged output as a string.

        """
        fileOld = io.StringIO(input)
        fileNew = io.StringIO()
        self.processFile(fileOld, fileNew, fname=fname)
        return fileNew.getvalue()

    def replaceFile(self, oldPath, newText):
        """Replace file oldPath with the contents newText"""
        if not os.access(oldPath, os.W_OK):
            # Need to ensure we can write.
            if self.options.makeWritableCmd:
                # Use an external command to make the file writable.
                cmd = self.options.makeWritableCmd.replace("%s", oldPath)
                with os.popen(cmd) as cmdout:
                    self.stdout.write(cmdout.read())
                if not os.access(oldPath, os.W_OK):
                    raise CogError(f"Couldn't make {oldPath} writable")
            else:
                # Can't write!
                raise CogError(f"Can't overwrite {oldPath}")
        f = self.openOutputFile(oldPath)
        f.write(newText)
        f.close()

    def saveIncludePath(self):
        self.savedInclude = self.options.includePath[:]
        self.savedSysPath = sys.path[:]

    def restoreIncludePath(self):
        self.options.includePath = self.savedInclude
        self.cogmodule.path = self.options.includePath
        sys.path = self.savedSysPath

    def addToIncludePath(self, includePath):
        self.cogmodule.path.extend(includePath)
        sys.path.extend(includePath)

    def processOneFile(self, fname):
        """Process one filename through cog."""

        self.saveIncludePath()
        needNewline = False

        try:
            self.addToIncludePath(self.options.includePath)
            # Since we know where the input file came from,
            # push its directory onto the include path.
            self.addToIncludePath([os.path.dirname(fname)])

            # How we process the file depends on where the output is going.
            if self.options.outputName:
                self.processFile(fname, self.options.outputName, fname)
            elif self.options.replace or self.options.check:
                # We want to replace the cog file with the output,
                # but only if they differ.
                verb = "Cogging" if self.options.replace else "Checking"
                if self.options.verbosity >= 2:
                    self.prout(f"{verb} {fname}", end="")
                    needNewline = True

                try:
                    fileOldFile = self.openInputFile(fname)
                    oldText = fileOldFile.read()
                    fileOldFile.close()
                    newText = self.processString(oldText, fname=fname)
                    if oldText != newText:
                        if self.options.verbosity >= 1:
                            if self.options.verbosity < 2:
                                self.prout(f"{verb} {fname}", end="")
                            self.prout("  (changed)")
                            needNewline = False
                        if self.options.replace:
                            self.replaceFile(fname, newText)
                        else:
                            assert self.options.check
                            self.checkFailed = True
                finally:
                    # The try-finally block is so we can print a partial line
                    # with the name of the file, and print (changed) on the
                    # same line, but also make sure to break the line before
                    # any traceback.
                    if needNewline:
                        self.prout("")
            else:
                self.processFile(fname, self.stdout, fname)
        finally:
            self.restoreIncludePath()

    def processWildcards(self, fname):
        files = glob.glob(fname)
        if files:
            for matchingFile in files:
                self.processOneFile(matchingFile)
        else:
            self.processOneFile(fname)

    def processFileList(self, fileNameList):
        """Process the files in a file list."""
        flist = self.openInputFile(fileNameList)
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
                self.processArguments(args)

    def processArguments(self, args):
        """Process one command-line."""
        saved_options = self.options
        self.options = self.options.clone()

        self.options.parseArgs(args[1:])
        self.options.validate()

        if args[0][0] == "@":
            if self.options.outputName:
                raise CogUsageError("Can't use -o with @file")
            self.processFileList(args[0][1:])
        elif args[0][0] == "&":
            if self.options.outputName:
                raise CogUsageError("Can't use -o with &file")
            file_list = args[0][1:]
            with change_dir(os.path.dirname(file_list)):
                self.processFileList(os.path.basename(file_list))
        else:
            self.processWildcards(args[0])

        self.options = saved_options

    def callableMain(self, argv):
        """All of command-line cog, but in a callable form.

        This is used by main.  `argv` is the equivalent of sys.argv.

        """
        argv = argv[1:]

        # Provide help if asked for anywhere in the command line.
        if "-?" in argv or "-h" in argv:
            self.prerr(usage, end="")
            return

        self.options.parseArgs(argv)
        self.options.validate()
        self._fixEndOutputPatterns()

        if self.options.showVersion:
            self.prout(f"Cog version {__version__}")
            return

        if self.options.args:
            for a in self.options.args:
                self.processArguments([a])
        else:
            raise CogUsageError("No files to process")

        if self.checkFailed:
            raise CogCheckFailed("Check failed")

    def main(self, argv):
        """Handle the command-line execution for cog."""

        try:
            self.callableMain(argv)
            return 0
        except CogUsageError as err:
            self.prerr(err)
            self.prerr("(for help use -h)")
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
