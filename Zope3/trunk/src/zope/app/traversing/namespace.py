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

$Id: namespace.py,v 1.13 2003/06/01 15:59:37 jim Exp $
"""

from zope.interface import Interface
from zope.exceptions import NotFoundError
from zope.app.context import ContextWrapper
from zope.context import getWrapperContext, getWrapperData
from zope.configuration.action import Action
from zope.component import queryAdapter, getAdapter, getServiceManager
from zope.component import queryDefaultViewName, queryView, getService
from zope.app.services.servicenames import Resources

from zope.app.interfaces.traversing import ITraversable
from zope.app.interfaces.services.module import IModuleService

import re

class UnexpectedParameters(NotFoundError):
    "Unexpected namespace parameters were provided."

class ExcessiveWrapping(NotFoundError):
    "Too many levels of acquisition wrapping. We don't believe them."

class NoRequest(NotFoundError):
    "Attempt to access a presentation component outside of a request context."


_namespace_handlers = {}

def provideNamespaceHandler(ns, handler):
    _namespace_handlers[ns] = handler

def directive(_context, name, handler):
    handler = _context.resolve(handler)
    return [Action(
               discriminator=("traversalNamespace", name),
               callable=provideNamespaceHandler,
               args=(name, handler),
               )]

def namespaceLookup(name, ns, qname, parameters, object, request=None):
    """Lookup a value from a namespace

    name -- the original name
    ns -- The namespace
    qname -- The name without any parameters

    The resulting object is returned in the context of the original.
    This means that the caller should *not* wrap the result.
    """

    handler = _namespace_handlers.get(ns)
    if handler is None:
        raise NotFoundError(name)

    new = handler(qname, parameters, name, object, request)
    if new is object:
        # The handler had a side effect only and didn't look up a
        # different object.  We want to retain the side-effect name
        # for things like URLs.

        # We'll just at the name to the side-effect names stored in
        # the object's wrapper.

        data = getWrapperData(new, create=True)
        data['side_effect_names'] = (data.get('side_effect_names', ())
                                     + (name, )
                                     )
    else:
        new = ContextWrapper(new, object, name=name)

    return new


namespace_pattern = re.compile('[+][+]([a-zA-Z0-9_]+)[+][+]')

def parameterizedNameParse(name):
    """Parse a name with parameters, including namespace parameters.

    Return:

    - namespace, or None if there isn't one.

    - unparameterized name.

    - sequence of parameters, as name-value pairs.
    """

    ns = ''
    if name.startswith('@@'):
        ns = 'view'
        name = name[2:]
    else:
        match = namespace_pattern.match(name)
        if match:
            prefix, ns = match.group(0, 1)
            name = name[len(prefix):]

    return ns, name, ()

def getResourceInContext(ob, name, request):
    resource = queryResourceInContext(ob, name, request)
    if resource is None:
        raise NotFoundError(ob, name)
    return resource

def queryResourceInContext(ob, name, request, default=None):
    resource_service = getService(ob, Resources)
    resource = resource_service.queryResource(ob, name, request)
    if resource is None:
        return default
    return ContextWrapper(resource, resource_service, name=name)


# ---- namespace processors below ----

def acquire(name, parameters, pname, ob, request):
    if parameters:
        raise UnexpectedParameters(parameters)

    i = 0
    origOb = ob
    while i < 200:
        i += 1
        traversable = queryAdapter(ob, ITraversable, None)
        if traversable is not None:

            try:
                # XXX what do we do if the path gets bigger?
                path = []
                next = traversable.traverse(name, parameters, pname, path)
                if path: continue
            except NotFoundError:
                pass
            else:
                return ContextWrapper(next, ob, name=name)

        ob = getWrapperContext(ob)
        if ob is None:
            raise NotFoundError(origOb, pname)

    raise ExcessiveWrapping(origOb, pname)

def attr(name, parameters, pname, ob, request):
    if parameters:
        raise UnexpectedParameters(parameters)
    return getattr(ob, name)

def item(name, parameters, pname, ob, request):
    if parameters:
        raise UnexpectedParameters(parameters)
    return ob[name]

from zope.app.applicationcontrol.applicationcontrol \
    import applicationController
from zope.app.content.folder import RootFolder
def etc(name, parameters, pname, ob, request):
    # XXX

    # This is here now to allow us to get service managers from a
    # separate namespace from the content. We add and etc
    # namespace to allow us to handle misc objects.  We'll apply
    # YAGNI for now and hard code this. We'll want something more
    # general later. We were thinking of just calling "get"
    # methods, but this is probably too magic. In particular, we
    # will treat returned objects as sub-objects wrt security and
    # not all get methods may satisfy this assumption. It might be
    # best to introduce some sort of etc registry.

    if parameters:
        raise UnexpectedParameters(parameters)

    if (name in ('process', 'ApplicationController')
        and ob.__class__ == RootFolder):
        return applicationController

    if name not in ('site', 'Services'):
        raise NotFoundError(ob, pname, request)

    method_name = "getServiceManager"
    method = getattr(ob, method_name, None)
    if method is None:
        raise NotFoundError(ob, pname, request)

    return method()

def module(name, parameters, pname, ob, request):
    """Used to traverse to a module (in dot notation)"""
    servicemanager = getServiceManager(ob)
    adapter = getAdapter(servicemanager, IModuleService)
    if adapter is not None:
        ob = adapter.resolve(name)
    if queryDefaultViewName(ob, request) is None:
        return Interface
    return ob

def help(name, parameters, pname, ob, request):
    """Used to traverse to an online help topic."""
    return getService(ob, 'OnlineHelp')

def view(name, parameters, pname, ob, request):
    if parameters:
        raise UnexpectedParameters(parameters)
    if not request:
        raise NoRequest(pname)
    view = queryView(ob, name, request)
    if view is None:
        raise NotFoundError(ob, name)

    return view

def resource(name, parameters, pname, ob, request):
    if parameters:
        raise UnexpectedParameters(parameters)
    if not request:
        raise NoRequest(pname)

    resource = queryResourceInContext(ob, name, request)
    if resource is None:
        raise NotFoundError(ob, pname)

    return resource

def skin(name, parameters, pname, ob, request):

    if parameters:
        raise UnexpectedParameters(parameters)

    if not request:
        raise NoRequest(pname)

    request.setViewSkin(name)

    return ob

def vh(name, parameters, pname, ob, request):

    traversal_stack = request.getTraversalStack()
    app_names = []

    if name:
        try:
            proto, host, port = name.split(":")
        except ValueError:
            raise ValueError("Vhost directive should have the form "
                             "++vh++protocol:host:port")

        request.setApplicationServer(host, proto, port)

    if '++' in traversal_stack:
        segment = traversal_stack.pop()
        while segment != '++':
            app_names.append(segment)
            segment = traversal_stack.pop()
        request.setTraversalStack(traversal_stack)

    request.setApplicationNames(app_names)
    request.setVirtualHostRoot()
    return ob
