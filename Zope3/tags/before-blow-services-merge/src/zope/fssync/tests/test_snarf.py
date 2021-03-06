##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests for the Snarfer and Unsnarfer classes.

$Id$
"""

import os
import unittest

from StringIO import StringIO

from zope.fssync.snarf import copybytes, Snarfer, Unsnarfer
from zope.fssync.tests.tempfiles import TempFiles

class TestCopyBytes(unittest.TestCase):

    def test_copybytes_short(self):
        data = "12345"*25
        istr = StringIO(data)
        ostr = StringIO()
        copybytes(100, istr, ostr)
        self.assertEqual(ostr.getvalue(), data[:100])

    def test_copybytes_long(self):
        data = "12345"*9000
        istr = StringIO(data)
        ostr = StringIO()
        copybytes(len(data), istr, ostr)
        self.assertEqual(ostr.getvalue(), data)

    def test_copybytes_fail_1(self):
        data = "12345"
        istr = StringIO(data)
        ostr = StringIO()
        self.assertRaises(IOError, copybytes, 9000, istr, ostr)

    def test_copybytes_fail_2(self):
        data = "12345"
        istr = StringIO(data)
        ostr = StringIO()
        self.assertRaises(IOError, copybytes, 6, istr, ostr)


class TestSnarfer(TempFiles):

    def setUp(self):
        TempFiles.setUp(self)
        self.ostr = StringIO()
        self.snf = Snarfer(self.ostr)

    def test_addstream(self):
        istr = StringIO("12345")
        self.snf.addstream(istr, 5, "foo")
        self.assertEqual(self.ostr.getvalue(), "5 foo\n12345")

    def test_addfile(self):
        tfn = self.tempfile("12345")
        self.snf.addfile(tfn, "foo")
        self.assertEqual(self.ostr.getvalue(), "5 foo\n12345")

    def test_addtree(self):
        tfn = self.maketree()
        self.snf.addtree(tfn)
        self.assertEqual(self.ostr.getvalue(),
                         "8 d1/f1\n"   "d1f1data"
                         "6 f1\n"      "f1data"
                         "7 f1~\n"     "f1adata"
                         "6 f2\n"      "f2data")

    def test_addtree_prefix(self):
        tfn = self.maketree()
        self.snf.addtree(tfn, "top/")
        self.assertEqual(self.ostr.getvalue(),
                         "8 top/d1/f1\n"   "d1f1data"
                         "6 top/f1\n"      "f1data"
                         "7 top/f1~\n"     "f1adata"
                         "6 top/f2\n"      "f2data")

    def test_addtree_filter(self):
        tfn = self.maketree()
        self.snf.addtree(tfn, filter=lambda x: not x.endswith("~"))
        self.assertEqual(self.ostr.getvalue(),
                         "8 d1/f1\n"   "d1f1data"
                         "6 f1\n"      "f1data"
                         "6 f2\n"      "f2data")

    def test_add_addfile(self):
        tfn = self.tempfile("12345")
        self.snf.add(tfn, "top")
        self.assertEqual(self.ostr.getvalue(),
                         "5 top\n"   "12345")

    def test_add_addtree(self):
        tfn = self.maketree()
        self.snf.add(tfn, "top")
        self.assertEqual(self.ostr.getvalue(),
                         "8 top/d1/f1\n"   "d1f1data"
                         "6 top/f1\n"      "f1data"
                         "7 top/f1~\n"     "f1adata"
                         "6 top/f2\n"      "f2data")

    def maketree(self):
        tfn = self.tempdir()
        f1 = os.path.join(tfn, "f1")
        f1a = os.path.join(tfn, "f1~")
        f2 = os.path.join(tfn, "f2")
        self.writefile("f1data", f1)
        self.writefile("f1adata", f1a)
        self.writefile("f2data", f2)
        d1 = os.path.join(tfn, "d1")
        os.mkdir(d1)
        d1f1 = os.path.join(d1, "f1")
        self.writefile("d1f1data", d1f1)
        return tfn

class TestUnsnarfer(unittest.TestCase):

    def test_translatepath(self):
        snf = Unsnarfer(StringIO(""))
        snf.root = "root"
        self.assertEqual(snf.translatepath("a/b/c"),
                         os.path.join("root", "a", "b", "c"))
        self.assertRaises(IOError, snf.translatepath, "a/./b")
        self.assertRaises(IOError, snf.translatepath, "a/../b")
        self.assertRaises(IOError, snf.translatepath, "a//b")
        self.assertRaises(IOError, snf.translatepath, "/a")
        self.assertRaises(IOError, snf.translatepath, "a/")
        self.assertRaises(IOError, snf.translatepath, "")

    # TODO: More to add...

def test_suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(TestCopyBytes))
    s.addTest(unittest.makeSuite(TestSnarfer))
    s.addTest(unittest.makeSuite(TestUnsnarfer))
    return s

def test_main():
    unittest.TextTestRunner().run(test_suite())

if __name__=='__main__':
    test_main()
