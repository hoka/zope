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
$Id: IHubEvent.py,v 1.3 2002/10/03 20:53:22 jim Exp $
"""
from Zope.Event.IEvent import IEvent
from Interface.Attribute import Attribute

class IHubEvent(IEvent):
    """Internal Object Hub Event : something has happened to an object for
       which there is an ruid.
       An ruid is a way of refering to an object independent of location.
    """

    object = Attribute("The subject of the event.")

    hid = Attribute("the object's hub-unique id")

    location = Attribute("An optional object location.")
   

class IRegistrationHubEvent(IHubEvent):
    """Some work could be done on registration or deregistration of an object.
    """

class IObjectRegisteredHubEvent(IRegistrationHubEvent):
    """An ruid has been freshly created and mapped against an object."""


class IObjectUnregisteredHubEvent(IRegistrationHubEvent):
    """We are no longer interested in this object."""


class IObjectAddedHubEvent(IObjectRegisteredHubEvent):
    """An ruid has been freshly created and mapped against an object.
       Also, implies the object has been newly added."""
    
    
class IObjectModifiedHubEvent(IHubEvent):
    """An object with an ruid has been modified."""
    
    
class IObjectMovedHubEvent(IHubEvent):
    """An object with an ruid has had its context changed. Typically, this
       means that it has been moved."""

    fromLocation = Attribute("The old location for the object.")

class IObjectRemovedHubEvent(IHubEvent):
    """An object with an ruid has been removed."""
