##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
This file contains some tests of zope.app.versioncontrol to figure
out whether the existing implementation fits our needs.


"""
import unittest
import doctest

from zope.interface import implements
from zope.app.container.sample import SampleContainer
from zope.app.tests.placelesssetup import setUp, tearDown
from zope.app.tests import ztapi

from zope.app.tests.setup import buildSampleFolderTree


def buildSite(items=None) :
    """ Returns s small test site of original content objects:
    
        >>> folders = buildSampleFolderTree()
        >>> folders is not None
        True
    """

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))
if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
