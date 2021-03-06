##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Component tests

$Id$
"""
import unittest
from zope.testing.doctestunit import DocFileSuite, DocTestSuite

__docformat__ = "reStructuredText"

def test_suite():
    return unittest.TestSuite([
        DocFileSuite('component.txt', package="Products.Five.component"),
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
