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
"""Test proper protection of inherited methods

Revision information:
$Id: testProtectSubClass.py,v 1.2 2002/06/10 23:28:16 jim Exp $
"""

from unittest import TestCase, TestSuite, main, makeSuite
from Zope.Testing.CleanUp import CleanUp # Base class w registry cleanup
from Zope.App.Security.protectClass import protectName
from Zope.App.Security.PermissionRegistry import permissionRegistry
from Zope.Security.Checker import selectChecker

class Test(CleanUp, TestCase):

    def testInherited(self):

        class B1(object):
            def g(self): return 'B1.g'

        class B2(object):
            def h(self): return 'B2.h'

        class S(B1, B2):
            pass

        permissionRegistry.definePermission('B1', '')
        permissionRegistry.definePermission('S', '')
        protectName(B1, 'g', 'B1')
        protectName(S, 'g', 'S')
        protectName(S, 'h', 'S')

        self.assertEqual(selectChecker(B1()).permission_id('g'), 'B1')
        self.assertEqual(selectChecker(B2()).permission_id('h'), None)
        self.assertEqual(selectChecker(S()).permission_id('g'), 'S')
        self.assertEqual(selectChecker(S()).permission_id('h'), 'S')

        self.assertEqual(S().g(), 'B1.g')
        self.assertEqual(S().h(), 'B2.h')
        

def test_suite():
    return TestSuite((
        makeSuite(Test),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
