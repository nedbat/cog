""" Test Handyxml.
    http://nedbatchelder.com/code/cog
    
    Copyright 2004-2005, Ned Batchelder.
"""

# $Id: test_handyxml.py 134 2008-05-21 12:05:09Z nedbat $

import unittest                         # This is a unittest, so this is fundamental.
import StringIO, shutil, os, types,sys  # We need these modules to write the tests.

import handyxml
from cogapp.makefiles import *

# Simple data that we use in different methods.
duckdata = """\
<mydata group='ducks'>
    <property name='duck1' value='huey' />
    <property name='duck2' value='louie' >
        <king true='no'/>
    </property>
    <property name='duck3' value='dewey' />
</mydata>
"""

def doDuckAsserts(x):
    """ Asserts we can make about properly parsed duckdata.
    """
    assert(x.group == u'ducks')
    assert(len(x.property) == 3)
    assert(x.property[0].name == u'duck1')
    assert(x.property[0].value == u'huey')
    assert(x.property[1].name == u'duck2')
    assert(x.property[1].value == u'louie')
    assert(x.property[1].king[0].true == u'no')
    assert(x.property[2].name == u'duck3')
    assert(x.property[2].value == u'dewey')
    assert(not hasattr(x.property[2], 'xyzzy'))

# A global flag that controls the parser used by handyxml.
bDomlette = False

class BaseTestCase(unittest.TestCase):
    """ A base class for test cases.
        It grabs the global bDomlette flag to switch handyxml between parsers.
    """
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        self.bDomlette = bDomlette

    def setUp(self):
        handyxml.bDomlette = self.bDomlette

    def tearDown(self):
        pass
        
class SimpleTests(BaseTestCase):
    """ Simple tests of handyxml.
    """

    def testAttributes(self):
        x = handyxml.xml(StringIO.StringIO("<mydata group='ducks' empty=''/>"))
        assert(x.group == u'ducks')
        assert(x.empty == u'')
        assert(not hasattr(x, 'xyzzy'))

    def testNodeName(self):
        x = handyxml.xml(StringIO.StringIO("<mydata/>"))
        assert(x.nodeName == 'mydata')
        assert(x.localName == 'mydata')
        
    def testStringDucks(self):
        x = handyxml.xml(StringIO.StringIO(duckdata))
        doDuckAsserts(x)

    def testWhichParserIsUnderThere(self):
        """ Ensure that we really are using different parsers.
        """
        x = handyxml.xml(StringIO.StringIO("<mydata/>"))
        modname = ''
        if isinstance(x.node, types.InstanceType):
            modname = x.node.__class__.__module__
        else:
            modname = type(x.node).__module__

        if self.bDomlette:
            assert(modname == 'cDomlette')
        else:
            assert(modname == 'xml.dom.Element')

    def testEmpty(self):
        try:
            x = handyxml.xml(StringIO.StringIO(''))
            self.fail()
        except:
            assert(True)
            
    def testBadXml(self):
        try:
            x = handyxml.xml(StringIO.StringIO('this is not XML!'))
            self.fail()
        except:
            assert(True)

class ElementTests(BaseTestCase):
    def testChildElements(self):
        x = handyxml.xml(StringIO.StringIO("<root><a foo='bar'/><b/><!-- comment --><a/><c baz='quux'/></root>"))
        enames = [ e.nodeName for e in x.childElements ]
        assert(enames == ['a', 'b', 'a', 'c'])
        assert(x.childElements[0].foo == 'bar')
        assert(x.childElements[3].baz == 'quux')
        
class AssignmentTests(BaseTestCase):
    def testAssignment(self):
        x = handyxml.xml(StringIO.StringIO("<mydata foo='a' bar='b'/>"))
        assert(x.foo == 'a')
        assert(x.bar == 'b')
        assert(not hasattr(x, 'quux'))
        x.quux = 'c'
        assert(x.quux == 'c')

    def testAssignmentToXPathNode(self):
        root = handyxml.xml(StringIO.StringIO("<root><mydata foo='a' bar='b'/></root>"))
        x = handyxml.xpath(root, ".//mydata")[0]
        assert(x.foo == 'a')
        assert(x.bar == 'b')
        assert(not hasattr(x, 'quux'))
        x.quux = 'c'
        assert(x.quux == 'c')
        
    def testAssigningToChildren(self):
        xmldata = """
            <root>
                <child name='one'>
                    <gchild name='oneone'/>
                    <gchild name='onetwo'/>
                </child>
                <child name='two'>
                    <gchild name='twoone'/>
                    <gchild name='twotwo'/>
                </child>
            </root>
            """
        children = {}
        for c in handyxml.xpath(StringIO.StringIO(xmldata), ".//child"):
            c.fullName = "" + c.name + " full"
            children[c.fullName] = c
            for gc in c.gchild:
                gc.fullName = "" + gc.name + " full"
                
        for c in children.values():
            assert(c.fullName.endswith(" full"))
            for gc in c.gchild:
                assert(gc.fullName.endswith(" full"))
                
class DuckFileTests(BaseTestCase):
    dFiles = { 'ducks.xml': duckdata }

    def setUp(self):
        BaseTestCase.setUp(self)
        makeFiles(self.dFiles)

    def testFileDucks(self):
        x = handyxml.xml('ducks.xml')
        doDuckAsserts(x)

    def tearDown(self):
        BaseTestCase.tearDown(self)
        removeFiles(self.dFiles)

class XPathTests(BaseTestCase):
    xmldata = """
        <top>
            <child name='one' type='first'>
                <subchild name='two' type='animal'>
                    <ape/><bear/><cat/><dog/>
                </subchild>
                <subchild name='three'/>
            </child>
            <middle/>
            <child name='four'>
                <subchild name='five' type='food'>
                    <apple/><banana/><carrot/>
                </subchild>
            </child>
        </top>
        """

    def testXPath(self):
        x = handyxml.xml(StringIO.StringIO(self.xmldata))
        grandchildren = handyxml.xpath(x, '//subchild/*')
        assert(len(grandchildren) == 7)
        gcnames = [e.localName for e in grandchildren]
        assert(gcnames[2] == u'cat')
        assert(gcnames[6] == u'carrot')
        cattype = handyxml.xpath(x, '//cat/../@type')[0].value
        assert(cattype == u'animal')
        food2 = handyxml.xpath(x, '//*[@type="food"]/*[2]')[0]
        assert(food2.nodeName == u'banana')
        foodparent = handyxml.xpath(food2, '..')[0]
        assert(foodparent.name == u'five')
        
class SearchPathTests(BaseTestCase):
    dFiles = {
        'test_handyxml_data': {
            'ducks.xml': duckdata,
            }
        }
    
    def setUp(self):
        BaseTestCase.setUp(self)
        makeFiles(self.dFiles)
        self.savedHandyXmlPath = handyxml.path
        
    def testNotOnPath(self):
        # ducks.xml is in the sub directory, so we shouldn't find it.
        try:
            x = handyxml.xml('ducks.xml')
            self.fail()
        except:
            assert(True)

    def testOnPath(self):
        handyxml.path += ['test_handyxml_data']
        x = handyxml.xml('ducks.xml')
        doDuckAsserts(x)

    def tearDown(self):
        BaseTestCase.tearDown(self)
        removeFiles(self.dFiles)
        handyxml.path = self.savedHandyXmlPath

# Tests to write:
# Unicode filenames.
# Unicode data.
# Can we test not having the xml.xpath module available?

def suite():
    """ Create a test suite for this module. """
    
    # We need to do some magic stuff here.  We want to load up all the test
    # cases twice: once for each setting of the bDomlette flag.  So we need
    # to get an explicit module reference, and load the cases manually.
    mod = sys.modules[__name__]
    suite = unittest.TestSuite()

    global bDomlette
    bDomlette = False
    suite.addTest(unittest.findTestCases(mod))

    try:
        from Ft.Xml.Domlette import NonvalidatingReader
    except ImportError:
        pass
    else:
        bDomlette = True
        suite.addTest(unittest.findTestCases(mod))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())

# History:
# 20040605: Added AssignmentTests.
