"""
Views have an application_url() method to easily retrieve the url of the
application::

  >>> getRootFolder()['cave'] = cave = Cave()
  >>> cave['caveman'] = CaveMan()

Asking for the application_url on the cave returns the URL to the cave::

  >>> from zope.testbrowser.testing import Browser
  >>> browser = Browser()
  >>> browser.handleErrors = False
  >>> browser.open('http://localhost/cave')
  >>> browser.contents
  'http://localhost/cave'
  
Asking for the application_url on the caveman returns the URL to the cave as
well::

  >>> browser.open('http://localhost/cave/caveman')
  >>> browser.contents
  'http://localhost/cave'

You can pass a name to specify a particular view or sub object to add
to the URL::

  >>> browser.open('http://localhost/cave/caveman/second')
  >>> browser.contents
  'http://localhost/cave/second'

application_url also works with empty containers::

  >>> from grok.ftests.url.application import Corridors
  >>> cave['corridors'] = Corridors()
  >>> browser.open('http://localhost/cave/corridors')
  >>> browser.contents
  'http://localhost/cave'
  
"""
import zope.interface

import grok


class Index(grok.View):
    grok.context(zope.interface.Interface)

    def render(self):
        return self.application_url()

class Second(grok.View):
    grok.context(zope.interface.Interface)

    def render(self):
        return self.application_url('second')
    
class Cave(grok.Application, grok.Container):
    pass


class CaveMan(grok.Model):
    pass

class Corridors(grok.Container):
    pass
