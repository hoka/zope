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
"""
$Id$
"""
from zope.interface import implements
from zope.app.server.interfaces import ISimpleRegistry
from zope.app.publication.interfaces import IPublicationRequestFactoryFactory
from zope.app.server.simpleregistry import SimpleRegistry


class IRequestFactoryRegistry(ISimpleRegistry):
    """
    The RequestFactory Registry manages a list of all the fields
    available in Zope. A registry is useful at this point, since
    fields can be initialized and registered by many places.

    Note that it does not matter whether we have classes or instances as
    fields. If the fields are instances, they must implement
    IInstanceFactory.
    """


class RequestFactoryRegistry(SimpleRegistry):
    implements(IRequestFactoryRegistry)


RequestFactoryRegistry = RequestFactoryRegistry(
    IPublicationRequestFactoryFactory)

registerRequestFactory = RequestFactoryRegistry.register
getRequestFactory = RequestFactoryRegistry.get

# Register our cleanup with Testing.CleanUp to make writing unit tests simpler.
from zope.testing.cleanup import addCleanUp
addCleanUp(RequestFactoryRegistry._clear)
del addCleanUp
