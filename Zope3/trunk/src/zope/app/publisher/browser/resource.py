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

$Id: resource.py,v 1.11 2004/03/05 22:09:14 jim Exp $
"""
__metaclass__ = type # All classes are new style when run with Python 2.2+

from zope.app import zapi
from zope.app.location import Location
from zope.app.interfaces.services.service import ISite
from zope.app.interfaces.traversing import IContainmentRoot
from zope.component.interfaces import IResource
from zope.interface import implements

class Resource(Location):

    implements(IResource)

    def __init__(self, request):
        self.request = request

    def __call__(self):
        names = []
        name = self.__name__
        if name.startswith('++resource++'):
            name = name[12:]
        names.append(name)

        site = self.__parent__
        while 1:
            if ISite.providedBy(site):
                break
            if IContainmentRoot.providedBy(site):
                site = None
                break
            if IResource.providedBy(site) and site.__name__:
                names.append(site.__name__)
            site = site.__parent__

        names.reverse()
        name = '/'.join(filter(None, names))
        url = str(zapi.getView(site, 'absolute_url', self.request))
        return "%s/@@/%s" % (url, name)
