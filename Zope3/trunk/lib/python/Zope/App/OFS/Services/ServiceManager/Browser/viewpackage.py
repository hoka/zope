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

Revision information: $Id: viewpackage.py,v 1.2 2002/12/19 20:38:25 jim Exp $
"""
from Zope.App.OFS.Container.Views.Browser.Contents import Contents
from Zope.App.OFS.Services.ServiceManager.IServiceManager \
     import IServiceManager
from Zope.App.OFS.Services.zpt import ZPTTemplate


from Zope.Publisher.Browser.BrowserView import BrowserView

from Zope.App.PageTemplate import ViewPageTemplateFile
from Zope.App.OFS.Container.IContainer import IContainer
from Zope.ComponentArchitecture import queryView, getView

class ViewPackageContents(Contents):

    __used_for__ = IServiceManager

    index = ViewPageTemplateFile('viewpackage_contents.pt')

    def add(self, name):
        self.context.setObject(name, ZPTTemplate())
        self.request.response.redirect('.')
