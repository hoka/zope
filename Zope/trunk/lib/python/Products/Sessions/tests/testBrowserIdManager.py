##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""
Test suite for session id manager.

$Id: testBrowserIdManager.py,v 1.10 2002/08/10 19:28:38 chrism Exp $
"""
__version__ = "$Revision: 1.10 $"[11:-2]

import sys
import ZODB
from Products.Sessions.BrowserIdManager import BrowserIdManager, BrowserIdManagerErr
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from sys import stdin
from os import environ

class TestBrowserIdManager(TestCase):
    def setUp(self):
        self.m = BrowserIdManager('foo')
        resp = HTTPResponse()
        environ['SERVER_NAME']='fred'
        environ['SERVER_PORT']='80'
        req = HTTPRequest(stdin, environ, resp)
        self.m.REQUEST = req
        
    def tearDown(self):
        del self.m

    def testSetBrowserIdName(self):
        self.m.setBrowserIdName('foo')
        self.failUnless(self.m.getBrowserIdName()== 'foo')

    def testSetBadBrowserIdName(self):
        self.assertRaises(BrowserIdManagerErr,
                          lambda self=self: self.m.setBrowserIdName(''))
        self.assertRaises(BrowserIdManagerErr,
                          lambda self=self: self.m.setBrowserIdName(1))

    def testSetBadNamespaces(self):
        d = {1:'gummy', 2:'froopy'}
        self.assertRaises(BrowserIdManagerErr,
                          lambda self=self,d=d:
                          self.m.setBrowserIdNamespaces(d))

    def testSetGoodNamespaces(self):
        d = {1:'cookies', 2:'form'}
        self.m.setBrowserIdNamespaces(d)
        self.failUnless(self.m.getBrowserIdNamespaces() == d)

    def testSetNamespacesByLocation(self):
        self.m.setBrowserIdLocation('cookiesonly')
        self.failUnless(self.m.getBrowserIdNamespaces() == {1:'cookies'})
        self.failUnless(self.m.getBrowserIdLocation() == 'cookiesonly')
        self.m.setBrowserIdLocation('cookiesthenform')
        self.failUnless(self.m.getBrowserIdNamespaces()=={1:'cookies',2:'form'})
        self.failUnless(self.m.getBrowserIdLocation() == 'cookiesthenform')
        self.m.setBrowserIdLocation('formonly')
        self.failUnless(self.m.getBrowserIdNamespaces() == {1:'form'})
        self.failUnless(self.m.getBrowserIdLocation() == 'formonly')
        self.m.setBrowserIdLocation('formthencookies')
        self.failUnless(self.m.getBrowserIdNamespaces()=={1:'form',2:'cookies'})
        self.failUnless(self.m.getBrowserIdLocation() == 'formthencookies')

    def testSetBadCookiePath(self):
        path = '/;'
        self.assertRaises(BrowserIdManagerErr,
                        lambda self=self, path=path:self.m.setCookiePath(path))

    def testSetGoodCookiePath(self):
        self.m.setCookiePath('/foo')
        self.failUnless(self.m.getCookiePath() == '/foo')

    def testSetBadCookieLifeDays(self):
        self.assertRaises(BrowserIdManagerErr,
                          lambda self=self: self.m.setCookieLifeDays(''))

    def testSetGoodCookieLifeDays(self):
        self.m.setCookieLifeDays(1)
        self.failUnless(self.m.getCookieLifeDays() == 1)

    def testSetBadCookieDomain(self):
        self.assertRaises(BrowserIdManagerErr,
                          lambda self=self: self.m.setCookieDomain('gubble'))

    def testSetGoodCookieLifeDays(self):
        self.m.setCookieLifeDays(1)
        self.failUnless(self.m.getCookieLifeDays() == 1)

    def testSetNoCookieDomain(self):
        domain = ''
        self.m.setCookieDomain(domain)
        setdomain = self.m.getCookieDomain()
        self.failUnless(setdomain == domain)

    def testSetBadCookieDomain(self):
        # not enough dots, must be stringtype, semicolon follows respectively
        for domain in ('zope.org', {1:1}, '.zope.org;'):
            self.assertRaises(BrowserIdManagerErr,
               lambda self=self, domain=domain: self.m.setCookieDomain(domain))

    def testSetGoodCookieDomain(self):
        self.m.setCookieDomain('.zope.org')
        setdomain = self.m.getCookieDomain()
        self.failUnless( setdomain == '.zope.org', "%s" % setdomain )
        
    def testSetCookieSecure(self):
        self.m.setCookieSecure(1)
        self.failUnless( self.m.getCookieSecure() == 1 )

    def testGetBrowserIdCookie(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.cookies[tokenkey] = token
        a = self.m.getBrowserId()
        self.failUnless( a == token, repr(a) )
        self.failUnless( self.m.isBrowserIdFromCookie() )

    def testSetBrowserIdDontCreate(self):
        a = self.m.getBrowserId(0)
        self.failUnless( a == None )

    def testSetBrowserIdCreate(self):
        a = self.m.getBrowserId(1)
        tokenkey = self.m.getBrowserIdName()
        b = self.m.REQUEST.RESPONSE.cookies[tokenkey]
        self.failUnless( a == b['value'] )

    def testHasBrowserId(self):
        self.failUnless( not self.m.hasBrowserId() )
        a = self.m.getBrowserId()
        self.failUnless( self.m.hasBrowserId() )
        
    def testBrowserIdIsNew(self):
        a = self.m.getBrowserId()
        self.failUnless( self.m.isBrowserIdNew() )

    def testIsBrowserIdFromCookieFirst(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.cookies[tokenkey] = token
        self.m.setBrowserIdNamespaces({1:'cookies', 2:'form'})
        a = self.m.getBrowserId()
        self.failUnless( self.m.isBrowserIdFromCookie() )

    def testIsBrowserIdFromFormFirst(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'form'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.form[tokenkey] = token
        self.m.setBrowserIdNamespaces({1:'form', 2:'cookies'})
        a = self.m.getBrowserId()
        self.failUnless( self.m.isBrowserIdFromForm() )

    def testIsBrowserIdFromCookieOnly(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.form[tokenkey] = token
        self.m.setBrowserIdNamespaces({1:'cookies'})
        a = self.m.getBrowserId()
        self.failUnless( self.m.isBrowserIdFromCookie() )
        self.failUnless( not self.m.isBrowserIdFromForm() )
 
    def testIsBrowserIdFromFormOnly(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'form'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.form[tokenkey] = token
        self.m.setBrowserIdNamespaces({1:'form'})
        a = self.m.getBrowserId()
        self.failUnless( not self.m.isBrowserIdFromCookie() )
        self.failUnless( self.m.isBrowserIdFromForm() )

    def testFlushBrowserIdCookie(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.cookies[tokenkey] = token
        a = self.m.getBrowserId()
        self.failUnless( a == token, repr(a) )
        self.failUnless( self.m.isBrowserIdFromCookie() )
        self.m.flushBrowserIdCookie()
        c = self.m.REQUEST.RESPONSE.cookies[tokenkey]
        self.failUnless( c['value'] == 'deleted' )
        
    def testSetBrowserIdCookieByForce(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.cookies[tokenkey] = token
        a = self.m.getBrowserId()
        self.failUnless( a == token )
        self.failUnless( self.m.isBrowserIdFromCookie() )
        token = 'abcdefghijk'
        self.m.setBrowserIdCookieByForce(token)
        c = self.m.REQUEST.RESPONSE.cookies[tokenkey]
        self.failUnless( c['value'] == token )

    def testEncodeUrl(self):
        keystring = self.m.getBrowserIdName()
        key = self.m.getBrowserId()
        u = '/home/chrism/foo'
        r = self.m.encodeUrl(u)
        self.failUnless( r == '%s?%s=%s' % (u, keystring, key) )
        u = 'http://www.zope.org/Members/mcdonc?foo=bar&spam=eggs'
        r = self.m.encodeUrl(u)
        self.failUnless( r == '%s&amp;%s=%s' % (u, keystring, key) )

    def testGetHiddenFormField(self):
        keystring = self.m.getBrowserIdName()
        key = self.m.getBrowserId()
        html = self.m.getHiddenFormField()
        expected = ('<input type="hidden" name="%s" value="%s">' %
                    (keystring, key))
        self.failUnless( html == expected )

def test_suite():
    testsuite = makeSuite(TestBrowserIdManager, 'test')
    return testsuite
        
if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9)
    runner.run(test_suite())
