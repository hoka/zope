##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""

$Id: test_httpserver.py,v 1.3 2003/03/13 18:49:18 alga Exp $
"""

import unittest
from asyncore import socket_map, poll
import socket

from threading import Thread
from zope.server.taskthreads import ThreadedTaskDispatcher
from zope.server.http.httpserver import HTTPServer
from zope.server.adjustments import Adjustments
from zope.server.interfaces import ITask
from zope.server.tests.asyncerror import AsyncoreErrorHook

from httplib import HTTPConnection
from httplib import HTTPResponse as ClientHTTPResponse

from time import sleep, time

td = ThreadedTaskDispatcher()

LOCALHOST = '127.0.0.1'
SERVER_PORT = 0      # Set these port numbers to 0 to auto-bind, or
CONNECT_TO_PORT = 0  # use specific numbers to inspect using TCPWatch.


my_adj = Adjustments()
# Reduce overflows to make testing easier.
my_adj.outbuf_overflow = 10000
my_adj.inbuf_overflow = 10000


class EchoHTTPServer(HTTPServer):

    def executeRequest(self, task):
        headers = task.request_data.headers
        if 'CONTENT_LENGTH' in headers:
            cl = headers['CONTENT_LENGTH']
            task.response_headers['Content-Length'] = cl
        instream = task.request_data.getBodyStream()
        while 1:
            data = instream.read(8192)
            if not data:
                break
            task.write(data)


class SleepingTask:

    __implements__ = ITask

    def service(self):
        sleep(0.2)

    def cancel(self):
        pass

    def defer(self):
        pass


class Tests(unittest.TestCase, AsyncoreErrorHook):

    def setUp(self):
        td.setThreadCount(4)
        self.orig_map_size = len(socket_map)
        self.hook_asyncore_error()
        self.server = EchoHTTPServer(LOCALHOST, SERVER_PORT,
                                     task_dispatcher=td, adj=my_adj)
        if CONNECT_TO_PORT == 0:
            self.port = self.server.socket.getsockname()[1]
        else:
            self.port = CONNECT_TO_PORT
        self.run_loop = 1
        self.counter = 0
        self.thread = Thread(target=self.loop)
        self.thread.start()
        sleep(0.1)  # Give the thread some time to start.

    def tearDown(self):
        self.run_loop = 0
        self.thread.join()
        td.shutdown()
        self.server.close()
        # Make sure all sockets get closed by asyncore normally.
        timeout = time() + 5
        while 1:
            if len(socket_map) == self.orig_map_size:
                # Clean!
                break
            if time() >= timeout:
                self.fail('Leaked a socket: %s' % `socket_map`)
            poll(0.1)
        self.unhook_asyncore_error()

    def loop(self):
        while self.run_loop:
            self.counter = self.counter + 1
            #print 'loop', self.counter
            poll(0.1)

    def testEchoResponse(self, h=None, add_headers=None, body=''):
        if h is None:
            h = HTTPConnection(LOCALHOST, self.port)
        h.putrequest('GET', '/')
        h.putheader('Accept', 'text/plain')
        if add_headers:
            for k, v in add_headers.items():
                h.putheader(k, v)
        if body:
            h.putheader('Content-Length', str(int(len(body))))
        h.endheaders()
        if body:
            h.send(body)
        response = h.getresponse()
        self.failUnlessEqual(int(response.status), 200)
        length = int(response.getheader('Content-Length', '0'))
        response_body = response.read()
        self.failUnlessEqual(length, len(response_body))
        self.failUnlessEqual(response_body, body)

    def testMultipleRequestsWithoutBody(self):
        # Tests the use of multiple requests in a single connection.
        h = HTTPConnection(LOCALHOST, self.port)
        for n in range(3):
            self.testEchoResponse(h)
        self.testEchoResponse(h, {'Connection': 'close'})

    def testMultipleRequestsWithBody(self):
        # Tests the use of multiple requests in a single connection.
        h = HTTPConnection(LOCALHOST, self.port)
        for n in range(3):
            self.testEchoResponse(h, body='Hello, world!')
        self.testEchoResponse(h, {'Connection': 'close'})

    def testPipelining(self):
        # Tests the use of several requests issued at once.
        s = ("GET / HTTP/1.0\r\n"
             "Connection: %s\r\n"
             "Content-Length: %d\r\n"
             "\r\n"
             "%s")
        to_send = ''
        count = 25
        for n in range(count):
            body = "Response #%d\r\n" % (n + 1)
            if n + 1 < count:
                conn = 'keep-alive'
            else:
                conn = 'close'
            to_send += s % (conn, len(body), body)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((LOCALHOST, self.port))
        sock.send(to_send)
        for n in range(count):
            expect_body = "Response #%d\r\n" % (n + 1)
            response = ClientHTTPResponse(sock)
            response.begin()
            self.failUnlessEqual(int(response.status), 200)
            length = int(response.getheader('Content-Length', '0'))
            response_body = response.read(length)
            self.failUnlessEqual(length, len(response_body))
            self.failUnlessEqual(response_body, expect_body)

    def testWithoutCRLF(self):
        # Tests the use of just newlines rather than CR/LFs.
        data = "Echo\nthis\r\nplease"
        s = ("GET / HTTP/1.0\n"
             "Connection: close\n"
             "Content-Length: %d\n"
             "\n"
             "%s") % (len(data), data)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((LOCALHOST, self.port))
        sock.send(s)
        response = ClientHTTPResponse(sock)
        response.begin()
        self.failUnlessEqual(int(response.status), 200)
        length = int(response.getheader('Content-Length', '0'))
        response_body = response.read(length)
        self.failUnlessEqual(length, len(data))
        self.failUnlessEqual(response_body, data)

    def testLargeBody(self):
        # Tests the use of multiple requests in a single connection.
        h = HTTPConnection(LOCALHOST, self.port)
        s = 'This string has 32 characters.\r\n' * 32  # 1024 characters.
        self.testEchoResponse(h, body=(s * 1024))  # 1 MB
        self.testEchoResponse(h, {'Connection': 'close'},
                              body=(s * 100))  # 100 KB

    def testManyClients(self):
        conns = []
        for n in range(50):  # Linux kernel (2.4.8) doesn't like > 128 ?
            #print 'open', n, clock()
            h = HTTPConnection(LOCALHOST, self.port)
            #h.debuglevel = 1
            h.putrequest('GET', '/')
            h.putheader('Accept', 'text/plain')
            h.endheaders()
            conns.append(h)
            # If you uncomment the next line, you can raise the
            # number of connections much higher without running
            # into delays.
            #sleep(0.01)
        responses = []
        for h in conns:
            response = h.getresponse()
            self.failUnlessEqual(response.status, 200)
            responses.append(response)
        for response in responses:
            response.read()

    def testThreading(self):
        # Ensures the correct number of threads keep running.
        for n in range(4):
            td.addTask(SleepingTask())
        # Try to confuse the task manager.
        td.setThreadCount(2)
        td.setThreadCount(1)
        sleep(0.5)
        # There should be 1 still running.
        self.failUnlessEqual(len(td.threads), 1)

    def testChunkingRequestWithoutContent(self):
        h = HTTPConnection(LOCALHOST, self.port)
        h.putrequest('GET', '/')
        h.putheader('Accept', 'text/plain')
        h.putheader('Transfer-Encoding', 'chunked')
        h.endheaders()
        h.send("0\r\n\r\n")
        response = h.getresponse()
        self.failUnlessEqual(int(response.status), 200)
        response_body = response.read()
        self.failUnlessEqual(response_body, '')

    def testChunkingRequestWithContent(self):
        control_line="20;\r\n"  # 20 hex = 32 dec
        s = 'This string has 32 characters.\r\n'
        expect = s * 12

        h = HTTPConnection(LOCALHOST, self.port)
        h.putrequest('GET', '/')
        h.putheader('Accept', 'text/plain')
        h.putheader('Transfer-Encoding', 'chunked')
        h.endheaders()
        for n in range(12):
            h.send(control_line)
            h.send(s)
        h.send("0\r\n\r\n")
        response = h.getresponse()
        self.failUnlessEqual(int(response.status), 200)
        response_body = response.read()
        self.failUnlessEqual(response_body, expect)


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase(Tests)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
