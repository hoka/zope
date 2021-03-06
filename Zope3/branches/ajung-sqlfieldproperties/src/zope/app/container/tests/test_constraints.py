##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Container constraint tests

$Id$
"""
import unittest
from zope.testing import doctest, module

def setUp(test):
    module.setUp(test, 'zope.app.container.constraints_txt')

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite('zope.app.container.constraints'),
        doctest.DocFileSuite('../constraints.txt',
                             setUp=setUp, tearDown=module.tearDown),
        ))

if __name__ == '__main__': unittest.main()
