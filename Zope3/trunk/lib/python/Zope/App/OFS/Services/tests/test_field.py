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
"""Tests for ComponentLocation field.

$Id: test_field.py,v 1.2 2002/12/19 20:38:26 jim Exp $
"""

from unittest import TestCase, TestSuite, main, makeSuite
from Zope.App.OFS.Services.ServiceManager.tests.PlacefulSetup \
     import PlacefulSetup
from Zope.App.Traversing import traverse
from Zope.Schema.Exceptions import ValidationError
from Interface import Interface
from Zope.App.OFS.Services.field import ComponentLocation

class I1(Interface):  pass

class C:
    __implements__ = I1

class D:
    pass

class Test(PlacefulSetup, TestCase):

    def test__validate(self):
        self.buildFolders()
        self.folder1.setObject('c', C())
        self.folder1.setObject('d', D())

        folder2 = traverse(self.rootFolder, 'folder2')

        field = ComponentLocation(type=I1)
        field = field.bind(folder2)

        field.validate(u'/folder1/c')

        self.assertRaises(ValidationError, field.validate, u'/folder1/d')
        self.assertRaises(ValidationError, field.validate, u'/folder1/e')

def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
