The cog module
==============

A synthetic module called ``cog`` provides functions you can call to produce
output into your file.  You don't need to use these functions: with the ``-P``
command-line option, your program's stdout writes to the output file, so
`print()` will be enough.

The module contents are:

**cog.out** `(sOut='' [, dedent=False][, trimblanklines=False])`
    Writes text to the output.  `sOut` is the string to write to the output.
    If `dedent` is True, then common initial white space is removed from the
    lines in `sOut` before adding them to the output.  If `trimblanklines` is
    True, then an initial and trailing blank line are removed from `sOut`
    before adding them to the output.  Together, these option arguments make it
    easier to use multi-line strings, and they only are useful for multi-line
    strings::

        cog.out("""
            These are lines I
            want to write into my source file.
        """, dedent=True, trimblanklines=True)

**cog.outl**
    Same as **cog.out**, but adds a trailing newline.

**cog.msg** `(msg)`
    Prints `msg` to stdout with a "Message: " prefix.

**cog.error** `(msg)`
    Raises an exception with `msg` as the text.  No traceback is included, so
    that non-Python programmers seeing the output won't be scared.

**cog.inFile**
    An attribute, the path of the input file.

**cog.outFile**
    An attribute, the path of the output file.

**cog.firstLineNum**
    An attribute, the line number of the first line of Python code in the
    current chunk.  This can be used to distinguish between two chunks in the
    same input file, if needed.

**cog.previous**
    An attribute, the text output of the previous run of this Python code.
    This can be used for whatever purpose you like, including outputting again
    with **cog.out**.
