##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id:$
"""
__docformat__ = "reStructuredText"

import base64
import transaction
import persistent
from urllib import urlencode

import zope.interface
from zope.publisher.interfaces.http import IHTTPRequest
from zope.session.interfaces import ISession
from zope.traversing.browser.absoluteurl import absoluteURL

from zope.app.component import hooks
from zope.app.container import contained

from z3c.authenticator import interfaces


class HTTPBasicAuthCredentialsPlugin(persistent.Persistent,
    contained.Contained):


    zope.interface.implements(interfaces.IHTTPBasicAuthCredentialsPlugin)

    realm = 'Zope Application Management'

    protocol = 'http auth'

    def extractCredentials(self, request):
        """Extracts HTTP basic auth credentials from a request.

        First we need to create a request that contains some credentials.

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest(
          ...     environ={'HTTP_AUTHORIZATION': u'Basic bWdyOm1ncnB3'})

        Now create the plugin and get the credentials.

          >>> plugin = HTTPBasicAuthCredentialsPlugin()
          >>> plugin.extractCredentials(request)
          {'login': u'mgr', 'password': u'mgrpw'}

        Make sure we return `None`, if no authentication header has been
        specified.

          >>> print plugin.extractCredentials(TestRequest())
          None

        Also, this plugin can *only* handle basic authentication.

          >>> request = TestRequest(environ={'HTTP_AUTHORIZATION': 'foo bar'})
          >>> print plugin.extractCredentials(TestRequest())
          None

        This plugin only works with HTTP requests.

          >>> from zope.publisher.base import TestRequest
          >>> print plugin.extractCredentials(TestRequest('/'))
          None

        """
        if not IHTTPRequest.providedBy(request):
            return None

        if request._auth:
            if request._auth.lower().startswith(u'basic '):
                credentials = request._auth.split()[-1]
                login, password = base64.decodestring(credentials).split(':')
                return {'login': login.decode('utf-8'),
                        'password': password.decode('utf-8')}
        return None

    def challenge(self, request):
        """Issues an HTTP basic auth challenge for credentials.

        The challenge is issued by setting the appropriate response headers.
        To illustrate, we'll create a plugin:

          >>> plugin = HTTPBasicAuthCredentialsPlugin()

        The plugin adds its challenge to the HTTP response.

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest()
          >>> response = request.response
          >>> plugin.challenge(request)
          True
          >>> response._status
          401
          >>> response.getHeader('WWW-Authenticate', literal=True)
          'basic realm="Zope Application Management"'

        Notice that the realm is quoted, as per RFC 2617.

        The plugin only works with HTTP requests.

          >>> from zope.publisher.base import TestRequest
          >>> request = TestRequest('/')
          >>> response = request.response
          >>> print plugin.challenge(request)
          False

        """
        if not IHTTPRequest.providedBy(request):
            return False
        request.response.setHeader("WWW-Authenticate",
                                   'basic realm="%s"' % self.realm,
                                   literal=True)
        request.response.setStatus(401)
        return True

    def logout(self, request):
        """Always returns False as logout is not supported by basic auth.

          >>> plugin = HTTPBasicAuthCredentialsPlugin()
          >>> from zope.publisher.browser import TestRequest
          >>> plugin.logout(TestRequest())
          False

        """
        return False


class SessionCredentials(object):
    """Credentials class for use with sessions.

    A session credential is created with a login and a password:

      >>> cred = SessionCredentials('scott', 'tiger')

    Logins are read using getLogin:
      >>> cred.getLogin()
      'scott'

    and passwords with getPassword:

      >>> cred.getPassword()
      'tiger'

    """
    zope.interface.implements(interfaces.ISessionCredentials)

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def getLogin(self): return self.login

    def getPassword(self): return self.password

    def __str__(self): return self.getLogin() + ':' + self.getPassword()


class SessionCredentialsPlugin(persistent.Persistent, contained.Contained):
    """A credentials plugin that uses Zope sessions to get/store credentials.

    To illustrate how a session plugin works, we'll first setup some session
    machinery:

      >>> from zope.app.testing import placelesssetup
      >>> from z3c.authenticator.testing import sessionSetUp
      >>> placelesssetup.setUp()
      >>> sessionSetUp()

    This lets us retrieve the same session info from any test request, which
    simulates what happens when a user submits a session ID as a cookie.

    We also need a session plugin:

      >>> plugin = SessionCredentialsPlugin()

    A session plugin uses an ISession component to store the last set of
    credentials it gets from a request. Credentials can be retrieved from
    subsequent requests using the session-stored credentials.

    If the given extractCredentials argument doesn't provide IHTTPRequest the
    result will always be None:

      >>> print plugin.extractCredentials(None)
      None

    Our test environment is initially configured without credentials:

      >>> from zope.publisher.tests.httprequest import TestRequest
      >>> request = TestRequest()
      >>> print plugin.extractCredentials(request)
      None

    We must explicitly provide credentials once so the plugin can store
    them in a session:

      >>> request = TestRequest(login='scott', password='tiger')
      >>> plugin.extractCredentials(request)
      {'login': 'scott', 'password': 'tiger'}

    Subsequent requests now have access to the credentials even if they're
    not explicitly in the request:

      >>> plugin.extractCredentials(TestRequest())
      {'login': 'scott', 'password': 'tiger'}

    We can always provide new credentials explicitly in the request:

      >>> plugin.extractCredentials(TestRequest(
      ...     login='harry', password='hirsch'))
      {'login': 'harry', 'password': 'hirsch'}

    and these will be used on subsequent requests:

      >>> plugin.extractCredentials(TestRequest())
      {'login': 'harry', 'password': 'hirsch'}

    We can also change the fields from which the credentials are extracted:

      >>> plugin.loginfield = "my_new_login_field"
      >>> plugin.passwordfield = "my_new_password_field"

    Now we build a request that uses the new fields:

      >>> request = TestRequest(my_new_login_field='luke', my_new_password_field='the_force')

    The plugin now extracts the credentials information from these new fields:

      >>> plugin.extractCredentials(request)
      {'login': 'luke', 'password': 'the_force'}

    Finally, we clear the session credentials using the logout method.
    If the given logout argument doesn't provide IHTTPRequest the
    result will always be False:

      >>> plugin.logout(None)
      False

    Now try to logout with the correct argument:

      >>> plugin.logout(TestRequest())
      True

    After logout we can not logaout again:

      >>> print plugin.extractCredentials(TestRequest())
      None

    """
    zope.interface.implements(interfaces.ISessionCredentialsPlugin)

    challengeProtocol = None

    loginpagename = 'loginForm.html'
    loginfield = 'login'
    passwordfield = 'password'

    def extractCredentials(self, request):
        """Extracts credentials from a session if they exist."""
        if not IHTTPRequest.providedBy(request):
            return None
        session = ISession(request, None)
        sessionData = session.get('z3c.authenticator.credential.session')
        login = request.get(self.loginfield, None)
        password = request.get(self.passwordfield, None)
        credentials = None

        if login and password:
            credentials = SessionCredentials(login, password)
        elif not sessionData:
            return None
        sessionData = session['z3c.authenticator.credential.session']
        if credentials:
            sessionData['credentials'] = credentials
        else:
            credentials = sessionData.get('credentials', None)
        if not credentials:
            return None
        return {'login': credentials.getLogin(),
                'password': credentials.getPassword()}

    def challenge(self, request):
        """Challenges by redirecting to a login form.

        To illustrate, we'll create a test request:

          >>> from zope.publisher.browser import TestRequest
          >>> request = TestRequest()

        and confirm its response's initial status and 'location' header:

          >>> request.response.getStatus()
          599
          >>> request.response.getHeader('location')

        When we issue a challenge using a session plugin:

          >>> plugin = SessionCredentialsPlugin()
          >>> plugin.challenge(request)
          True

        we get a redirect:

          >>> request.response.getStatus()
          302
          >>> request.response.getHeader('location')
          'http://127.0.0.1/@@loginForm.html?camefrom=%2F'

        The plugin redirects to the page defined by the loginpagename
        attribute:

          >>> plugin.loginpagename = 'mylogin.html'
          >>> plugin.challenge(request)
          True
          >>> request.response.getHeader('location')
          'http://127.0.0.1/@@mylogin.html?camefrom=%2F'

        It also provides the request URL as a 'camefrom' GET style parameter.
        To illustrate, we'll pretend we've traversed a couple names:

          >>> env = {
          ...     'REQUEST_URI': '/foo/bar/folder/page%201.html?q=value',
          ...     'QUERY_STRING': 'q=value'
          ...     }
          >>> request = TestRequest(environ=env)
          >>> request._traversed_names = [u'foo', u'bar']
          >>> request._traversal_stack = [u'page 1.html', u'folder']
          >>> request['REQUEST_URI']
          '/foo/bar/folder/page%201.html?q=value'

        When we challenge:

          >>> plugin.challenge(request)
          True

        We see the 'camefrom' points to the requested URL:

          >>> request.response.getHeader('location') # doctest: +ELLIPSIS
          '.../@@mylogin.html?camefrom=%2Ffoo%2Fbar%2Ffolder%2Fpage+1.html%3Fq%3Dvalue'

        If the given challenge argument doesn't provide IHTTPRequest the
        result will always be False:

          >>> plugin.challenge(None)
          False

        This can be used by the login form to redirect the user back to the
        originating URL upon successful authentication.
        """
        if not IHTTPRequest.providedBy(request):
            return False

        site = hooks.getSite()
        # We need the traversal stack to complete the 'camefrom' parameter
        stack = request.getTraversalStack()
        stack.reverse()
        # Better to add the query string, if present
        query = request.get('QUERY_STRING')

        camefrom = '/'.join([request.getURL(path_only=True)] + stack)
        if query:
            camefrom = camefrom + '?' + query
        url = '%s/@@%s?%s' % (absoluteURL(site, request),
                              self.loginpagename,
                              urlencode({'camefrom': camefrom}))
        request.response.redirect(url)
        return True

    def logout(self, request):
        """Performs logout by clearing session data credentials."""
        if not IHTTPRequest.providedBy(request):
            return False

        sessionData = ISession(request)['z3c.authenticator.credential.session']
        sessionData['credentials'] = None
        transaction.commit()
        return True
