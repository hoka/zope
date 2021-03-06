#
# Tests the ZopeTestCase, eating its own dogfood
#
# NOTE: This is *not* an example TestCase. Do not
# use this file as a blueprint for your own tests!
#
# See testPythonScript.py and testShoppingCart.py for
# example test cases. See testSkeleton.py for a quick
# way of getting started.
#

# $Id: testZopeTestCase.py,v 1.21 2004/09/04 18:01:08 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from Acquisition import aq_base
from AccessControl import getSecurityManager
from types import ListType
from transaction import begin

folder_name = ZopeTestCase.folder_name
user_name = ZopeTestCase.user_name
user_role = ZopeTestCase.user_role
standard_permissions = ZopeTestCase.standard_permissions


def hasattr_(ob, attr):
    return hasattr(aq_base(ob), attr)


class TestZopeTestCase(ZopeTestCase.ZopeTestCase):
    '''Incrementally exercise the ZopeTestCase API.'''

    _setUp = ZopeTestCase.ZopeTestCase.setUp
    _tearDown = ZopeTestCase.ZopeTestCase.tearDown

    def setUp(self):
        # For this test case we *want* to start
        # with an empty fixture.
        self._called = []
        # Implicitly aborts previous transaction
        begin()

    def beforeSetUp(self):
        self._called.append('beforeSetUp')

    def afterSetUp(self):
        self._called.append('afterSetUp')

    def beforeTearDown(self):
        self._called.append('beforeTearDown')

    def beforeClose(self):
        self._called.append('beforeClose')

    def afterClear(self):
        self._called.append('afterClear')

    def test_setupFolder(self):
        # Folder should be set up
        self.app = self._app()
        self._setupFolder()
        self.failUnless(hasattr_(self.app, folder_name))
        self.failUnless(hasattr_(self, 'folder'))
        self.failUnless(user_role in self.folder.userdefined_roles())
        self.assertPermissionsOfRole(standard_permissions, user_role)

    def test_setupUserFolder(self):
        # User folder should be set up
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.failUnless(hasattr_(self.folder, 'acl_users'))

    def test_setupUser(self):
        # User should be set up
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        acl_user = self.folder.acl_users.getUserById(user_name)
        self.failUnless(acl_user)
        self.assertEqual(acl_user.getRoles(), (user_role, 'Authenticated'))
        self.assertEqual(type(acl_user.roles), ListType)

    def test_setRoles(self):
        # Roles should be set for user
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        test_roles = ['Manager', user_role]
        self.setRoles(test_roles)
        acl_user = self.folder.acl_users.getUserById(user_name)
        self.assertRolesOfUser(test_roles, acl_user)

    def test_setRoles_2(self):
        # Roles of logged in user should be updated
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        test_roles = ['Manager', user_role]
        self.setRoles(test_roles)
        auth_user = getSecurityManager().getUser()
        self.assertRolesOfUser(test_roles, auth_user)

    def test_setRoles_3(self):
        # Roles should be set for a specified user
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.folder.acl_users.userFolderAddUser('user_2', 'secret', [], [])
        test_roles = ['Manager', user_role]
        self.setRoles(test_roles, 'user_2')
        acl_user = self.folder.acl_users.getUserById('user_2')
        self.assertRolesOfUser(test_roles, acl_user)

    def test_setRolesAssertsArgumentType(self):
        # setRoles should fail if 'roles' argument is not a list
        self.assertRaises(self.failureException, self.setRoles, 'foo')
        self.assertRaises(self.failureException, self.setRoles, ('foo',))

    def test_getRoles(self):
        # Should return roles of user
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        self.assertEqual(self.getRoles(), (user_role, 'Authenticated'))

    def test_getRoles_2(self):
        # Should return roles of specified user
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.folder.acl_users.userFolderAddUser('user_2', 'secret', ['Manager'], [])
        self.assertEqual(self.getRoles('user_2'), ('Manager', 'Authenticated'))

    def test_setPermissions(self):
        # Permissions should be set for user
        self.app = self._app()
        self._setupFolder()
        test_perms = ['Add Folders']
        self.assertPermissionsOfRole(standard_permissions, user_role)
        self.setPermissions(test_perms)
        self.assertPermissionsOfRole(test_perms, user_role)

    def test_setPermissions_2(self):
        # Permissions should be set for specified role
        self.app = self._app()
        self._setupFolder()
        self.folder._addRole('role_2')
        self.assertPermissionsOfRole([], 'role_2')
        self.setPermissions(standard_permissions, 'role_2')
        self.assertPermissionsOfRole(standard_permissions, 'role_2')

    def test_setPermissionsAssertsArgumentType(self):
        # setPermissions should fail if 'permissions' argument is not a list
        self.assertRaises(self.failureException, self.setPermissions, 'foo')
        self.assertRaises(self.failureException, self.setPermissions, ('foo',))

    def test_getPermissions(self):
        # Should return permissions of user
        self.app = self._app()
        self._setupFolder()
        self.assertEqual(self.getPermissions(), standard_permissions) 

    def test_getPermissions_2(self):
        # Should return permissions of specified role
        self.app = self._app()
        self._setupFolder()
        test_perms = ['Add Folders']
        self.folder._addRole('role_2')
        self.setPermissions(test_perms, 'role_2')
        self.assertEqual(self.getPermissions('role_2'), test_perms) 

    def test_login(self):
        # User should be able to log in
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.login()
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, user_name)

    def test_login_2(self):
        # A specified user should be logged in
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.folder.acl_users.userFolderAddUser('user_2', 'secret', [], [])
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.login('user_2')
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, 'user_2')

    def test_login_3(self):
        # Unknown user should raise AttributeError
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.assertRaises(AttributeError, self.login, 'user_3')

    def test_logout(self):
        # User should be able to log out
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        self.logout()
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')

    def test_clear(self):
        # Everything should be removed
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        self._clear(1)
        self.failIf(self.app.__dict__.has_key(folder_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['beforeClose', 'afterClear'])
        # _clear must not fail when called repeatedly
        self._clear()

    def test_setUp(self):
        # Everything should be set up
        self._setUp()
        self.failUnless(hasattr_(self.app, folder_name))
        self.failUnless(hasattr_(self, 'folder'))
        self.failUnless(user_role in self.folder.userdefined_roles())
        self.assertPermissionsOfRole(standard_permissions, user_role)
        self.failUnless(hasattr_(self.folder, 'acl_users'))
        acl_user = self.folder.acl_users.getUserById(user_name)
        self.failUnless(acl_user)
        self.assertEqual(acl_user.getRoles(), (user_role, 'Authenticated'))
        self.assertEqual(type(acl_user.roles), ListType)
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, user_name)
        # XXX: Changed in 0.9.0
        #self.assertEqual(self._called, ['afterClear', 'beforeSetUp', 'afterSetUp'])
        self.assertEqual(self._called, ['beforeSetUp', 'afterSetUp'])

    def test_tearDown(self):
        # Everything should be removed
        self._setUp()
        self._called = []
        self._tearDown()
        self.failIf(self.app.__dict__.has_key(folder_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['beforeTearDown', 'beforeClose', 'afterClear'])

    def test_setupFlag(self):
        # Nothing should be set up
        self._setup_fixture = 0
        self._setUp()
        self.failIf(hasattr_(self.app, folder_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        # XXX: Changed in 0.9.0
        #self.assertEqual(self._called, ['afterClear', 'beforeSetUp', 'afterSetUp'])
        self.assertEqual(self._called, ['beforeSetUp', 'afterSetUp'])

    # Bug tests

    def test_setOwnerPermissions(self):
        # Permissions should be modified for the Owner role
        self.app = self._app()
        self._setupFolder()
        self.assertPermissionsOfRole([], 'Owner')
        self.setPermissions(standard_permissions, 'Owner')
        self.assertPermissionsOfRole(standard_permissions, 'Owner')

    def test_setManagerPermissions(self):
        # Permissions should *not* be modified for the Manager role
        self.app = self._app()
        self._setupFolder()
        # Setting permissions for Manager role does not work like this
        manager_perms = self.getPermissionsOfRole('Manager')
        self.setPermissions(standard_permissions, 'Manager')
        # Manager does still have all permissions
        self.assertPermissionsOfRole(manager_perms, 'Manager')

    def test_setManagerPermissions_2(self):
        # Permissions should be modified for the Manager role
        self.app = self._app()
        self._setupFolder()
        # However, it works like that (because we turn off acquisition?)
        manager_perms = self.getPermissionsOfRole('Manager')
        self.folder.manage_permission('Take ownership', ['Owner'], acquire=0)
        self.assertPermissionsOfRole(['Take ownership'], 'Owner')
        # Manager does not have 'Take ownership' anymore
        manager_perms.remove('Take ownership')
        self.assertPermissionsOfRole(manager_perms, 'Manager')

    # This is crazy 

    def __test_crazyRoles_0(self):
        # Permission assignments should be reset
        self.app = self._app()
        perms = self.getPermissionsOfRole('Anonymous', self.app)
        for perm in ['Access contents information', 'View', 'Query Vocabulary', 'Search ZCatalog']:
            if perm not in perms:
                self.fail('Expected permission "%s"' % perm)

    def __test_crazyRoles_1(self):
        # Permission assignments should be reset
        self.app = self._app()
        self.app.manage_role('Anonymous', ['View'])
        self.assertPermissionsOfRole(['View'], 'Anonymous', self.app)
        self.failIf(getSecurityManager().checkPermission('Access contents information', self.app))

    def __test_crazyRoles_2(self):
        # Permission assignments should be reset
        self.app = self._app()
        try:
            self.assertPermissionsOfRole(['View'], 'Anonymous', self.app)
        except self.failureException:
            pass

    def __test_crazyRoles_3(self):
        # Permission assignments should be reset
        self.app = self._app()
        self.failUnless(getSecurityManager().checkPermission('Access contents information', self.app))

    def __test_crazyRoles_4(self):
        # Permission assignments should be reset
        self.app = self._app()
        perms = self.getPermissionsOfRole('Anonymous', self.app)
        for perm in ['Access contents information', 'View', 'Query Vocabulary', 'Search ZCatalog']:
            if perm not in perms:
                self.fail('Expected permission "%s"' % perm)

    # Helpers

    def getPermissionsOfRole(self, role, context=None):
        '''Returns sorted list of permission names of the
           given role in the given context.
        '''
        if context is None:
            context = self.folder
        perms = context.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]

    def assertPermissionsOfRole(self, permissions, role, context=None):
        '''Compares list of permission names to permissions of the
           given role in the given context. Fails if the lists are not
           found equal.
        '''
        lhs = list(permissions)[:]
        lhs.sort()
        rhs = self.getPermissionsOfRole(role, context)
        rhs.sort()
        self.assertEqual(lhs, rhs)

    def assertRolesOfUser(self, roles, user):
        '''Compares list of role names to roles of user. Fails if the
           lists are not found equal.
        '''
        lhs = list(roles)[:]
        lhs.sort()
        rhs = list(user.getRoles())[:]
        rhs.remove('Authenticated')
        rhs.sort()
        self.assertEqual(lhs, rhs)


from AccessControl.User import UserFolder
from Acquisition import aq_inner, aq_parent, aq_chain

class WrappingUserFolder(UserFolder):
    '''User folder returning wrapped user objects'''

    def getUser(self, name):
        return UserFolder.getUser(self, name).__of__(self)


class TestPlainUserFolder(ZopeTestCase.ZopeTestCase):
    '''Tests whether user objects are properly wrapped'''

    def testGetUserDoesNotWrapUser(self):
        user = self.folder.acl_users.getUserById(user_name)
        self.failIf(hasattr(user, 'aq_base'))
        self.failUnless(user is aq_base(user))

    def testLoggedInUserIsWrapped(self):
        user = getSecurityManager().getUser()
        self.assertEqual(user.getId(), user_name)
        self.failUnless(hasattr(user, 'aq_base'))
        self.failUnless(user.__class__.__name__, 'User')
        self.failUnless(user.aq_parent.__class__.__name__, 'UserFolder')
        self.failUnless(user.aq_parent.aq_parent.__class__.__name__, 'Folder')


class TestWrappingUserFolder(ZopeTestCase.ZopeTestCase):
    '''Tests whether user objects are properly wrapped'''

    def _setupUserFolder(self):
        self.folder._setObject('acl_users', WrappingUserFolder())

    def testGetUserWrapsUser(self):
        user = self.folder.acl_users.getUserById(user_name)
        self.failUnless(hasattr(user, 'aq_base'))
        self.failIf(user is aq_base(user))
        self.failUnless(user.aq_parent.__class__.__name__, 'WrappingUserFolder')

    def testLoggedInUserIsWrapped(self):
        user = getSecurityManager().getUser()
        self.assertEqual(user.getId(), user_name)
        self.failUnless(hasattr(user, 'aq_base'))
        self.failUnless(user.__class__.__name__, 'User')
        self.failUnless(user.aq_parent.__class__.__name__, 'WrappingUserFolder')
        self.failUnless(user.aq_parent.aq_parent.__class__.__name__, 'Folder')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestZopeTestCase))
    suite.addTest(makeSuite(TestPlainUserFolder))
    suite.addTest(makeSuite(TestWrappingUserFolder))
    return suite

if __name__ == '__main__':
    framework()

