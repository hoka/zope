##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Functional testing framework for Zope 3.

There should be a file 'ftesting.zcml' in the current directory.

$Id$
"""
import logging
import re
import rfc822
import sys
import traceback
import unittest
import urllib

from StringIO import StringIO
from Cookie import SimpleCookie

from transaction import abort, commit
from ZODB.DB import DB
from ZODB.DemoStorage import DemoStorage
import zope.interface
from zope.publisher.browser import BrowserRequest
from zope.publisher.http import HTTPRequest
from zope.publisher.publish import publish
from zope.publisher.xmlrpc import XMLRPCRequest
from zope.security.interfaces import Forbidden, Unauthorized
from zope.security.management import endInteraction
import zope.server.interfaces
from zope.testing import doctest

from zope.app.debug import Debugger
import zope.app.pluggableauth
from zope.app.publication.http import HTTPPublication
from zope.app.publication.browser import BrowserPublication
from zope.app.publication.xmlrpc import XMLRPCPublication
from zope.app.publication.zopepublication import ZopePublication
from zope.app.publication.http import HTTPPublication
import zope.app.tests.setup
from zope.app.component.hooks import setSite, getSite

HTTPTaskStub = StringIO

class ResponseWrapper(object):
    """A wrapper that adds several introspective methods to a response."""

    def __init__(self, response, outstream, path):
        self._response = response
        self._outstream = outstream
        self._path = path

    def getOutput(self):
        """Returns the full HTTP output (headers + body)"""
        return self._outstream.getvalue()

    def getBody(self):
        """Returns the response body"""
        output = self._outstream.getvalue()
        idx = output.find('\r\n\r\n')
        if idx == -1:
            return None
        else:
            return output[idx+4:]

    def getPath(self):
        """Returns the path of the request"""
        return self._path

    def __getattr__(self, attr):
        return getattr(self._response, attr)


grant_request = r"""
POST /@@PrincipalRoles.html HTTP/1.1
Authorization: Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3
Content-Length: 97
Content-Type: application/x-www-form-urlencoded
Referer: http://localhost:8081/@@PrincipalRoles.html

grid.zope.Manager.zope.mgr=Allow&principals%3Alist=zope.mgr&roles%3Alist=zope.Manager&APPLY=Apply"""

class FunctionalTestSetup(object):
    """Keeps shared state across several functional test cases."""

    __shared_state = { '_init': False }

    def __init__(self, config_file=None):
        """Initializes Zope 3 framework.

        Creates a volatile memory storage.  Parses Zope3 configuration files.
        """
        self.__dict__ = self.__shared_state

        if not self._init:

            # Make sure unit tests are cleaned up
            zope.app.tests.setup.placefulSetUp()
            zope.app.tests.setup.placefulTearDown()

            if not config_file:
                config_file = 'ftesting.zcml'
            self.log = StringIO()
            # Make it silent but keep the log available for debugging
            logging.root.addHandler(logging.StreamHandler(self.log))
            self.base_storage = DemoStorage("Memory Storage")
            self.db = DB(self.base_storage)
            self.app = Debugger(self.db, config_file)
            self.connection = None
            self._config_file = config_file
            self._init = True

            # Make a local grant for the test user
            # TODO, find a better way to make this grant happen.
            # The way I did this is way too messy, given how
            # strang FunctionalTestSetup is.  Later, when we
            # have time, we should clean up this (perhaps with an
            # event) and clean up FunctionalTestSetup.
            response = http(grant_request, handle_errors=False)
            FunctionalTestSetup().connection = None
            
        elif config_file and config_file != self._config_file:
            # Running different tests with different configurations is not
            # supported at the moment
            raise NotImplementedError('Already configured'
                                      ' with a different config file')

    def setUp(self):
        """Prepares for a functional test case."""
        # Tear down the old demo storage (if any) and create a fresh one
        abort()
        self.db.close()
        storage = DemoStorage("Demo Storage", self.base_storage)
        self.db = self.app.db = DB(storage)
        self.connection = None

    def tearDown(self):
        """Cleans up after a functional test case."""
        abort()
        if self.connection:
            self.connection.close()
            self.connection = None
        self.db.close()

    def getRootFolder(self):
        """Returns the Zope root folder."""
        if not self.connection:
            self.connection = self.db.open()
        root = self.connection.root()
        return root[ZopePublication.root_name]

    def getApplication(self):
        """Returns the Zope application instance."""
        return self.app


class FunctionalTestCase(unittest.TestCase):
    """Functional test case."""

    def setUp(self):
        """Prepares for a functional test case."""
        super(FunctionalTestCase, self).setUp()
        FunctionalTestSetup().setUp()

    def tearDown(self):
        """Cleans up after a functional test case."""

        FunctionalTestSetup().tearDown()
        super(FunctionalTestCase, self).tearDown()

    def getRootFolder(self):
        """Returns the Zope root folder."""
        return FunctionalTestSetup().getRootFolder()

    def commit(self):
        commit()

    def abort(self):
        abort()

class BrowserTestCase(FunctionalTestCase):
    """Functional test case for Browser requests."""

    def setUp(self):
        super(BrowserTestCase, self).setUp()
        # Somewhere to store cookies between consecutive requests
        self.cookies = SimpleCookie()

    def tearDown(self):
        del self.cookies

        self.setSite(None)
        super(BrowserTestCase, self).tearDown()

    def setSite(self, site):
        """Set the site which will be used to look up local services"""
        setSite(site)

    def getSite(self):
        """Returns the site which is used to look up local services"""
        return getSite()

    def makeRequest(self, path='', basic=None, form=None, env={},
                    outstream=None):
        """Creates a new request object.

        Arguments:
          path   -- the path to be traversed (e.g. "/folder1/index.html")
          basic  -- basic HTTP authentication credentials ("user:password")
          form   -- a dictionary emulating a form submission
                    (Note that field values should be Unicode strings)
          env    -- a dictionary of additional environment variables
                    (You can emulate HTTP request header
                       X-Header: foo
                     by adding 'HTTP_X_HEADER': 'foo' to env)
          outstream -- a stream where the HTTP response will be written
        """
        if outstream is None:
            outstream = HTTPTaskStub()
        environment = {"HTTP_HOST": 'localhost',
                       "HTTP_REFERER": 'localhost',
                       "HTTP_COOKIE": self.__http_cookie(path)}
        environment.update(env)
        app = FunctionalTestSetup().getApplication()
        request = app._request(path, '', outstream,
                               environment=environment,
                               basic=basic, form=form,
                               request=BrowserRequest)
        return request

    def __http_cookie(self, path):
        '''Return self.cookies as an HTTP_COOKIE environment format string'''
        l = [m.OutputString() for m in self.cookies.values()
                if path.startswith(m['path'])]
        return '; '.join(l)

    def publish(self, path, basic=None, form=None, env={},
                handle_errors=False):
        """Renders an object at a given location.

        Arguments are the same as in makeRequest with the following exception:
          handle_errors  -- if False (default), exceptions will not be caught
                            if True, exceptions will return a formatted error
                            page.

        Returns the response object enhanced with the following methods:
          getOutput()    -- returns the full HTTP output as a string
          getBody()      -- returns the full response body as a string
          getPath()      -- returns the path used in the request
        """
        outstream = HTTPTaskStub()
        old_site = self.getSite()
        self.setSite(None)
        # A cookie header has been sent - ensure that future requests
        # in this test also send the cookie, as this is what browsers do.
        # We pull it apart and reassemble the header to block cookies
        # with invalid paths going through, which may or may not be correct
        if env.has_key('HTTP_COOKIE'):
            self.cookies.load(env['HTTP_COOKIE'])
            del env['HTTP_COOKIE'] # Added again in makeRequest

        request = self.makeRequest(path, basic=basic, form=form, env=env,
                                   outstream=outstream)
        response = ResponseWrapper(request.response, outstream, path)
        if env.has_key('HTTP_COOKIE'):
            self.cookies.load(env['HTTP_COOKIE'])
        publish(request, handle_errors=handle_errors)
        # Urgh - need to play with the response's privates to extract
        # cookies that have been set
        for k,v in response._cookies.items():
            k = k.encode('utf8')
            self.cookies[k] = v['value'].encode('utf8')
            if self.cookies[k].has_key('Path'):
                self.cookies[k]['Path'] = v['Path']
        self.setSite(old_site)
        return response

    def checkForBrokenLinks(self, body, path, basic=None):
        """Looks for broken links in a page by trying to traverse relative
        URIs.
        """
        if not body: return

        old_site = self.getSite()
        self.setSite(None)

        from htmllib import HTMLParser
        from formatter import NullFormatter
        class SimpleHTMLParser(HTMLParser):
            def __init__(self, fmt, base):
                HTMLParser.__init__(self, fmt)
                self.base = base
            def do_base(self, attrs):
                self.base = dict(attrs).get('href', self.base)

        parser = SimpleHTMLParser(NullFormatter(), path)
        parser.feed(body)
        parser.close()
        base = parser.base
        while not base.endswith('/'):
            base = base[:-1]
        if base.startswith('http://localhost/'):
            base = base[len('http://localhost/') - 1:]

        errors = []
        for a in parser.anchorlist:
            if a.startswith('http://localhost/'):
                a = a[len('http://localhost/') - 1:]
            elif a.find(':') != -1:
                # Assume it is an external link
                continue
            elif not a.startswith('/'):
                a = base + a
            if a.find('#') != -1:
                a = a[:a.index('#') - 1]
            # XXX what about queries (/path/to/foo?bar=baz&etc)?
            request = None
            try:
                try:
                    request = self.makeRequest(a, basic=basic)
                    publication = request.publication
                    request.processInputs()
                    publication.beforeTraversal(request)
                    object = publication.getApplication(request)
                    object = request.traverse(object)
                    publication.afterTraversal(request, object)
                except (KeyError, NameError, AttributeError, Unauthorized, Forbidden):
                    e = traceback.format_exception_only(*sys.exc_info()[:2])[-1]
                    errors.append((a, e.strip()))
            finally:
                publication.endRequest(request, object)
                self.setSite(old_site)
                # Bad Things(TM) related to garbage collection and special
                # __del__ methods happen if request.close() is not called here
                if request:
                    request.close()
        if errors:
            self.fail("%s contains broken links:\n" % path
                      + "\n".join(["  %s:\t%s" % (a, e) for a, e in errors]))


class HTTPTestCase(FunctionalTestCase):
    """Functional test case for HTTP requests."""

    def makeRequest(self, path='', basic=None, form=None, env={},
                    instream=None, outstream=None):
        """Creates a new request object.

        Arguments:
          path   -- the path to be traversed (e.g. "/folder1/index.html")
          basic  -- basic HTTP authentication credentials ("user:password")
          form   -- a dictionary emulating a form submission
                    (Note that field values should be Unicode strings)
          env    -- a dictionary of additional environment variables
                    (You can emulate HTTP request header
                       X-Header: foo
                     by adding 'HTTP_X_HEADER': 'foo' to env)
          instream  -- a stream from where the HTTP request will be read
          outstream -- a stream where the HTTP response will be written
        """
        if outstream is None:
            outstream = HTTPTaskStub()
        if instream is None:
            instream = ''
        environment = {"HTTP_HOST": 'localhost',
                       "HTTP_REFERER": 'localhost'}
        environment.update(env)
        app = FunctionalTestSetup().getApplication()
        request = app._request(path, instream, outstream,
                               environment=environment,
                               basic=basic, form=form,
                               request=HTTPRequest, publication=HTTPPublication)
        return request

    def publish(self, path, basic=None, form=None, env={},
                handle_errors=False, request_body=''):
        """Renders an object at a given location.

        Arguments are the same as in makeRequest with the following exception:
          handle_errors  -- if False (default), exceptions will not be caught
                            if True, exceptions will return a formatted error
                            page.

        Returns the response object enhanced with the following methods:
          getOutput()    -- returns the full HTTP output as a string
          getBody()      -- returns the full response body as a string
          getPath()      -- returns the path used in the request
        """
        outstream = HTTPTaskStub()
        request = self.makeRequest(path, basic=basic, form=form, env=env,
                                   instream=request_body, outstream=outstream)
        response = ResponseWrapper(request.response, outstream, path)
        publish(request, handle_errors=handle_errors)
        return response


class HTTPHeaderOutput:

    zope.interface.implements(zope.server.interfaces.IHeaderOutput)

    def __init__(self, protocol, omit):
        self.headers = {}
        self.headersl = []
        self.protocol = protocol
        self.omit = omit
    
    def setResponseStatus(self, status, reason):
        self.status, self.reason = status, reason

    def setResponseHeaders(self, mapping):
        self.headers.update(dict(
            [('-'.join([s.capitalize() for s in name.split('-')]), v)
             for name, v in mapping.items()
             if name.lower() not in self.omit]
        ))

    def appendResponseHeaders(self, lst):
        headers = [split_header(header) for header in lst]
        self.headersl.extend(
            [('-'.join([s.capitalize() for s in name.split('-')]), v)
             for name, v in headers
             if name.lower() not in self.omit]
        )

    def __str__(self):
        out = ["%s: %s" % header for header in self.headers.items()]
        out.extend(["%s: %s" % header for header in self.headersl])
        out.sort()
        out.insert(0, "%s %s %s" % (self.protocol, self.status, self.reason))
        return '\n'.join(out)

class DocResponseWrapper(ResponseWrapper):
    """Response Wrapper for use in doc tests
    """

    def __init__(self, response, outstream, path, header_output):
        ResponseWrapper.__init__(self, response, outstream, path)
        self.header_output = header_output

    def __str__(self):
        body = self.getOutput()
        if body:
            return "%s\n\n%s" % (self.header_output, body)
        return "%s\n" % (self.header_output)

    def getBody(self):
        return self.getOutput()

def http(request_string, handle_errors=True):
    """Execute an HTTP request string via the publisher

    This is used for HTTP doc tests.
    """
    # Commit work done by previous python code.
    commit()

    # Discard leading white space to make call layout simpler
    request_string = request_string.lstrip()

    # split off and parse the command line
    l = request_string.find('\n')
    command_line = request_string[:l].rstrip()
    request_string = request_string[l+1:]
    method, path, protocol = command_line.split()
    path = urllib.unquote(path)
    

    instream = StringIO(request_string)
    environment = {"HTTP_HOST": 'localhost',
                   "HTTP_REFERER": 'localhost',
                   "REQUEST_METHOD": method,
                   "SERVER_PROTOCOL": protocol,
                   }

    headers = [split_header(header)
               for header in rfc822.Message(instream).headers]
    for name, value in headers:
        name = ('_'.join(name.upper().split('-')))
        if name not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            name = 'HTTP_' + name
        environment[name] = value.rstrip()

    outstream = HTTPTaskStub()


    old_site = getSite()
    setSite(None)
    app = FunctionalTestSetup().getApplication()
    header_output = HTTPHeaderOutput(
        protocol, ('x-content-type-warning', 'x-powered-by'))

    if method in ('GET', 'POST', 'HEAD'):
        if (method == 'POST' and
            environment.get('CONTENT_TYPE', '').startswith('text/xml')
            ):
            request_cls = XMLRPCRequest
            publication_cls = XMLRPCPublication
        else:
            request_cls = BrowserRequest
            publication_cls = BrowserPublication
    else:
        request_cls = HTTPRequest
        publication_cls = HTTPPublication
    
    request = app._request(path, instream, outstream,
                           environment=environment,
                           request=request_cls, publication=publication_cls)
    request.response.setHeaderOutput(header_output)
    response = DocResponseWrapper(request.response, outstream, path,
                                  header_output)
    
    publish(request, handle_errors=handle_errors)
    setSite(old_site)

    # sync Python connection:
    getRootFolder()._p_jar.sync()
    
    return response

headerre = re.compile('(\S+): (.+)$')
def split_header(header):
    return headerre.match(header).group(1, 2)

def getRootFolder():
    return FunctionalTestSetup().getRootFolder()

def sync():
    getRootFolder()._p_jar.sync()

#
# Sample functional test case
#

class SampleFunctionalTest(BrowserTestCase):

    def testRootPage(self):
        response = self.publish('/')
        self.assertEquals(response.getStatus(), 200)

    def testRootPage_preferred_languages(self):
        response = self.publish('/', env={'HTTP_ACCEPT_LANGUAGE': 'en'})
        self.assertEquals(response.getStatus(), 200)

    def testNotExisting(self):
        response = self.publish('/nosuchthing', handle_errors=True)
        self.assertEquals(response.getStatus(), 404)

    def testLinks(self):
        response = self.publish('/')
        self.assertEquals(response.getStatus(), 200)
        self.checkForBrokenLinks(response.getBody(), response.getPath())


def sample_test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SampleFunctionalTest))
    return suite

def FunctionalDocFileSuite(*paths, **kw):
    globs = kw.setdefault('globs', {})
    globs['http'] = http
    globs['getRootFolder'] = getRootFolder
    globs['sync'] = sync

    kw['package'] = doctest._normalize_module(kw.get('package'))

    kwsetUp = kw.get('setUp')
    def setUp(test):
        FunctionalTestSetup().setUp()
        
        if kwsetUp is not None:
            kwsetUp(test)
    kw['setUp'] = setUp

    kwtearDown = kw.get('tearDown')
    def tearDown(test):
        if kwtearDown is not None:
            kwtearDown(test)
        FunctionalTestSetup().tearDown()
    kw['tearDown'] = tearDown

    kw['optionflags'] = doctest.ELLIPSIS | doctest.REPORT_CDIFF

    return doctest.DocFileSuite(*paths, **kw)

if __name__ == '__main__':
    unittest.main()
