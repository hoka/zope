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
"""Content Workflows Manager

Associates content objects with some workflow process definitions.

$Id: contentworkflow.py,v 1.7 2003/07/30 00:00:25 srichter Exp $
"""
__metaclass__ = type

from persistence import Persistent
from persistence.dict import PersistentDict
from zope.component import getService, queryAdapter
from zope.context import ContextMethod

from zope.app.interfaces.event import ISubscriber
from zope.app.interfaces.event import IObjectCreatedEvent
from zope.app.services.servicenames import EventSubscription, Workflows

from zope.app.interfaces.workflow import IProcessInstanceContainer
from zope.app.interfaces.workflow import IProcessInstanceContainerAdaptable
from zope.app.interfaces.workflow.stateful import IContentWorkflowsManager
from zope.interface import implements, providedBy


class ContentWorkflowsManager(Persistent):

    implements(IContentWorkflowsManager, ISubscriber)

    currentlySubscribed = False # Default subscription state

    def __init__(self):
        super(ContentWorkflowsManager, self).__init__()
        self._registry = PersistentDict()

    def notify(self, event):
        """See zope.app.interfaces.event.ISubscriber"""
        obj = event.object

        # check if it implements IProcessInstanceContainerAdaptable
        # This interface ensures that the object can store process instances. 
        if not IProcessInstanceContainerAdaptable.isImplementedBy(obj):
            return

        pi_container = queryAdapter(obj, IProcessInstanceContainer)
        # probably need to adapt to IZopeContainer to use pi_container with
        # context.
        if pi_container is None:
            # Object can't have associated PIs.
            return

        if IObjectCreatedEvent.isImplementedBy(event):
            wfs = getService(self, Workflows)

            # here we will lookup the configured processdefinitions
            # for the newly created compoent. For every pd_name
            # returned we will create a processinstance.
            for pd_name in self.getProcessDefinitionNamesForObject(obj):

                if pd_name in pi_container.keys():
                    continue
                try:
                    pi = wfs.createProcessInstance(pd_name)
                except KeyError:
                    # No registered PD with that name..
                    continue
                pi_container.setObject(pd_name, pi)

    notify = ContextMethod(notify)


    def subscribe(self):
        """See interfaces.workflows.stateful.IContentWorkflowsManager"""
        if self.currentlySubscribed:
            raise ValueError, "already subscribed; please unsubscribe first"
        channel = self._getChannel(None)
        channel.subscribe(self, IObjectCreatedEvent)
        self.currentlySubscribed = True
    subscribe = ContextMethod(subscribe)

    def unsubscribe(self):
        """See interfaces.workflows.stateful.IContentWorkflowsManager"""
        if not self.currentlySubscribed:
            raise ValueError, "not subscribed; please subscribe first"
        channel = self._getChannel(None)
        channel.unsubscribe(self, IObjectCreatedEvent)
        self.currentlySubscribed = False
    unsubscribe = ContextMethod(unsubscribe)

    def isSubscribed(self):
        """See interfaces.workflows.stateful.IContentWorkflowsManager"""
        return self.currentlySubscribed

    def _getChannel(self, channel):
        if channel is None:
            channel = getService(self, EventSubscription)
        return channel
    _getChannel = ContextMethod(_getChannel)

    def getProcessDefinitionNamesForObject(self, object):
        """See interfaces.workflows.stateful.IContentWorkflowsManager"""
        names = ()
        for iface in providedBy(object):
            names += self.getProcessNamesForInterface(iface)
        return names

    def register(self, iface, name):
        """See zope.app.interfaces.workflows.stateful.IContentProcessRegistry"""
        if iface not in self._registry.keys():
            self._registry[iface] = ()
        self._registry[iface] += (name,)
        
    def unregister(self, iface, name):
        """See zope.app.interfaces.workflows.stateful.IContentProcessRegistry"""
        names = list(self._registry[iface])
        names = filter(lambda n: n != name, names)
        if not names:
            del self._registry[iface]
        else:
            self._registry[iface] = tuple(names)

    def getProcessNamesForInterface(self, iface):
        """See zope.app.interfaces.workflows.stateful.IContentProcessRegistry"""
        return self._registry.get(iface, ())

    def getInterfacesForProcessName(self, name):
        ifaces = []
        for iface, names in self._registry.items():
            if name in names:
                ifaces.append(iface)
        return tuple(ifaces)
