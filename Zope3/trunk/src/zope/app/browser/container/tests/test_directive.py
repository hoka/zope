##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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

import re
import pprint
import cStringIO

import unittest
from zope.interface import Interface
from zope.testing.doctestunit import DocTestSuite
from zope.app.browser.container.metaconfigure import containerViews

atre = re.compile(' at [0-9a-fA-Fx]+')

class Context:
    actions = ()
    
    def action(self, discriminator, callable, args):
        self.actions += ((discriminator, callable, args), )

    def __repr__(self):
        stream = cStringIO.StringIO()
        pprinter = pprint.PrettyPrinter(stream=stream, width=60)
        pprinter.pprint(self.actions)
        r = stream.getvalue()
        return (''.join(atre.split(r))).strip()

class I(Interface):
    pass

def test_containerViews():
    """
    >>> context = Context()
    >>> containerViews(context, for_=I, contents='zope.ManageContent',
    ...                add='zope.ManageContent', index='zope.View')
    >>> context
    ((('browser:menuItem',
       'zmi_views',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       u'Contents'),
      <bound method GlobalBrowserMenuService.menuItem of <zope.app.publisher.browser.globalbrowsermenuservice.GlobalBrowserMenuService object>>,
      ('zmi_views',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       '@@contents.html',
       u'Contents',
       '',
       None,
       'zope.ManageContent',
       None)),
     (None,
      <function checkPermission>,
      (None, 'zope.ManageContent')),
     (None,
      <function handler>,
      ('Interfaces',
       'provideInterface',
       None,
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>)),
     (('view',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       'contents.html',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       'default'),
      <function handler>,
      ('Presentation',
       'provideView',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       'contents.html',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       [<class 'zope.app.publisher.browser.viewmeta.Contents'>],
       'default')),
     (None,
      <function _handle_usage_from_menu>,
      (<class 'zope.app.publisher.browser.viewmeta.Contents'>,
       'zmi_views')),
     (None,
      <function checkPermission>,
      (None, 'zope.View')),
     (None,
      <function handler>,
      ('Interfaces',
       'provideInterface',
       None,
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>)),
     (('view',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       'index.html',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       'default'),
      <function handler>,
      ('Presentation',
       'provideView',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       'index.html',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       [<class 'zope.app.publisher.browser.viewmeta.Contents'>],
       'default')),
     (('browser:menuItem',
       'zmi_actions',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       u'Add'),
      <bound method GlobalBrowserMenuService.menuItem of <zope.app.publisher.browser.globalbrowsermenuservice.GlobalBrowserMenuService object>>,
      ('zmi_actions',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       '@@+',
       u'Add',
       '',
       None,
       'zope.ManageContent',
       None)),
     (None,
      <function checkPermission>,
      (None, 'zope.ManageContent')),
     (None,
      <function handler>,
      ('Interfaces',
       'provideInterface',
       None,
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>)),
     (None,
      <function handler>,
      ('Interfaces',
       'provideInterface',
       'zope.interface.Interface',
       <InterfaceClass zope.interface.Interface>)),
     (('view',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       '+',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       'default',
       <InterfaceClass zope.interface.Interface>),
      <function handler>,
      ('Presentation',
       'provideView',
       <InterfaceClass zope.app.browser.container.tests.test_directive.I>,
       '+',
       <InterfaceClass zope.publisher.interfaces.browser.IBrowserRequest>,
       [<class 'zope.app.publisher.browser.viewmeta.+'>],
       'default',
       <InterfaceClass zope.interface.Interface>)))
    """
    
       
def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main()
