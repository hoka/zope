##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Component registry export / import support unit tests.
"""

import unittest
import Testing

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from OFS.Folder import Folder
from OFS.SimpleItem import SimpleItem
from Products.Five.component import enableSite
from Products.Five.component.interfaces import IObjectManagerSite
from zope.site.hooks import clearSite
from zope.site.hooks import setHooks
from zope.site.hooks import setSite
from zope.component import getMultiAdapter
from zope.component import getGlobalSiteManager
from zope.component import getSiteManager
from zope.component import handle
from zope.component import queryAdapter
from zope.component import queryUtility
from zope.component import subscribers
from zope.component.globalregistry import base
from zope.interface import implements
from zope.interface import Interface

from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import IComponentsHandlerBlacklist
from Products.GenericSetup.testing import BodyAdapterTestCase
from Products.GenericSetup.testing import DummySetupEnviron
from Products.GenericSetup.testing import ExportImportZCMLLayer
from Products.GenericSetup.tests.common import DummyImportContext

try:
    from five.localsitemanager.registry import PersistentComponents
except ImportError:
    # Avoid generating a spurious dependency
    PersistentComponents = None

def createComponentRegistry(context):
    enableSite(context, iface=IObjectManagerSite)

    components = PersistentComponents('++etc++site')
    components.__bases__ = (base,)
    components.__parent__ = aq_base(context)
    # Make sure calls to getSiteManager on me return myself
    # necessary because OFS.ObjectManager.getSiteManager expects _components
    components._components = components
    context.setSiteManager(components)

class IDummyInterface(Interface):
    """A dummy interface."""

    def verify():
        """Returns True."""

class IDummyInterface2(Interface):
    """A second dummy interface."""

    def verify():
        """Returns True."""

class DummyUtility(object):
    """A dummy utility."""

    implements(IDummyInterface)

    def verify(self):
        return True

class IAnotherDummyInterface(Interface):
    """A third dummy interface."""

    def inc():
        """Increments handle count"""

class IAnotherDummyInterface2(Interface):
    """A second dummy interface."""

    def verify():
        """Returns True."""

class DummyObject(object):
    """A dummy object to pass to the handler."""

    implements(IAnotherDummyInterface)

    handled = 0

    def inc(self):
        self.handled += 1

class DummyAdapter(object):
    """A dummy adapter."""

    implements(IAnotherDummyInterface2)

    def __init__(self, context):
        pass

    def verify(self):
        return True

def dummy_handler(context):
    """A dummy event handler."""
    
    context.inc()

class DummyTool(SimpleItem):
    """A dummy tool."""
    implements(IDummyInterface)

    id = 'dummy_tool'
    meta_type = 'dummy tool'
    security = ClassSecurityInfo()

    security.declarePublic('verify')
    def verify(self):
        return True

InitializeClass(DummyTool)


class DummyTool2(SimpleItem):
    """A second dummy tool."""
    implements(IDummyInterface2)

    id = 'dummy_tool2'
    meta_type = 'dummy tool2'
    security = ClassSecurityInfo()

    security.declarePublic('verify')
    def verify(self):
        return True

InitializeClass(DummyTool2)


class DummyBlacklist(object):
    """A blacklist."""

    implements(IComponentsHandlerBlacklist)

    def getExcludedInterfaces(self):
        return (IDummyInterface, )


_COMPONENTS_BODY = """\
<?xml version="1.0"?>
<componentregistry>
 <adapters>
  <adapter factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     for="zope.interface.Interface"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummyInterface2"/>
  <adapter name="foo"
     factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     for="zope.interface.Interface"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummyInterface2"/>
 </adapters>
 <subscribers>
  <subscriber
     factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     for="Products.GenericSetup.tests.test_components.IAnotherDummyInterface"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummyInterface2"/>
  <subscriber
     for="Products.GenericSetup.tests.test_components.IAnotherDummyInterface"
     handler="Products.GenericSetup.tests.test_components.dummy_handler"/>
 </subscribers>
 <utilities>
  <utility factory="Products.GenericSetup.tests.test_components.DummyUtility"
     id="dummy_utility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"/>
  <utility name="dummy tool name"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"
     object="dummy_tool"/>
  <utility name="dummy tool name2"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface2"
     object="dummy_tool2"/>
  <utility name="foo"
     factory="Products.GenericSetup.tests.test_components.DummyUtility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface2"/>
 </utilities>
</componentregistry>
"""

_REMOVE_IMPORT = """\
<?xml version="1.0"?>
<componentregistry>
 <adapters>
  <adapter factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummyInterface2"
     for="*" remove="True"/>
 </adapters>
 <subscribers>
  <subscriber
     factory="Products.GenericSetup.tests.test_components.DummyAdapter"
     for="Products.GenericSetup.tests.test_components.IAnotherDummyInterface"
     provides="Products.GenericSetup.tests.test_components.IAnotherDummyInterface2"
     remove="True"/>
  <subscriber
     for="Products.GenericSetup.tests.test_components.IAnotherDummyInterface"
     handler="Products.GenericSetup.tests.test_components.dummy_handler"
     remove="True"/>
 </subscribers>
 <utilities>
  <utility id="dummy_utility"
     factory="Products.GenericSetup.tests.test_components.DummyUtility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"
     remove="True"/>
  <utility name="dummy tool name"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface"
     object="dummy_tool" remove="True"/>
  <utility name="foo"
     factory="Products.GenericSetup.tests.test_components.DummyUtility"
     interface="Products.GenericSetup.tests.test_components.IDummyInterface2"
     remove="True"/>
 </utilities>
</componentregistry>
"""


class ComponentRegistryXMLAdapterTests(BodyAdapterTestCase, unittest.TestCase):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from Products.GenericSetup.components import \
            ComponentRegistryXMLAdapter
        return ComponentRegistryXMLAdapter

    def _populate(self, obj):
        obj.registerAdapter(DummyAdapter, required=(None,))
        obj.registerAdapter(DummyAdapter, required=(None,), name=u'foo')

        obj.registerSubscriptionAdapter(DummyAdapter, required=(IAnotherDummyInterface,))
        obj.registerHandler(dummy_handler, required=(IAnotherDummyInterface,))

        util = DummyUtility()
        name = 'dummy_utility'
        util.__name__ = name
        util.__parent__ = aq_base(obj)
        obj._setObject(name, aq_base(util),
            set_owner=False, suppress_events=True)
        obj.registerUtility(aq_base(obj[name]), IDummyInterface)

        util = DummyUtility()
        name = 'Products.GenericSetup.tests.test_components.IDummyInterface2-foo'
        util.__name__ = name
        util.__parent__ = aq_base(obj)
        obj._setObject(name, aq_base(util),
            set_owner=False, suppress_events=True)
        obj.registerUtility(aq_base(obj[name]), IDummyInterface2, name=u'foo')

        tool = aq_base(obj.aq_parent['dummy_tool'])
        obj.registerUtility(tool, IDummyInterface, name=u'dummy tool name')

        tool2 = aq_base(obj.aq_parent['dummy_tool2'])
        obj.registerUtility(tool2, IDummyInterface2, name=u'dummy tool name2')

    def _verifyImport(self, obj):
        adapted = queryAdapter(object(), IAnotherDummyInterface2)
        self.failUnless(IAnotherDummyInterface2.providedBy(adapted))
        self.failUnless(adapted.verify())

        adapted = queryAdapter(object(), IAnotherDummyInterface2, name=u'foo')
        self.failUnless(IAnotherDummyInterface2.providedBy(adapted))
        self.failUnless(adapted.verify())

        dummy = DummyObject()
        results = [adap.verify() for adap in subscribers([dummy], IAnotherDummyInterface2)]
        self.assertEquals(results, [True])

        dummy = DummyObject()
        handle(dummy)
        self.assertEquals(dummy.handled, 1)

        util = queryUtility(IDummyInterface2, name=u'foo')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        self.failUnless(util.__parent__ == obj)
        name = 'Products.GenericSetup.tests.test_components.IDummyInterface2-foo'
        self.assertEquals(util.__name__, name)
        self.failUnless(name in obj.objectIds())

        util = queryUtility(IDummyInterface)
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        self.failUnless(util.__parent__ == obj)
        name = 'dummy_utility'
        self.assertEquals(util.__name__, name)
        self.failUnless(name in obj.objectIds())

        util = queryUtility(IDummyInterface, name='dummy tool name')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        self.assertEqual(util.meta_type, 'dummy tool')

        # make sure we can get the tool by normal means
        tool = getattr(obj.aq_parent, 'dummy_tool')
        self.assertEqual(tool.meta_type, 'dummy tool')
        self.assertEquals(repr(aq_base(util)), repr(aq_base(tool)))

        util = queryUtility(IDummyInterface2, name='dummy tool name2')
        self.failUnless(IDummyInterface2.providedBy(util))
        self.failUnless(util.verify())
        self.assertEqual(util.meta_type, 'dummy tool2')

        # make sure we can get the tool by normal means
        tool = getattr(obj.aq_parent, 'dummy_tool2')
        self.assertEqual(tool.meta_type, 'dummy tool2')
        self.assertEquals(repr(aq_base(util)), repr(aq_base(tool)))

    def test_blacklist_get(self):
        obj = self._obj
        self._populate(obj)

        # Register our blacklist
        gsm = getGlobalSiteManager()
        gsm.registerUtility(DummyBlacklist(),
                            IComponentsHandlerBlacklist,
                            name=u'dummy')

        context = DummySetupEnviron()
        adapted = getMultiAdapter((obj, context), IBody)

        body = adapted.body
        self.failIf('IComponentsHandlerBlacklist' in body)
        self.failIf('test_components.IDummyInterface"' in body)

    def test_blacklist_set(self):
        obj = self._obj
        # Register our blacklist
        gsm = getGlobalSiteManager()
        gsm.registerUtility(DummyBlacklist(),
                            IComponentsHandlerBlacklist,
                            name=u'dummy')

        context = DummySetupEnviron()
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name=u'foo')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        util = queryUtility(IDummyInterface)
        self.failUnless(util is None)

        # now in update mode
        context._should_purge = False
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name=u'foo')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        util = queryUtility(IDummyInterface)
        self.failUnless(util is None)

        # and again in update mode
        adapted = getMultiAdapter((obj, context), IBody)
        adapted.body = self._BODY

        util = queryUtility(IDummyInterface2, name=u'foo')
        self.failUnless(IDummyInterface.providedBy(util))
        self.failUnless(util.verify())
        util = queryUtility(IDummyInterface)
        self.failUnless(util is None)

    def test_remove_components(self):
        from Products.GenericSetup.components import importComponentRegistry

        obj = self._obj
        self._populate(obj)
        self._verifyImport(obj)

        context = DummyImportContext(obj, False)
        context._files['componentregistry.xml'] = _REMOVE_IMPORT
        importComponentRegistry(context)

        adapted = queryAdapter(object(), IAnotherDummyInterface2)
        self.failUnless(adapted is None)

        # This one should still exist
        adapted = queryAdapter(object(), IAnotherDummyInterface2, name=u'foo')
        self.failIf(adapted is None)

        dummy = DummyObject()
        results = [adap.verify() for adap in subscribers([dummy], IAnotherDummyInterface2)]
        self.assertEquals(results, [])

        dummy = DummyObject()
        handle(dummy)
        self.assertEquals(dummy.handled, 0)

        util = queryUtility(IDummyInterface2, name=u'foo')
        name = 'Products.GenericSetup.tests.test_components.IDummyInterface2-foo'
        self.failUnless(util is None)
        self.failIf(name in obj.objectIds())

        util = queryUtility(IDummyInterface)
        self.failUnless(util is None)
        self.failIf('dummy_utility' in obj.objectIds())

        util = queryUtility(IDummyInterface, name='dummy tool name')
        self.failUnless(util is None)

        # This one should still exist
        util = queryUtility(IDummyInterface2, name='dummy tool name2')
        self.failIf(util is None)

    def setUp(self):
        # Create and enable a local component registry
        site = Folder()
        createComponentRegistry(site)
        setHooks()
        setSite(site)
        sm = getSiteManager()

        tool = DummyTool()
        site._setObject(tool.id, tool)

        tool2 = DummyTool2()
        site._setObject(tool2.id, tool2)

        self._obj = sm
        self._BODY = _COMPONENTS_BODY

    def tearDown(self):
        clearSite()
        # Make sure our global utility is gone again
        gsm = getGlobalSiteManager()
        gsm.unregisterUtility(provided=IComponentsHandlerBlacklist,
                              name=u'dummy')


if PersistentComponents is not None:
    def test_suite():
        # reimport to make sure tests are run from Products
        from Products.GenericSetup.tests.test_components \
                import ComponentRegistryXMLAdapterTests

        return unittest.TestSuite((
            unittest.makeSuite(ComponentRegistryXMLAdapterTests),
            ))
else:
    def test_suite():
        return unittest.TestSuite()
