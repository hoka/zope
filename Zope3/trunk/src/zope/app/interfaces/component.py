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
"""Locale Component Architecuture interfaces

$Id: component.py,v 1.5 2004/02/24 14:16:59 srichter Exp $
"""
from zope.interface import Interface
from zope.schema import Field
from zope.schema.interfaces import IEnumerated, IField, ITuple


class IInterfaceService(Interface):
    """Service that keeps track of used interfaces
    """

    def getInterface(id):
        """Return the interface registered for the given id

        A ComponentLookupError is raised if the interface can't be found.
        """

    def queryInterface(id, default=None):
        """Return the interface registered for the given id

        The default is returned if the interface can't be found.
        """

    def searchInterface(search_string=None, base=None):
        """Return the interfaces that match the search criteria

        If a search string is given, only interfaces that contain the
        string in their documentation will be returned.

        If base is given, only interfaces that equal or extend base
        will be returned.
        """

    def searchInterfaceIds(search_string=None, base=None):
        """Return the ids of the interfaces that match the search criteria.

        See searchInterface
        """

    def items(search_string=None, base=None):
        """Return id, interface pairs for all items matching criteria.

        See searchInterface for the meaning of search-string and base.
        """

class IGlobalInterfaceService(IInterfaceService):
    """Global registry for Interface
    """

    def provideInterface(id, interface):
        """Register an interface with a given id

        The id is the full dotted name for the interface.

        If the id is false, the id will be computed from the interface
        module and name.
        """

class IDAVSchemaService(IInterfaceService):
    """Service that keeps tracks of namespace to interfaces mapping"""
    pass

class IGlobalDAVSchemaService(IDAVSchemaService):
    """Global registry from DAV namespaces to interfaces
    """

    def provideInterface(id, interface):
        """Register an interface with a given id

        The id is the URI for the namespace.
        """

    def availableNamespaces():
        """Returns a list of available namespaces we know about"""

    def getNamespace(interface):
        """Find what namespace is associated with an interface.

        A ComponentLookupError is raised if the interface is not found.
        """

    def queryNamespace(interface, default=None):
        """Find what namespace is associated with an interface.

        The default value is returned if the interface is not found.
        """

class IInterfaceField(IEnumerated, IField):
    u"""A type of Field that has an Interfaces as its value."""

    basetype = Field(
        title=u"Base type",
        description=(u"All values must extend (or be) this type,"
                     u" unless it is None which means 'anything'."),
        default=Interface,
        )

class IInterfacesField(ITuple):
    u"""A type of Field that is has a tuple of Interfaces as its value."""

    basetype = Field(
            title=u"Base type",
            description=(u"All values must extend or be this type,"
                         u" unless it is None, which means 'anything'."),
            default=Interface,
            )
