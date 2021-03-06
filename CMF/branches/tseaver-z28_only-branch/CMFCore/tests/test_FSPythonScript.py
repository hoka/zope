##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for FSPythonScript module.

$Id$
"""
from unittest import TestSuite, makeSuite, main
import Testing
import Zope2
Zope2.startup()

from os.path import join
from sys import exc_info
from thread import start_new_thread
from time import sleep

from OFS.Folder import Folder
from Products.StandardCacheManagers import RAMCacheManager

from Products.CMFCore.FSPythonScript import FSPythonScript
from Products.CMFCore.FSMetadata import FSMetadata
from Products.CMFCore.tests.base.testcase import FSDVTest
from Products.CMFCore.tests.base.testcase import SecurityTest


class FSPSMaker(FSDVTest):

    def _makeOne( self, id, filename ):
        path = join(self.skin_path_name, filename)
        metadata = FSMetadata(path)
        metadata.read()
        return FSPythonScript( id, path, properties=metadata.getProperties() ) 


class FSPythonScriptTests(FSPSMaker):

    def test_GetSize( self ):
        # Test get_size returns correct value
        script = self._makeOne('test1', 'test1.py')
        self.assertEqual(len(script.read()),script.get_size())

    def testInitializationRaceCondition(self):
        # Tries to exercise a former race condition where
        # FSObject._updateFromFS() set self._parsed before the
        # object was really parsed.
        for n in range(10):
            f = Folder()
            script = self._makeOne('test1', 'test1.py').__of__(f)
            res = []

            def call_script(script=script, res=res):
                try:
                    res.append(script())
                except:
                    res.append('%s: %s' % exc_info()[:2])

            start_new_thread(call_script, ())
            call_script()
            while len(res) < 2:
                sleep(0.05)
            self.assertEqual(res, ['test1', 'test1'], res)


class FSPythonScriptCustomizationTests(SecurityTest, FSPSMaker):

    def setUp( self ):
        FSPSMaker.setUp(self)
        SecurityTest.setUp( self )

        self.root._setObject( 'portal_skins', Folder( 'portal_skins' ) )
        self.skins = self.root.portal_skins

        self.skins._setObject( 'custom', Folder( 'custom' ) )
        self.custom = self.skins.custom

        self.skins._setObject( 'fsdir', Folder( 'fsdir' ) )
        self.fsdir = self.skins.fsdir

        self.fsdir._setObject( 'test6'
                             , self._makeOne( 'test6', 'test6.py' ) )

        self.fsPS = self.fsdir.test6

    def test_customize( self ):

        self.fsPS.manage_doCustomize( folder_path='custom' )

        self.assertEqual( len( self.custom.objectIds() ), 1 )
        self.failUnless( 'test6' in self.custom.objectIds() )  

    def test_customize_caching(self):
        # Test to ensure that cache manager associations survive customizing
        cache_id = 'gofast'
        RAMCacheManager.manage_addRAMCacheManager( self.root
                                                 , cache_id
                                                 , REQUEST=None
                                                 )
        self.fsPS.ZCacheable_setManagerId(cache_id, REQUEST=None)

        self.assertEqual(self.fsPS.ZCacheable_getManagerId(), cache_id)

        self.fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = self.custom.test6

        self.assertEqual(custom_ps.ZCacheable_getManagerId(), cache_id)

    def test_customize_proxyroles(self):
        # Test to ensure that proxy roles survive customizing
        self.fsPS._proxy_roles = ('Manager', 'Anonymous')
        self.failUnless(self.fsPS.manage_haveProxy('Anonymous'))
        self.failUnless(self.fsPS.manage_haveProxy('Manager'))

        self.fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = self.custom.test6
        self.failUnless(custom_ps.manage_haveProxy('Anonymous'))
        self.failUnless(custom_ps.manage_haveProxy('Manager'))

    def test_customization_permissions(self):
        # Test to ensure that permission settings survive customizing
        perm = 'View management screens'

        # First, set a permission to an odd role and verify
        self.fsPS.manage_permission( perm
                                   , roles=('Anonymous',)
                                   , acquire=0
                                   )
        rop = self.fsPS.rolesOfPermission(perm)
        for rop_info in rop:
            if rop_info['name'] == 'Anonymous':
                self.failIf(rop_info['selected'] == '')
            else:
                self.failUnless(rop_info['selected'] == '')

        # Now customize and verify again
        self.fsPS.manage_doCustomize(folder_path='custom')
        custom_ps = self.custom.test6
        rop = custom_ps.rolesOfPermission(perm)
        for rop_info in rop:
            if rop_info['name'] == 'Anonymous':
                self.failIf(rop_info['selected'] == '')
            else:
                self.failUnless(rop_info['selected'] == '')

    def tearDown(self):
        SecurityTest.tearDown(self)
        FSPSMaker.tearDown(self)


def test_suite():
    return TestSuite((
        makeSuite(FSPythonScriptTests),
        makeSuite(FSPythonScriptCustomizationTests),
        ))

if __name__ == '__main__':
    main(defaultTest='test_suite')
