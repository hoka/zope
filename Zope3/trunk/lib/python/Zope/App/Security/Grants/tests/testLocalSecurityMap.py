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
#############################################################################
import unittest
from Interface.Verify import verifyClass
from Zope.App.Security.Grants.ILocalSecurityMap import ILocalSecurityMap
from Zope.App.Security.Grants.LocalSecurityMap import LocalSecurityMap

class TestLocalSecuritMap(unittest.TestCase):

    def testInterface(self):
        verifyClass(ILocalSecurityMap, LocalSecurityMap)


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(TestLocalSecuritMap)

if __name__ == '__main__':
    unittest.main()
