import os, sys, unittest

from Products.PageTemplates import Expressions

class ExpressionTests(unittest.TestCase):

    def setUp(self):
        self.e = e = Expressions.getEngine()
        self.ec = e.getContext(
            one = 1,
            d = {'one': 1, 'b': 'b', '': 'blank', '_': 'under'},
            blank = '',
            )

    def tearDown(self):
        del self.e, self.ec

    def testCompile(self):
        '''Test expression compilation'''
        e = self.e
        for p in ('x', 'x/y', 'x/y/z'):
            e.compile(p)
        e.compile('path:a|b|c/d/e')
        e.compile('string:Fred')
        e.compile('string:A$B')
        e.compile('string:a ${x/y} b ${y/z} c')
        e.compile('python: 2 + 2')
        e.compile('python: 2 \n+\n 2\n')

    def testSimpleEval(self):
        '''Test simple expression evaluation'''
        ec = self.ec
        assert ec.evaluate('one') == 1
        assert ec.evaluate('d/one') == 1
        assert ec.evaluate('d/b') == 'b'

    def testEval1(self):
        '''Test advanced expression evaluation 1'''
        ec = self.ec
        assert ec.evaluate('x | nothing') is None
        assert ec.evaluate('d/') == 'blank'
        assert ec.evaluate('d/_') == 'under'
        assert ec.evaluate('d/ | nothing') == 'blank'
        assert ec.evaluate('d/?blank') == 'blank'

def test_suite():
    return unittest.makeSuite(ExpressionTests)

if __name__=='__main__':
    main()
