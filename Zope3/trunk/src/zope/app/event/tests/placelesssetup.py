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
"""Unit test logic for setting up and tearing down basic infrastructure


$Id: placelesssetup.py,v 1.7 2003/02/12 02:17:22 seanb Exp $
"""

from zope.component import getServiceManager
from zope.app.services.servicenames import Events
from zope.app.interfaces.event import IPublisher, ISubscriber
from zope.app.event.globalservice import eventPublisher
from zope.interface import Interface

events = []

class EventRecorderClass:
    __implements__ = ISubscriber

    notify = events.append

EventRecorder = EventRecorderClass()

def getEvents(event_type=None, filter=None):
    r = []
    for event in events:
        if event_type is not None and not event_type.isImplementedBy(event):
            continue
        if filter is not None and not filter(event):
            continue
        r.append(event)

    return r

class PlacelessSetup:

    def setUp(self):
        sm = getServiceManager(None)
        defineService = sm.defineService
        provideService = sm.provideService

        defineService(Events, IPublisher)
        provideService(Events, eventPublisher)

        del events[:]
        eventPublisher.globalSubscribe(EventRecorder)
