##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
""" Web-configurable workflow UI.

$Id$
"""

import os

from Globals import DTMLFile
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Acquisition import aq_get

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from permissions import ManagePortal
from Guard import Guard
from utils import _dtmldir
from Products.CMFCore.utils import postonly

try:
    #
    #   XXX: 2004/04/28  This factoring *has* to go;  if necessary,
    #         this module could have a hook function, which the dependent
    #         module could replace.
    #

    # If base_cms exists, include the roles it defines.
    from Products.base_cms.permissions import getDefaultRolePermissionMap
except ImportError:
    def getDefaultRolePermissionMap():
        return {}


class WorkflowUIMixin:
    '''
    '''

    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'manage_properties')
    manage_properties = DTMLFile('workflow_properties', _dtmldir)
    manage_groups = PageTemplateFile('workflow_groups.pt', _dtmldir)

    security.declareProtected(ManagePortal, 'setProperties')
    def setProperties(self, title, manager_bypass=0, props=None, REQUEST=None):
        """Sets basic properties.
        """
        self.title = str(title)
        self.manager_bypass = manager_bypass and 1 or 0
        g = Guard()
        if g.changeFromProperties(props or REQUEST):
            self.creation_guard = g
        else:
            self.creation_guard = None
        if REQUEST is not None:
            return self.manage_properties(
                REQUEST, manage_tabs_message='Properties changed.')
    setProperties = postonly(setProperties)

    _permissions_form = DTMLFile('workflow_permissions', _dtmldir)

    security.declareProtected(ManagePortal, 'manage_permissions')
    def manage_permissions(self, REQUEST, manage_tabs_message=None):
        """Displays the form for choosing which permissions to manage.
        """
        return self._permissions_form(REQUEST,
                                      management_view='Permissions',
                                      manage_tabs_message=manage_tabs_message,
                                      )

    security.declareProtected(ManagePortal, 'addManagedPermission')
    def addManagedPermission(self, p, REQUEST=None):
        """Adds to the list of permissions to manage.
        """
        if p in self.permissions:
            raise ValueError, 'Already a managed permission: ' + p
        if REQUEST is not None and p not in self.getPossiblePermissions():
            raise ValueError, 'Not a valid permission name:' + p
        self.permissions = self.permissions + (p,)
        if REQUEST is not None:
            return self.manage_permissions(
                REQUEST, manage_tabs_message='Permission added.')
    addManagedPermission = postonly(addManagedPermission)

    security.declareProtected(ManagePortal, 'delManagedPermissions')
    def delManagedPermissions(self, ps, REQUEST=None):
        """Removes from the list of permissions to manage.
        """
        if ps:
            l = list(self.permissions)
            for p in ps:
                l.remove(p)
            self.permissions = tuple(l)
        if REQUEST is not None:
            return self.manage_permissions(
                REQUEST, manage_tabs_message='Permission(s) removed.')
    delManagedPermissions = postonly(delManagedPermissions)

    security.declareProtected(ManagePortal, 'getPossiblePermissions')
    def getPossiblePermissions(self):
        """Returns the list of all permissions that can be managed.
        """
        # possible_permissions is in AccessControl.Role.RoleManager.
        return list(self.possible_permissions())

    security.declareProtected(ManagePortal, 'getGroups')
    def getGroups(self):
        """Returns the names of groups managed by this workflow.
        """
        return tuple(self.groups)

    security.declareProtected(ManagePortal, 'getAvailableGroups')
    def getAvailableGroups(self):
        """Returns a list of available group names.
        """
        gf = aq_get( self, '__allow_groups__', None, 1 )
        if gf is None:
            return ()
        try:
            groups = gf.searchGroups()
        except AttributeError:
            return ()
        else:
            return [g['id'] for g in groups]

    security.declareProtected(ManagePortal, 'addGroup')
    def addGroup(self, group, RESPONSE=None, REQUEST=None):
        """Adds a group by name.
        """
        if group not in self.getAvailableGroups():
            raise ValueError(group)
        self.groups = self.groups + (group,)
        if RESPONSE is not None:
            RESPONSE.redirect(
                "%s/manage_groups?manage_tabs_message=Added+group."
                % self.absolute_url())
    addGroup = postonly(addGroup)

    security.declareProtected(ManagePortal, 'delGroups')
    def delGroups(self, groups, RESPONSE=None, REQUEST=None):
        """Removes groups by name.
        """
        self.groups = tuple([g for g in self.groups if g not in groups])
        if RESPONSE is not None:
            RESPONSE.redirect(
                "%s/manage_groups?manage_tabs_message=Groups+removed."
                % self.absolute_url())
    delGroups = postonly(delGroups)

    security.declareProtected(ManagePortal, 'getAvailableRoles')
    def getAvailableRoles(self):
        """Returns the acquired roles mixed with base_cms roles.
        """
        roles = list(self.valid_roles())
        for role in getDefaultRolePermissionMap().keys():
            if role not in roles:
                roles.append(role)
        roles.sort()
        return roles

    security.declareProtected(ManagePortal, 'getRoles')
    def getRoles(self):
        """Returns the list of roles managed by this workflow.
        """
        roles = self.roles
        if roles is not None:
            return roles
        roles = getDefaultRolePermissionMap().keys()
        if roles:
            # Map the base_cms roles by default.
            roles.sort()
            return roles
        return self.valid_roles()

    security.declareProtected(ManagePortal, 'setRoles')
    def setRoles(self, roles, RESPONSE=None, REQUEST=None):
        """Changes the list of roles mapped to groups by this workflow.
        """
        avail = self.getAvailableRoles()
        for role in roles:
            if role not in avail:
                raise ValueError(role)
        self.roles = tuple(roles)
        if RESPONSE is not None:
            RESPONSE.redirect(
                "%s/manage_groups?manage_tabs_message=Roles+changed."
                % self.absolute_url())
    setRoles = postonly(setRoles)

    security.declareProtected(ManagePortal, 'getGuard')
    def getGuard(self):
        """Returns the initiation guard.

        If no init guard has been created, returns a temporary object.
        """
        if self.creation_guard is not None:
            return self.creation_guard
        else:
            return Guard().__of__(self)  # Create a temporary guard.

    security.declarePublic('guardExprDocs')
    def guardExprDocs(self):
        """Returns documentation on guard expressions.
        """
        here = os.path.dirname(__file__)
        fn = os.path.join(here, 'doc', 'expressions.stx')
        f = open(fn, 'rt')
        try:
            text = f.read()
        finally:
            f.close()
        from DocumentTemplate.DT_Var import structured_text
        return structured_text(text)

InitializeClass(WorkflowUIMixin)
