#
# Test case for Zope testing
#

# $Id: base.py,v 1.1 2004/08/19 13:59:41 shh42 Exp $

import ZopeLite as Zope

import unittest
import transaction
import profiler
import utils

from AccessControl.SecurityManagement import noSecurityManager

_connections = utils.ConnectionRegistry()



def app():
    '''Opens a ZODB connection and returns the app object.'''
    app = Zope.app()
    _connections.register(app._p_jar)
    return utils.makerequest(app)

def close(app):
    '''Closes the app's ZODB connection.'''
    _connections.close(app._p_jar)

def closeConnections():
    '''Closes all registered ZODB connections.'''
    _connections.closeAll()



class TestCase(profiler.Profiled, unittest.TestCase):
    '''Base test case for Zope testing

       __implements__ = (IZopeTestCase,)

       See doc/IZopeTestCase.py for more
    '''

    def afterSetUp(self):
        '''Called after setUp() has completed. This is
           far and away the most useful hook.
        '''
        pass

    def beforeTearDown(self):
        '''Called before tearDown() is executed.
           Note that tearDown() is not called if
           setUp() fails.
        '''
        pass

    def afterClear(self):
        '''Called after the fixture has been cleared.
           Note that this may occur during setUp() *and*
           tearDown().
        '''
        pass

    def beforeSetUp(self):
        '''Called before the ZODB connection is opened,
           at the start of setUp(). By default begins
           a new transaction.
        '''
        transaction.begin()

    def beforeClose(self):
        '''Called before the ZODB connection is closed,
           at the end of tearDown(). By default aborts
           the transaction.
        '''
        transaction.abort()

    def setUp(self):
        '''Sets up the fixture. Do not override,
           use the hooks instead.
        '''
        try:
            self.beforeSetUp()
            self.app = self._app()
            self._setup()
            self.afterSetUp()
        except:
            self._clear()
            raise

    def tearDown(self):
        '''Tears down the fixture. Do not override,
           use the hooks instead.
        '''
        try:
            self.beforeTearDown()
            self._clear(1)
        except:
            self._clear()
            raise

    def _app(self):
        '''Returns the app object for a test.'''
        return app()

    def _setup(self):
        '''Sets up the fixture. Framework authors may
           override.
        '''

    def _clear(self, call_close_hook=0):
        '''Clears the fixture.'''
        if call_close_hook:
            self.beforeClose()
        self._close()
        self.logout()
        self.afterClear()

    def _close(self):
        '''Closes the ZODB connection.'''
        transaction.abort()
        closeConnections()

    def logout(self):
        '''Logs out.'''
        noSecurityManager()

