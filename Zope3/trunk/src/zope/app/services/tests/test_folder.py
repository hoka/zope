##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Site-management folder tests

$Id: test_folder.py,v 1.2 2003/03/23 18:04:27 jim Exp $
"""

import unittest
from zope.app.services.tests import placefulsetup
from zope.app.traversing import traverse
from zope.app.services.configuration import ConfigurationManager

class TestSomething(placefulsetup.PlacefulSetup, unittest.TestCase):

    def test_getConfigurationManager(self):
        self.buildFolders()
        sm = placefulsetup.createServiceManager(self.rootFolder)
        default = traverse(sm, 'default')
        self.assertEqual(default.getConfigurationManager(),
                         default['configure'])
        default.setObject('xxx', ConfigurationManager())
        del default['configure']
        self.assertEqual(default.getConfigurationManager(),
                         default['xxx'])


#       Can't test empty because there's no way to make it empty.
##         del default['xxx']
##         self.assertRaises(Exception,
##                           default.getConfigurationManager)

    def test_cant_remove_last_cm(self):
        self.buildFolders()
        sm = placefulsetup.createServiceManager(self.rootFolder)
        default = traverse(sm, 'default')
        self.assertRaises(Exception,
                          default.__delitem__, 'configuration')
        default.setObject('xxx', ConfigurationManager())
        del default['configure']
        
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSomething))
    return suite


if __name__ == '__main__':
    unittest.main()
