import os, sys
import glob

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from AccessControl import getSecurityManager
from Testing import ZopeTestCase
from Testing.ZopeTestCase.functional import Functional
from AccessControl import Unauthorized

# we need to install FiveTest *before* Five as Five processes zcml
# in all the products it can find.
ZopeTestCase.installProduct('FiveTest')
ZopeTestCase.installProduct('Five')
ZopeTestCase.installProduct('PythonScripts')

from Products import FiveTest
_prefix = os.path.dirname(FiveTest.__file__)
dir_resource_names = [os.path.basename(r)
                      for r in (glob.glob('%s/*.png' % _prefix) +
                                glob.glob('%s/*.pt' % _prefix) +
                                glob.glob('%s/[a-z]*.py' % _prefix) +
                                glob.glob('%s/*.css' % _prefix))]

ViewManagementScreens = 'View management screens'

class RestrictedPythonTest(ZopeTestCase.ZopeTestCase):
    """
    Test whether code is really restricted

    Kind permission from Plone to use this.
    """

    def addPS(self, id, params='', body=''):
        # clean up any 'ps' that's already here..
        try:
            self.folder._getOb('ps')
            self.folder.manage_delObjects(['ps'])
        except AttributeError:
            pass # it's okay, no 'ps' exists yet
        factory = self.folder.manage_addProduct['PythonScripts']
        factory.manage_addPythonScript(id)
        self.folder[id].ZPythonScript_edit(params, body)

    def check(self, psbody):
        self.addPS('ps', body=psbody)
        try:
            self.folder.ps()
        except (ImportError, Unauthorized), e:
            self.fail(e)

    def checkUnauthorized(self, psbody):
        self.addPS('ps', body=psbody)
        try:
            self.folder.ps()
        except (AttributeError, Unauthorized):
            pass
        else:
            self.fail("Authorized but shouldn't be")

view_names = [
    'eagle.txt',
    'falcon.html',
    'owl.html',
    'flamingo.html',
    'flamingo2.html',
    'condor.html']

public_view_names = [
    'public_attribute_page',
    'public_template_page',
    'public_template_class_page']

resource_names = [
    'cockatiel.html',
    'style.css',
    'pattern.png'
    ]

class SecurityTestCase(RestrictedPythonTest):

    def afterSetUp(self):
        self.folder.manage_addProduct['FiveTest'].manage_addSimpleContent(
            'testoid', 'Testoid')
        uf = self.folder.acl_users
        uf._doAddUser('viewer', 'secret', [], [])
        uf._doAddUser('manager', 'r00t', ['Manager'], [])

    def test_no_permission(self):
        self.login('viewer')
        for view_name in view_names:
            self.checkUnauthorized(
                'context.restrictedTraverse("testoid/%s")()' % view_name)

    def test_resource_no_permission(self):
        self.login('viewer')
        for resource in resource_names:
            self.checkUnauthorized(
                'context.restrictedTraverse("testoid/++resource++%s")()' %
                resource)

    def test_directory_resource_no_permission(self):
        self.login('viewer')
        base = 'testoid/++resource++fivetest_resources/%s'
        for resource in dir_resource_names:
            path = base % resource
            self.checkUnauthorized(
                'context.restrictedTraverse("%s")' % path)

    def test_permission(self):
        self.login('manager')
        for view_name in view_names:
            self.check(
                'context.restrictedTraverse("testoid/%s")()' % view_name)

    def test_resource_permission(self):
        self.login('manager')
        for resource in resource_names:
            self.check(
                'context.restrictedTraverse("testoid/++resource++%s")()' %
                resource)

    def test_directory_resource_permission(self):
        self.login('manager')
        base = 'testoid/++resource++fivetest_resources/%s'
        for resource in dir_resource_names:
            path = base % resource
            self.check(
                'context.restrictedTraverse("%s")' % path)

    def test_public_permission(self):
        for view_name in public_view_names:
            self.check(
                'context.restrictedTraverse("testoid/%s")()' % view_name)

    def test_view_method_permission(self):
        self.login('manager')
        self.check(
            'context.restrictedTraverse("testoid/eagle.method").eagle()')

class PublishTestCase(Functional, ZopeTestCase.ZopeTestCase):
    """A functional test for security actually involving the publisher.
    """
    def afterSetUp(self):
        self.folder.manage_addProduct['FiveTest'].manage_addSimpleContent(
            'testoid', 'Testoid')
        uf = self.folder.acl_users
        uf._doAddUser('viewer', 'secret', [], [])
        uf._doAddUser('manager', 'r00t', ['Manager'], [])

    def test_no_permission(self):
        for view_name in view_names:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name,
                                    basic='viewer:secret')
            # we expect that we get a 401 Unauthorized
            self.assertEqual(response.getStatus(), 401)


    def test_permission(self):
        for view_name in view_names:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name,
                                    basic='manager:r00t')
            # we expect that we get a 200 Ok
            self.assertEqual(response.getStatus(), 200)

    def test_public_permission(self):
        for view_name in public_view_names:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name)
            self.assertEqual(response.getStatus(), 200)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SecurityTestCase))
    suite.addTest(unittest.makeSuite(PublishTestCase))
    return suite

if __name__ == '__main__':
    framework()
