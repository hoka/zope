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
"""Mappings between principals and roles, stored in an object locally."""

from Zope.ComponentArchitecture import getAdapter
from Zope.App.OFS.Annotation.IAnnotations import IAnnotations
from Zope.App.Security.IPrincipalRoleManager \
     import IPrincipalRoleManager
from Zope.App.Security.LocalSecurityMap import LocalSecurityMap
from Zope.App.Security.Settings import Assign, Remove, Unset

annotation_key = 'Zope.App.Security.AnnotationPrincipalRoleManager'

class AnnotationPrincipalRoleManager:
    """Mappings between principals and roles."""

    __implements__ = IPrincipalRoleManager

    def __init__(self, context):
        self._context = context

    def assignRoleToPrincipal(self, role_id, principal_id):
        ''' See the interface IPrincipalRoleManager '''
        pp = self._getPrincipalRoles(create=1)
        pp.addCell(role_id, principal_id, Assign)
        self._context._p_changed = 1

    def removeRoleFromPrincipal(self, role_id, principal_id):
        ''' See the interface IPrincipalRoleManager '''
        pp = self._getPrincipalRoles(create=1)
        pp.addCell(role_id, principal_id, Remove)
        self._context._p_changed = 1

    def unsetRoleForPrincipal(self, role_id, principal_id):
        ''' See the interface IPrincipalRoleManager '''
        pp = self._getPrincipalRoles()
        # Only unset if there is a security map, otherwise, we're done
        if pp:
            pp.delCell(role_id, principal_id)
            self._context._p_changed = 1

    def getPrincipalsForRole(self, role_id):
        ''' See the interface IPrincipalRoleManager '''
        pp = self._getPrincipalRoles()
        if pp: 
            return pp.getRow(role_id)
        return []

    def getRolesForPrincipal(self, principal_id):
        ''' See the interface IPrincipalRoleManager '''
        pp = self._getPrincipalRoles()
        if pp: 
            return pp.getCol(principal_id)
        return []

    def getSetting(self, role_id, principal_id):
        ''' See the interface IPrincipalRoleManager '''
        pp = self._getPrincipalRoles()
        if pp: 
            return pp.getCell(role_id, principal_id, default=Unset)
        return Unset

    def getPrincipalsAndRoles(self):
        ''' See the interface IPrincipalRoleManager '''
        pp = self._getPrincipalRoles()
        if pp:
            return pp.getAllCells()
        return []

    # Implementation helpers

    def _getPrincipalRoles(self, create=0):
        """ Get the principal role map stored in the context, optionally
            creating one if necessary """
        annotations = getAdapter(self._context, IAnnotations)
        try:
            return annotations[annotation_key]
        except KeyError:
            if create:
                rp = annotations[annotation_key] = LocalSecurityMap()
                return rp
        return None
