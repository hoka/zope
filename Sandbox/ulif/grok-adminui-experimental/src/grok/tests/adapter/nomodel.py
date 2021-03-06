"""
If no model can be found in the module, we get an error:

  >>> grok.grok(__name__)
  Traceback (most recent call last):
    ...
  GrokError: No module-level context for
  <class 'grok.tests.adapter.nomodel.Home'>, please use grok.context.

"""
import grok
from zope import interface

class IHome(interface.Interface):
    pass

class Home(grok.Adapter):
    grok.implements(IHome)
