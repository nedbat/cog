Writing the source files
========================

Source files to be run through cog are mostly just plain text that will be
passed through untouched.  The Python code in your source file is standard
Python code.  Any way you want to use Python to generate text to go into your
file is fine.  Each chunk of Python code (between the ``[[[cog`` and ``]]]``
lines) is executed in sequence.

The output area for each Python chunk (between the ``]]]`` and ``[[[end]]]``
lines) is deleted, and the output of running the Python code is inserted in its
place.  To accommodate all source file types, the format of the marker lines is
irrelevant.  If the line contains the special character sequence, the whole
line is taken as a marker.  For example, any of these lines mark the beginning
of executable Python code:

.. code-block:: text

    //[[[cog
    /* cog starts now: [[[cog */
    -- [[[cog (this is cog Python code)
    #if 0 // [[[cog

Cog can also be used in files that don't support multi-line comments.  If the
marker lines all have the same text before the triple brackets, and all the
lines in the Python chunk also have this text as a prefix, then the prefixes
are removed from all the Python lines before execution.  For example, in a SQL
file, this:

.. code-block:: sql

    --[[[cog
    --   import cog
    --   for table in ['customers', 'orders', 'suppliers']:
    --      cog.outl("drop table %s;" % table)
    --]]]
    --[[[end]]]

will produce this:

.. code-block:: sql

    --[[[cog
    --   import cog
    --   for table in ['customers', 'orders', 'suppliers']:
    --      cog.outl("drop table %s;" % table)
    --]]]
    drop table customers;
    drop table orders;
    drop table suppliers;
    --[[[end]]]

Finally, a compact form can be used for single Python lines.  The begin-code
marker and the end-code marker can appear on the same line, and all the text
between them will be taken as one Python line:

.. code-block:: cpp

    // blah blah
    //[[[cog import MyModule as m; m.generateCode() ]]]
    //[[[end]]]

You can also use this form to simply import a module.  The top-level statements
in the module can generate the code.

If you have special requirements for the syntax of your file, you can use the
``--markers`` option to define new markers.

If there are multiple Python chunks in the same file, they are executed with
the same globals dictionary, so it is as if they were all one Python module.
This lets you import modules or create functions for use throughout a file.

Cog tries to do the right thing with white space.  Your Python code can be
block-indented to match the surrounding text in the source file, and cog will
re-indent the output to fit as well.  All of the output for a chunk is
collected as a block of text, a common whitespace prefix is removed, and then
the block is indented to match the indentation of the Python code. This means
the left-most non-whitespace character in your output will have the same
indentation as the begin-code marker line.  Other lines in your output keep
their relative indentation.
