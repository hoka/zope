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
"""Tests for the FSMerger class.

$Id: test_fsmerger.py,v 1.1 2003/05/14 22:16:09 gvanrossum Exp $
"""

import os
import shutil
import unittest
import tempfile

from os.path import exists, isdir, isfile, realpath, normcase, split, join

from zope.fssync.fsmerger import FSMerger

class MockMetadata(object):

    def __init__(self):
        self.database = {}

    def getentry(self, filename):
        key, filename = self.makekey(filename)
        if key not in self.database:
            self.database[key] = {}
        return self.database[key]

    def getnames(self, dirpath):
        dirkey, dirpath = self.makekey(dirpath)
        names = []
        for key in self.database:
            head, tail = split(key)
            if head == dirkey:
                names.append(tail)
        return names

    def flush(self):
        pass

    # These only exist for the test framework

    def makekey(self, path):
        path = realpath(path)
        key = normcase(path)
        return key, path

    def setmetadata(self, filename, metadata={}):
        key, filename = self.makekey(filename)
        if key not in self.database:
            self.database[key] = {"path": filename}
        self.database[key].update(metadata)

    def delmetadata(self, filename):
        key, filename = self.makekey(filename)
        if key in self.database:
            del self.database[key]

    def dump(self):
        return dict([(k, v) for (k, v) in self.database.iteritems() if v])

class TestFSMerger(unittest.TestCase):

    def setUp(self):
        # Create a mock metadata database
        self.metadata = MockMetadata()
        # Create a list of temporary names to be removed in tearDown
        self.tempnames = []
        # Create a handy entry
        self.entry = {"path": "/foo"}

    def tearDown(self):
        # Clean up temporary files and directories
        for fn in self.tempnames:
            if isdir(fn):
                shutil.rmtree(fn)
            elif isfile(fn):
                os.remove(fn)

    def adddir(self):
        # Create and register a temporary directory
        dir = tempfile.mktemp()
        self.tempnames.append(dir)
        os.mkdir(dir)
        return dir

    def ensuredir(self, dir):
        # Ensure that a given directory exists
        if not isdir(dir):
            os.makedirs(dir)

    def addfile(self, dir, path, data, entry=None):
        # Create a file or directory and write some data to it.  If
        # entry is not None, add it as the file's entry.  If data is a
        # dict, create a directory; the dict key/value entries are
        # used as name/data for the directory contents; if entry is
        # not None, entries are also synthesized for the directory
        # contents.
        path = join(dir, path)
        if entry is not None:
            self.addentry(path, entry)
        if isinstance(data, dict):
            self.ensuredir(path)
            pentry = self.metadata.getentry(path)
            for x in data:
                if entry is not None:
                    newentry = entry.copy()
                    newentry["path"] += "/" + x
                else:
                    newentry = None
                self.addfile(path, x, data[x], newentry)
        elif data is not None:
            f = open(path, "w")
            try:
                f.write(data)
            finally:
                f.close()
        return path

    def addorigfile(self, dir, path, data):
        # Create the 'original' for a file or directory and write data to it
        if isinstance(data, dict):
            path = join(dir, path)
            self.ensuredir(path)
            for x in data:
                self.addorigfile(path, x, data[x])
            return None
        else:
            origdir = join(dir, "@@Zope", "Original")
            self.ensuredir(origdir)
            return self.addfile(origdir, path, data)

    def checkfile(self, path, expected_data):
        # Assert that a file or directory contains the expected data
        if isinstance(expected_data, dict):
            self.assert_(isdir(path))
            for x in expected_data:
                self.checkfile(join(path, x), expected_data[x])
        elif expected_data is None:
            self.assert_(not exists(path))
        else:
            f = open(path, "r")
            try:
                actual_data = f.read()
            finally:
                f.close()
            self.assertEqual(actual_data, expected_data)

    def checkorigfile(self, path, expected_data):
        # Assert that the 'original' contains the expected data
        if isinstance(expected_data, dict):
            self.assert_(isdir(path))
            for x in expected_data:
                self.checkorigfile(join(path, x), expected_data[x])
        else:
            head, tail = split(path)
            self.checkfile(join(head, "@@Zope", "Original", tail),
                           expected_data)

    def addentry(self, path, entry):
        e = self.metadata.getentry(path)
        e.update(entry)

    def checkentry(self, path, entry):
        e = self.metadata.getentry(path)
        self.assertEqual(e, entry)

    def test_ignore(self):
        m = FSMerger(None, None)
        self.assertEqual(m.ignore("foo"), False)
        self.assertEqual(m.ignore("foo~"), True)

    def test_reportaction(self):
        reports = []
        m = FSMerger(None, reports.append)
        for action in "Fix", "Copy", "Merge", "Delete", "Nothing":
            for state in ("Conflict", "Uptodate", "Modified",
                          "Added", "Removed", "Spurious", "Nonexistent"):
                m.reportaction(action, state, action+state)
        # I cheated a little here: the list of expected reports was
        # constructed by printing the actual list of reports in a
        # previous run.  But then I carefully looked it over and
        # verified that all was as expected, so now at least it serves
        # as a regression test.
        self.assertEqual(reports,
                         ['C FixConflict',
                          'U FixUptodate',
                          'M FixModified',
                          'A FixAdded',
                          'R FixRemoved',
                          '? FixSpurious',
                          '* FixNonexistent',

                          'C CopyConflict',
                          'U CopyUptodate',
                          'M CopyModified',
                          'A CopyAdded',
                          'R CopyRemoved',
                          '? CopySpurious',
                          '* CopyNonexistent',

                          'C MergeConflict',
                          'U MergeUptodate',
                          'M MergeModified',
                          'A MergeAdded',
                          'R MergeRemoved',
                          '? MergeSpurious',
                          '* MergeNonexistent',

                          'C DeleteConflict',
                          '* DeleteUptodate',
                          'M DeleteModified',
                          'A DeleteAdded',
                          'R DeleteRemoved',
                          '? DeleteSpurious',
                          'D DeleteNonexistent',

                          'C NothingConflict',
                          '* NothingUptodate',
                          'M NothingModified',
                          'A NothingAdded',
                          'R NothingRemoved',
                          '? NothingSpurious',
                          '* NothingNonexistent'])

    def test_reportdir(self):
        reports = []
        m = FSMerger(None, reports.append)
        m.reportdir("X", "foo")
        self.assertEqual(reports, ["X foo" + os.sep])

    def mergetest(self, name, localdata, origdata, remotedata,
                  localentry, remoteentry,
                  expected_reports_template,
                  expected_localdata, expected_origdata, expected_remotedata,
                  expected_localentry, expected_remoteentry):
        # Generic test setup to test merging files
        reports = []
        m = FSMerger(self.metadata, reports.append)

        localtopdir = self.adddir()
        remotetopdir = self.adddir()
        localdir = join(localtopdir, "local")
        remotedir = join(remotetopdir, "remote")
        os.mkdir(localdir)
        os.mkdir(remotedir)

        localfile = self.addfile(localdir, name, localdata, localentry)
        origfile = self.addorigfile(localdir, name, origdata)
        remotefile = self.addfile(remotedir, name, remotedata, remoteentry)

        m.merge_dirs(localdir, remotedir)

        expected_reports = []
        for er in expected_reports_template:
            er = er.replace("%l", localfile)
            er = er.replace("%r", remotefile)
            expected_reports.append(er)
        filtered_reports = [r for r in reports if r[0] not in "*/"]
        self.assertEqual(filtered_reports, expected_reports)

        if isinstance(expected_localdata, str):
            expected_localdata = expected_localdata.replace("%l", localfile)
            expected_localdata = expected_localdata.replace("%r", remotefile)

        self.checkfile(localfile, expected_localdata)
        self.checkorigfile(localfile, expected_origdata)
        self.checkfile(remotefile, expected_remotedata)

        if callable(expected_localentry):
            expected_localentry = expected_localentry(localfile)
        self.checkentry(localfile, expected_localentry)
        self.checkentry(remotefile, expected_remoteentry)

    def test_merge_nochange(self):
        self.mergetest("foo", "a", "a", "a", self.entry, self.entry,
                       [], "a", "a", "a", self.entry, self.entry)

    def test_merge_localchange(self):
        self.mergetest("foo", "b", "a", "a", self.entry, self.entry,
                       ["M %l"], "b", "a", "a", self.entry, self.entry)

    def test_merge_remotechange(self):
        self.mergetest("foo", "a", "a", "b", self.entry, self.entry,
                       ["U %l"], "b", "b", "b", self.entry, self.entry)

    def test_merge_diff3(self):
        self.mergetest("foo", "a\nl\n", "a\n", "r\na\n",
                       self.entry, self.entry,
                       ["M %l"], "r\na\nl\n", "r\na\n", "r\na\n",
                       self.entry, self.entry)

    def test_merge_equal(self):
        self.mergetest("foo", "ab", "a", "ab", self.entry, self.entry,
                       ["U %l"], "ab", "ab", "ab", self.entry, self.entry)

    def test_merge_conflict(self):
        conflict = "<<<<<<< %l\nl\n=======\nr\n>>>>>>> %r\n"
        self.mergetest("foo", "l\n", "a\n", "r\n", self.entry, self.entry,
                       ["C %l"], conflict, "r\n", "r\n",
                       self.make_conflict_entry, self.entry)

    def make_conflict_entry(self, local):
        e = {"conflict": os.path.getmtime(local)}
        e.update(self.entry)
        return e

    def test_new_directory(self):
        self.mergetest("foo", None, None, {"x": "x"}, None, self.entry,
                       ["N %l/", "U %l/x"],
                       {"x": "x"}, {"x": "x"}, {"x": "x"},
                       self.entry, self.entry)

def test_suite():
    s = unittest.TestSuite()
    s.addTest(unittest.makeSuite(TestFSMerger))
    return s

def test_main():
    unittest.TextTestRunner().run(test_suite())

if __name__=='__main__':
    test_main()
