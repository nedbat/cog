The cog module
==============

A module called ``cog`` provides the functions you call to produce output into
your file.  The functions are:

..
    <dl>

    <dt><b>cog.out</b><i>(sOut='' [, dedent=False][, trimblanklines=False])</i></dt>
    <dd>Writes text to the output.</dd>
    <dd><i>sOut</i> is the string to write to the output.</dd>
    <dd>If <i>dedent</i> is True, then common initial white space is removed from the
    lines in <i>sOut</i> before adding them to the output.
    If <i>trimblanklines</i> is True, then an initial and trailing
    blank line are removed from <i>sOut</i> before adding them to the output.
    Together, these option arguments make it easier to use multi-line strings,
    and they only are useful for multi-line strings:</dd>
    <code><![CDATA[
    cog.out("""
        These are lines I
        want to write into my source file.
    """, dedent=True, trimblanklines=True)
    ]]></code>

    <dt><b>cog.outl</b></dt>
    <dd>Same as <b>cog.out</b>, but adds a trailing newline.</dd>

    <dt><b>cog.msg</b><i>(msg)</i></dt>
    <dd>Prints <i>msg</i> to stdout with a "Message: " prefix.</dd>

    <dt><b>cog.error</b><i>(msg)</i></dt>
    <dd>Raises an exception with <i>msg</i> as the text.
    No traceback is included, so that non-Python programmers using your code
    generators won't be scared.</dd>

    <dt><b>cog.inFile</b></dt>
    <dd>An attribute, the path of the input file.</dd>

    <dt><b>cog.outFile</b></dt>
    <dd>An attribute, the path of the output file.</dd>

    <dt><b>cog.firstLineNum</b></dt>
    <dd>An attribute, the line number of the first line of Python code
    in the generator.  This can be used to distinguish between two
    generators in the same input file, if needed.</dd>

    <dt><b>cog.previous</b></dt>
    <dd>An attribute, the text output of the previous run of this
    generator.  This can be used for whatever purpose you like, including
    outputting again with cog.out().</dd>
    </dl>
