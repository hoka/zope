##############################################################################
#
# Copyright (c) 2003, 2004 Zope Corporation and Contributors.
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
"""Functional tests for the case-insensitive traverser and folder.

$Id: ftests.py,v 1.1 2004/02/13 23:28:45 srichter Exp $
"""
import unittest
from zope.testing.functional import BrowserTestCase
from zope.publisher.interfaces import NotFound

class TestCaseInsensitiveFolder(BrowserTestCase):

    def testAddCasInsensitiveFolder(self):
        # Step 1: add the case insensitive folder
        response = self.publish(
            '/+/action.html',
            basic='mgr:mgrpw',
            form={'type_name': u'zope.CaseInsensitiveFolder',
                  'id': u'cisf'})
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/@@contents.html')
        # Step 2: add the file
        response = self.publish('/cisf/+/action.html',
                                basic='mgr:mgrpw',
                                form={'type_name': u'File', 'id': u'foo'})
        self.assertEqual(response.getStatus(), 302)
        self.assertEqual(response.getHeader('Location'),
                         'http://localhost/cisf/@@contents.html')
        # Step 3: check that the file is traversed
        response = self.publish('/cisf/foo')
        self.assertEqual(response.getStatus(), 200)
        response = self.publish('/cisf/foO')
        self.assertEqual(response.getStatus(), 200)
        self.assertRaises(NotFound, self.publish, '/cisf/bar')
                          

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCaseInsensitiveFolder))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
