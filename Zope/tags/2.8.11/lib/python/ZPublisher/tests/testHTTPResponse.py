import unittest

class HTTPResponseTests(unittest.TestCase):

    def _getTargetClass(self):

        from ZPublisher.HTTPResponse import HTTPResponse
        return HTTPResponse

    def _makeOne(self, *args, **kw):

        return self._getTargetClass()(*args, **kw)

    def test_setStatus_with_exceptions(self):

        from zExceptions import Unauthorized
        from zExceptions import Forbidden
        from zExceptions import NotFound
        from zExceptions import BadRequest
        from zExceptions import InternalError

        for exc_type, code in ((Unauthorized, 401),
                               (Forbidden, 403),
                               (NotFound, 404),
                               (BadRequest, 400),
                               (InternalError, 500)):
            response = self._makeOne()
            response.setStatus(exc_type)
            self.assertEqual(response.status, code)

    def test_setCookie(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        cookie = response.cookies.get('foo', None)
        self.failUnless(cookie)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('path'), '/')

    def test_expireCookie(self):
        response = self._makeOne()
        response.expireCookie('foo', path='/')
        cookie = response.cookies.get('foo', None)
        self.failUnless(cookie)
        self.assertEqual(cookie.get('expires'), 'Wed, 31-Dec-97 23:59:59 GMT')
        self.assertEqual(cookie.get('max_age'), 0)
        self.assertEqual(cookie.get('path'), '/')

    def test_expireCookie1160(self):
        # Verify that the cookie is expired even if an expires kw arg is passed
        # http://zope.org/Collectors/Zope/1160
        response = self._makeOne()
        response.expireCookie('foo', path='/', expires='Mon, 22-Mar-2004 17:59 GMT', max_age=99)
        cookie = response.cookies.get('foo', None)
        self.failUnless(cookie)
        self.assertEqual(cookie.get('expires'), 'Wed, 31-Dec-97 23:59:59 GMT')
        self.assertEqual(cookie.get('max_age'), 0)
        self.assertEqual(cookie.get('path'), '/')

    def test_appendCookie(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        response.appendCookie('foo', 'baz')
        cookie = response.cookies.get('foo', None)
        self.failUnless(cookie)
        self.assertEqual(cookie.get('value'), 'bar:baz')
        self.assertEqual(cookie.get('path'), '/')

    def test_appendHeader(self):
        response = self._makeOne()
        response.setHeader('foo', 'bar')
        response.appendHeader('foo', 'foo')
        self.assertEqual(response.headers.get('foo'), 'bar,\n\tfoo')
        response.setHeader('xxx', 'bar')
        response.appendHeader('XXX', 'foo')
        self.assertEqual(response.headers.get('xxx'), 'bar,\n\tfoo')

    def test_setStatus_ResourceLockedError(self):
        response = self._makeOne()
        from webdav.Lockable import ResourceLockedError
        response.setStatus(ResourceLockedError)
        self.assertEqual(response.status, 423)

    def test_addHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.addHeader('Location',
                           'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.accumulated_headers,
                         'Location: http://www.ietf.org/rfc/rfc2616.txt\n')

    def test_appendHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.appendHeader('Location',
                               'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.headers['location'],
                         'http://www.ietf.org/rfc/rfc2616.txt')

    def test_setHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.setHeader('Location',
                           'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.headers['location'],
                         'http://www.ietf.org/rfc/rfc2616.txt')

    def test_setHeader_drops_CRLF_when_accumulating(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.setHeader('Set-Cookie', 'allowed="OK"')
        response.setHeader('Set-Cookie',
                       'violation="http://www.ietf.org/rfc/\r\nrfc2616.txt"')
        self.assertEqual(response.accumulated_headers,
                'Set-Cookie: allowed="OK"\n' +
                'Set-Cookie: violation="http://www.ietf.org/rfc/rfc2616.txt"\n')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HTTPResponseTests, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
