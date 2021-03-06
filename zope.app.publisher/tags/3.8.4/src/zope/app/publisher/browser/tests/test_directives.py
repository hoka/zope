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
"""'browser' namespace directive tests

$Id$
"""

import sys
import os
import unittest
from cStringIO import StringIO

from zope import component
from zope.interface import Interface, implements, directlyProvides, providedBy

import zope.security.management
from zope.configuration.xmlconfig import xmlconfig, XMLConfig
from zope.configuration.exceptions import ConfigurationError
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces import IDefaultViewName
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.interfaces.browser import IBrowserSkinType, IDefaultSkin
from zope.security.proxy import removeSecurityProxy, ProxyFactory
from zope.security.permission import Permission
from zope.security.interfaces import IPermission
from zope.testing.doctestunit import DocTestSuite
from zope.traversing.adapters import DefaultTraversable
from zope.traversing.interfaces import ITraversable

import zope.publisher.defaultview
import zope.app.publisher.browser
from zope.component.testfiles.views import IC, V1, VZMI, R1, IV
from zope.app.publisher.browser.fileresource import FileResource
from zope.app.publisher.browser.i18nfileresource import I18nFileResource
from zope.app.publisher.browser.menu import getFirstMenuItem
from zope.app.publisher.interfaces.browser import IMenuItemType, IBrowserMenu
from zope.app.testing import placelesssetup, ztapi

tests_path = os.path.join(
    os.path.dirname(zope.app.publisher.browser.__file__),
    'tests')

template = """<configure
   xmlns='http://namespaces.zope.org/zope'
   xmlns:browser='http://namespaces.zope.org/browser'
   i18n_domain='zope'>
   %s
   </configure>"""


request = TestRequest()

class V2(V1, object):

    def action(self):
        return self.action2()

    def action2(self):
        return "done"

class VT(V1, object):
    def publishTraverse(self, request, name):
        try:
            return int(name)
        except:
            return super(VT, self).publishTraverse(request, name)

class Ob(object):
    implements(IC)

ob = Ob()

class NCV(object):
    "non callable view"

    def __init__(self, context, request):
        pass

class CV(NCV):
    "callable view"
    def __call__(self):
        pass


class C_w_implements(NCV):
    implements(Interface)

    def index(self):
        return self

class ITestMenu(Interface):
    """Test menu."""

directlyProvides(ITestMenu, IMenuItemType)


class ITestLayer(IBrowserRequest):
    """Test Layer."""

class ITestSkin(ITestLayer):
    """Test Skin."""


class MyResource(object):

    def __init__(self, request):
        self.request = request


class Test(placelesssetup.PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(Test, self).setUp()
        XMLConfig('meta.zcml', zope.app.publisher.browser)()
        ztapi.provideAdapter(None, ITraversable, DefaultTraversable)

    def tearDown(self):
        if 'test_menu' in dir(sys.modules['zope.app.menus']):
            delattr(sys.modules['zope.app.menus'], 'test_menu')
        super(Test, self).tearDown()

    def testPage(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template % (
            '''
            <browser:page
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                />
            '''
            )))

        v = component.queryMultiAdapter((ob, request), name='test')
        self.assert_(issubclass(v.__class__, V1))

    def testMenuOverride(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')

        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:page
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                template="%s"
                menu="test_menu"
                title="Test View"
                />
            ''' % testtemplate
            )))
        menu1 = component.getUtility(IBrowserMenu, 'test_menu')
        menuItem1 = getFirstMenuItem('test_menu', ob, TestRequest())
        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu"
                class="zope.app.publisher.browser.tests.support.M1" />
            '''
            )))
        menu2 = component.getUtility(IBrowserMenu, 'test_menu')
        menuItem2 = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertNotEqual(menu1, menu2)
        self.assertEqual(menuItem1, menuItem2)

    def testPageWithClassWithMenu(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')


        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:page
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                template="%s"
                menu="test_menu"
                title="Test View"
                />
            ''' % testtemplate
            )))
        menuItem = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertEqual(menuItem["title"], "Test View")
        self.assertEqual(menuItem["action"], "@@test")
        v = component.queryMultiAdapter((ob, request), name='test')
        self.assertEqual(v(), "<html><body><p>test</p></body></html>\n")


    def testPageWithTemplateWithMenu(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')

        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu"/>
            <browser:page
                name="test"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                template="%s"
                menu="test_menu"
                title="Test View"
                />
            ''' % testtemplate
            )))

        menuItem = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertEqual(menuItem["title"], "Test View")
        self.assertEqual(menuItem["action"], "@@test")
        v = component.queryMultiAdapter((ob, request), name='test')
        self.assertEqual(v(), "<html><body><p>test</p></body></html>\n")


    def testPageInPagesWithTemplateWithMenu(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')

        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:pages
                for="zope.component.testfiles.views.IC"
                permission="zope.Public">
              <browser:page
                  name="test"
                  template="%s"
                  menu="test_menu"
                  title="Test View"
                  />
            </browser:pages>
            ''' % testtemplate
            )))

        menuItem = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertEqual(menuItem["title"], "Test View")
        self.assertEqual(menuItem["action"], "@@test")
        v = component.queryMultiAdapter((ob, request), name='test')
        self.assertEqual(v(), "<html><body><p>test</p></body></html>\n")


    def testPageInPagesWithClassWithMenu(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        testtemplate = os.path.join(tests_path, 'testfiles', 'test.pt')

        xmlconfig(StringIO(template % (
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:pages
                for="zope.component.testfiles.views.IC"
                class="zope.component.testfiles.views.V1"
                permission="zope.Public">
              <browser:page
                  name="test"
                  template="%s"
                  menu="test_menu"
                  title="Test View"
                  />
            </browser:pages>
            ''' % testtemplate
            )))

        menuItem = getFirstMenuItem('test_menu', ob, TestRequest())
        self.assertEqual(menuItem["title"], "Test View")
        self.assertEqual(menuItem["action"], "@@test")
        v = component.queryMultiAdapter((ob, request), name='test')
        self.assertEqual(v(), "<html><body><p>test</p></body></html>\n")

    def testDefaultView(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), IDefaultViewName),
            None)

        xmlconfig(StringIO(template % (
            '''
            <browser:defaultView
                name="test"
                for="zope.component.testfiles.views.IC" />
            '''
            )))

        self.assertEqual(
            zope.publisher.defaultview.getDefaultViewName(ob, request),
            'test')

    def testDefaultViewWithLayer(self):
        class FakeRequest(TestRequest):
            implements(ITestLayer)
        request2 = FakeRequest()

        self.assertEqual(
            component.queryMultiAdapter((ob, request2), IDefaultViewName),
            None)

        xmlconfig(StringIO(template % (
            '''
            <browser:defaultView
                name="test"
                for="zope.component.testfiles.views.IC" />

            <browser:defaultView
                name="test2"
                for="zope.component.testfiles.views.IC"
                layer="
                  zope.app.publisher.browser.tests.test_directives.ITestLayer"
                />
            '''
            )))

        self.assertEqual(
            zope.publisher.defaultview.getDefaultViewName(ob, request2),
            'test2')
        self.assertEqual(
            zope.publisher.defaultview.getDefaultViewName(ob, request),
            'test')

    def testDefaultViewForClass(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), IDefaultViewName),
            None)

        xmlconfig(StringIO(template % (
            '''
            <browser:defaultView
                for="zope.app.publisher.browser.tests.test_directives.Ob"
                name="test"
                />
            '''
            )))

        self.assertEqual(
            zope.publisher.defaultview.getDefaultViewName(ob, request),
            'test')


    def testSkinResource(self):
        self.assertEqual(
            component.queryAdapter(Request(IV), name='test'), None)

        xmlconfig(StringIO(template % (
            '''
            <browser:resource
                name="test"
                factory="zope.component.testfiles.views.RZMI"
                layer="
                  zope.app.publisher.browser.tests.test_directives.ITestLayer"
                />
            <browser:resource
                name="test"
                factory="zope.component.testfiles.views.R1"
                />
            '''
            )))

        self.assertEqual(
            component.queryAdapter(request, name='test').__class__, R1)
        self.assertEqual(
            component.queryAdapter(
                TestRequest(skin=ITestSkin), name='test').__class__,
            RZMI)

    def testDefaultSkin(self):
        request = TestRequest()
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        XMLConfig('meta.zcml', zope.component)()
        xmlconfig(StringIO(template % (
            '''
            <interface
                interface="
                  zope.app.publisher.browser.tests.test_directives.ITestSkin"
                type="zope.publisher.interfaces.browser.IBrowserSkinType"
                name="Test Skin"
                />
            <browser:defaultSkin name="Test Skin" />
            <browser:page
                name="test"
                class="zope.component.testfiles.views.VZMI"
                layer="
                  zope.app.publisher.browser.tests.test_directives.ITestLayer"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                />
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                />
            '''
            )))

        # Simulate Zope Publication behavior in beforeTraversal()
        adapters = component.getSiteManager().adapters
        skin = adapters.lookup((providedBy(request),), IDefaultSkin, '')
        directlyProvides(request, skin)

        v = component.queryMultiAdapter((ob, request), name='test')
        self.assert_(issubclass(v.__class__, VZMI))

    def testSkinPage(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template % (
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.VZMI"
                layer="
                  zope.app.publisher.browser.tests.test_directives.ITestLayer"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                />
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                />
            '''
            )))

        v = component.queryMultiAdapter((ob, request), name='test')
        self.assert_(issubclass(v.__class__, V1))
        v = component.queryMultiAdapter(
            (ob, TestRequest(skin=ITestSkin)), name='test')
        self.assert_(issubclass(v.__class__, VZMI))

    def testI18nResource(self):
        self.assertEqual(component.queryAdapter(request, name='test'), None)

        path1 = os.path.join(tests_path, 'testfiles', 'test.pt')
        path2 = os.path.join(tests_path, 'testfiles', 'test2.pt')

        xmlconfig(StringIO(template % (
            '''
            <browser:i18n-resource name="test" defaultLanguage="fr">
              <browser:translation language="en" file="%s" />
              <browser:translation language="fr" file="%s" />
            </browser:i18n-resource>
            ''' % (path1, path2)
            )))

        v = component.getAdapter(request, name='test')
        self.assertEqual(
            component.queryAdapter(request, name='test').__class__,
            I18nFileResource)
        self.assertEqual(v._testData('en'), open(path1, 'rb').read())
        self.assertEqual(v._testData('fr'), open(path2, 'rb').read())

        # translation must be provided for the default language
        config = StringIO(template % (
            '''
            <browser:i18n-resource name="test" defaultLanguage="fr">
              <browser:translation language="en" file="%s" />
              <browser:translation language="lt" file="%s" />
            </browser:i18n-resource>
            ''' % (path1, path2)
            ))
        self.assertRaises(ConfigurationError, xmlconfig, config)

        # files and images can't be mixed
        config = StringIO(template % (
            '''
            <browser:i18n-resource name="test" defaultLanguage="fr">
              <browser:translation language="en" file="%s" />
              <browser:translation language="fr" image="%s" />
            </browser:i18n-resource>
            ''' % (path1, path2)
            ))
        self.assertRaises(ConfigurationError, xmlconfig, config)

    def testInterfaceProtectedPage(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                attribute="index"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                allowed_interface="zope.component.testfiles.views.IV"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        v = ProxyFactory(v)
        self.assertEqual(v.index(), 'V1 here')
        self.assertRaises(Exception, getattr, v, 'action')

    def testAttributeProtectedPage(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page name="test"
                class="zope.app.publisher.browser.tests.test_directives.V2"
                for="zope.component.testfiles.views.IC"
                attribute="action"
                permission="zope.Public"
                allowed_attributes="action2"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        v = ProxyFactory(v)
        self.assertEqual(v.action(), 'done')
        self.assertEqual(v.action2(), 'done')
        self.assertRaises(Exception, getattr, v, 'index')

    def testAttributeProtectedView(self):
        xmlconfig(StringIO(template %
            '''
            <browser:view name="test"
                class="zope.app.publisher.browser.tests.test_directives.V2"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                allowed_attributes="action2"
                >
              <browser:page name="index.html" attribute="action" />
           </browser:view>
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        v = ProxyFactory(v)
        page = v.publishTraverse(request, 'index.html')
        self.assertEqual(page(), 'done')
        self.assertEqual(v.action2(), 'done')
        self.assertRaises(Exception, getattr, page, 'index')

    def testInterfaceAndAttributeProtectedPage(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                attribute="index"
                allowed_attributes="action"
                allowed_interface="zope.component.testfiles.views.IV"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def testDuplicatedInterfaceAndAttributeProtectedPage(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                attribute="index"
                permission="zope.Public"
                allowed_attributes="action index"
                allowed_interface="zope.component.testfiles.views.IV"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        self.assertEqual(v.index(), 'V1 here')
        self.assertEqual(v.action(), 'done')

    def test_class_w_implements(self):
        xmlconfig(StringIO(template %
            '''
            <browser:page
                name="test"
                class="
             zope.app.publisher.browser.tests.test_directives.C_w_implements"
                for="zope.component.testfiles.views.IC"
                attribute="index"
                permission="zope.Public"
                />
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='test')
        self.assertEqual(v.index(), v)
        self.assert_(IBrowserPublisher.providedBy(v))

    def testIncompleteProtectedPageNoPermission(self):
        self.assertRaises(
            ConfigurationError,
            xmlconfig,
            StringIO(template %
            '''
            <browser:page name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                attribute="index"
                allowed_attributes="action index"
                />
            '''
            ))


    def testPageViews(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        test3 = os.path.join(tests_path, 'testfiles', 'test3.pt')

        xmlconfig(StringIO(template %
            '''
            <browser:pages
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
              <browser:page name="test.html" template="%s" />
            </browser:pages>
            ''' % test3
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v(), 'V1 here')
        v = component.getMultiAdapter((ob, request), name='action.html')
        self.assertEqual(v(), 'done')
        v = component.getMultiAdapter((ob, request), name='test.html')
        self.assertEqual(str(v()), '<html><body><p>done</p></body></html>\n')

    def testNamedViewPageViewsCustomTraversr(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.app.publisher.browser.tests.test_directives.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
            </browser:view>
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(view.browserDefault(request)[1], (u'index.html', ))


        v = view.publishTraverse(request, 'index.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'V1 here')
        v = view.publishTraverse(request, 'action.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'done')


    def testNamedViewNoPagesForCallable(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.app.publisher.browser.tests.test_directives.CV"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                />
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(view.browserDefault(request), (view, ()))

    def testNamedViewNoPagesForNonCallable(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.app.publisher.browser.tests.test_directives.NCV"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                />
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(getattr(view, 'browserDefault', None), None)

    def testNamedViewPageViewsNoDefault(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        test3 = os.path.join(tests_path, 'testfiles', 'test3.pt')

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
              <browser:page name="test.html" template="%s" />
            </browser:view>
            ''' % test3
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(view.browserDefault(request)[1], (u'index.html', ))


        v = view.publishTraverse(request, 'index.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'V1 here')
        v = view.publishTraverse(request, 'action.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'done')
        v = view.publishTraverse(request, 'test.html')
        v = removeSecurityProxy(v)
        self.assertEqual(str(v()), '<html><body><p>done</p></body></html>\n')

    def testNamedViewPageViewsWithDefault(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)
        test3 = os.path.join(tests_path, 'testfiles', 'test3.pt')

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:defaultPage name="test.html" />
              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
              <browser:page name="test.html" template="%s" />
            </browser:view>
            ''' % test3
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        self.assertEqual(view.browserDefault(request)[1], (u'test.html', ))


        v = view.publishTraverse(request, 'index.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'V1 here')
        v = view.publishTraverse(request, 'action.html')
        v = removeSecurityProxy(v)
        self.assertEqual(v(), 'done')
        v = view.publishTraverse(request, 'test.html')
        v = removeSecurityProxy(v)
        self.assertEqual(str(v()), '<html><body><p>done</p></body></html>\n')

    def testTraversalOfPageForView(self):
        """Tests proper traversal of a page defined for a view."""

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public" />

            <browser:page name="index.html"
                for="zope.component.testfiles.views.IV"
                class="zope.app.publisher.browser.tests.test_directives.CV"
                permission="zope.Public" />
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        view.publishTraverse(request, 'index.html')

    def testTraversalOfPageForViewWithPublishTraverse(self):
        """Tests proper traversal of a page defined for a view.

        This test is different from testTraversalOfPageForView in that it
        tests the behavior on a view that has a publishTraverse method --
        the implementation of the lookup is slightly different in such a
        case.
        """
        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.app.publisher.browser.tests.test_directives.VT"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public" />

            <browser:page name="index.html"
                for="zope.component.testfiles.views.IV"
                class="zope.app.publisher.browser.tests.test_directives.CV"
                permission="zope.Public" />
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        view = removeSecurityProxy(view)
        view.publishTraverse(request, 'index.html')

    def testProtectedPageViews(self):
        ztapi.provideUtility(IPermission, Permission('p', 'P'), 'p')

        request = TestRequest()
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <include package="zope.app.security" file="meta.zcml" />

            <permission id="zope.TestPermission" title="Test permission" />

            <browser:pages
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.TestPermission"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
            </browser:pages>
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        v = ProxyFactory(v)
        zope.security.management.getInteraction().add(request)
        self.assertRaises(Exception, v)
        v = component.getMultiAdapter((ob, request), name='action.html')
        v = ProxyFactory(v)
        self.assertRaises(Exception, v)

    def testProtectedNamedViewPageViews(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <include package="zope.app.security" file="meta.zcml" />

            <permission id="zope.TestPermission" title="Test permission" />

            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >

              <browser:page name="index.html" attribute="index" />
              <browser:page name="action.html" attribute="action" />
            </browser:view>
            '''
            ))

        view = component.getMultiAdapter((ob, request), name='test')
        self.assertEqual(view.browserDefault(request)[1], (u'index.html', ))

        v = view.publishTraverse(request, 'index.html')
        self.assertEqual(v(), 'V1 here')

    def testSkinnedPageView(self):
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:pages
                for="*"
                class="zope.component.testfiles.views.V1"
                permission="zope.Public"
                >
              <browser:page name="index.html" attribute="index" />
            </browser:pages>

            <browser:pages
                for="*"
                class="zope.component.testfiles.views.V1"
                layer="
                  zope.app.publisher.browser.tests.test_directives.ITestLayer"
                permission="zope.Public"
                >
              <browser:page name="index.html" attribute="action" />
            </browser:pages>
            '''
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v(), 'V1 here')
        v = component.getMultiAdapter((ob, TestRequest(skin=ITestSkin)),
                                 name='index.html')
        self.assertEqual(v(), 'done')

    def testFactory(self):
        self.assertEqual(
            component.queryAdapter(request, name='index.html'), None)

        xmlconfig(StringIO(template %
            '''
            <browser:resource
                name="index.html"
                factory="
                  zope.app.publisher.browser.tests.test_directives.MyResource"
                />
            '''
            ))

        r = component.getAdapter(request, name='index.html')
        self.assertEquals(r.__class__, MyResource)
        r = ProxyFactory(r)
        self.assertEqual(r.__name__, "index.html")

    def testFile(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')

        self.assertEqual(component.queryAdapter(request, name='test'), None)

        xmlconfig(StringIO(template %
            '''
            <browser:resource
                name="index.html"
                file="%s"
                />
            ''' % path
            ))

        r = component.getAdapter(request, name='index.html')
        self.assertEquals(r.__class__, FileResource)
        r = ProxyFactory(r)
        self.assertEqual(r.__name__, "index.html")

        # Make sure we can access available attrs and not others
        for n in ('GET', 'HEAD', 'publishTraverse', 'request', '__call__'):
            getattr(r, n)
        self.assertEqual(r.__name__, "index.html")

        self.assertRaises(Exception, getattr, r, '_testData')

        r = removeSecurityProxy(r)
        self.assert_(r.__class__ is FileResource)
        self.assertEqual(r._testData(), open(path, 'rb').read())


    def testSkinResource(self):
        self.assertEqual(component.queryAdapter(request, name='test'), None)

        path = os.path.join(tests_path, 'testfiles', 'test.pt')
        xmlconfig(StringIO(template % (
            '''
            <browser:resource
                name="test"
                file="%s"
                layer="
                  zope.app.publisher.browser.tests.test_directives.ITestLayer"
                />
            ''' % path
            )))

        self.assertEqual(component.queryAdapter(request, name='test'), None)

        r = component.getAdapter(TestRequest(skin=ITestSkin), name='test')
        r = removeSecurityProxy(r)
        self.assertEqual(r._testData(), open(path, 'rb').read())

    def test_template_page(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')

        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='index.html'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:page
                name="index.html"
                template="%s"
                permission="zope.Public"
                for="zope.component.testfiles.views.IC" />
            ''' % path
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v().strip(), '<html><body><p>test</p></body></html>')

    def test_page_menu_within_different_layers(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='index.html'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:menu
                id="test_menu"
                title="Test menu"
                interface="zope.app.publisher.browser.tests.test_directives.ITestMenu"/>

            <browser:page
                name="index.html"
                permission="zope.Public"
                for="zope.component.testfiles.views.IC"
                template="%s"
                menu="test_menu" title="Index"/>

            <browser:page
                name="index.html"
                permission="zope.Public"
                for="zope.component.testfiles.views.IC"
                menu="test_menu" title="Index"
                template="%s"
                layer="zope.app.publisher.browser.tests.test_directives.ITestLayer"/>
            ''' % (path, path)
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v().strip(), '<html><body><p>test</p></body></html>')

    def testtemplateWClass(self):
        path = os.path.join(tests_path, 'testfiles', 'test2.pt')

        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='index.html'),
            None)

        xmlconfig(StringIO(template %
            '''
            <browser:page
                name="index.html"
                template="%s"
                permission="zope.Public"
          class="zope.app.publisher.browser.tests.templateclass.templateclass"
                for="zope.component.testfiles.views.IC" />
            ''' % path
            ))

        v = component.getMultiAdapter((ob, request), name='index.html')
        self.assertEqual(v().strip(), '<html><body><p>42</p></body></html>')

    def testProtectedtemplate(self):

        path = os.path.join(tests_path, 'testfiles', 'test.pt')

        request = TestRequest()
        self.assertEqual(
            component.queryMultiAdapter((ob, request), name='test'),
            None)

        xmlconfig(StringIO(template %
            '''
            <include package="zope.app.security" file="meta.zcml" />

            <permission id="zope.TestPermission" title="Test permission" />

            <browser:page
                name="xxx.html"
                template="%s"
                permission="zope.TestPermission"
                for="zope.component.testfiles.views.IC" />
            ''' % path
            ))

        xmlconfig(StringIO(template %
            '''
            <browser:page
                name="index.html"
                template="%s"
                permission="zope.Public"
                for="zope.component.testfiles.views.IC" />
            ''' % path
            ))

        v = component.getMultiAdapter((ob, request), name='xxx.html')
        v = ProxyFactory(v)
        zope.security.management.getInteraction().add(request)
        self.assertRaises(Exception, v)

        v = component.getMultiAdapter((ob, request), name='index.html')
        v = ProxyFactory(v)
        self.assertEqual(v().strip(), '<html><body><p>test</p></body></html>')


    def testtemplateNoName(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')
        self.assertRaises(
            ConfigurationError,
            xmlconfig,
            StringIO(template %
            '''
            <browser:page
                template="%s"
                for="zope.component.testfiles.views.IC"
                />
            ''' % path
            ))

    def testtemplateAndPage(self):
        path = os.path.join(tests_path, 'testfiles', 'test.pt')
        self.assertRaises(
            ConfigurationError,
            xmlconfig,
            StringIO(template %
            '''
            <browser:view
                name="index.html"
                template="%s"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                >
              <browser:page name="foo.html" attribute="index" />
            </browser:view>
            ''' % path
            ))

    def testViewThatProvidesAnInterface(self):
        request = TestRequest()
        self.assertEqual(
            component.queryMultiAdapter((ob, request), IV, name='test'), None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                />
            '''
            ))

        v = component.queryMultiAdapter((ob, request), IV, name='test')
        self.assertEqual(v, None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                name="test"
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                provides="zope.component.testfiles.views.IV"
                permission="zope.Public"
                />
            '''
            ))

        v = component.queryMultiAdapter((ob, request), IV, name='test')
        self.assert_(isinstance(v, V1))

    def testUnnamedViewThatProvidesAnInterface(self):
        request = TestRequest()
        self.assertEqual(component.queryMultiAdapter((ob, request), IV),
                         None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                permission="zope.Public"
                />
            '''
            ))

        v = component.queryMultiAdapter((ob, request), IV)
        self.assertEqual(v, None)

        xmlconfig(StringIO(template %
            '''
            <browser:view
                class="zope.component.testfiles.views.V1"
                for="zope.component.testfiles.views.IC"
                provides="zope.component.testfiles.views.IV"
                permission="zope.Public"
                />
            '''
            ))

        v = component.queryMultiAdapter((ob, request), IV)

        self.assert_(isinstance(v, V1))

    def testMenuItemNeedsFor(self):
        # <browser:menuItem> directive fails if no 'for' argument was provided
        from zope.configuration.exceptions import ConfigurationError
        self.assertRaises(ConfigurationError, xmlconfig, StringIO(template %
            '''
            <browser:menu
                id="test_menu" title="Test menu" />
            <browser:menuItem
                title="Test Entry"
                menu="test_menu"
                action="@@test"
            />
            '''
            ))

	# it works, when the argument is there and a valid interface
	xmlconfig(StringIO(template %
            '''
            <browser:menuItem
                for="zope.component.testfiles.views.IC"
                title="Test Entry"
                menu="test_menu"
               action="@@test"
            />
            '''
            ))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Test),
        DocTestSuite('zope.app.publisher.browser.metaconfigure',
                     setUp=placelesssetup.setUp,
                     tearDown=placelesssetup.tearDown)
        ))

if __name__=='__main__':
    unittest.main(defaultTest="test_suite")

