##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
"""
Basic tests for Page Templates used in content-space.

$Id: testDTMLPage.py,v 1.1 2002/07/11 00:17:03 srichter Exp $
"""

import unittest

from Zope.App.OFS.Content.DTMLPage.DTMLPage import DTMLPage

# Wow, this is a lot of work. :(
from Zope.ComponentArchitecture.tests.PlacelessSetup import PlacelessSetup
from Zope.App.Traversing.Traverser import Traverser
from Zope.App.Traversing.ITraverser import ITraverser
from Zope.App.Traversing.DefaultTraversable import DefaultTraversable
from Zope.App.Traversing.ITraversable import ITraversable
from Zope.ComponentArchitecture.GlobalAdapterService import provideAdapter
from Zope.ContextWrapper import Wrapper
from Zope.Security.Checker import NamesChecker, defineChecker


class Data(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __getitem__(self, name):
        return getattr(self, name)
    
    
class DTMLPageTests(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        PlacelessSetup.setUp(self)
        provideAdapter(None, ITraverser, Traverser)
        provideAdapter(None, ITraversable, DefaultTraversable)
        defineChecker(Data, NamesChecker(['URL', 'name', '__getitem__']))

    def test(self):
        page = DTMLPage()
        page.setSource(
            '<html>'
            '<head><title><dtml-var title></title></head>'
            '<body>'
            '<a href="<dtml-var "REQUEST.URL[\'1\']">">'
            '<dtml-var name>'
            '</a></body></html>'
            )

        page = Wrapper(page, Data(name='zope'))

        out = page.render(Data(URL={'1': 'http://foo.com/'}),
                          title="Zope rules")
        out = ' '.join(out.split())
        

        self.assertEqual(
            out,
            '<html><head><title>Zope rules</title></head><body>'
            '<a href="http://foo.com/">'
            'zope'
            '</a></body></html>'
            )

def test_suite():
   return unittest.makeSuite(DTMLPageTests)

if __name__=='__main__':
   unittest.TextTestRunner().run(test_suite())
