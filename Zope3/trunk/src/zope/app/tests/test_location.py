##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Location support tests

$Id: test_location.py,v 1.2 2003/09/21 17:33:36 jim Exp $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite


def test_suite():
    return DocTestSuite('zope.app.location')

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
