"""
  >>> import grok
  >>> grok.grok('grok.ftests.security.require')

Viewing a protected view with insufficient privileges will yield
Unauthorized:

  >>> from zope.testbrowser.testing import Browser
  >>> browser = Browser()
  >>> browser.open("http://localhost/@@cavepainting")
  Traceback (most recent call last):
  httperror_seek_wrapper: HTTP Error 401: Unauthorized

When we log in (e.g. as a manager), we can access the view just fine:

  >>> from zope.app.securitypolicy.rolepermission import rolePermissionManager
  >>> rolePermissionManager.grantPermissionToRole('grok.ViewPainting',
  ...                                             'zope.Manager')
  >>> browser.addHeader('Authorization', 'Basic mgr:mgrpw')
  >>> browser.handleErrors = False
  >>> browser.open("http://localhost/@@cavepainting")
  >>> print browser.contents
  What a beautiful painting.

A view protected with 'zope.Public' is always accessible:

  >>> browser = Browser()
  >>> browser.open("http://localhost/@@publicnudity")
  >>> print browser.contents
  Everybody can see this.
"""

import grok
import zope.interface

grok.define_permission('grok.ViewPainting')

class CavePainting(grok.View):

    grok.context(zope.interface.Interface)
    grok.require('grok.ViewPainting')

    def render(self):
        return 'What a beautiful painting.'

class PublicNudity(grok.View):

    grok.context(zope.interface.Interface)
    grok.require('zope.Public')

    def render(self):
        return 'Everybody can see this.'
