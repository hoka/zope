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
"""Cache configuration support classes.

$Id: cache.py,v 1.6 2003/04/28 15:04:38 gvanrossum Exp $
"""

from zope.app.browser.services.configuration import AddComponentConfiguration
from zope.app.interfaces.services.configuration import IUseConfiguration
from zope.component import getAdapter, getServiceManager, getView
from zope.publisher.browser import BrowserView
from zope.app.traversing import traverse

class Caches(BrowserView):

    # self.context is the local caching service

    def getConfigs(self):
        L = []
        for name in self.context.listConfigurationNames():
            cr = self.context.queryConfigurations(name)
            active = cr.active()
            d = {"name": name,
                 "url": "",
                 "configurl": ("@@configureCache.html?name=%s" % name),
                 }
            if active is not None:
                d["url"] = str(getView(active.getComponent(),
                                       "absolute_url",
                                       self.request))
            L.append((name, d))
        L.sort()
        return [d for name, d in L]

class ConfigureCache(BrowserView):

    def update(self):
        cr = self.context.queryConfigurations(self.request['name'])
        form = getView(cr, "ChangeConfigurations", self.request)
        form.update()
        return form

class UseConfiguration(BrowserView):

    """View for displaying the configurations for a cache."""

    def uses(self):
        """Get a sequence of configuration summaries."""
        component = self.context
        useconfig = getAdapter(component, IUseConfiguration)
        result = []
        for path in useconfig.usages():
            config = traverse(component, path)
            url = getView(config, 'absolute_url', self.request)
            result.append({'name': config.name,
                           'path': path,
                           'url': url(),
                           'status': config.status,
                           })
        return result

class AddCacheConfiguration(AddComponentConfiguration):

    pass
