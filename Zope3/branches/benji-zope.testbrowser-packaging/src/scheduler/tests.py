##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Tests for the Preferences System

$Id: tests.py 29143 2005-02-14 22:43:16Z srichter $
"""
import unittest
from zope.testing import doctest, doctestunit
from zope.app.testing import placelesssetup

def isSameTime(time1, time2, error=1):
    """Check whether the time is the same within a range +/- error."""
    if time1-error < time2 and time1+error > time2:
        return True
    return False

def setUp(test):
    placelesssetup.setUp(test)

def tearDown(test):
    placelesssetup.tearDown(test)
    # Let's remove all those delayed calls from the reactor
    from twisted.internet import reactor
    reactor._newTimedCalls = []
    

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt',
                             setUp=setUp, tearDown=tearDown,
                             globs={'pprint': doctestunit.pprint,
                                    'isSameTime': isSameTime},
                             optionflags=doctest.NORMALIZE_WHITESPACE),
        ))

if __name__ == '__main__':
    unittest.main(default='test_suite')
