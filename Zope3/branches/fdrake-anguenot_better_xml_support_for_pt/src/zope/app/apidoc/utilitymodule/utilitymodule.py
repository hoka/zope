##############################################################################
#
# Copyright (c) 2004 Zope Corporation and Contributors.
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
"""Utility Documentation Module

$Id: __init__.py 29199 2005-02-17 22:38:55Z srichter $
"""
__docformat__ = 'restructuredtext'

from zope.component.site import UtilityRegistration
from zope.interface import implements

from zope.app import zapi
from zope.app.i18n import ZopeMessageFactory as _
from zope.app.component import queryNextSiteManager
from zope.app.location.interfaces import ILocation
from zope.app.apidoc.interfaces import IDocumentationModule
from zope.app.apidoc.utilities import ReadContainerBase, getPythonPath

# Constant used when the utility has no name
NONAME = '__noname__'

class Utility(object):
    """Representation of a utility for the API Documentation"""
    implements(ILocation)
    
    def __init__(self, parent, reg):
        """Initialize Utility object."""
        self.__parent__ = parent
        self.__name__ = reg.name or NONAME
        self.registration = reg
        self.interface = reg.provided
        self.component = reg.component
        self.doc = reg.doc


class UtilityInterface(ReadContainerBase):
    """Representation of an interface a utility provides."""
    implements(ILocation)

    def __init__(self, parent, name, interface):
        self.__parent__ = parent
        self.__name__ = name
        self.interface = interface

    def get(self, key, default=None):
        """See zope.app.container.interfaces.IReadContainer"""
        sm = zapi.getGlobalSiteManager()
        if key == NONAME:
            key = ''
        utils = [Utility(self, reg)
                 for reg in sm.registrations()
                 if zapi.isinstance(reg, UtilityRegistration) and \
                     reg.name == key and reg.provided == self.interface]
        return utils and utils[0] or default

    def items(self):
        """See zope.app.container.interfaces.IReadContainer"""
        sm = zapi.getGlobalSiteManager()
        items = [(reg.name or NONAME, Utility(self, reg))
                 for reg in sm.registrations()
                 if zapi.isinstance(reg, UtilityRegistration) and \
                     self.interface == reg.provided]
        items.sort()
        return items


class UtilityModule(ReadContainerBase):
    """Represent the Documentation of all Interfaces.

    This documentation is implemented using a simple `IReadContainer`. The
    items of the container are all utility interfaces.
    """
    implements(IDocumentationModule)

    # See zope.app.apidoc.interfaces.IDocumentationModule
    title = _('Utilities')

    # See zope.app.apidoc.interfaces.IDocumentationModule
    description = _("""
    Utilities are also nicely registered in a site manager, so that it is easy
    to create a listing of available utilities. A utility is identified by the
    providing interface and a name, which can be empty. The menu provides you
    with a list of interfaces that utilities provide and as sub-items the
    names of the various implementations.

    Again, the documentation of a utility lists all the attributes/fields and
    methods the utility provides and provides a link to the implementation.
    """)

    def get(self, key, default=None):
        parts = key.split('.')
        try:
            mod = __import__('.'.join(parts[:-1]), {}, {}, ('*',))
        except ImportError:
            return default
        else:
            return UtilityInterface(self, key, getattr(mod, parts[-1], default))

    def items(self):
        sm = zapi.getSiteManager()
        ifaces = {}
        while sm is not None:
            for reg in sm.registrations():
                if isinstance(reg, UtilityRegistration):
                    path = getPythonPath(reg.provided)
                    ifaces[path] = UtilityInterface(self, path, reg.provided)
            sm = queryNextSiteManager(sm)

        items = ifaces.items()
        items.sort(lambda x, y: cmp(x[0].split('.')[-1], y[0].split('.')[-1]))
        return items

