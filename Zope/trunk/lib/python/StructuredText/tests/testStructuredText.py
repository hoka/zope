##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

from StructuredText import ST
from StructuredText import DocumentClass
from StructuredText import ClassicDocumentClass
from StructuredText import StructuredText
from StructuredText import HTMLClass
from StructuredText.StructuredText import HTML
import sys, os, unittest, cStringIO
from OFS import ndiff

"""
This tester first ensures that all regression files
can at least parse all files.
Secondly, the tester will compare the output between
StructuredText and ClassicDocumentClass->HTMLClass
to help ensure backwards compatability.
"""

package_dir = os.path.split(ST.__file__)[0]
regressions=os.path.join(package_dir, 'regressions')

files = ['index.stx','Acquisition.stx','ExtensionClass.stx',
        'MultiMapping.stx','examples.stx','Links.stx','examples1.stx',
        'table.stx','InnerLinks.stx']

def readFile(dirname,fname):

    myfile  = open(os.path.join(dirname, fname),"r")
    lines   = myfile.readlines()
    myfile.close()
    return  ''.join(lines)


class StructuredTextTests(unittest.TestCase):

    def testStructuredText(self):
        """ testing StructuredText """

        for f in files:
            raw_text = readFile(regressions,f)
            assert StructuredText.StructuredText(raw_text),\
                'StructuredText failed on %s' % f

    def testStructuredTextNG(self):
        """ testing StructuredTextNG """

        for f in files:
            raw_text = readFile(regressions,f)
            assert ST.StructuredText(raw_text),\
                'StructuredText failed on %s' % f


    def testDocumentClass(self):
        """ testing DocumentClass"""

        for f in files:
            Doc = DocumentClass.DocumentClass()
            raw_text = readFile(regressions,f)
            text = ST.StructuredText(raw_text)
            assert Doc(text),\
                'DocumentClass failed on %s' % f

    def testClassicDocumentClass(self):
        """ testing ClassicDocumentClass"""

        for f in files:
            Doc = ClassicDocumentClass.DocumentClass()
            raw_text = readFile(regressions,f)
            text = ST.StructuredText(raw_text)
            assert Doc(text),\
                'ClassicDocumentClass failed on %s' % f

    def testClassicHTMLDocumentClass(self):
        """ testing HTML ClassicDocumentClass"""

        for f in files:
            Doc = ClassicDocumentClass.DocumentClass()
            HTML = HTMLClass.HTMLClass()
            raw_text = readFile(regressions,f)
            text = Doc(ST.StructuredText(raw_text))
            assert HTML(text),\
                'HTML ClassicDocumentClass failed on %s' % f


    def testRegressionsTests(self):
        """ HTML regression test """

        for f in files:
            Doc  = DocumentClass.DocumentClass()
            HTML = HTMLClass.HTMLClass()
            raw_text = readFile(regressions,f)
            text = Doc(ST.StructuredText(raw_text))
            html = HTML(text)

            reg_fname = f.replace('.stx','.ref')
            reg_html  = readFile(regressions , reg_fname)

            if reg_html.strip()!= html.strip():

                IO = cStringIO.StringIO()

                oldStdout = sys.stdout
                sys.stdout = IO                

                try:
                    open('_tmpout','w').write(html)
                    ndiff.fcompare(os.path.join(regressions,reg_fname),
                                   '_tmpout')
                    os.unlink('_tmpout')
                finally:
                    sys.stdout = oldStdout 

                raise AssertionError, \
                    'HTML regression test failed on %s\nDiff:\n%s\n' % (f,
                     IO.getvalue())


class BasicTests(unittest.TestCase):

    def _test(self,stxtxt , expected):

        res = HTML(stxtxt,level=1,header=0)
        if res.find(expected)==-1:
            print "Text:     ",stxtxt
            print "Converted:",res
            print "Expected: ",expected
            raise AssertionError,"basic test failed for '%s'" % stxtxt
            

    def testUnderline(self):
        """underline"""
        self._test("xx _this is html_ xx",
                   "xx <u>this is html</u> xx")
        
    def testEmphasis(self):
        """ emphasis """
        self._test("xx *this is html* xx",
                   "xx <em>this is html</em> xx")

    def testStrong(self):
        """ strong """
        self._test("xx **this is html** xx",
                   "xx <strong>this is html</strong> xx")
        
    def testUnderlineThroughoutTags(self):
        """Underlined text containing tags should not be transformed"""
        self._test('<a href="index_html">index_html</a>', 
                   '<a href="index_html">index_html</a>')

    
    def testUnderscoresInLiteral1(self):
        """ underscores in literals shouldn't do unterlining """

        self._test("def __init__(self)",
                   "def __init__(self)")

    def testUnderscoresInLiteral2(self):
        """ underscores in literals shouldn't do unterlining """

        self._test("this is '__a_literal__' eh",
                   "<code>__a_literal__</code>")


    def testUnderlinesWithoutWithspaces(self):
        """ underscores in literals shouldn't do unterlining """

        self._test("Zopes structured_text is sometimes a night_mare",
                   "Zopes structured_text is sometimes a night_mare")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( StructuredTextTests ) )
    suite.addTest( unittest.makeSuite( BasicTests ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
