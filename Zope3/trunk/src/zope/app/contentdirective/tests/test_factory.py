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
##############################################################################
""" Test handler for 'factory' subdirective of 'content' directive """

import unittest
import sys
import os
from cStringIO import StringIO

from zope.configuration.xmlconfig import xmlconfig, ZopeXMLConfigurationError
from zope.configuration.xmlconfig import XMLConfig
from zope.app.services.servicenames import Factories
from zope.app.tests.placelesssetup import PlacelessSetup
from zope.security.management import newSecurityManager, system_user

import zope.configuration
import zope.app.security
from zope.app.security.exceptions import UndefinedPermissionError

import zope.app.contentdirective
from zope.app.contentdirective.tests.exampleclass \
    import ExampleClass, IExample, IExampleContainer

def configfile(s):
    return StringIO("""<zopeConfigure
      xmlns='http://namespaces.zope.org/zope'>
      %s
      </zopeConfigure>
      """ % s)

class Test(PlacelessSetup, unittest.TestCase):
    def setUp(self):
        PlacelessSetup.setUp(self)
        newSecurityManager(system_user)
        XMLConfig('metameta.zcml', zope.configuration)()
        XMLConfig('meta.zcml', zope.app.contentdirective)()
        XMLConfig('meta.zcml', zope.app.security)()


    def testFactory(self):
        from zope.component import getService
        from zope.proxy.introspection import removeAllProxies
        f = configfile("""
<permission id="zope.Foo" title="Zope Foo Permission" />
<content class="zope.app.contentdirective.tests.exampleclass.ExampleClass">
    <factory
      id="Example"
      permission="zope.Foo"
      title="Example content"
      description="Example description"
       />
</content>
                       """)
        xmlconfig(f)
        obj = getService(None, Factories).createObject('Example')
        obj = removeAllProxies(obj)
        self.failUnless(isinstance(obj, ExampleClass))

    def testFactoryDefaultId(self):
        from zope.component import getService
        from zope.proxy.introspection import removeAllProxies
        f = configfile("""
<permission id="zope.Foo" title="Zope Foo Permission" />
<content class="zope.app.contentdirective.tests.exampleclass.ExampleClass">
    <factory
      permission="zope.Foo"
      title="Example content"
      description="Example description"
       />
</content>
                       """)
        xmlconfig(f)
        obj = getService(None, Factories).createObject(
            'zope.app.contentdirective.tests.exampleclass.ExampleClass')
        obj = removeAllProxies(obj)
        self.failUnless(isinstance(obj, ExampleClass))


def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
