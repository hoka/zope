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

import unittest

from zope.pagetemplate.tests import util
from zope.app.pagetemplate.tests.testpackage.content \
     import Content, PTComponent

# Wow, this is a lot of work. :(
from zope.app.tests.placelesssetup import PlacelessSetup
from zope.app.traversing.traverser import Traverser
from zope.app.interfaces.traversing import ITraverser
from zope.app.traversing.defaulttraversable import DefaultTraversable
from zope.app.interfaces.traversing import ITraversable
from zope.component.adapter import provideAdapter


class BindingTestCase(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        PlacelessSetup.setUp(self)
        provideAdapter(None, ITraverser, Traverser)
        provideAdapter(None, ITraversable, DefaultTraversable)

    def test_binding(self):
        comp = PTComponent(Content())
        self.assertEqual(comp.index(), "42\n")

def test_suite():
    return unittest.makeSuite(BindingTestCase)

if __name__=='__main__':
    unittest.main()
