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

from unittest import TestCase, TestSuite, main, makeSuite

from Products.ZCTextIndex.Index import Index
from Products.ZCTextIndex.Lexicon import Lexicon, Splitter

class IndexTest(TestCase):
    def setUp(self):
        self.lexicon = Lexicon(Splitter())
        self.index = Index(self.lexicon)

    def test_index_document(self, DOCID=1):
        doc = "simple document contains five words"
        self.index.index_doc(DOCID, doc)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._wordinfo), 5)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index._get_undoinfo(DOCID)), 5)
        for map in self.index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_unindex_document(self):
        DOCID = 1
        self.test_index_document(DOCID)
        self.index.unindex_doc(DOCID)
        self.assertEqual(len(self.index._docweight), 0)
        self.assertEqual(len(self.index._wordinfo), 0)
        self.assertEqual(len(self.index._docwords), 0)

    def test_index_two_documents(self):
        self.test_index_document()
        doc = "another document just four"
        DOCID = 2
        self.index.index_doc(DOCID, doc)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._wordinfo), 8)
        self.assertEqual(len(self.index._docwords), 2)
        self.assertEqual(len(self.index._get_undoinfo(DOCID)), 4)
        wids = self.lexicon.termToWordIds("document")
        self.assertEqual(len(wids), 1)
        document_wid = wids[0]
        for wid, map in self.index._wordinfo.items():
            if wid == document_wid:
                self.assertEqual(len(map), 2)
                self.assert_(map.has_key(1))
                self.assert_(map.has_key(DOCID))
            else:
                self.assertEqual(len(map), 1)

    def test_index_two_unindex_one(self):
        # index two documents, unindex one, and test the results
        self.test_index_two_documents()
        self.index.unindex_doc(1)
        DOCID = 2
        self.assertEqual(len(self.index._docweight), 1)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._wordinfo), 4)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index._get_undoinfo(DOCID)), 4)
        for map in self.index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_index_duplicated_words(self, DOCID=1):
        doc = "very simple repeat repeat repeat document test"
        self.index.index_doc(DOCID, doc)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._wordinfo), 5)
        self.assertEqual(len(self.index._docwords), 1)
##        self.assertEqual(len(self.index._get_undoinfo(DOCID)), 5)
        wids = self.lexicon.termToWordIds("repeat")
        self.assertEqual(len(wids), 1)
        repititive_wid = wids[0]
        for wid, map in self.index._wordinfo.items():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_simple_query_oneresult(self):
        self.index.index_doc(1, 'not the same document')
        results = self.index.search("document")
        self.assertEqual(list(results.keys()), [1])

    def test_simple_query_noresults(self):
        self.index.index_doc(1, 'not the same document')
        results = self.index.search("frobnicate")
        self.assertEqual(list(results.keys()), [])

    def test_query_oneresult(self):
        self.index.index_doc(1, 'not the same document')
        self.index.index_doc(2, 'something about something else')
        results = self.index.search("document")
        self.assertEqual(list(results.keys()), [1])

    def test_search_phrase(self):
        self.index.index_doc(1, "the quick brown fox jumps over the lazy dog")
        self.index.index_doc(2, "the quick fox jumps lazy over the brown dog")
        results = self.index.search_phrase("quick brown fox")
        self.assertEqual(list(results.keys()), [1])

    def test_search_glob(self):
        self.index.index_doc(1, "how now brown cow")
        self.index.index_doc(2, "hough nough browne cough")
        self.index.index_doc(3, "bar brawl")
        results = self.index.search_glob("bro*")
        self.assertEqual(list(results.keys()), [1, 2])
        results = self.index.search_glob("b*")
        self.assertEqual(list(results.keys()), [1, 2, 3])

def test_suite():
    return makeSuite(IndexTest)

if __name__=='__main__':
    main(defaultTest='test_suite')
