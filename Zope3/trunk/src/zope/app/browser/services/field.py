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
"""A widget for ComponentPath field.

$Id: field.py,v 1.14 2003/08/17 06:05:47 philikon Exp $
"""

from zope.app.browser.form.widget import BrowserWidget
from zope.app.traversing import traverse
from zope.component import getServiceManager, getView

__metaclass__ = type


class ComponentPathWidget(BrowserWidget):

    def _convert(self, value):
        return value or None

    def __call__(self):
        selected = self._showData()
        field = self.context
        return renderPathSelect(field.context, field.type,
                                self.name, selected)


class ComponentPathDisplayWidget(ComponentPathWidget):

    def __call__(self):
        path = self._showData()
        path = canonicalPath(path)
        ob = traverse(self.context.context, path)
        url = str(getView(ob, 'absolute_url', self.request))
        url += "/@@SelectedManagementView.html"
        return '<a href="%s">%s</a>' % (url, path)


def renderPathSelect(context, type, name, selected, empty_message=''):
    service_manager = getServiceManager(context)
    info = service_manager.queryComponent(type)
    result = []

    result.append('<select name="%s">' % name)
    result.append('<option>%s</option>' % empty_message)

    for item in info:
        item = item['path']
        if item == selected:
            result.append('<option selected>%s</option>' % item)
        else:
            result.append('<option>%s</option>' % item)

    result.append('</select>')
    return ''.join(result)

