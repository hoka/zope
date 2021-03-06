#
# Support for ZODB sandboxes in ZTC
#

# $Id: sandbox.py,v 1.2 2004/08/19 15:31:26 shh42 Exp $

import ZopeLite as Zope
import transaction
import utils


class Sandboxed:
    '''Derive from this class and an xTestCase to make each test
       run in its own ZODB sandbox::

           class MyTest(Sandboxed, ZopeTestCase):
               ...
    '''

    def _app(self):
        '''Returns the app object for a test.'''
        app = Zope.app(Zope.sandbox().open())
        AppZapper().set(app)
        return utils.makerequest(app)

    def _close(self):
        '''Clears the transaction and the AppZapper.'''
        transaction.abort()
        AppZapper().clear()


class AppZapper:
    '''Application object share point'''

    __shared_state = {'_app': None}

    def __init__(self):
        self.__dict__ = self.__shared_state

    def set(self, app):
        self._app = app

    def clear(self):
        self._app = None

    def app(self):
        return self._app


def __bobo_traverse__(self, REQUEST=None, name=None):
    '''Makes ZPublisher.publish() use the current app object.'''
    app = AppZapper().app()
    if app is not None:
        return app
    return self.__old_bobo_traverse__(REQUEST, name)


from ZODB.ZApplication import ZApplicationWrapper
if not hasattr(ZApplicationWrapper, '__old_bobo_traverse__'):
    ZApplicationWrapper.__old_bobo_traverse__ = ZApplicationWrapper.__bobo_traverse__
    ZApplicationWrapper.__bobo_traverse__ = __bobo_traverse__

