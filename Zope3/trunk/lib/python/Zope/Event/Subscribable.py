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

Revision information:
$Id: Subscribable.py,v 1.6 2002/12/05 17:18:12 stevea Exp $
"""
__metaclass__ = type

from Interface.Registry.TypeRegistry import TypeRegistry
from Zope.Exceptions import NotFoundError
from ISubscribable import ISubscribable
from ISubscriptionAware import ISubscriptionAware
from IEvent import IEvent
from Zope.Proxy.ProxyIntrospection import removeAllProxies

class Subscribable:
    """a global mix-in"""
    
    __implements__ = ISubscribable
        # plus has subscriptionsForEvent

    def __init__(self):
        self._registry = TypeRegistry()
        self._subscribers = [] # using a list rather than a dict so
        # that subscribers may define custom __eq__ methods
        
    _clear = __init__

    def subscribe(self, subscriber, event_type=IEvent, filter=None):
        clean_subscriber = removeAllProxies(subscriber)
        
        if ISubscriptionAware.isImplementedBy(subscriber):
            subscriber.subscribedTo(self, event_type, filter)
        
        if event_type is IEvent:
            event_type = None # optimization
        
        subscribers = self._registry.setdefault(event_type, [])
        subscribers.append((clean_subscriber, filter))

        for sub in self._subscribers:
            if sub[0] == clean_subscriber:
                sub[1][event_type] = 1
                break
        else:
            self._subscribers.append((clean_subscriber, {event_type: 1}))

        self._registry = self._registry #trigger persistence, if pertinent
        
    
    def unsubscribe(self, subscriber, event_type=None, filter=None):
        
        clean_subscriber=removeAllProxies(subscriber)
        
        for subscriber_index in range(len(self._subscribers)):
            sub=self._subscribers[subscriber_index]
            if sub[0]==clean_subscriber:
                ev_set=sub[1]
                break
        else:
            if event_type: raise NotFoundError(subscriber)
            else: return # this was a generic unsubscribe all request;
            # work may have been done by a local service
        
        
        do_alert=ISubscriptionAware.isImplementedBy(clean_subscriber)
        
        if event_type:
            ev_type=event_type
            if event_type is IEvent:
                ev_type=None # handle optimization
            if ev_type not in ev_set:
                raise NotFoundError(subscriber, event_type, filter)
            subscriptions = self._registry.get(ev_type)
            if not subscriptions:
                raise NotFoundError(subscriber, event_type, filter)
            try: 
                subscriptions.remove((clean_subscriber, filter))
            except ValueError:
                raise NotFoundError(subscriber, event_type, filter)
            if do_alert:
                subscriber.unsubscribedFrom(self, event_type, filter)
            if len(ev_set)==1:
                for sub in subscriptions:
                    if sub[0]==clean_subscriber:
                        break
                else:
                    del self._subscribers[subscriber_index]
        else:
            for ev_type in ev_set:
                subscriptions = self._registry.get(ev_type)
                subs=subscriptions[:]
                subscriptions[:] = []
                for sub in subs:
                    if sub[0] == clean_subscriber: # deleted (not added back)
                        if do_alert:
                            subscriber.unsubscribedFrom(
                                self, ev_type or IEvent, sub[1])
                            # IEvent switch is to make optimization transparent
                    else: # kept (added back)
                        subscriptions.append(sub)
            del self._subscribers[subscriber_index]
        self._registry=self._registry #trigger persistence, if pertinent

    def subscriptionsForEvent(self, event):
        # XXX currently a non-interface method:
        # just a more readable prettification
        # used only for notify methods now.  Could this be replaced
        # with an explanatory comment in the code that uses it?
        return self._registry.getAllForObject(event)
    
    def listSubscriptions(self, subscriber, event_type=None):
        
        subscriber=removeAllProxies(subscriber)
        
        result=[]
        if event_type:
            ev_type=event_type
            if event_type is IEvent:
                ev_type=None # handle optimization
            subscriptions = self._registry.get(ev_type)
            if subscriptions:
                for sub in subscriptions:
                    if sub[0]==subscriber:
                        result.append((event_type, sub[1]))
        else:
            for subscriber_index in range(len(self._subscribers)):
                sub=self._subscribers[subscriber_index]
                if sub[0]==subscriber:
                    ev_set=sub[1]
                    break
            else:
                return result
            for ev_type in ev_set:
                subscriptions = self._registry.get(ev_type)
                if subscriptions:
                    for sub in subscriptions:
                        if sub[0]==subscriber:
                            result.append((ev_type or IEvent, sub[1]))
        return result
