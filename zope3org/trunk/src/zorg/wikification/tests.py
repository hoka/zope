##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id: tests.py 38895 2005-10-07 15:09:36Z dominikhuber $
"""
__docformat__ = 'restructuredtext'

import unittest

import zope.component
import zope.interface
import zope.app.testing.setup

from zope.testing import doctest, doctestunit
from zope.app import zapi
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.annotation.interfaces import IAnnotations
from zope.annotation.interfaces import IAnnotatable
from zope.annotation.attribute import AttributeAnnotations
from zope.dublincore.interfaces import IZopeDublinCore
from zope.dublincore.annotatableadapter import ZDCAnnotatableAdapter
from zope.traversing.interfaces import ITraversable, ITraverser
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.traversing.interfaces import IContainmentRoot
from zope.traversing.adapters import DefaultTraversable
from zope.location.traversing import LocationPhysicallyLocatable
from zope.traversing.adapters import RootPhysicallyLocatable
from zope.traversing.adapters import Traverser

from zope.app.container.interfaces import IContained
from zope.app.container.contained import NameChooser
from zope.app.container.interfaces import INameChooser
from zope.app.folder.interfaces import IFolder

from zope.app.folder import rootFolder
from zope.app.folder import Folder
from zope.app.file import File

from zorg.ajax.tests import sessionSetUp
from zorg.ajax.tests import TestUUIDGenerator
from zorg.edition.interfaces import IUUIDGenerator
from zorg.comment.testing import commentSetUp
from zorg.comment import IAttributeAnnotableComments
from zorg.wikification.browser.interfaces import ILinkProcessor
from zorg.wikification.browser.interfaces import IWikiPage
from zorg.wikification.browser.wikilink import WikiLinkProcessor


example1 = u"""<html>
    <body>
        <p>Wikifiable</p>
        <p>An <a href="target">existing file</a></p>
        <p>An <a href="folder">existing folder</a></p>
        <p>An <a href="index.html">existing page</a></p>
        <p>A <a href="newitem">new page</a></p>
        <p>A <a href="folder1/newitem">new page in a subfolder</a></p>
        <p>A [New Subject]</p>
        <p>An <a href="http://www.google.org">external absolute link</a></p>
        <p>An <a href="http://127.0.0.1/site/target">internal absolute link</a></p>
        <p>A <a href="http://127.0.0.1/site/newitem">new absolute link</a></p>
        <p>A [Topic] can occurr once.</p>
        <p>A [Topic] can occurr twice.</p>
        <p>A [Topic] can occurr thrice.</p>
    </body>
</html>"""

example2 = u"""<html>
    <body>
        <p>Wikifiable</p>
        <p>A [New Subject]</p>
    </body>
</html>"""

def buildSampleSite() :
    """ Build a sample structure
    
        root
            index.html          (with example1 as content)
            target              (an existing file)
            folder              (a sample folder)
                subfolder       (a sub folder)
            
        Usage :
        
        
        >>> site = buildSampleSite()
        >>> IZopeDublinCore(site).title
        u'Wiki site'

        
        
    """
    root = rootFolder()
    IZopeDublinCore(root).title = u'Wiki site'
    root.__name__ = u"site"
    root[u"target"] = File()
    folder = root[u"folder"] = Folder()
    filledsubfolder = folder[u"filledsubfolder"] = Folder()
    folder[u"emptysubfolder"] = Folder()
    index = root[u"index.html"] = File(example1, 'text/html')
    filledsubfolder[u"index.html"] = File(example2, 'text/html')
    
    IZopeDublinCore(index).title = u'Wiki page'
    return root    

    
def setUpWikification(test) :
   
    zope.app.testing.setup.placefulSetUp()
    
    from zope.app.testing import ztapi
    
    sessionSetUp(test) 
    commentSetUp(test)
    
    zope.interface.classImplements(File, IAnnotatable)
    zope.interface.classImplements(Folder, IAnnotatable)
    zope.interface.classImplements(File, IAttributeAnnotatable)
    zope.interface.classImplements(Folder, IAttributeAnnotatable)
    zope.interface.classImplements(File, IAttributeAnnotableComments)
    zope.interface.classImplements(Folder, IAttributeAnnotableComments)

    zope.component.provideAdapter(NameChooser, [IFolder], INameChooser)
    zope.component.provideAdapter(Traverser, [None], ITraverser)
    zope.component.provideAdapter(DefaultTraversable, [None], ITraversable)
    zope.component.provideAdapter(LocationPhysicallyLocatable,
                                            [None], IPhysicallyLocatable)
    zope.component.provideAdapter(RootPhysicallyLocatable,
                                            [IContainmentRoot], 
                                            IPhysicallyLocatable)

    zope.component.provideAdapter(ZDCAnnotatableAdapter,
                                            [IAnnotatable], 
                                            IZopeDublinCore)
 
    
    zope.component.provideAdapter(WikiLinkProcessor,
                                            [IWikiPage], 
                                            ILinkProcessor)
    
    zope.component.provideUtility(TestUUIDGenerator(), IUUIDGenerator)
   
                                            
def tearDownWikification(test) :
    zope.app.testing.setup.placefulTearDown()   



def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(setUp=setUpWikification, 
                                    tearDown=tearDownWikification),
                                    
        doctest.DocFileSuite("README.txt", 
                    setUp=setUpWikification, 
                    tearDown=tearDownWikification,
                    globs={'zapi': zope.app.zapi,
                           'pprint': doctestunit.pprint,
                           'TestRequest': zope.publisher.browser.TestRequest                                
                          },
                    optionflags=doctest.NORMALIZE_WHITESPACE+doctest.ELLIPSIS),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
