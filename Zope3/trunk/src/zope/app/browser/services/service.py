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
"""View support for adding and configuring services and other components.

$Id: service.py,v 1.8 2003/03/08 01:51:38 gvanrossum Exp $
"""

from zope.app.browser.container.adding import Adding
from zope.component import getView, getAdapter
from zope.proxy.context import ContextWrapper, ContextSuper
from zope.app.interfaces.container import IZopeContainer
from zope.component import getServiceManager
from zope.publisher.browser import BrowserView
from zope.app.services.service import ServiceConfiguration
from zope.app.interfaces.services.configuration import IConfiguration
from zope.app.form.utility import setUpWidgets, getWidgetsDataForContent
from zope.app.traversing import traverse, getPhysicalPathString
from zope.app.traversing import getPhysicalPath
from zope.app.interfaces.services.interfaces import ILocalService
from zope.proxy.context import getWrapperContainer
from zope.app.interfaces.services.configuration \
     import Unregistered, Registered, Active

__metaclass__ = type

class ComponentAdding(Adding):
    """Adding subclass used for configurable components."""

    menu_id = "add_component"

    def action(self, type_name, id):
        if type_name == "../AddService":
            # Special case
            url = type_name
            if id:
                url += "?id=" + id
            self.request.response.redirect(url)
            return

        if not id:
            # Generate an id from the type name
            id = type_name
            l = id.rfind('.')
            if l >= 0:
                id = id[l+1:]
            i = 1
            while ("%s-%s" % (id, i)) in self.context:
                i=i+1
            id = "%s-%s" % (id, i)

        # Call the superclass action() method.
        # As a side effect, self.added_object is set by add() above.
        ContextSuper(ComponentAdding, self).action(type_name, id)


class ServiceAdding(ComponentAdding):
    """Adding subclass used for adding services."""

    menu_id = "add_service"

    def add(self, content):
        # Override so as to save a reference to the added object
        self.added_object = ContextSuper(ComponentAdding, self).add(content)
        return self.added_object

    def action(self, type_name, id):
        # Call the superclass action() method.
        # As a side effect, self.added_object is set by add() above.
        ContextSuper(ServiceAdding, self).action(type_name, id)

        if not ILocalService.isImplementedBy(self.added_object):
            raise TypeError("%s is not a local service" % self.added_object)

        url = getPhysicalPathString(self.added_object)
        self.request.response.redirect(url + "/addConfiguration.html")


class ConfigurationAdding(Adding):
    """Adding subclass for adding configurations."""

    menu_id = "add_configuration"


class EditConfiguration(BrowserView):
    """Adding component for service containers."""

    menu_id = "add_component"

    def __init__(self, context, request):
        self.request = request
        self.context = context

    def action(self):
        """Perform actions depending on user input."""
        if 'add_submit' in self.request:
            self.request.response.redirect('+')
            return ''

        if 'keys' in self.request:
            k = self.request['keys']
        else:
            k = []

        msg = 'You must select at least one item to use this action'

        if 'remove_submit' in self.request:
            if not k: return msg
            self.remove_objects(k)
        elif 'top_submit' in self.request:
            if not k: return msg
            self.context.moveTop(k)
        elif 'bottom_submit' in self.request:
            if not k: return msg
            self.context.moveBottom(k)
        elif 'up_submit' in self.request:
            if not k: return msg
            self.context.moveUp(k)
        elif 'down_submit' in self.request:
            if not k: return msg
            self.context.moveDown(k)

        return ''

    def remove_objects(self, key_list):
        """Remove the directives from the container."""
        container = getAdapter(self.context, IZopeContainer)
        for item in key_list:
            del container[item]

    def configInfo(self):
        """Render View for each directives."""
        r = []
        for name, directive in self.context.items():
            d = ContextWrapper(directive, self.context, name = name)
            view = getView(d, 'ItemEdit', self.request)
            view.setPrefix('config'+str(name))
            r.append({'key': name, 'view': view})
        return r


class AddServiceConfiguration(BrowserView):
    """A view on a service implementation, used by add_svc_config.py."""

    def listServiceTypes(self):

        # Collect all defined services interfaces that it implements.
        sm = getServiceManager(self.context)
        lst = []
        for servicename, interface in sm.getServiceDefinitions():
            if interface.isImplementedBy(self.context):
                registry = sm.queryConfigurations(servicename)
                checked = True
                if registry and registry.active():
                    checked = False
                d = {'name': servicename, 'checked': checked}
                lst.append(d)
        return lst

    def action(self, name=[], active=[]):
        path = getPhysicalPathString(self.context)
        configure = traverse(getWrapperContainer(self.context), 'configure')
        container = getAdapter(configure, IZopeContainer)

        for nm in name:
            # XXX Shouldn't hardcode 'configure'
            sc = ServiceConfiguration(nm, path, self.context)
            name = container.setObject("", sc)
            sc = container[name]
            if nm in active:
                sc.status = Active
            else:
                sc.status = Registered

        self.request.response.redirect("@@useConfiguration.html")


class ServiceSummary(BrowserView):
    """A view on the service manager, used by services.pt."""

    def listConfiguredServices(self):
        names = list(self.context.listConfigurationNames())
        names.sort()

        items = []
        for name in names:
            registry = self.context.queryConfigurations(name)
            assert registry
            infos = registry.info()
            assert infos
            if infos[0]['active']:
                # XXX This assumes if there is an active one it is the
                # first one.  The implementation promises this, but
                # the interface does not.  However Jim doesn't want
                # the implementation changed so I guess the interface
                # docs should be fixed.
                configobj = infos[0]['configuration']
                component = configobj.getComponent()
                url = str(getView(component, 'absolute_url', self.request))
            else:
                url = ""
            items.append({'name': name, 'url': url})

        return items


class ServiceActivation(BrowserView):
    """A view on the service manager, used by serviceactivation.pt.

    This really wants to be a view on a configuration registry
    containing service configurations, but registries don't have names,
    so we make it a view on the service manager; the request parameter
    'type' determines which service is to be configured."""

    def isDisabled(self):
        sm = getServiceManager(self.context)
        registry = sm.queryConfigurations(self.request.get('type'))
        return not (registry and registry.active())

    def listRegistry(self):
        sm = getServiceManager(self.context)
        registry = sm.queryConfigurations(self.request.get('type'))
        if not registry:
            return []

        result = []
        for info in registry.info():
            configobj = info['configuration']
            component = configobj.getComponent()
            path = getPhysicalPath(component)
            info['name'] = "/".join(path[-2:])
            info['url'] = str(getView(component, 'absolute_url', self.request))
            info['config'] = str(getView(configobj, 'absolute_url',
                                         self.request))
            result.append(info)
        return result

    def action(self):
        active = self.request.get("active")
        if not active:
            return ""

        sm = getServiceManager(self.context)
        registry = sm.queryConfigurations(self.request.get('type'))
        if not registry:
            return "Invalid service type specified"
        old_active = registry.active()
        if active == "None":
            new_active = None
        else:
            new_active = traverse(sm, "Packages/" + active)
        if old_active == new_active:
            return "No change"

        if new_active is None:
            old_active.status = Registered
            return "Service deactivated"
        else:
            new_active.status = Active
            return active + " activated"
