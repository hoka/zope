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
"""Introspector

$Id: introspector.py,v 1.16 2003/08/17 06:05:18 philikon Exp $
"""
from zope.interface import Interface

from zope.app.interfaces.introspector import IIntrospector
from zope.app.interfaces.services.module import IModuleService
from zope.component import getService, getAdapter, getServiceDefinitions
from zope.proxy import removeAllProxies
from zope.interface import implements, implementedBy
from zope.interface import directlyProvides, directlyProvidedBy, providedBy
from zope.interface.interfaces import IInterface
from zope.app.services.servicenames import Interfaces

class Introspector:
    """Introspects an object"""

    implements(IIntrospector)

    def __init__(self, context):
        self.context = context
        self.request = None
        self.currentclass = None

    def isInterface(self):
        "Checks if the context is class or interface"
        return IInterface.isImplementedBy(self.context)

    def setRequest(self, request):
        """sets the request"""
        self.request = request
        if 'PATH_INFO' in request:
            path = self.request['PATH_INFO']
        else:
            path = ''
        name = path[path.rfind('++module++') + len('++module++'):]
        name = name.split('/')[0]
        if path.find('++module++') != -1:
            if (self.context == Interface and
                name != 'Interface._Interface.Interface'):
                servicemanager = getServiceManager(self.context)
                adapter = getAdapter(servicemanager, IModuleService)
                self.currentclass = adapter.resolve(name)
                self.context = self.currentclass
            else:
                self.currentclass = self.context
        else:
            self.currentclass = self.context.__class__

    def _unpackTuple(self, tuple_obj):
        res = []
        for item in tuple_obj:
            if type(item)==tuple:
                res.extend(self._unpackTuple(item))
            else:
                res.append(item)
        return tuple(res)

    def getClass(self):
        """Returns the class name"""
        return removeAllProxies(self.currentclass).__name__

    def getBaseClassNames(self):
        """Returns the names of the classes"""
        bases = self.getExtends()
        base_names = []
        for base in bases:
            base_names.append(base.__module__+'.'+base.__name__)
        return base_names

    def getModule(self):
        """Returns the module name of the class"""
        return removeAllProxies(self.currentclass).__module__

    def getDocString(self):
        """Returns the description of the class"""
        return removeAllProxies(self.currentclass).__doc__

    def getInterfaces(self):
        """Returns interfaces implemented by this class"""
        return tuple(implementedBy(removeAllProxies(self.currentclass)))

    def getInterfaceNames(self, interfaces=None):
        if interfaces is None:
            interfaces = self.getInterfaces()
        names = []
        for intObj in interfaces:
            names.append(interfaceToName(self.context, intObj))
        names.sort()
        return names

    def getInterfaceDetails(self):
        """Returns the entire documentation in the interface"""
        interface = self.context
        Iname = interfaceToName(self.context, interface).split('.')[-1]
        bases = []
        desc = ''
        methods = []
        attributes = []
        if interface is not None:
            namesAndDescriptions = list(interface.namesAndDescriptions())
            namesAndDescriptions.sort()
            for name, desc in namesAndDescriptions:
                if hasattr(desc, 'getSignatureString'):
                    methods.append((desc.getName(),
                                    desc.getSignatureString(),
                                    desc.getDoc()))
                else:
                    attributes.append((desc.getName(), desc.getDoc()))

            for base in interface.getBases():
                bases.append(base.__module__+'.'+base.__name__)
            desc = str(interface.getDoc())
        return [Iname, bases, desc, methods, attributes]

    def getExtends(self):
        """Returns all the class extended up to the top most level"""
        bases = self._unpackTuple(
            removeAllProxies(self.currentclass).__bases__)
        return bases

    def getInterfaceRegistration(self):
        """Returns details for a interface configuration"""
        #sm = queryServiceManager(self.context)
        service = []
        for name, interface in getServiceDefinitions(self.context):
            if self.context.extends(interface):
                service.append(str(name))
        return service

    def getDirectlyProvided(self):
        """See IIntrospector"""
        return directlyProvidedBy(removeAllProxies(self.context))

    def getDirectlyProvidedNames(self):
        """See IIntrospector"""
        return self.getInterfaceNames(self.getDirectlyProvided())

    def getMarkerInterfaceNames(self):
        """See IIntrospector"""
        result = list(self.getInterfaceNames(self.getMarkerInterfaces()))
        result.sort()
        return tuple(result)

    def getMarkerInterfaces(self):
        """See IIntrospector"""
        results = []
        iservice = getService(self.context, Interfaces)
        todo = list(providedBy(removeAllProxies(self.context)))
        done = []

        while todo:
            interface = todo.pop()
            done.append(interface)
            for base in interface.__bases__:
                if base not in todo and base not in done:
                    todo.append(base)
            markers = self.getDirectMarkersOf(interface)
            for interface in markers:
                if (interface not in results
                    and not interface.isImplementedBy(self.context)):
                    results.append(interface)
            todo += markers
        results.sort()
        return tuple(results)

    def getDirectMarkersOf(self, base):
        """Returns empty interfaces directly inheriting from the given one"""
        results = []
        iservice = getService(self.context, Interfaces)
        for id, interface in iservice.items(base=base):
            if base in interface.getBases() and not interface.names():
                results.append(interface)
        results.sort()
        return tuple(results)

def nameToInterface(context, name):
    if name == 'None':
        return None
    service = getService(context, Interfaces)
    iface = service.getInterface(name)
    return iface

def interfaceToName(context, interface):
    interface = removeAllProxies(interface)
    if interface is None:
        return 'None'
    service = getService(context, Interfaces)
    items = service.items(base=interface)
    ids = [id for id, iface in items
           if iface == interface]
    if not ids:
        # XXX Do not fail badly, instead resort to the standard
        # way of getting the interface name, cause not all interfaces
        # may be registered.
        return interface.__module__ + '.' + interface.getName()

    assert len(ids) == 1, "Ambiguous interface names: %s" % ids
    return ids[0]
