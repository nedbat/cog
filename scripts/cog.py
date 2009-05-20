#!/usr/bin/python
""" Cog code generation tool.
    http://nedbatchelder.com/code/cog

    Copyright 2004-2005, Ned Batchelder.
"""

# $Id: cog.py 110 2005-08-27 22:35:20Z ned $

import time
start = time.clock()

import sys
from cogapp import Cog

ret = Cog().main(sys.argv)

#print "Time: %.2f sec" % (time.clock() - start)
sys.exit(ret)
