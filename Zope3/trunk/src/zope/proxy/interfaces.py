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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""

Revision information:
$Id: interfaces.py,v 1.4 2003/05/28 17:19:23 jim Exp $
"""

from zope.interface import Interface

class IProxyIntrospection(Interface):
    """Provides methods for indentifying proxies and extracting proxied objects
    """

    def isProxy(obj, proxytype=None):
        """Check whether the given object is a proxy

        If proxytype is not None, checkes whether the object is
        proxied by the given proxytype.
        """

    def getProxiedObject(obj):
        """Get the proxied Object

        If the object isn't proxied, then just return the object.
        """

    def removeAllProxies(obj):
        """Get the proxied object with no proxies

        If obj is not a proxied object, return obj.

        The returned object has no proxies.
        """

    def queryProxy(obj, proxytype, default=None):
        """Look for a proxy of the given type around the object

        If no such proxy can be found, return the default.
        """

    def queryInnerProxy(obj, proxytype, default=None):
        """Look for the inner-most proxy of the given type around the object

        If no such proxy can be found, return the default.

        If there is such a proxy, return the inner-most one.
        """
