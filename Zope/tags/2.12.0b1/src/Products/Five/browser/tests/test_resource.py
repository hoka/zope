##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Test browser resources

$Id$
"""
import unittest

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    from Testing.ZopeTestCase import ZopeDocFileSuite
    from Testing.ZopeTestCase import installProduct
    installProduct('PythonScripts')
    return unittest.TestSuite((
            ZopeDocFileSuite('resource.txt',
                             package='Products.Five.browser.tests'),
            FunctionalDocFileSuite('resource_ftest.txt',
                                   package='Products.Five.browser.tests'),
            ))
