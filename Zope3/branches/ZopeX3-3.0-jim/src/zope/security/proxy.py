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
"""Helper functions for Proxies.

$Id$
"""

from warnings import warn

from zope.security._proxy import getChecker, getObject
from zope.security._proxy import _Proxy as Proxy

removeSecurityProxy = getObject

# This import represents part of the API for this module
from zope.security.checker import ProxyFactory

def trustedRemoveSecurityProxy(object):
    """Deprecated, use removeSecurityProxy instead"""
    warn("trustedRemoveSecurityProxy is deprecated."
         " It will disappear in Zope X3.1. "
         " Use removeSecurityProxy instead",
         DeprecationWarning, 2)

    return removeSecurityProxy(object)

def getProxiedObject(object):
    """Deprecated, use removeSecurityProxy instead"""
    warn("getProxiedObject is deprecated."
         " It will disappear in Zope X3.1. "
         " Use removeSecurityProxy instead",
         DeprecationWarning, 2)

    return removeSecurityProxy(object)

def getTestProxyItems(proxy):
    """Try to get checker names and permissions for testing

    If this succeeds, a sorted sequence of items is returned,
    otherwise, None is returned.
    """
    checker = getChecker(proxy)
    items = checker.get_permissions.items()
    items.sort()
    return items
