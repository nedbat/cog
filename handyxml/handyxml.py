""" HandyXml
    Make simple XML use convenient.
    http://nedbatchelder.com/code/cog

    Copyright 2004-2009, Ned Batchelder.
"""

# $Id: handyxml.py 110 2005-08-27 22:35:20Z ned $

import os.path, sys

from xml.dom import EMPTY_NAMESPACE
from xml.dom import Node
from xml.dom.ext.reader import PyExpat

__version__ = '1.1.20040127'        # History at the end of the file.
__all__ = ['path', 'xml', 'xpath']

# Try to use 4Suite for speed.
bDomlette = False
try:
    from Ft.Xml.Domlette import NonvalidatingReader
    bDomlette = True
except:     #pragma: no cover
    pass

# Try to use the optional xml.xpath.
bXPath = False
try:
    from xml import xpath as xml_xpath
    bXPath = True
except ImportError:     #pragma: no cover
    pass

#
# XML support
#

class HandyXmlWrapper:
    """ This class wraps an XML element to give it convenient
        attribute access.
        <element attr1='foo' attr2='bar'>
            <child attr3='baz' />
        </element>
        element.attr1 == 'foo'
        element.child[0].attr3 == 'baz'
    """
    def __init__(self, node):
        self.node = node

    def _getChildElements(self):
        els = []
        if hasattr(self.node, 'childNodes'):
            for e in self.node.childNodes:
                if e.nodeType == Node.ELEMENT_NODE:
                    els.append(e)
        else:   #pragma: no cover
            raise "Can't look for children on node?"
        # If we found some elements, wrap each one in a HandyXmlWrapper.
        if els:
            els = map(HandyXmlWrapper, els)
        return els
        
    childElements = property(_getChildElements)
    
    def __getattr__(self, attr):
        if attr[0:2] != '__':        
            if hasattr(self.node, attr):
                #print "Returning node attribute %s" % attr
                return getattr(self.node, attr)
    
            #print "Looking for "+attr, self.node, dir(self.node)
            if hasattr(self.node, 'hasAttribute'):
                if self.node.hasAttribute(attr):
                    return self.node.getAttribute(attr)
            elif hasattr(self.node, 'hasAttributeNS'):
                if self.node.hasAttributeNS(EMPTY_NAMESPACE, attr):
                    return self.node.getAttributeNS(EMPTY_NAMESPACE, attr)
            else:   #pragma: no cover
                raise "Can't look for attributes on node?"

            els = []
            for e in self.childElements:
                if e.localName == attr:
                    els.append(e)
            if els:
                # Save the attribute, since this could be a hasattr
                # that will be followed by getattr
                setattr(self, attr, els)
                return els

        raise AttributeError, "Couldn't find %s for node" % attr

# The path on which we look for XML files.
path = ['.']

def _findFile(filename):
    """ Find files on path.
    """
    ret = None
    searchPath = path
    # If cog is in use, then use its path as well.
    if sys.modules.has_key('cog'):
        searchPath += sys.modules['cog'].path
    # Search the directories on the path.
    for dir in searchPath:
        p = os.path.join(dir, filename)
        if os.path.exists(p):
            ret = os.path.abspath(p)
    return ret

# A dictionary from full file paths to parsed XML.
_xmlcache = {}

def xml(xmlin):
    """ Parse some XML.
        Argument xmlin can be a string, the filename of some XML;
        or an open file, from which xml is read.
        The return value is the parsed XML as DOM nodes.
    """

    filename = None

    # A string argument is a file name.
    if isinstance(xmlin, basestring):
        filename = _findFile(xmlin)
        if not filename:
            raise "Couldn't find XML to parse: %s" % xmlin

    if filename:
        if _xmlcache.has_key(filename):
            return _xmlcache[filename]
        xmlin = open(filename)

    xmldata = xmlin.read()

    if bDomlette:
        doc = NonvalidatingReader.parseString(xmldata, filename or ' ')
    else:
        doc = PyExpat.Reader().fromString(xmldata)

    parsedxml = HandyXmlWrapper(doc.documentElement)

    if filename:
        _xmlcache[filename] = parsedxml

    return parsedxml

if bXPath:
    def xpath(input, expr):
        """ Evaluate the xpath expression against the input XML.
        """
        if isinstance(input, basestring) or hasattr(input, 'read'):
            # If input is a filename or an open file, then parse the XML.
            input = xml(input)
        return map(HandyXmlWrapper, xml_xpath.Evaluate(expr, input))

else:   #pragma: no cover
    def xpath(input, expr):
        raise "The xml.xpath module is not installed! Get it from http://pyxml.sourceforge.net/"

# History:
# 1.0.20040125  First version.
# 1.1.20040127  xml.xpath is an optional module.  Be forgiving if it is absent.
#               xml() and xpath() can now take an open file as well as a file name.
# Rolled into cog.
# 20040605  Fixes to make sure you can assign to an element node.
