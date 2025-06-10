Design
======

Cog is designed to be easy to run.  It writes its results back into the
original file while retaining the code it executed.  This means cog can be run
any number of times on the same file.  Rather than have a source
file and a separate output file, typically cog is run with one file serving as
both code and output.

Because the marker lines accommodate any language syntax, the markers can hide
the cog Python code in your text file.  This means cog files can be checked
into source control without worrying about keeping the source files separate
from the output files, without modifying build procedures, and so on.

I experimented with using a templating engine for generating code, and found
myself constantly struggling with white space in the generated output, and
mentally converting from the Python code I could imagine, into its templating
equivalent.  The advantages of a templating system (that most of the code could
be entered literally) were lost as the code generation tasks became more
complex, and the generation process needed more logic.

Cog lets you use the full power of Python for text generation, without a
templating system dumbing down your tools for you.
