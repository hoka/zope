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
"""XXX short summary goes here.

$Id: browser.py,v 1.16 2004/05/01 14:37:43 philikon Exp $
"""
__metaclass__ = type

from zope.app.publication.publicationtraverse \
     import PublicationTraverser as PublicationTraverser_
from zope.app.publication.http import BaseHTTPPublication
from zope.component import queryViewProviding
from zope.proxy import removeAllProxies
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.security.checker import ProxyFactory

class PublicationTraverser(PublicationTraverser_):

    def traverseRelativeURL(self, request, ob, path):
        ob = self.traversePath(request, ob, path)

        while True:
            adapter = IBrowserPublisher(ob, None)
            if adapter is None:
                return ob
            ob, path = adapter.browserDefault(request)
            ob = ProxyFactory(ob)
            if not path:
                return ob

            ob = self.traversePath(request, ob, path)

class BrowserPublication(BaseHTTPPublication):
    """Web browser publication handling."""

    def getDefaultTraversal(self, request, ob):
        if IBrowserPublisher.providedBy(removeAllProxies(ob)):
            # ob is already proxied, so the result of calling a method will be
            return ob.browserDefault(request)
        else:
            adapter = queryViewProviding(ob, IBrowserPublisher, request , None)
            if adapter is not None:
                ob, path = adapter.browserDefault(request)
                ob = ProxyFactory(ob)
                return ob, path
            else:
                # ob is already proxied
                return ob, None

    def afterCall(self, request, ob):
        super(BrowserPublication, self).afterCall(request, ob)
        if request.method == 'HEAD':
            request.response.setBody('')

# For now, have a factory that returns a singleton
class PublicationFactory:

    def __init__(self, db):
        self.__pub = BrowserPublication(db)

    def __call__(self):
        return self.__pub
