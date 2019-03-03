# coding: utf8
""" Cog code generation tool.
    http://nedbatchelder.com/code/cog

    Copyright 2004-2019, Ned Batchelder.
"""

from __future__ import absolute_import, print_function

import copy
import getopt
import hashlib
import imp
import os
import re
import shlex
import sys
import traceback

from .backward import PY3, StringIO, string_types, to_bytes

__all__ = ['Cog', 'CogUsageError']

__version__ = '2.5.1'   # History at the end of the file.

usage = """\
cog - generate code with inlined Python code.

cog [OPTIONS] [INFILE | @FILELIST] ...

INFILE is the name of an input file, '-' will read from stdin.
FILELIST is the name of a text file containing file names or
    other @FILELISTs.

OPTIONS:
    -c          Checksum the output to protect it against accidental change.
    -d          Delete the generator code from the output file.
    -D name=val Define a global string available to your generator code.
    -e          Warn if a file has no cog code in it.
    -I PATH     Add PATH to the list of directories for data files and modules.
    -n ENCODING Use ENCODING when reading and writing files.
    -o OUTNAME  Write the output to OUTNAME.
    -r          Replace the input file with the output.
    -s STRING   Suffix all generated output lines with STRING.
    -U          Write the output with Unix newlines (only LF line-endings).
    -w CMD      Use CMD if the output file needs to be made writable.
                    A %s in the CMD will be filled with the filename.
    -x          Excise all the generated output without running the generators.
    -z          The end-output marker can be omitted, and is assumed at eof.
    -v          Print the version of cog and exit.
    --verbosity=VERBOSITY
                Control the amount of output. 2 (the default) lists all files,
                1 lists only changed files, 0 lists no files.
    --markers='START END END-OUTPUT'
                The patterns surrounding cog inline instructions. Should
                include three values separated by spaces, the start, end,
                and end-output markers. Defaults to '[[[cog ]]] [[[end]]]'.
    -h          Print this help.
"""

# Other package modules
from .whiteutils import *

class CogError(Exception):
    """ Any exception raised by Cog.
    """
    def __init__(self, msg, file='', line=0):
        if file:
            Exception.__init__(self, "%s(%d): %s" % (file, line, msg))
        else:
            Exception.__init__(self, msg)

class CogUsageError(CogError):
    """ An error in usage of command-line arguments in cog.
    """
    pass    #pragma: no cover

class CogInternalError(CogError):
    """ An error in the coding of Cog. Should never happen.
    """
    pass    #pragma: no cover

class CogGeneratedError(CogError):
    """ An error raised by a user's cog generator.
    """
    pass    #pragma: no cover

class Redirectable:
    """ An object with its own stdout and stderr files.
    """
    def __init__(self):
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def setOutput(self, stdout=None, stderr=None):
        """ Assign new files for standard out and/or standard error.
        """
        if stdout:
            self.stdout = stdout
        if stderr:
            self.stderr = stderr

    def prout(self, s, end="\n"):
        print(s, file=self.stdout, end=end)

    def prerr(self, s, end="\n"):
        print(s, file=self.stderr, end=end)


class CogGenerator(Redirectable):
    """ A generator pulled from a source file.
    """
    def __init__(self):
        Redirectable.__init__(self)
        self.markers = []
        self.lines = []

    def parseMarker(self, l):
        self.markers.append(l)

    def parseLine(self, l):
        self.lines.append(l.strip('\n'))

    def getCode(self):
        """ Extract the executable Python code from the generator.
        """
        # If the markers and lines all have the same prefix
        # (end-of-line comment chars, for example),
        # then remove it from all the lines.
        prefIn = commonPrefix(self.markers + self.lines)
        if prefIn:
            self.markers = [ l.replace(prefIn, '', 1) for l in self.markers ]
            self.lines = [ l.replace(prefIn, '', 1) for l in self.lines ]

        return reindentBlock(self.lines, '')

    def evaluate(self, cog, globals, fname='cog generator'):
        # figure out the right whitespace prefix for the output
        prefOut = whitePrefix(self.markers)

        intext = self.getCode()
        if not intext:
            return ''

        # In Python 2.2, the last line has to end in a newline.
        intext = "import cog\n" + intext + "\n"
        code = compile(intext, str(fname), 'exec')

        # Make sure the "cog" module has our state.
        cog.cogmodule.msg = self.msg
        cog.cogmodule.out = self.out
        cog.cogmodule.outl = self.outl
        cog.cogmodule.error = self.error

        self.outstring = ''
        eval(code, globals)

        # We need to make sure that the last line in the output
        # ends with a newline, or it will be joined to the
        # end-output line, ruining cog's idempotency.
        if self.outstring and self.outstring[-1] != '\n':
            self.outstring += '\n'

        return reindentBlock(self.outstring, prefOut)

    def msg(self, s):
        self.prout("Message: "+s)

    def out(self, sOut='', dedent=False, trimblanklines=False):
        """ The cog.out function.
        """
        if trimblanklines and ('\n' in sOut):
            lines = sOut.split('\n')
            if lines[0].strip() == '':
                del lines[0]
            if lines and lines[-1].strip() == '':
                del lines[-1]
            sOut = '\n'.join(lines)+'\n'
        if dedent:
            sOut = reindentBlock(sOut)
        self.outstring += sOut

    def outl(self, sOut='', **kw):
        """ The cog.outl function.
        """
        self.out(sOut, **kw)
        self.out('\n')

    def error(self, msg='Error raised by cog generator.'):
        """ The cog.error function.
            Instead of raising standard python errors, cog generators can use
            this function.  It will display the error without a scary Python
            traceback.
        """
        raise CogGeneratedError(msg)


class NumberedFileReader:
    """ A decorator for files that counts the readline()'s called.
    """
    def __init__(self, f):
        self.f = f
        self.n = 0

    def readline(self):
        l = self.f.readline()
        if l:
            self.n += 1
        return l

    def linenumber(self):
        return self.n


class CogOptions:
    """ Options for a run of cog.
    """
    def __init__(self):
        # Defaults for argument values.
        self.args = []
        self.includePath = []
        self.defines = {}
        self.bShowVersion = False
        self.sMakeWritableCmd = None
        self.bReplace = False
        self.bNoGenerate = False
        self.sOutputName = None
        self.bWarnEmpty = False
        self.bHashOutput = False
        self.bDeleteCode = False
        self.bEofCanBeEnd = False
        self.sSuffix = None
        self.bNewlines = False
        self.sBeginSpec = '[[[cog'
        self.sEndSpec = ']]]'
        self.sEndOutput = '[[[end]]]'
        self.sEncoding = "utf-8"
        self.verbosity = 2

    def __eq__(self, other):
        """ Comparison operator for tests to use.
        """
        return self.__dict__ == other.__dict__

    def clone(self):
        """ Make a clone of these options, for further refinement.
        """
        return copy.deepcopy(self)

    def addToIncludePath(self, dirs):
        """ Add directories to the include path.
        """
        dirs = dirs.split(os.pathsep)
        self.includePath.extend(dirs)

    def parseArgs(self, argv):
        # Parse the command line arguments.
        try:
            opts, self.args = getopt.getopt(
                argv,
                'cdD:eI:n:o:rs:Uvw:xz',
                [
                    'markers=',
                    'verbosity=',
                ]
            )
        except getopt.error as msg:
            raise CogUsageError(msg)

        # Handle the command line arguments.
        for o, a in opts:
            if o == '-c':
                self.bHashOutput = True
            elif o == '-d':
                self.bDeleteCode = True
            elif o == '-D':
                if a.count('=') < 1:
                    raise CogUsageError("-D takes a name=value argument")
                name, value = a.split('=', 1)
                self.defines[name] = value
            elif o == '-e':
                self.bWarnEmpty = True
            elif o == '-I':
                self.addToIncludePath(a)
            elif o == '-n':
                self.sEncoding = a
            elif o == '-o':
                self.sOutputName = a
            elif o == '-r':
                self.bReplace = True
            elif o == '-s':
                self.sSuffix = a
            elif o == '-U':
                self.bNewlines = True
            elif o == '-v':
                self.bShowVersion = True
            elif o == '-w':
                self.sMakeWritableCmd = a
            elif o == '-x':
                self.bNoGenerate = True
            elif o == '-z':
                self.bEofCanBeEnd = True
            elif o == '--markers':
                self._parse_markers(a)
            elif o == '--verbosity':
                self.verbosity = int(a)
            else:
                # Since getopt.getopt is given a list of possible flags,
                # this is an internal error.
                raise CogInternalError("Don't understand argument %s" % o)

    def _parse_markers(self, val):
        try:
            self.sBeginSpec, self.sEndSpec, self.sEndOutput = val.split(' ')
        except ValueError:
            raise CogUsageError(
                '--markers requires 3 values separated by spaces, could not parse %r' % val
            )

    def validate(self):
        """ Does nothing if everything is OK, raises CogError's if it's not.
        """
        if self.bReplace and self.bDeleteCode:
            raise CogUsageError("Can't use -d with -r (or you would delete all your source!)")

        if self.bReplace and self.sOutputName:
            raise CogUsageError("Can't use -o with -r (they are opposites)")


class Cog(Redirectable):
    """ The Cog engine.
    """
    def __init__(self):
        Redirectable.__init__(self)
        self.options = CogOptions()
        self._fixEndOutputPatterns()
        self.installCogModule()

    def _fixEndOutputPatterns(self):
        end_output = re.escape(self.options.sEndOutput)
        self.reEndOutput = re.compile(end_output + r'(?P<hashsect> *\(checksum: (?P<hash>[a-f0-9]+)\))')
        self.sEndFormat = self.options.sEndOutput + ' (checksum: %s)'

    def showWarning(self, msg):
        self.prout("Warning: "+msg)

    def isBeginSpecLine(self, s):
        return self.options.sBeginSpec in s

    def isEndSpecLine(self, s):
        return self.options.sEndSpec in s and not self.isEndOutputLine(s)

    def isEndOutputLine(self, s):
        return self.options.sEndOutput in s

    def installCogModule(self):
        """ Magic mumbo-jumbo so that imported Python modules
            can say "import cog" and get our state.
        """
        self.cogmodule = imp.new_module('cog')
        self.cogmodule.path = []
        sys.modules['cog'] = self.cogmodule

    def openOutputFile(self, fname):
        """ Open an output file, taking all the details into account.
        """
        opts = {}
        mode = "w"
        if PY3:
            opts['encoding'] = self.options.sEncoding
        if self.options.bNewlines:
            if PY3:
                opts['newline'] = "\n"
            else:
                mode = "wb"
        fdir = os.path.dirname(fname)
        if os.path.dirname(fdir) and not os.path.exists(fdir):
            os.makedirs(fdir)
        return open(fname, mode, **opts)

    def openInputFile(self, fname):
        """ Open an input file. """
        if fname == "-":
            return sys.stdin
        else:
            opts = {}
            if PY3:
                opts['encoding'] = self.options.sEncoding
            return open(fname, "r", **opts)

    def processFile(self, fIn, fOut, fname=None, globals=None):
        """ Process an input file object to an output file object.
            fIn and fOut can be file objects, or file names.
        """

        sFileIn = fname or ''
        sFileOut = fname or ''
        fInToClose = fOutToClose = None
        # Convert filenames to files.
        if isinstance(fIn, string_types):
            # Open the input file.
            sFileIn = fIn
            fIn = fInToClose = self.openInputFile(fIn)
        if isinstance(fOut, string_types):
            # Open the output file.
            sFileOut = fOut
            fOut = fOutToClose = self.openOutputFile(fOut)

        try:
            fIn = NumberedFileReader(fIn)

            bSawCog = False

            self.cogmodule.inFile = sFileIn
            self.cogmodule.outFile = sFileOut

            # The globals dict we'll use for this file.
            if globals is None:
                globals = {}

            # If there are any global defines, put them in the globals.
            globals.update(self.options.defines)

            # loop over generator chunks
            l = fIn.readline()
            while l:
                # Find the next spec begin
                while l and not self.isBeginSpecLine(l):
                    if self.isEndSpecLine(l):
                        raise CogError("Unexpected '%s'" % self.options.sEndSpec,
                            file=sFileIn, line=fIn.linenumber())
                    if self.isEndOutputLine(l):
                        raise CogError("Unexpected '%s'" % self.options.sEndOutput,
                            file=sFileIn, line=fIn.linenumber())
                    fOut.write(l)
                    l = fIn.readline()
                if not l:
                    break
                if not self.options.bDeleteCode:
                    fOut.write(l)

                # l is the begin spec
                gen = CogGenerator()
                gen.setOutput(stdout=self.stdout)
                gen.parseMarker(l)
                firstLineNum = fIn.linenumber()
                self.cogmodule.firstLineNum = firstLineNum

                # If the spec begin is also a spec end, then process the single
                # line of code inside.
                if self.isEndSpecLine(l):
                    beg = l.find(self.options.sBeginSpec)
                    end = l.find(self.options.sEndSpec)
                    if beg > end:
                        raise CogError("Cog code markers inverted",
                            file=sFileIn, line=firstLineNum)
                    else:
                        sCode = l[beg+len(self.options.sBeginSpec):end].strip()
                        gen.parseLine(sCode)
                else:
                    # Deal with an ordinary code block.
                    l = fIn.readline()

                    # Get all the lines in the spec
                    while l and not self.isEndSpecLine(l):
                        if self.isBeginSpecLine(l):
                            raise CogError("Unexpected '%s'" % self.options.sBeginSpec,
                                file=sFileIn, line=fIn.linenumber())
                        if self.isEndOutputLine(l):
                            raise CogError("Unexpected '%s'" % self.options.sEndOutput,
                                file=sFileIn, line=fIn.linenumber())
                        if not self.options.bDeleteCode:
                            fOut.write(l)
                        gen.parseLine(l)
                        l = fIn.readline()
                    if not l:
                        raise CogError(
                            "Cog block begun but never ended.",
                            file=sFileIn, line=firstLineNum)

                    if not self.options.bDeleteCode:
                        fOut.write(l)
                    gen.parseMarker(l)

                l = fIn.readline()

                # Eat all the lines in the output section.  While reading past
                # them, compute the md5 hash of the old output.
                previous = ""
                hasher = hashlib.md5()
                while l and not self.isEndOutputLine(l):
                    if self.isBeginSpecLine(l):
                        raise CogError("Unexpected '%s'" % self.options.sBeginSpec,
                            file=sFileIn, line=fIn.linenumber())
                    if self.isEndSpecLine(l):
                        raise CogError("Unexpected '%s'" % self.options.sEndSpec,
                            file=sFileIn, line=fIn.linenumber())
                    previous += l
                    hasher.update(to_bytes(l))
                    l = fIn.readline()
                curHash = hasher.hexdigest()

                if not l and not self.options.bEofCanBeEnd:
                    # We reached end of file before we found the end output line.
                    raise CogError("Missing '%s' before end of file." % self.options.sEndOutput,
                        file=sFileIn, line=fIn.linenumber())

                # Make the previous output available to the current code
                self.cogmodule.previous = previous

                # Write the output of the spec to be the new output if we're
                # supposed to generate code.
                hasher = hashlib.md5()
                if not self.options.bNoGenerate:
                    sFile = "%s+%d" % (sFileIn, firstLineNum)
                    sGen = gen.evaluate(cog=self, globals=globals, fname=sFile)
                    sGen = self.suffixLines(sGen)
                    hasher.update(to_bytes(sGen))
                    fOut.write(sGen)
                newHash = hasher.hexdigest()

                bSawCog = True

                # Write the ending output line
                hashMatch = self.reEndOutput.search(l)
                if self.options.bHashOutput:
                    if hashMatch:
                        oldHash = hashMatch.groupdict()['hash']
                        if oldHash != curHash:
                            raise CogError("Output has been edited! Delete old checksum to unprotect.",
                                file=sFileIn, line=fIn.linenumber())
                        # Create a new end line with the correct hash.
                        endpieces = l.split(hashMatch.group(0), 1)
                    else:
                        # There was no old hash, but we want a new hash.
                        endpieces = l.split(self.options.sEndOutput, 1)
                    l = (self.sEndFormat % newHash).join(endpieces)
                else:
                    # We don't want hashes output, so if there was one, get rid of
                    # it.
                    if hashMatch:
                        l = l.replace(hashMatch.groupdict()['hashsect'], '', 1)

                if not self.options.bDeleteCode:
                    fOut.write(l)
                l = fIn.readline()

            if not bSawCog and self.options.bWarnEmpty:
                self.showWarning("no cog code found in %s" % sFileIn)
        finally:
            if fInToClose:
                fInToClose.close()
            if fOutToClose:
                fOutToClose.close()


    # A regex for non-empty lines, used by suffixLines.
    reNonEmptyLines = re.compile(r"^\s*\S+.*$", re.MULTILINE)

    def suffixLines(self, text):
        """ Add suffixes to the lines in text, if our options desire it.
            text is many lines, as a single string.
        """
        if self.options.sSuffix:
            # Find all non-blank lines, and add the suffix to the end.
            repl = r"\g<0>" + self.options.sSuffix.replace('\\', '\\\\')
            text = self.reNonEmptyLines.sub(repl, text)
        return text

    def processString(self, sInput, fname=None):
        """ Process sInput as the text to cog.
            Return the cogged output as a string.
        """
        fOld = StringIO(sInput)
        fNew = StringIO()
        self.processFile(fOld, fNew, fname=fname)
        return fNew.getvalue()

    def replaceFile(self, sOldPath, sNewText):
        """ Replace file sOldPath with the contents sNewText
        """
        if not os.access(sOldPath, os.W_OK):
            # Need to ensure we can write.
            if self.options.sMakeWritableCmd:
                # Use an external command to make the file writable.
                cmd = self.options.sMakeWritableCmd.replace('%s', sOldPath)
                self.stdout.write(os.popen(cmd).read())
                if not os.access(sOldPath, os.W_OK):
                    raise CogError("Couldn't make %s writable" % sOldPath)
            else:
                # Can't write!
                raise CogError("Can't overwrite %s" % sOldPath)
        f = self.openOutputFile(sOldPath)
        f.write(sNewText)
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

    def processOneFile(self, sFile):
        """ Process one filename through cog.
        """

        self.saveIncludePath()
        bNeedNewline = False

        try:
            self.addToIncludePath(self.options.includePath)
            # Since we know where the input file came from,
            # push its directory onto the include path.
            self.addToIncludePath([os.path.dirname(sFile)])

            # How we process the file depends on where the output is going.
            if self.options.sOutputName:
                self.processFile(sFile, self.options.sOutputName, sFile)
            elif self.options.bReplace:
                # We want to replace the cog file with the output,
                # but only if they differ.
                if self.options.verbosity >= 2:
                    self.prout("Cogging %s" % sFile, end="")
                    bNeedNewline = True

                try:
                    fOldFile = self.openInputFile(sFile)
                    sOldText = fOldFile.read()
                    fOldFile.close()
                    sNewText = self.processString(sOldText, fname=sFile)
                    if sOldText != sNewText:
                        if self.options.verbosity >= 1:
                            if self.options.verbosity < 2:
                                self.prout("Cogging %s" % sFile, end="")
                            self.prout("  (changed)")
                            bNeedNewline = False
                        self.replaceFile(sFile, sNewText)
                finally:
                    # The try-finally block is so we can print a partial line
                    # with the name of the file, and print (changed) on the
                    # same line, but also make sure to break the line before
                    # any traceback.
                    if bNeedNewline:
                        self.prout("")
            else:
                self.processFile(sFile, self.stdout, sFile)
        finally:
            self.restoreIncludePath()

    def processFileList(self, sFileList):
        """ Process the files in a file list.
        """
        flist = self.openInputFile(sFileList)
        lines = flist.readlines()
        flist.close()
        for l in lines:
            # Use shlex to parse the line like a shell.
            lex = shlex.shlex(l, posix=True)
            lex.whitespace_split = True
            lex.commenters = '#'
            # No escapes, so that backslash can be part of the path
            lex.escape = ''
            args = list(lex)
            if args:
                self.processArguments(args)

    def processArguments(self, args):
        """ Process one command-line.
        """
        saved_options = self.options
        self.options = self.options.clone()

        self.options.parseArgs(args[1:])
        self.options.validate()

        if args[0][0] == '@':
            if self.options.sOutputName:
                raise CogUsageError("Can't use -o with @file")
            self.processFileList(args[0][1:])
        else:
            self.processOneFile(args[0])

        self.options = saved_options

    def callableMain(self, argv):
        """ All of command-line cog, but in a callable form.
            This is used by main.
            argv is the equivalent of sys.argv.
        """
        argv = argv[1:]

        # Provide help if asked for anywhere in the command line.
        if '-?' in argv or '-h' in argv:
            self.prerr(usage, end="")
            return

        self.options.parseArgs(argv)
        self.options.validate()
        self._fixEndOutputPatterns()

        if self.options.bShowVersion:
            self.prout("Cog version %s" % __version__)
            return

        if self.options.args:
            for a in self.options.args:
                self.processArguments([a])
        else:
            raise CogUsageError("No files to process")

    def main(self, argv):
        """ Handle the command-line execution for cog.
        """

        try:
            self.callableMain(argv)
            return 0
        except CogUsageError as err:
            self.prerr(err)
            self.prerr("(for help use -?)")
            return 2
        except CogGeneratedError as err:
            self.prerr("Error: %s" % err)
            return 3
        except CogError as err:
            self.prerr(err)
            return 1
        except:
            traceback.print_exc(None, self.stderr)
            return 1

# History:
# 20040210: First public version.
# 20040220: Text preceding the start and end marker are removed from Python lines.
#           -v option on the command line shows the version.
# 20040311: Make sure the last line of output is properly ended with a newline.
# 20040605: Fixed some blank line handling in cog.
#           Fixed problems with assigning to xml elements in handyxml.
# 20040621: Changed all line-ends to LF from CRLF.
# 20041002: Refactor some option handling to simplify unittesting the options.
# 20041118: cog.out and cog.outl have optional string arguments.
# 20041119: File names weren't being properly passed around for warnings, etc.
# 20041122: Added cog.firstLineNum: a property with the line number of the [[[cog line.
#           Added cog.inFile and cog.outFile: the names of the input and output file.
# 20041218: Single-line cog generators, with start marker and end marker on
#           the same line.
# 20041230: Keep a single globals dict for all the code fragments in a single
#           file so they can share state.
# 20050206: Added the -x switch to remove all generated output.
# 20050218: Now code can be on the marker lines as well.
# 20050219: Added -c switch to checksum the output so that edits can be
#           detected before they are obliterated.
# 20050521: Added cog.error, contributed by Alexander Belchenko.
# 20050720: Added code deletion and settable globals contributed by Blake Winton.
# 20050724: Many tweaks to improve code coverage.
# 20050726: Error messages are now printed with no traceback.
#           Code can no longer appear on the marker lines,
#               except for single-line style.
#           -z allows omission of the [[[end]]] marker, and it will be assumed
#               at the end of the file.
# 20050729: Refactor option parsing into a separate class, in preparation for
#               future features.
# 20050805: The cogmodule.path wasn't being properly maintained.
# 20050808: Added the -D option to define a global value.
# 20050810: The %s in the -w command is dealt with more robustly.
#           Added the -s option to suffix output lines with a marker.
# 20050817: Now @files can have arguments on each line to change the cog's
#               behavior for that line.
# 20051006: Version 2.0
# 20080521: -U options lets you create Unix newlines on Windows.  Thanks,
#               Alexander Belchenko.
# 20080522: It's now ok to have -d with output to stdout, and now we validate
#               the args after each line of an @file.
# 20090520: Use hashlib where it's available, to avoid a warning.
#           Use the builtin compile() instead of compiler, for Jython.
#           Explicitly close files we opened, Jython likes this.
# 20120205: Port to Python 3.  Lowest supported version is 2.6.
# 20150104: --markers option added by Doug Hellmann.
# 20150104: -n ENCODING option added by Petr Gladkiy.
# 20150107: Added --verbose to control what files get listed.
# 20150111: Version 2.4
# 20160213: v2.5: -o makes needed directories, thanks Jean-François Giraud.
# 20161019: Added a LICENSE.txt file.
