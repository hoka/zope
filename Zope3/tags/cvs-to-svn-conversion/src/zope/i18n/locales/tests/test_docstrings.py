##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Tests for the ZCML Documentation Module

$Id: test_docstrings.py,v 1.1 2004/02/05 22:52:32 srichter Exp $
"""
import unittest
from zope.testing.doctestunit import DocTestSuite
from zope.i18n.locales.inheritance import AttributeInheritance, NoParentException

class LocaleInheritanceStub(AttributeInheritance):

    def __init__(self, nextLocale=None):
        self.__nextLocale__ = nextLocale

    def getInheritedSelf(self):
        if self.__nextLocale__ is None:
            raise NoParentException, 'No parent was specified.'
        return self.__nextLocale__


def test_suite():
    return unittest.TestSuite((
        DocTestSuite('zope.i18n.locales'),
        DocTestSuite('zope.i18n.locales.inheritance'),
        DocTestSuite('zope.i18n.locales.xmlfactory'),
        ))

if __name__ == '__main__':
    unittest.main()
