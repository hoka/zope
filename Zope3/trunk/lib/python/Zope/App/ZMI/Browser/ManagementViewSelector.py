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
$Id: ManagementViewSelector.py,v 1.2 2002/10/03 12:25:14 jim Exp $
"""

__metaclass__ = type

from Zope.ComponentArchitecture import getService
from Zope.Publisher.Browser.BrowserView import BrowserView
from Zope.Publisher.Browser.IBrowserPublisher import IBrowserPublisher
from Zope.Exceptions import Unauthorized

class ManagementViewSelector(BrowserView):
    """View that selects the first available management view
    """

    __implements__ = BrowserView.__implements__, IBrowserPublisher

    def browserDefault(self, request):
        return self, ()

    def __call__(self):
        context = self.context
        request = self.request
        browser_menu_service = getService(context, 'BrowserMenu')
        item = browser_menu_service.getFirstMenuItem(
            'zmi_views', context, request)
        if item:
            request.response.redirect(item['action'])
            return ''

        request.response.redirect('.') # Redirect to content/
        
        

__doc__ = ManagementViewSelector.__doc__ + __doc__

