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
"""Views for local view configuration.

  ViewSeviceView -- it's a bit different from other services, as it
  has a lot of things in it, so we provide a search interface:

    search page
    browsing page

  ViewConfigrationAdd

$Id: view.py,v 1.2 2002/12/19 20:38:23 jim Exp $
"""
__metaclass__ = type

import md5
from Zope.App.Forms.Utility \
     import setUpWidgets, getWidgetsData, getWidgetsDataForContent, fieldNames
from Zope.Publisher.Browser.BrowserView import BrowserView
from Zope.App.OFS.Services.interfaces \
     import IViewConfiguration, IViewConfigurationInfo
from Zope.App.OFS.Services.interfaces \
     import IPageConfiguration, IPageConfigurationInfo
from Zope.Event import publish
from Zope.Event.ObjectEvent import ObjectCreatedEvent
from Zope.App.OFS.Services.ConfigurationInterfaces import IConfiguration
from Zope.App.OFS.Services.view import ViewConfiguration, PageConfiguration
from Zope.App.ComponentArchitecture.InterfaceField import InterfaceField
from Interface import Interface
from Zope.ComponentArchitecture import getView
from Zope.Proxy.ContextWrapper import ContextWrapper
from Zope.Schema import TextLine, BytesLine
from Zope.ComponentArchitecture.IPresentation import IPresentation

class IViewSearch(Interface):

    forInterface = InterfaceField(title=u"For interface",
                                  required=False,
                                  )
    presentationType = InterfaceField(title=u"Provided interface",
                                      required=False,
                                      type=IPresentation
                                      )

    viewName = TextLine(title=u'View name',
                        required=False,
                        )

    layer = BytesLine(title=u'Layer',
                      required=False,
                        )
    

class ViewServiceView(BrowserView):

    def __init__(self, *args):
        super(ViewServiceView, self).__init__(*args)
        setUpWidgets(self, IViewSearch)
    
    def configInfo(self):
        input_for = self.forInterface.getData()
        input_type = self.presentationType.getData()
        input_name = self.viewName.getData()
        input_layer = self.layer.getData()

        result = []
        for info in self.context.getRegisteredMatching(
            input_for, input_type, input_name, input_layer):

            forInterface, presentationType, registry, layer, viewName = info
            
            forInterface = (
                forInterface.__module__ +"."+ forInterface.__name__)
            presentationType = (
                presentationType.__module__ +"."+ presentationType.__name__)

            registry = ContextWrapper(registry, self.context)
            view = getView(registry, "ChangeConfigurations", self.request)
            prefix = md5.new('%s %s' %
                             (forInterface, presentationType)).hexdigest()
            view.setPrefix(prefix)
            view.update()

            if input_name is not None:
                viewName = None

            if input_layer is not None:
                layer = None
            
            result.append(
                {'forInterface': forInterface,
                 'presentationType': presentationType,
                 'view': view,
                 'viewName': viewName,
                 'layer': layer,
                 })

        return result
