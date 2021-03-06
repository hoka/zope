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
"""Viewlet implementation

$Id: metaconfigure.py 38437 2005-09-10 01:59:07Z rogerineichen $
"""
__docformat__ = 'restructuredtext'

import sys
import zope.interface
from zope.app.pagetemplate.simpleviewclass import simple
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile
from zope.app.publisher.browser import BrowserView

from zope.app.viewlet import interfaces


class ViewletPageTemplateFile(ViewPageTemplateFile):

    def pt_getContext(self, instance, request, **_kw):
        namespace = super(ViewletPageTemplateFile, self).pt_getContext(
            instance, request, **_kw)
        namespace['view'] = instance.view
        namespace['viewlet'] = instance
        return namespace


class SimpleViewlet(BrowserView):
    """Viewlet adapter class used in meta directive as a mixin class."""

    zope.interface.implements(interfaces.IViewlet)

    _weight = 0

    def __init__(self, context, request, view):
        super(SimpleViewlet, self).__init__(context, request)
        self.view = view

    def _getWeight (self):
        """The weight of the viewlet."""
        return self._weight

    # See zope.app.viewlet.interfaces.IViewlet
    weight = property(_getWeight)


class SimpleAttributeViewlet(SimpleViewlet):

    def publishTraverse(self, request, name):
        raise NotFound(self, name, request)

    def __call__(self, *args, **kw):
        # If a class doesn't provide it's own call, then get the attribute
        # given by the browser default.

        attr = self.__page_attribute__
        if attr == '__call__':
            raise AttributeError("__call__")

        meth = getattr(self, attr)
        return meth(*args, **kw)


def SimpleViewletClass(template, offering=None, bases=(), name=u'', weight=0):
    # Get the current frame
    if offering is None:
        offering = sys._getframe(1).f_globals

    # Create the base class hierarchy
    bases += (SimpleViewlet, simple)

    # Generate a derived view class.
    class_ = type("SimpleViewletClass from %s" % template, bases,
                  {'index' : ViewletPageTemplateFile(template, offering),
                   '_weight' : weight,
                   '__name__' : name})

    return class_
