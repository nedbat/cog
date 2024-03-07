Changelog
=========

..
    <history>
    <what when='20051006t222500'>split out from the main page.</what>
    <what when='20080521t090400'>2.1: -u flag</what>
    <what when='20080522t065300'>more 2.1 stuff</what>
    <what when='20080524t095147'>add a pointer to the russian.</what>
    <what when='20090520t061826'>started the 2.2 list.</what>
    <what when='20090625t211136'>2.2</what>
    <what when='20120205t162700'>2.3</what>
    <what when='20150111t202900'>2.4</what>
    <what when='20161019t192100'>2.5.1</what>
    <what when='20190402t063900'>3.0.0</what>
    <what when='20210831t172000'>3.1.0</what>
    </history>

These are changes to Cog over time.

Unreleased
----------

- Dropped support for Python 2.7, 3.5, and 3.6, and added 3.11 and 3.12.

- Removed the ``cog.py`` installed file.  Use the ``cog`` command, or ``python
  -m cogapp`` to run cog.

- Processing long files has been made much faster.  Thanks, Panayiotis Gavriil.

- Files listing other files to process can now be specified as
  ``&files_to_cog.txt`` to interpret the file names relative to the location of
  the list file.  The existing ``@files_to_cog.txt`` syntax interprets file
  names relative to the current working directory.  Thanks, Phil Kirkpatrick.

- Support FIPS mode computers by marking our MD5 use as not related to
  security.  Thanks, Ryan Santos.

- Docs have moved to https://cog.readthedocs.io


3.3.0 – November 19 2021
------------------------

- Added the ``--check`` option to check whether files would change if run
  again, for use in continuous integration scenarios.


3.2.0 – November 7 2021
-----------------------

- Added the ``-P`` option to use `print()` instead of `cog.outl()` for code
  output.


3.1.0 – August 31 2021
----------------------

- Fix a problem with Python 3.8.10 and 3.9.5 that require absolute paths in
  sys.path. `issue 16`_.

- Python 3.9 and 3.10 are supported.

.. _issue 16: https://github.com/nedbat/cog/issues/16


3.0.0 – April 2 2019
--------------------

- Dropped support for Pythons 2.6, 3.3, and 3.4.

- Errors occurring during content generation now print accurate tracebacks,
  showing the correct filename, line number, and source line.

- Cog can now (again?) be run as just "cog" on the command line.

- The ``-p=PROLOGUE`` option was added to specify Python text to prepend to
  embedded code. Thanks, Anders Hovmöller.

- Wildcards in command line arguments will be expanded by cog to help on
  Windows.  Thanks, Hugh Perkins.

- When using implicitly imported "cog", a new module is made for each run.
  This is important when using the cog API multi-threaded.  Thanks, Daniel
  Murdin.

- Moved development to GitHub.


2.5.1 – October 19 2016
-----------------------

- Corrected a long-standing oversight: added a LICENSE.txt file.

2.5 – February 13 2016
----------------------

- When specifying an output file with ``-o``, directories will be created as
  needed to write the file. Thanks, Jean-François Giraud.

2.4 – January 11 2015
---------------------

- A ``--markers`` option lets you control the three markers that separate the
  cog code and result from the rest of the file. Thanks, Doug Hellmann.

- A ``-n=ENCODING`` option that lets you specify the encoding for the input and
  output files. Thanks, Petr Gladkiy.

- A ``--verbose`` option that lets you control how much chatter is in the
  output while cogging.

2.3 – February 27 2012
----------------------

- Python 3 is now supported.  Older Pythons (2.5 and below) no longer are.

- Added the `cog.previous` attribute to get the output from the last time cog was
  run.

- An input file name of "-" will read input from standard in.

- Cog can now be run with "python3 -m cogapp [args]".

- All files are assumed to be encoded with UTF-8.


2.2 – June 25 2009
------------------

- Jython 2.5 is now supported.

- Removed a warning about using the no-longer-recommended md5 module.

- Removed handyxml: most Cog users don't need it.


2.1 – May 22 2008
-----------------

- Added the ``-U`` switch to create Unix newlines on Windows.

- Improved argument validation: ``-d`` can be used with stdout-destined output,
  and switches are validated for every line of an @file, to prevent bad
  interactions.


2.0 – October 6 2005
--------------------

Incompatible changes:

- Python 2.2 is no longer supported.

- In 1.4, you could put some generator code on the ``[[[cog`` line and some on
  the ``]]]`` line, to make the generators more compact.  Unfortunately, this
  also made it more difficult to seamlessly embed those markers in source files
  of all kinds.  Now code is only allowed on marker lines when the entire
  generator is single-line.

- In 1.x, you could leave out the ``[[[end]]]`` marker, and it would be assumed
  at the end of the file.  Now that behavior must be enabled with a ``-z``
  switch.  Without the switch, omitting the end marker is an error.

Beneficial changes:

- The new ``-d`` switch removes all the generator code from the output file
  while running it to generate output (thanks, Blake).

- The new ``-D`` switch lets you define global string values for the
  generators.

- The new ``-s`` switch lets you mark generated output lines with a suffix.

- @-files now can have command line switches in addition to file names.

- Cog error messages now print without a traceback, and use a format similar to
  compiler error messages, so that clicking the message will likely bring you
  to the spot in your code (thanks, Mike).

- New cog method #1: `cog.error(msg)` will raise an error and end processing
  without creating a scary Python traceback (thanks, Alexander).

- New cog method #2: `cog.msg(msg)` will print the msg to stdout.  This is
  better than print because it allows for all cog output to be managed through
  Cog.

- The sequence of Cog marker lines is much stricter.  This helps to ensure that
  Cog isn't eating up your precious source code (thanks, Kevin).



1.4 – February 25 2005
----------------------

- Added the ``-x`` switch to excise generated output.

- Added the ``-c`` switch to checksum the generated output.



1.3 – December 30 2004
----------------------

- All of the generators in a single file are now run with a common globals
  dictionary, so that state may be carried from one to the next.



1.2 – December 29 2004
----------------------

- Added module attributes `cog.inFile`, `cog.outFile`, and `cog.firstLineNum`.

- Made the `sOut` argument optional in `cog.out` and `cog.outl`.

- Added the compact one-line form of cog markers.

- Some warning messages weren't properly printing the file name.



1.12 – June 21 2004
-------------------

- Changed all the line endings in the source to the more-portable LF from the
  Windows-only CRLF.



1.11 – June 5 2004
------------------

Just bug fixes:

- Cog's whitespace handling deals correctly with a completely blank line (no
  whitespace at all) in a chunk of Cog code.

- Elements returned by handyxml can now have attributes assigned to them after
  parsing.



1.1 – March 21 2004
-------------------

- Now if the cog marker lines and all the lines they contain have the same
  prefix characters, then the prefix is removed from each line.  This allows
  cog to be used with languages that don't support multi-line comments.

- Ensure the last line of the output ends with a newline, or it will merge with
  the end marker, ruining cog's idempotency.

- Add the ``-v`` command line option, to print the version.

- Running cog with no options prints the usage help.



1.0 – February 10 2004
----------------------

First version.

..
    # History moved from cogapp.py:
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
    # 20150104: -markers option added by Doug Hellmann.
    # 20150104: -n ENCODING option added by Petr Gladkiy.
    # 20150107: Added -verbose to control what files get listed.
    # 20150111: Version 2.4
    # 20160213: v2.5: -o makes needed directories, thanks Jean-François Giraud.
    # 20161019: Added a LICENSE.txt file.
