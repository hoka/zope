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

Revision information:
$Id: test_unauthorized.py,v 1.8 2003/07/18 14:00:20 alga Exp $
"""

from unittest import TestCase, main, makeSuite
from zope.publisher.browser import TestRequest
from zope.app.context import ContextWrapper
from zope.app.interfaces.security import IAuthenticationService, IPrincipal
from zope.interface import implements

class DummyPrincipal:
    implements(IPrincipal)  # this is a lie

    def __init__(self, id):
        self.id = id

    def getId(self):
        return self.id

class DummyAuthService:
    implements(IAuthenticationService)  # this is a lie

    def unauthorized(self, principal_id, request):
        self.principal_id = principal_id
        self.request = request

class DummyPrincipalSource:
    pass

class Test(TestCase):

    def test(self):
        from zope.app.browser.exception.unauthorized import Unauthorized
        exception = Exception()
        try:
            raise exception
        except:
            pass
        request = TestRequest('/')
        authservice = DummyAuthService()
        request.setUser(ContextWrapper(DummyPrincipal(23), authservice))
        u = Unauthorized(exception, request)
        u.issueChallenge()

        # Make sure the response status was set
        self.assertEqual(request.response.getStatus(), 403)

        # Make sure the auth service was called
        self.failUnless(authservice.request is request)
        self.assertEqual(authservice.principal_id, 23)

    def testPluggableAuthService(self):
        from zope.app.browser.exception.unauthorized import Unauthorized
        exception = Exception()
        try:
            raise exception
        except:
            pass
        request = TestRequest('/')
        authservice = DummyAuthService()
        psrc = DummyPrincipalSource()
        psrc = ContextWrapper(psrc, authservice)
        request.setUser(ContextWrapper(DummyPrincipal(23), psrc))
        u = Unauthorized(exception, request)
        u.issueChallenge()

        # Make sure the response status was set
        self.assertEqual(request.response.getStatus(), 403)

        # Make sure the auth service was called
        self.failUnless(authservice.request is request)
        self.assertEqual(authservice.principal_id, 23)

def test_suite():
    return makeSuite(Test)

if __name__=='__main__':
    main(defaultTest='test_suite')
