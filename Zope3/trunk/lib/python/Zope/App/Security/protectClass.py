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
"""Make assertions about permissions needed to access class instances attributes
"""

from Exceptions import UndefinedPermissionError
from PermissionRegistry import permissionRegistry

from Zope.Security.Checker import defineChecker, getCheckerForInstancesOf
from Zope.Security.Checker import Checker, CheckerPublic

def checkPermission(permission):
    """Check to make sure that the permission is valid.
    """
    if not permissionRegistry.definedPermission(permission):
        raise UndefinedPermissionError(permission)

def protectName(class_, name, permission):
    "Set a permission on a particular name."
    
    checkPermission(permission)
    
    checker = getCheckerForInstancesOf(class_)
    if checker is None:
        checker = Checker({}.get)
        defineChecker(class_, checker)

    if permission == 'Zope.Public':
        # Translate public permission to CheckerPublic
        permission = CheckerPublic

    # OK, so it's a hack.
    protections = checker.getPermission_func().__self__    
    protections[name] = permission

def protectLikeUnto(class_, like_unto):
    """Use the protections from like_unto for class_
    """
    
    unto_checker = getCheckerForInstancesOf(like_unto)
    if unto_checker is None:
        return

    # OK, so it's a hack.
    unto_protections = unto_checker.getPermission_func().__self__
    
    checker = getCheckerForInstancesOf(class_)
    if checker is None:
        checker = Checker({}.get)
        defineChecker(class_, checker)

    # OK, so it's a hack.
    protections = checker.getPermission_func().__self__
    for name in unto_protections:
        protections[name] = unto_protections[name]
