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
$Id: EventChannel.py,v 1.2 2002/06/10 23:29:25 jim Exp $
"""

from Subscribable import Subscribable
from IEventChannel import IEventChannel

class EventChannel(Subscribable):
    
    __implements__ = IEventChannel
        
    def notify(self, event):
        
        subscriptionses = self._registry.getAllForObject(event)

        for subscriptions in subscriptionses:
            
            for subscriber,filter in subscriptions:
                if filter is not None and not filter(event):
                    continue
                subscriber.notify(event)

    

    
