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

from Products.ZCTextIndex.QueryParser import QueryParser

from Products.ZCTextIndex.ParseTree import ParseError, ParseTreeNode
from Products.ZCTextIndex.ParseTree import OrNode, AndNode, NotNode
from Products.ZCTextIndex.ParseTree import AtomNode, PhraseNode, GlobNode

class TestQueryParser(TestCase):

    def compareParseTrees(self, got, expected):
        self.assertEqual(isinstance(got, ParseTreeNode), 1)
        self.assertEqual(got.__class__, expected.__class__)
        if isinstance(got, PhraseNode):
            self.assertEqual(got.nodeType(), "PHRASE")
            self.assertEqual(got.getValue(), expected.getValue())
        elif isinstance(got, GlobNode):
            self.assertEqual(got.nodeType(), "GLOB")
            self.assertEqual(got.getValue(), expected.getValue())
        elif isinstance(got, AtomNode):
            self.assertEqual(got.nodeType(), "ATOM")
            self.assertEqual(got.getValue(), expected.getValue())
        elif isinstance(got, NotNode):
            self.assertEqual(got.nodeType(), "NOT")
            self.compareParseTrees(got.getValue(), expected.getValue())
        elif isinstance(got, AndNode) or isinstance(got, OrNode):
            self.assertEqual(got.nodeType(),
                             isinstance(got, AndNode) and "AND" or "OR")
            list1 = got.getValue()
            list2 = expected.getValue()
            self.assertEqual(len(list1), len(list2))
            for i in range(len(list1)):
                self.compareParseTrees(list1[i], list2[i])

    def expect(self, input, output):
        tree = self.p.parseQuery(input)
        self.compareParseTrees(tree, output)

    def failure(self, input):
        self.assertRaises(ParseError, self.p.parseQuery, input)

    def setUp(self):
        self.p = QueryParser()

    def testParseQuery(self):
        self.expect("foo", AtomNode("foo"))
        self.expect("note", AtomNode("note"))
        self.expect("a and b AND c",
                    AndNode([AtomNode("a"), AtomNode("b"), AtomNode("c")]))
        self.expect("a OR b or c",
                    OrNode([AtomNode("a"), AtomNode("b"), AtomNode("c")]))
        self.expect("a AND b OR c AnD d",
                    OrNode([AndNode([AtomNode("a"), AtomNode("b")]),
                            AndNode([AtomNode("c"), AtomNode("d")])]))
        self.expect("(a OR b) AND (c OR d)",
                    AndNode([OrNode([AtomNode("a"), AtomNode("b")]),
                             OrNode([AtomNode("c"), AtomNode("d")])]))
        self.expect("a AND not b",
                    AndNode([AtomNode("a"), NotNode(AtomNode("b"))]))

        self.expect('"foo bar"', PhraseNode("foo bar"))
        self.expect("foo bar", AndNode([AtomNode("foo"), AtomNode("bar")]))
    
        self.expect('(("foo bar"))"', PhraseNode("foo bar"))
        self.expect("((foo bar))", AndNode([AtomNode("foo"), AtomNode("bar")]))

        self.expect('and/', AtomNode("and"))

        self.expect("foo-bar", PhraseNode("foo bar"))
        self.expect("foo -bar", AndNode([AtomNode("foo"),
                                         NotNode(AtomNode("bar"))]))
        self.expect("-foo bar", AndNode([AtomNode("bar"),
                                         NotNode(AtomNode("foo"))]))
        self.expect("booh -foo-bar",
                    AndNode([AtomNode("booh"),
                             NotNode(PhraseNode("foo bar"))]))
        self.expect('booh -"foo bar"',
                    AndNode([AtomNode("booh"),
                             NotNode(PhraseNode("foo bar"))]))
        self.expect('foo"bar"',
                    AndNode([AtomNode("foo"), AtomNode("bar")]))
        self.expect('"foo"bar',
                    AndNode([AtomNode("foo"), AtomNode("bar")]))
        self.expect('foo"bar"blech',
                    AndNode([AtomNode("foo"), AtomNode("bar"),
                             AtomNode("blech")]))

        self.expect("foo*", GlobNode("foo*"))
        self.expect("foo* bar", AndNode([GlobNode("foo*"),
                                         AtomNode("bar")]))

    def testParseFailures(self):
        self.failure("")
        self.failure("not")
        self.failure("OR")
        self.failure("AND")
        self.failure("not foo")
        self.failure(")")
        self.failure("(")
        self.failure("foo OR")
        self.failure("foo AND")
        self.failure("OR foo")
        self.failure("and foo")
        self.failure("(foo) bar")
        self.failure("(foo OR)")
        self.failure("(foo AND)")
        self.failure("(NOT foo)")
        self.failure("-foo")
        self.failure("-foo -bar")
        self.failure('""')


def test_suite():
    return makeSuite(TestQueryParser)

if __name__=="__main__":
    main(defaultTest='test_suite')
