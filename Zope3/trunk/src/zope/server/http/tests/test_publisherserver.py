##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors.  All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 1.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################
"""

$Id: test_publisherserver.py,v 1.4 2003/03/13 18:49:18 alga Exp $
"""

import unittest
from asyncore import socket_map, poll
import sys
from threading import Thread

from zope.server.taskthreads import ThreadedTaskDispatcher
from zope.server.http.publisherhttpserver import PublisherHTTPServer

from zope.component.tests.placelesssetup import PlacelessSetup
from zope.component.adapter import provideAdapter

from zope.i18n.interfaces import IUserPreferredCharsets

from zope.publisher.http import IHTTPRequest
from zope.publisher.http import HTTPCharsets
from zope.publisher.browser import BrowserRequest
from zope.publisher.base import DefaultPublication
from zope.publisher.interfaces import Redirect, Retry
from zope.publisher.http import HTTPRequest

from httplib import HTTPConnection

from time import sleep, time

td = ThreadedTaskDispatcher()

LOCALHOST = '127.0.0.1'

HTTPRequest.STAGGER_RETRIES = 0  # Don't pause.


class Conflict (Exception):
    """
    Pseudo ZODB conflict error.
    """


class PublicationWithConflict(DefaultPublication):

    def handleException(self, object, request, exc_info, retry_allowed=1):
        if exc_info[0] is Conflict and retry_allowed:
            # This simulates a ZODB retry.
            raise Retry(exc_info)
        else:
            DefaultPublication.handleException(self, object, request, exc_info,
                                               retry_allowed)


class tested_object:
    " "
    tries = 0

    def __call__(self, REQUEST):
        return 'URL invoked: %s' % REQUEST.URL

    def redirect_method(self, REQUEST):
        "Generates a redirect using the redirect() method."
        REQUEST.response.redirect("http://somewhere.com/redirect")

    def redirect_exception(self):
        "Generates a redirect using an exception."
        raise Redirect("http://somewhere.com/exception")

    def conflict(self, REQUEST, wait_tries):
        """
        Returns 202 status only after (wait_tries) tries.
        """
        if self.tries >= int(wait_tries):
            raise "Accepted"
        else:
            self.tries += 1
            raise Conflict



class Tests(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        PlacelessSetup.setUp(self)
        provideAdapter(IHTTPRequest, IUserPreferredCharsets, HTTPCharsets)
        obj = tested_object()
        obj.folder = tested_object()
        obj.folder.item = tested_object()

        obj._protected = tested_object()

        pub = PublicationWithConflict(obj)

        def request_factory(input_stream, output_steam, env):
            request = BrowserRequest(input_stream, output_steam, env)
            request.setPublication(pub)
            return request

        td.setThreadCount(4)
        # Bind to any port on localhost.
        self.server = PublisherHTTPServer(request_factory, 'Browser',
                                          LOCALHOST, 0, task_dispatcher=td)
        self.port = self.server.socket.getsockname()[1]
        self.run_loop = 1
        self.thread = Thread(target=self.loop)
        self.thread.start()
        sleep(0.1)  # Give the thread some time to start.

    def tearDown(self):
        self.run_loop = 0
        self.thread.join()
        td.shutdown()
        self.server.close()

    def loop(self):
        while self.run_loop:
            poll(0.1, socket_map)

    def testResponse(self, path='/', status_expected=200,
                     add_headers=None, request_body=''):
        h = HTTPConnection(LOCALHOST, self.port)
        h.putrequest('GET', path)
        h.putheader('Accept', 'text/plain')
        if add_headers:
            for k, v in add_headers.items():
                h.putheader(k, v)
        if request_body:
            h.putheader('Content-Length', str(int(len(request_body))))
        h.endheaders()
        if request_body:
            h.send(request_body)
        response = h.getresponse()
        length = int(response.getheader('Content-Length', '0'))
        if length:
            response_body = response.read(length)
        else:
            response_body = ''

        # Please do not disable the status code check.  It must work.
        self.failUnlessEqual(int(response.status), status_expected)

        self.failUnlessEqual(length, len(response_body))

        if (status_expected == 200):
            if path == '/': path = ''
            expect_response = 'URL invoked: http://%s:%d%s' % (LOCALHOST,
                self.port, path)
            self.failUnlessEqual(response_body, expect_response)

    def testDeeperPath(self):
        self.testResponse(path='/folder/item')

    def testNotFound(self):
        self.testResponse(path='/foo/bar', status_expected=404)

    def testUnauthorized(self):
        self.testResponse(path='/_protected', status_expected=401)

    def testRedirectMethod(self):
        self.testResponse(path='/redirect_method', status_expected=302)

    def testRedirectException(self):
        self.testResponse(path='/redirect_exception', status_expected=302)
        self.testResponse(path='/folder/redirect_exception',
                          status_expected=302)

    def testConflictRetry(self):
        # Expect the "Accepted" response since the retries will succeed.
        self.testResponse(path='/conflict?wait_tries=2', status_expected=202)

    def testFailedConflictRetry(self):
        # Expect a "Conflict" response since there will be too many
        # conflicts.
        self.testResponse(path='/conflict?wait_tries=10', status_expected=409)



def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(Tests)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
