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
"""
$Id$
"""

__metaclass__ = type

from zope.interface import providedBy, implements
from zope.publisher.interfaces import Unauthorized, NotFound
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.publisher.interfaces.xmlrpc import IXMLRPCPublisher
from zope.component import queryView, getView, getDefaultViewName

class SimpleComponentTraverser:
    """Browser traverser for simple components that can only traverse to views
    """
    implements(IBrowserPublisher, IXMLRPCPublisher)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def browserDefault(self, request):
        ob = self.context
        view_name = getDefaultViewName(ob, request)
        return ob, (view_name,)

    def publishTraverse(self, request, name):
        ob = self.context
        view = queryView(ob, name, request)
        if view is None:
            raise NotFound(ob, name)
        return view

class FileContentTraverser(SimpleComponentTraverser):
    """Browser traverser for file content.

    The default view for file content has effective URLs that don't end in
    /.  In particular, if the content inclused HTML, relative links in
    the HTML are relative to the container the content is in.
    """

    def browserDefault(self, request):
        ob = self.context

        view_name = getDefaultViewName(ob, request)
        view = self.publishTraverse(request, view_name)
        if hasattr(view, 'browserDefault'):
            view, path = view.browserDefault(request)
            if len(path) == 1:
                view = view.publishTraverse(request, path[0])
                path = ()
        else:
            path = ()

        return view, path

class TestTraverser:
    """Bobo-style traverser, mostly useful for testing"""
    implements(IBrowserPublisher)

    def __init__(self, context, request):
        self.context = context

    def browserDefault(self, request):
        ob = self.context

        if providedBy(ob):
            view_name = getDefaultViewName(ob, request)
            return ob, (("@@%s" % view_name),)

        return ob, ()

    def publishTraverse(self, request, name):
        ob = self.context
        if name.startswith('@@'):
            return getView(ob, name[6:], request)

        if name.startswith('_'):
            raise Unauthorized("Name %s begins with an underscore" % `name`)

        subob = getattr(ob, name, self) # self is marker here
        if subob is self:
            # no attribute
            try:
                subob = ob[name]
            except (KeyError, IndexError,
                    TypeError, AttributeError):
                raise NotFound(ob, name, request)

        return subob
