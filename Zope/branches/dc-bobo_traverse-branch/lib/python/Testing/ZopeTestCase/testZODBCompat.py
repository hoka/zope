#
# Tests ZODB behavior in ZopeTestCase
#
# Demonstrates that cut/copy/paste/clone/rename and import/export 
# work in ZopeTestCase if a subtransaction is commited before performing
# the respective operations.
#

# $Id: testZODBCompat.py,v 1.17 2004/04/09 12:38:37 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase

from AccessControl.Permissions import add_documents_images_and_files
from AccessControl.Permissions import delete_objects
import tempfile

folder_name = ZopeTestCase.folder_name
cutpaste_permissions = [add_documents_images_and_files, delete_objects]


class TestCopyPaste(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.setPermissions(cutpaste_permissions)
        self.folder.addDTMLMethod('doc', file='foo')
        # _p_oids are None until we commit a subtransaction
        self.assertEqual(self.folder._p_oid, None)
        get_transaction().commit(1)
        self.failIfEqual(self.folder._p_oid, None)

    def testCutPaste(self):
        cb = self.folder.manage_cutObjects(['doc'])
        self.folder.manage_pasteObjects(cb)
        self.failUnless(hasattr(self.folder, 'doc'))
        self.failIf(hasattr(self.folder, 'copy_of_doc'))

    def testCopyPaste(self):
        cb = self.folder.manage_copyObjects(['doc'])
        self.folder.manage_pasteObjects(cb)
        self.failUnless(hasattr(self.folder, 'doc'))
        self.failUnless(hasattr(self.folder, 'copy_of_doc'))

    def testClone(self):
        self.folder.manage_clone(self.folder.doc, 'new_doc')
        self.failUnless(hasattr(self.folder, 'doc'))
        self.failUnless(hasattr(self.folder, 'new_doc'))

    def testRename(self):
        self.folder.manage_renameObjects(['doc'], ['new_doc'])
        self.failIf(hasattr(self.folder, 'doc'))
        self.failUnless(hasattr(self.folder, 'new_doc'))

    def testCOPY(self):
        # WebDAV COPY
        request = self.app.REQUEST
        request.environ['HTTP_DEPTH'] = 'infinity'
        request.environ['HTTP_DESTINATION'] = 'http://foo.com/%s/new_doc' % folder_name
        self.folder.doc.COPY(request, request.RESPONSE)
        self.failUnless(hasattr(self.folder, 'doc'))
        self.failUnless(hasattr(self.folder, 'new_doc'))

    def testMOVE(self):
        # WebDAV MOVE
        request = self.app.REQUEST
        request.environ['HTTP_DEPTH'] = 'infinity'
        request.environ['HTTP_DESTINATION'] = 'http://foo.com/%s/new_doc' % folder_name
        self.folder.doc.MOVE(request, request.RESPONSE)
        self.failIf(hasattr(self.folder, 'doc'))
        self.failUnless(hasattr(self.folder, 'new_doc'))


class TestImportExport(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        self.setupLocalEnvironment()
        self.folder.addDTMLMethod('doc', file='foo')
        # _p_oids are None until we commit a subtransaction
        self.assertEqual(self.folder._p_oid, None)
        get_transaction().commit(1)
        self.failIfEqual(self.folder._p_oid, None)

    def testExport(self):
        self.folder.manage_exportObject('doc')
        self.failUnless(os.path.exists(self.zexp_file))

    def testImport(self):
        self.folder.manage_exportObject('doc')
        self.folder._delObject('doc')
        self.folder.manage_importObject('doc.zexp')
        self.failUnless(hasattr(self.folder, 'doc'))

    # To make export and import happy, we have to provide a file-
    # system 'import' directory and adapt the configuration a bit:

    local_home = tempfile.gettempdir()
    import_dir = os.path.join(local_home, 'import')
    zexp_file  = os.path.join(import_dir, 'doc.zexp')

    def setupLocalEnvironment(self):
        # Create the 'import' directory
        os.mkdir(self.import_dir)
        try:
            import App.config
        except ImportError:
            # Modify builtins
            builtins = getattr(__builtins__, '__dict__', __builtins__)
            self._ih = INSTANCE_HOME
            builtins['INSTANCE_HOME'] = self.local_home
            self._ch = CLIENT_HOME
            builtins['CLIENT_HOME'] = self.import_dir
        else:
            # Zope >= 2.7
            config = App.config.getConfiguration()
            self._ih = config.instancehome
            config.instancehome = self.local_home
            self._ch = config.clienthome
            config.clienthome = self.import_dir
            App.config.setConfiguration(config)

    def afterClear(self):
        # Remove external resources
        try: os.remove(self.zexp_file)
        except OSError: pass
        try: os.rmdir(self.import_dir)
        except OSError: pass
        try:
            import App.config
        except ImportError:
            # Restore builtins
            builtins = getattr(__builtins__, '__dict__', __builtins__)
            if hasattr(self, '_ih'):
                builtins['INSTANCE_HOME'] = self._ih
            if hasattr(self, '_ch'):
                builtins['CLIENT_HOME'] = self._ch
        else:
            # Zope >= 2.7
            config = App.config.getConfiguration()
            if hasattr(self, '_ih'):
                config.instancehome = self._ih
            if hasattr(self, '_ch'):
                config.clienthome = self._ch
            App.config.setConfiguration(config)


# Dummy object
from OFS.SimpleItem import SimpleItem

class DummyObject(SimpleItem):
    id = 'dummy'
    foo = None
    _v_foo = None
    _p_foo = None

app = ZopeTestCase.app()
app._setObject('dummy1', DummyObject())
app._setObject('dummy2', DummyObject())
get_transaction().commit()
ZopeTestCase.close(app)


class TestAttributesOfCleanObjects(ZopeTestCase.ZopeTestCase):
    '''This testcase shows that _v_ and _p_ attributes are NOT bothered
       by transaction boundaries, if the respective object is otherwise
       left untouched (clean). This means that such variables will keep
       their values across tests.

       The only use case yet encountered in the wild is portal_memberdata's
       _v_temps attribute. Test authors are cautioned to watch out for 
       occurrences of _v_ and _p_ attributes of objects that are not recreated
       for every test method execution, but preexist in the test ZODB.

       It is therefore deemed essential to initialize any _v_ and _p_ 
       attributes of such objects in afterSetup(), as otherwise test results 
       will be distorted!

       Note that _v_ attributes used to be transactional in Zope < 2.6.

       This testcase exploits the fact that test methods are sorted by name.
    '''
    
    def afterSetUp(self):
        self.dummy = self.app.dummy1 # See above

    def testNormal_01(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)
        self.dummy.foo = 'foo'

    def testNormal_02(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)
        self.dummy.foo = 'bar'

    def testNormal_03(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)

    def testPersistent_01(self):
        # _p_foo is initially None
        self.assertEqual(self.dummy._p_foo, None)
        self.dummy._p_foo = 'foo'

    def testPersistent_02(self):
        # _p_foo retains value assigned by previous test
        self.assertEqual(self.dummy._p_foo, 'foo')
        self.dummy._p_foo = 'bar'

    def testPersistent_03(self):
        # _p_foo retains value assigned by previous test
        self.assertEqual(self.dummy._p_foo, 'bar')

    def testVolatile_01(self):
        # _v_foo is initially None
        self.assertEqual(self.dummy._v_foo, None)
        self.dummy._v_foo = 'foo'

    def testVolatile_02(self):
        if hasattr(self.app._p_jar, 'register'):
            # _v_foo retains value assigned by previous test
            self.assertEqual(self.dummy._v_foo, 'foo')
        else:
            # XXX: _v_foo is transactional in Zope < 2.6
            self.assertEqual(self.dummy._v_foo, None)
        self.dummy._v_foo = 'bar'

    def testVolatile_03(self):
        if hasattr(self.app._p_jar, 'register'):
            # _v_foo retains value assigned by previous test
            self.assertEqual(self.dummy._v_foo, 'bar')
        else:
            # XXX: _v_foo is transactional in Zope < 2.6
            self.assertEqual(self.dummy._v_foo, None)


class TestAttributesOfDirtyObjects(ZopeTestCase.ZopeTestCase):
    '''This testcase shows that _v_ and _p_ attributes of dirty objects 
       ARE removed on abort.

       This testcase exploits the fact that test methods are sorted by name.
    '''

    def afterSetUp(self):
        self.dummy = self.app.dummy2 # See above
        self.dummy.touchme = 1 # Tag, you're dirty

    def testDirtyNormal_01(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)
        self.dummy.foo = 'foo'

    def testDirtyNormal_02(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)
        self.dummy.foo = 'bar'

    def testDirtyNormal_03(self):
        # foo is always None
        self.assertEqual(self.dummy.foo, None)

    def testDirtyPersistent_01(self):
        # _p_foo is alwas None
        self.assertEqual(self.dummy._p_foo, None)
        self.dummy._p_foo = 'foo'

    def testDirtyPersistent_02(self):
        # _p_foo is alwas None
        self.assertEqual(self.dummy._p_foo, None)
        self.dummy._p_foo = 'bar'

    def testDirtyPersistent_03(self):
        # _p_foo is alwas None
        self.assertEqual(self.dummy._p_foo, None)

    def testDirtyVolatile_01(self):
        # _v_foo is always None
        self.assertEqual(self.dummy._v_foo, None)
        self.dummy._v_foo = 'foo'

    def testDirtyVolatile_02(self):
        # _v_foo is always None
        self.assertEqual(self.dummy._v_foo, None)
        self.dummy._v_foo = 'bar'

    def testDirtyVolatile_03(self):
        # _v_foo is always None
        self.assertEqual(self.dummy._v_foo, None)


class TestTransactionAbort(ZopeTestCase.ZopeTestCase):

    def testTransactionAbort(self):
        self.folder.foo = 1
        self.failUnless(hasattr(self.folder, 'foo'))
        get_transaction().abort()
        # The foo attribute is still present
        self.failUnless(hasattr(self.folder, 'foo'))

    def testSubTransactionAbort(self):
        self.folder.foo = 1
        self.failUnless(hasattr(self.folder, 'foo'))
        get_transaction().commit(1)
        get_transaction().abort()
        # This time the abort nukes the foo attribute...
        self.failIf(hasattr(self.folder, 'foo'))

    def testTransactionAbortPersistent(self):
        self.folder._p_foo = 1
        self.failUnless(hasattr(self.folder, '_p_foo'))
        get_transaction().abort()
        # The _p_foo attribute is still present
        self.failUnless(hasattr(self.folder, '_p_foo'))

    def testSubTransactionAbortPersistent(self):
        self.folder._p_foo = 1
        self.failUnless(hasattr(self.folder, '_p_foo'))
        get_transaction().commit(1)
        get_transaction().abort()
        # This time the abort nukes the _p_foo attribute...
        self.failIf(hasattr(self.folder, '_p_foo'))

    def testTransactionAbortVolatile(self):
        self.folder._v_foo = 1
        self.failUnless(hasattr(self.folder, '_v_foo'))
        get_transaction().abort()
        # The _v_foo attribute is still present
        self.failUnless(hasattr(self.folder, '_v_foo'))

    def testSubTransactionAbortVolatile(self):
        self.folder._v_foo = 1
        self.failUnless(hasattr(self.folder, '_v_foo'))
        get_transaction().commit(1)
        get_transaction().abort()
        # This time the abort nukes the _v_foo attribute...
        self.failIf(hasattr(self.folder, '_v_foo'))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCopyPaste))
    suite.addTest(makeSuite(TestImportExport))
    suite.addTest(makeSuite(TestAttributesOfCleanObjects))
    suite.addTest(makeSuite(TestAttributesOfDirtyObjects))
    suite.addTest(makeSuite(TestTransactionAbort))
    return suite

if __name__ == '__main__':
    framework()

