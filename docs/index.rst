===
Cog
===

..
    <history>
    <!-- Actually created 20040208, but not posted until the 10th. -->
    <what when='20040210T200100'>Created.</what>
    <what when='20040321T000000'>Version 1.1.</what>
    <what when='20040515T204000'>Minor edits for clarity.</what>
    <what when='20040605T140000'>Updated to cog 1.11, added a See Also section, and fixed a sample.</what>
    <what when='20040621T221600'>Updated to cog 1.12.</what>
    <what when='20041229T203300'>Updated to cog 1.2.</what>
    <what when='20041230T172100'>Updated to cog 1.3.</what>
    <what when='20050225T191900'>Updated to cog 1.4.</what>
    <what when='20050517T063000'>Added links to other Cog implementations.</what>
    <what when='20050828T125100'>Added links to 2.0 beta 2.</what>
    <what when='20051006T220000'>Updating for 2.0.</what>
    <what when='20060205T090500'>Added PCG.</what>
    <what when='20060214T195400'>Added an explicit mention of the license: MIT.</what>
    <what when='20060810T081800'>Added links to 3rd-party packages.</what>
    <what when='20070720T080700'>Clarified -D value types, and fixed a 3rd-party link.</what>
    <what when='20080318T081200'>Tried to explain better about indentation, and fixed an incorrect parameter name.</what>
    <what when='20080521T085800'>Added -U switch from Alexander Belchenko.</what>
    <what when='20080524T092000'>Fixed the russian pointer to be to a current document.</what>
    <what when='20090625T202912'>Removed handyxml, files are now at pypi.</what>
    <what when='20120205T141000'>Python 3 is supported!</what>
    <what when='20120227T192300'>Polish up Cog 2.3</what>
    <what when='20150111T203100'>Version 2.4</what>
    <what when='20190402T063800'>Version 3.0.0</what>
    <what when='20211107T112100'>Version 3.2.0</what>
    <what when='20211119T104100'>Version 3.3.0</what>
    </history>

Cog is a content generation tool.  It lets you use small bits of Python code
in otherwise static files to generate whatever text you need.

This page describes version 3.5.1, released June 5, 2025.


What does it do?
================

Cog transforms files in a very simple way: it finds chunks of Python code
embedded in them, executes the Python code, and inserts its output back into
the original file.  The file can contain whatever text you like around the
Python code.

For example, if you run this file through cog:

.. code-block:: cpp

    // This is my C++ file.
    ...
    /*[[[cog
    import cog
    fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
    for fn in fnames:
        cog.outl("void %s();" % fn)
    ]]]*/
    //[[[end]]]
    ...

it will come out like this:

.. code-block:: cpp

    // This is my C++ file.
    ...
    /*[[[cog
    import cog
    fnames = ['DoSomething', 'DoAnotherThing', 'DoLastThing']
    for fn in fnames:
        cog.outl("void %s();" % fn)
    ]]]*/
    void DoSomething();
    void DoAnotherThing();
    void DoLastThing();
    //[[[end]]]
    ...

Lines with triple square brackets are marker lines.  The lines between
``[[[cog`` and ``]]]`` are Python code.  The lines between
``]]]`` and ``[[[end]]]`` are the output from the Python.

Output is written with `cog.outl()`, or if you use the ``-P`` option,
normal `print()` calls.

When cog runs, it discards the last generated Python output, executes the
Python code, and writes its generated output into the file.  All text
lines outside of the special markers are passed through unchanged.

The cog marker lines can contain any text in addition to the triple square
bracket tokens.  This makes it possible to hide the Python code from whatever
tools might read the file.  In the sample above, the entire chunk of Python
code is a C++ comment, so the Python code can be left in place while the file
is treated as C++ code.


Installation
============

Cog requires Python 3.9 or higher.

Cog is installed in the usual way, except the installation name is "cogapp",
not "cog":

.. code-block:: bash

    $ python3 -m pip install cogapp

You should now have a "cog" command you can run.

See the :ref:`changelog <changes>` for the history of changes.

Cog is distributed under the `MIT license`_.  Use it to spread goodness through
the world.

.. _MIT License: http://www.opensource.org/licenses/mit-license.php


More
====

.. toctree::
   :maxdepth: 1

   changes
   design
   source
   module
   running
