#############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
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

import unittest
import gocept.selenium.zope2
from gocept.selenium.zope2 import testing
import gocept.selenium.tests.isolation
import Products.PloneTestCase.PloneTestCase

from Products.PloneTestCase.layer import PloneSiteLayer

Products.PloneTestCase.PloneTestCase.setupPloneSite(id='plone')


class Plone4Tests(gocept.selenium.tests.isolation.IsolationTests,
                 gocept.selenium.plone.TestCase):

    layer = gocept.selenium.zope2.Layer(PloneSiteLayer, testing.isolationLayer)

    def test_plone_login(self):
        sel = self.selenium
        sel.open('/plone')
        sel.click('link=Log in')
        sel.waitForElementPresent('name=__ac_name')
        sel.type('name=__ac_name', 'portal_owner')
        sel.type('name=__ac_password', 'secret')
        sel.click('name=submit')
        sel.waitForPageToLoad()
        sel.assertTextPresent('portal_owner')


def test_suite():
    return unittest.makeSuite(Plone4Tests)
