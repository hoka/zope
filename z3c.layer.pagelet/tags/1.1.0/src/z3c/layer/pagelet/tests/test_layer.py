##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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
$Id: __init__.py 97 2007-03-29 22:58:27Z rineichen $
"""

import re
import unittest
from zope.testing import renormalizing
from zope.app.testing import functional

functional.defineLayer('TestLayer', 'ftesting.zcml')

checker = renormalizing.RENormalizing([
    (re.compile(r'httperror_seek_wrapper:', re.M), 'HTTPError:'),
    ])


def test_suite():
    suite = unittest.TestSuite()
    s = functional.FunctionalDocFileSuite('../README.txt', checker=checker)
    s.layer = TestLayer
    suite.addTest(s)
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
