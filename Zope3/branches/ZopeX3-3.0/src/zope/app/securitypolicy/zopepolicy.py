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
""" Define Zope\'s default security policy

$Id$
"""
from zope.security.checker import CheckerPublic
from zope.security.management import system_user
import zope.security.simplepolicies
from zope.security.interfaces import ISecurityPolicy

from zope.app.location import LocationIterator
from zope.app.security.settings import Allow, Deny
from zope.app.securitypolicy.interfaces import \
     IRolePermissionMap, IPrincipalPermissionMap, IPrincipalRoleMap
from zope.app.securitypolicy.principalpermission \
     import principalPermissionManager
from zope.app.securitypolicy.rolepermission import rolePermissionManager
from zope.app.securitypolicy.principalrole import principalRoleManager

getPermissionsForPrincipal = \
                principalPermissionManager.getPermissionsForPrincipal
getPermissionsForRole = rolePermissionManager.getPermissionsForRole
getRolesForPrincipal = principalRoleManager.getRolesForPrincipal

globalContext = object()


class ZopeSecurityPolicy(zope.security.simplepolicies.ParanoidSecurityPolicy):
    zope.interface.classProvides(ISecurityPolicy)

    def checkPermission(self, permission, object):
        if permission is CheckerPublic:
            return True
        # XXX We aren't really handling multiple principals yet
        assert len(self.participations) == 1 # XXX
        user = self.participations[0].principal

        # mapping from principal to set of roles
        if user is system_user:
            return True

        roledict = {'zope.Anonymous': Allow}
        principals = {user.id : roledict}

        role_permissions = {}
        remove = {}

        # Look for placeless grants first.

        # get placeless principal permissions
        for principal in principals:
            for principal_permission, setting in (
                getPermissionsForPrincipal(principal)):
                if principal_permission == permission:
                    if setting is Deny:
                        return False
                    assert setting is Allow
                    remove[principal] = True

        # Clean out removed principals
        if remove:
            for principal in remove:
                del principals[principal]
            if principals:
                # not done yet
                remove.clear()
            else:
                # we've eliminated all the principals
                return True

        # get placeless principal roles
        for principal in principals:
            roles = principals[principal]
            for role, setting in getRolesForPrincipal(principal):
                assert setting in (Allow, Deny)
                if role not in roles:
                    roles[role] = setting

        for perm, role, setting in (
            rolePermissionManager.getRolesAndPermissions()):
            assert setting in (Allow, Deny)
            if role not in role_permissions:
                role_permissions[role] = {perm: setting}
            else:
                if perm not in role_permissions[role]:
                    role_permissions[role][perm] = setting

        # Get principal permissions based on roles
        for principal in principals:
            roles = principals[principal]
            for role, role_setting in roles.items():
                if role_setting is Deny:
                    return False
                if role in role_permissions:
                    if permission in role_permissions[role]:
                        setting = role_permissions[role][permission]
                        if setting is Deny:
                            return False
                        remove[principal] = True


        # Clean out removed principals
        if remove:
            for principal in remove:
                del principals[principal]
            if principals:
                # not done yet
                remove.clear()
            else:
                # we've eliminated all the principals
                return True

        # Look for placeful grants
        for place in LocationIterator(object):

            # Copy specific principal permissions
            prinper = IPrincipalPermissionMap(place, None)
            if prinper is not None:
                for principal in principals:
                    for principal_permission, setting in (
                        prinper.getPermissionsForPrincipal(principal)):
                        if principal_permission == permission:
                            if setting is Deny:
                                return False

                            assert setting is Allow
                            remove[principal] = True

            # Clean out removed principals
            if remove:
                for principal in remove:
                    del principals[principal]
                if principals:
                    # not done yet
                    remove.clear()
                else:
                    # we've eliminated all the principals
                    return True

            # Collect principal roles
            prinrole = IPrincipalRoleMap(place, None)
            if prinrole is not None:
                for principal in principals:
                    roles = principals[principal]
                    for role, setting in (
                        prinrole.getRolesForPrincipal(principal)):
                        assert setting in (Allow, Deny)
                        if role not in roles:
                            roles[role] = setting

            # Collect role permissions
            roleper = IRolePermissionMap(place, None)
            if roleper is not None:
                for perm, role, setting in roleper.getRolesAndPermissions():
                    assert setting in (Allow, Deny)
                    if role not in role_permissions:
                        role_permissions[role] = {perm: setting}
                    else:
                        if perm not in role_permissions[role]:
                            role_permissions[role][perm] = setting

            # Get principal permissions based on roles
            for principal in principals:
                roles = principals[principal]
                for role, role_setting in roles.items():
                    if role_setting is Deny:
                        return False
                    if role in role_permissions:
                        if permission in role_permissions[role]:
                            setting = role_permissions[role][permission]
                            if setting is Deny:
                                return False
                            remove[principal] = True

            # Clean out removed principals
            if remove:
                for principal in remove:
                    del principals[principal]
                if principals:
                    # not done yet
                    remove.clear()
                else:
                    # we've eliminated all the principals
                    return True

        return False # deny by default


def permissionsOfPrincipal(principal, object):
    permissions = {}

    roles = {'zope.Anonymous': Allow}
    principalid = principal.id

    # Make two passes.

    # First, collect what we know about the principal:


    # get placeless principal permissions
    for permission, setting in getPermissionsForPrincipal(principalid):
        if permission not in permissions:
            permissions[permission] = setting

    # get placeless principal roles
    for role, setting in getRolesForPrincipal(principalid):
        if role not in roles:
            roles[role] = setting

    # get placeful principal permissions and roles
    for place in LocationIterator(object):

        # Copy specific principal permissions
        prinper = IPrincipalPermissionMap(place, None)
        if prinper is not None:
            for permission, setting in prinper.getPermissionsForPrincipal(
                principalid):
                if permission not in permissions:
                    permissions[permission] = setting

        # Collect principal roles
        prinrole = IPrincipalRoleMap(place, None)
        if prinrole is not None:
            for role, setting in prinrole.getRolesForPrincipal(principalid):
                if role not in roles:
                    roles[role] = setting

    # Second, update permissions using principal

    for perm, role, setting in (
        rolePermissionManager.getRolesAndPermissions()):
        if role in roles and perm not in permissions:
            permissions[perm] = setting

    for place in LocationIterator(object):

        # Collect role permissions
        roleper = IRolePermissionMap(place, None)
        if roleper is not None:
            for perm, role, setting in roleper.getRolesAndPermissions():
                if role in roles and perm not in permissions:
                    permissions[perm] = setting



    result = [permission
              for permission in permissions
              if permissions[permission] is Allow]

    return result

