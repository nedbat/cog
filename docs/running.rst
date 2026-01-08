Running cog
===========

Cog is a command-line utility which takes arguments in standard form.

.. {{{cog
    # Re-run this with `make cogdoc`
    # Here we use unconventional markers so the docs can use [[[ without
    # getting tangled up in the cog processing.

    import io
    import os
    import textwrap
    from cogapp import Cog

    print("\n.. code-block:: text\n")
    outf = io.StringIO()
    print("$ cog -h", file=outf)
    os.environ["COLUMNS"] = "80"  # standardize / insulate from caller terminal width
    cog = Cog()
    cog.set_output(stdout=outf, stderr=outf)
    cog.main(["cog", "-h"])
    print(textwrap.indent(outf.getvalue(), "    "))
.. }}}

.. code-block:: text

    $ cog -h
    cog - generate content with inlined Python code.

    cog [OPTIONS] [INFILE | @FILELIST | &FILELIST] ...

    positional arguments:
      [INFILE | @FILELIST | &FILELIST]
                            FILELIST is the name of a text file containing file
                            names or other @FILELISTs. For @FILELIST, paths in the
                            file list are relative to the working directory where
                            cog was called. For &FILELIST, paths in the file list
                            are relative to the file list location."

    options:
      -h, --help            show this help message and exit
      -c                    Checksum the output to protect it against accidental
                            change.
      -d                    Delete the Python code from the output file.
      -D name=val           Define a global string available to your Python code.
      -e                    Warn if a file has no cog code in it.
      -I PATH               Add PATH to the list of directories for data files and
                            modules.
      -n ENCODING           Use ENCODING when reading and writing files.
      -o OUTNAME            Write the output to OUTNAME.
      -p PROLOGUE           Prepend the Python source with PROLOGUE. Useful to
                            insert an import line. Example: -p "import math"
      -P                    Use print() instead of cog.outl() for code output.
      -r                    Replace the input file with the output.
      -s STRING             Suffix all generated output lines with STRING.
      -U                    Write the output with Unix newlines (only LF line-
                            endings).
      -w CMD                Use CMD if the output file needs to be made writable.
                            A %s in the CMD will be filled with the filename.
      -x                    Excise all the generated output without running the
                            Pythons.
      -z                    The end-output marker can be omitted, and is assumed
                            at eof.
      -v                    Print the version of cog and exit.
      --check               Check that the files would not change if run again.
      --check-fail-msg MSG  If --check fails, include MSG in the output to help
                            devs understand how to run cog in your project.
      --diff                With --check, show a diff of what failed the check.
      --markers 'START END END-OUTPUT'
                            The patterns surrounding cog inline instructions.
                            Should include three values separated by spaces, the
                            start, end, and end-output markers. Defaults to
                            '[[[cog ]]] [[[end]]]'.
      --verbosity VERBOSITY
                            Control the amount of output. 2 (the default) lists
                            all files, 1 lists only changed files, 0 lists no
                            files.

.. {{{end}}} (sum: PC7aU7vkZv)

In addition to running cog as a command on the command line, you can also
invoke it as a module with the Python interpreter:

.. code-block:: bash

    $ python3 -m cogapp [options] [arguments]

Note that the Python module is called "cogapp".


Input files
-----------

Files on the command line are processed as input files. All input files are
assumed to be UTF-8 encoded. Using a minus for a filename (``-``) will read the
standard input.

Files can also be listed in a text file named on the command line
with an ``@``:

.. code-block:: bash

    $ cog @files_to_cog.txt

File names in the list file are relative to the current directory. You can also
use ``&files_to_cog.txt`` and the file names will be relative to the location
of the list file.

These list files can be nested, and each line can contain switches as well as a
file to process.  For example, you can create a file cogfiles.txt:

.. code-block:: text

    # These are the files I run through cog
    mycode.cpp
    myothercode.cpp
    myschema.sql -s " --**cogged**"
    readme.txt -s ""

then invoke cog like this:

.. code-block:: bash

    $ cog -s " //**cogged**" @cogfiles.txt

Now cog will process four files, using C++ syntax for markers on all the C++
files, SQL syntax for the .sql file, and no markers at all on the readme.txt
file.

As another example, cogfiles2.txt could be:

.. code-block:: text

    template.h -D thefile=data1.xml -o data1.h
    template.h -D thefile=data2.xml -o data2.h

with cog invoked like this:

.. code-block:: bash

    $ cog -D version=3.4.1 @cogfiles2.txt

Cog will process template.h twice, creating both data1.h and data2.h.  Both
executions would define the variable version as "3.4.1", but the first run
would have thefile equal to "data1.xml" and the second run would have thefile
equal to "data2.xml".


Overwriting files
-----------------

The ``-r`` flag tells cog to write the output back to the input file.  If the
input file is not writable (for example, because it has not been checked out of
a source control system), a command to make the file writable can be provided
with ``-w``:

.. code-block:: bash

    $ cog -r -w "p4 edit %s" @files_to_cog.txt


Setting globals
---------------

Global values can be set from the command line with the ``-D`` flag.  For
example, invoking Cog like this:

.. code-block:: bash

    $ cog -D thefile=fooey.xml mycode.txt

will run Cog over mycode.txt, but first define a global variable called thefile
with a value of "fooey.xml". This variable can then be referenced in your
Python code. You can provide multiple ``-D`` arguments on the command line,
and all will be defined and available.

The value is always interpreted as a Python string, to simplify the problem of
quoting.  This means that:

.. code-block:: bash

    $ cog -D NUM_TO_DO=12

will define ``NUM_TO_DO`` not as the integer ``12``, but as the string
``"12"``, which are different and not equal values in Python. Use
`int(NUM_TO_DO)` to get the numeric value.


Checksummed output
------------------

If cog is run with the ``-c`` flag, then generated output is accompanied by
a checksum:

.. code-block:: sql

    --[[[cog
    --   import cog
    --   for i in range(10):
    --      cog.out("%d " % i)
    --]]]
    0 1 2 3 4 5 6 7 8 9
    --[[[end]]] (sum: vXcVMEUp9m)

The checksum uses a compact base64 encoding to be less visually distracting.
If the generated code is edited by a misguided developer, the next time cog
is run, the checksum won't match, and cog will stop to avoid overwriting the
edited output.

Cog can also read files with the older hex checksum format:

.. code-block:: sql

    --[[[end]]] (checksum: bd7715304529f66c4d3493e786bb0f1f)

When such files are regenerated, the checksum will be updated to the shorter
base64 format automatically.


Continuous integration
----------------------

You can use the ``--check`` option to run cog just to check that the files
would not change if run again.  This is useful in continuous integration to
check that your files have been updated properly.

The ``--diff`` option will show a unified diff of the change that caused
``--check`` to fail.

The ``--check-fail-msg`` option can be used to provide a message as part of the
output if ``--check`` fails.  This can be used to give instructions about how
to run cog in your project to fix the problem.


Output line suffixes
--------------------

To make it easier to identify generated lines when grepping your source files,
the ``-s`` switch provides a suffix which is appended to every non-blank text
line generated by Cog.  For example, with this input file (mycode.txt):

.. code-block:: text

    [[[cog
    cog.outl('Three times:\n')
    for i in range(3):
        cog.outl('This is line %d' % i)
    ]]]
    [[[end]]]

invoking cog like this:

.. code-block:: bash

    $ cog -s " //(generated)" mycode.txt

will produce this output:

.. code-block:: text

    [[[cog
    cog.outl('Three times:\n')
    for i in range(3):
        cog.outl('This is line %d' % i)
    ]]]
    Three times: //(generated)

    This is line 0 //(generated)
    This is line 1 //(generated)
    This is line 2 //(generated)
    [[[end]]]


Miscellaneous
-------------

The ``-n`` option lets you tell cog what encoding to use when reading and
writing files.

The ``--verbose`` option lets you control how much cog should chatter about the
files it is cogging.  ``--verbose=2`` is the default: cog will name every file
it considers, and whether it has changed.  ``--verbose=1`` will only name the
changed files. ``--verbose=0`` won't mention any files at all.

The ``--markers`` option lets you control the syntax of the marker lines.  The
value must be a string with two spaces in it.  The three markers are the three
pieces separated by the spaces.  The default value for markers is ``"[[[cog ]]]
[[[end]]]"``.

The ``-x`` flag tells cog to delete the old generated output without running
the Python code.  This lets you remove all the generated output from a source
file.

The ``-d`` flag tells cog to delete the Python code from the output file.  This
lets you generate content in a public file but not have to show the Python
to your customers.

The ``-U`` flag causes the output file to use pure Unix newlines rather than
the platform's native line endings.  You can use this on Windows to produce
Unix-style output files.

The ``-I`` flag adds a directory to the path used to find Python modules.

The ``-p`` option specifies Python text to prepend to your Python, which can
keep common imports out of source files.

The ``-z`` flag lets you omit the ``[[[end]]]`` marker line, and it will be
assumed at the end of the file.
