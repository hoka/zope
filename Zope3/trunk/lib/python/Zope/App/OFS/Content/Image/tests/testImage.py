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

$Id: testImage.py,v 1.2 2002/06/10 23:28:05 jim Exp $
"""

import unittest
from Interface.Verify import verifyClass

class Test( unittest.TestCase ):


    def _makeImage(self, *args, **kw):
        """ """
        from Zope.App.OFS.Content.Image.Image import Image

        return Image(*args, **kw)
        

    def testEmpty( self ):

        file = self._makeImage()

        self.assertEqual(file.getContentType(), '')
        self.assertEqual(file.getData(), None)


    def testConstructor(self):

        file = self._makeImage('Data')
        self.assertEqual(file.getContentType(), '')
        self.assertEqual(file.getData(), 'Data')
    


        
    def testMutators(self):

        # XXX What's the point of this test? Does it test that data
        # contents override content-type? Or not? If the former, then
        # real image data should be used.

        file = self._makeImage()
        
        file.setContentType('text/plain')
        self.assertEqual(file.getContentType(), 'text/plain')

        file.setData('Foobar')
        self.assertEqual(file.getData(), 'Foobar')

        file.edit('Blah', 'text/html')
        self.assertEqual(file.getContentType(), 'text/html')
        self.assertEqual(file.getData(), 'Blah')


    def testInterface(self):
        
        from Zope.App.OFS.Content.Image.Image import Image, IImage

        self.failUnless(IImage.isImplementedByInstancesOf(Image))
        self.failUnless(verifyClass(IImage, Image))        
        


def test_suite():
    loader = unittest.TestLoader()
    return loader.loadTestsFromTestCase( Test )

if __name__=='__main__':
    unittest.TextTestRunner().run( test_suite() )
