##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
$Id: directoryresource.py,v 1.1 2003/08/11 14:58:07 philikon Exp $
"""

import os

from zope.interface import implements
from zope.exceptions import NotFoundError
from zope.security.proxy import Proxy
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces.browser import IBrowserResource, \
     IBrowserPublisher

from zope.app.publisher.browser.resource import Resource

from fileresource import FileResourceFactory, ImageResourceFactory
from pagetemplateresource import PageTemplateResourceFactory
from resources import empty

_marker = []

# we only need this class a context for DirectoryResource
class Directory:

    def __init__(self, path, checker):
        self.path = path
        self.checker = checker

class DirectoryResource(BrowserView, Resource):

    implements(IBrowserResource, IBrowserPublisher)

    resource_factories = {
        'gif':  ImageResourceFactory,
        'png':  ImageResourceFactory,
        'jpg':  ImageResourceFactory,
        'pt':   PageTemplateResourceFactory,
        'zpt':  PageTemplateResourceFactory,
        'html': PageTemplateResourceFactory,
        }

    default_factory = FileResourceFactory

    def publishTraverse(self, request, name):
        '''See interface IBrowserPublisher'''
        return self.get(name)

    def browserDefault(self, request):
        '''See interface IBrowserPublisher'''
        return empty, ()

    def __getitem__(self, name):
        res = self.get(name, None)
        if res is None:
            raise KeyError, name
        return res

    def get(self, name, default=_marker):
        path = self.context.path
        filename = os.path.join(path, name)
        if not os.path.isfile(filename):
            if default is _marker:
                raise NotFoundError(name)
            return default
        ext = name.split('.')[-1]
        factory = self.resource_factories.get(ext, self.default_factory)
        return factory(filename, self.context.checker)(self.request)

class DirectoryResourceFactory:

    def __init__(self, path, checker):
        self.__dir = Directory(path, checker)
        self.__checker = checker

    def __call__(self, request):
        return Proxy(DirectoryResource(self.__dir, request),
                     self.__checker)
