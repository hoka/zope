#! /usr/bin/env python1.5
"""Tests for the HTMLTALParser code generator."""

import pprint
import sys

from TAL.tests import utils
import unittest

from string import rfind

from TAL import HTMLTALParser
from TAL.TALDefs import TAL_VERSION, TALError, METALError


class TestCaseBase(unittest.TestCase):

    prologue = ""
    epilogue = ""
    initial_program = [('version', TAL_VERSION), ('mode', 'html')]
    final_program = []

    def _merge(self, p1, p2):
        if p1 and p2:
            op1, args1 = p1[-1]
            op2, args2 = p2[0]
            if op1[:7] == 'rawtext' and op2[:7] == 'rawtext':
                return (p1[:-1]
                        + [rawtext(args1[0] + args2[0])]
                        + p2[1:])
        return p1+p2

    def _run_check(self, source, program, macros={}):
        parser = HTMLTALParser.HTMLTALParser()
        parser.parseString(self.prologue + source + self.epilogue)
        got_program, got_macros = parser.getCode()
        program = self._merge(self.initial_program, program)
        program = self._merge(program, self.final_program)
        self.assert_(got_program == program,
                     "Program:\n" + pprint.pformat(got_program)
                     + "\nExpected:\n" + pprint.pformat(program))
        self.assert_(got_macros == macros,
                     "Macros:\n" + pprint.pformat(got_macros)
                     + "\nExpected:\n" + pprint.pformat(macros))

    def _get_check(self, source, program=[], macros={}):
        parser = HTMLTALParser.HTMLTALParser()
        parser.parseString(source)
        got_program, got_macros = parser.getCode()
        pprint.pprint(got_program)
        pprint.pprint(got_macros)

    def _should_error(self, source, exc=TALError):
        def parse(self=self, source=source):
            parser = HTMLTALParser.HTMLTALParser()
            parser.parseString(self.prologue + source + self.epilogue)
        self.assertRaises(exc, parse)


def rawtext(s):
    """Compile raw text to the appropriate instruction."""
    if "\n" in s:
        return ("rawtextColumn", (s, len(s) - (rfind(s, "\n") + 1)))
    else:
        return ("rawtextOffset", (s, len(s)))


class HTMLTALParserTestCases(TestCaseBase):

    def check_code_simple_identity(self):
        self._run_check("""<html a='b' b="c" c=d><title>My Title</html>""", [
            rawtext('<html a="b" b="c" c="d">'
                    '<title>My Title</title></html>'),
            ])

    def check_code_implied_list_closings(self):
        self._run_check("""<ul><li><p><p><li></ul>""", [
            rawtext('<ul><li><p></p><p></p></li><li></li></ul>'),
            ])
        self._run_check("""<dl><dt><dt><dd><dd><ol><li><li></ol></dl>""", [
            rawtext('<dl><dt></dt><dt></dt><dd></dd>'
                    '<dd><ol><li></li><li></li></ol></dd></dl>'),
            ])

    def check_code_implied_table_closings(self):
        self._run_check("""<p>text <table><tr><th>head\t<tr><td>cell\t"""
                        """<table><tr><td>cell \n \t \n<tr>""", [
            rawtext('<p>text</p> <table><tr><th>head</th>'
                    '</tr>\t<tr><td>cell\t<table><tr><td>cell</td>'
                    '</tr> \n \t \n<tr></tr></table></td></tr></table>'),
            ])
        self._run_check("""<table><tr><td>cell """
                        """<table><tr><td>cell </table></table>""", [
            rawtext('<table><tr><td>cell <table><tr><td>cell</td></tr>'
                    ' </table></td></tr></table>'),
            ])

    def check_code_bad_nesting(self):
        def check(self=self):
            self._run_check("<a><b></a></b>", [])
        self.assertRaises(HTMLTALParser.NestingError, check)

    def check_cdata_mode(self):
        """This routine should NOT detect an error with an end tag </a></b> not
           matching the start <script> tag.  The contents are within a
           HTML comment, and should be ignored.
        """
        # The above comment is not generally true.  The HTML 4 specification
        # gives <script> a CDATA content model, which means comments are not
        # syntactically recognized (those characters contribute to the text
        # content of the <script> element).  The '</a' in the '</a>' causes
        # the SGML markup-in-context rules to kick in, and '</a>' should then
        # be recognized as an improperly nested end tag.  See:
        # http://www.w3.org/TR/html401/types.html#type-cdata
        #
        s = """<html><script>\n<!--\ndocument.write("</a></b>");\n// -->\n</script></html>"""
        output = [
            rawtext(s),
            ]
        self._run_check(s, output)

    def check_code_attr_syntax(self):
        output = [
            rawtext('<a b="v" c="v" d="v" e></a>'),
            ]
        self._run_check("""<a b='v' c="v" d=v e>""", output)
        self._run_check("""<a  b = 'v' c = "v" d = v e>""", output)
        self._run_check("""<a\nb\n=\n'v'\nc\n=\n"v"\nd\n=\nv\ne>""", output)
        self._run_check("""<a\tb\t=\t'v'\tc\t=\t"v"\td\t=\tv\te>""", output)

    def check_code_attr_values(self):
        self._run_check(
            """<a b='xxx\n\txxx' c="yyy\t\nyyy" d='\txyz\n'>""", [
            rawtext('<a b="xxx\n\txxx" c="yyy\t\nyyy" d="\txyz\n"></a>')])
        self._run_check("""<a b='' c="">""", [
            rawtext('<a b="" c=""></a>'),
            ])

    def check_code_attr_entity_replacement(self):
        # we expect entities *not* to be replaced by HTLMParser!
        self._run_check("""<a b='&amp;&gt;&lt;&quot;&apos;'>""", [
            rawtext('<a b="&amp;&gt;&lt;&quot;\'"></a>'),
            ])
        self._run_check("""<a b='\"'>""", [
            rawtext('<a b="&quot;"></a>'),
            ])
        self._run_check("""<a b='&'>""", [
            rawtext('<a b="&amp;"></a>'),
            ])
        self._run_check("""<a b='<'>""", [
            rawtext('<a b="&lt;"></a>'),
            ])

    def check_code_attr_funky_names(self):
        self._run_check("""<a a.b='v' c:d=v e-f=v>""", [
            rawtext('<a a.b="v" c:d="v" e-f="v"></a>'),
            ])

    def check_code_pcdata_entityref(self):
        self._run_check("""&nbsp;""", [
            rawtext('&nbsp;'),
            ])

    def check_code_short_endtags(self):
        self._run_check("""<html><img/></html>""", [
            rawtext('<html><img /></html>'),
            ])


class METALGeneratorTestCases(TestCaseBase):

    def check_null(self):
        self._run_check("", [])

    def check_define_macro(self):
        macro = self.initial_program + [
            ('startTag', ('p', [('metal:define-macro', 'M', 2)])),
            rawtext('booh</p>'),
            ]
        program = [
            ('setPosition', (1, 0)),
            ('defineMacro', ('M', macro)),
            ]
        macros = {'M': macro}
        self._run_check('<p metal:define-macro="M">booh</p>', program, macros)

    def check_use_macro(self):
        self._run_check('<p metal:use-macro="M">booh</p>', [
            ('setPosition', (1, 0)),
            ('useMacro',
             ('M', '$M$', {},
              [('startTag', ('p', [('metal:use-macro', 'M', 2)])),
               rawtext('booh</p>')])),
            ])

    def check_define_slot(self):
        macro = self.initial_program + [
            ('startTag', ('p', [('metal:define-macro', 'M', 2)])),
            rawtext('foo'),
            ('setPosition', (1, 29)),
            ('defineSlot', ('S',
             [('startTag', ('span', [('metal:define-slot', 'S', 2)])),
              rawtext('spam</span>')])),
            rawtext('bar</p>'),
            ]
        program = [('setPosition', (1, 0)),
                   ('defineMacro', ('M', macro))]
        macros = {'M': macro}
        self._run_check('<p metal:define-macro="M">foo'
                        '<span metal:define-slot="S">spam</span>bar</p>',
                        program, macros)

    def check_fill_slot(self):
        self._run_check('<p metal:use-macro="M">foo'
                        '<span metal:fill-slot="S">spam</span>bar</p>', [
            ('setPosition', (1, 0)),
            ('useMacro',
             ('M', '$M$',
              {'S': [('startTag', ('span',
                                   [('metal:fill-slot', 'S', 2)])),
                     rawtext('spam</span>')]},
             [('startTag', ('p', [('metal:use-macro', 'M', 2)])),
              rawtext('foo'),
              ('setPosition', (1, 26)),
              ('fillSlot', ('S',
               [('startTag', ('span', [('metal:fill-slot', 'S', 2)])),
                rawtext('spam</span>')])),
              rawtext('bar</p>')])),
            ])


class TALGeneratorTestCases(TestCaseBase):

    def check_null(self):
        self._run_check("", [])

    def check_define_1(self):
        self._run_check("<p tal:define='xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'xyzzy string:spam'}),
            ('setLocal', ('xyzzy', '$string:spam$')),
            ('startTag', ('p', [('tal:define', 'xyzzy string:spam', 3)])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_2(self):
        self._run_check("<p tal:define='local xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'local xyzzy string:spam'}),
            ('setLocal', ('xyzzy', '$string:spam$')),
            ('startTag', ('p',
             [('tal:define', 'local xyzzy string:spam', 3)])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_3(self):
        self._run_check("<p tal:define='global xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'global xyzzy string:spam'}),
            ('setGlobal', ('xyzzy', '$string:spam$')),
            ('startTag', ('p',
             [('tal:define', 'global xyzzy string:spam', 3)])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_4(self):
        self._run_check("<p tal:define='x string:spam; y x'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'x string:spam; y x'}),
            ('setLocal', ('x', '$string:spam$')),
            ('setLocal', ('y', '$x$')),
            ('startTag', ('p', [('tal:define', 'x string:spam; y x', 3)])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_5(self):
        self._run_check("<p tal:define='x string:;;;;; y x'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'x string:;;;;; y x'}),
            ('setLocal', ('x', '$string:;;$')),
            ('setLocal', ('y', '$x$')),
            ('startTag', ('p', [('tal:define', 'x string:;;;;; y x', 3)])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_6(self):
        self._run_check(
            "<p tal:define='x string:spam; global y x; local z y'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:define': 'x string:spam; global y x; local z y'}),
            ('setLocal', ('x', '$string:spam$')),
            ('setGlobal', ('y', '$x$')),
            ('setLocal', ('z', '$y$')),
            ('startTag', ('p',
             [('tal:define', 'x string:spam; global y x; local z y', 3)])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_condition(self):
        self._run_check(
            "<p><span tal:condition='python:1'><b>foo</b></span></p>", [
            rawtext('<p>'),
            ('setPosition', (1, 3)),
            ('beginScope', {'tal:condition': 'python:1'}),
            ('condition', ('$python:1$',
             [('startTag', ('span', [('tal:condition', 'python:1', 3)])),
              rawtext('<b>foo</b></span>')])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_content_1(self):
        self._run_check("<p tal:content='string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:content': 'string:foo'}), 
             ('startTag', ('p', [('tal:content', 'string:foo', 3)])),
             ('insertText', ('$string:foo$', [rawtext('bar')])),
             ('endScope', ()),
             rawtext('</p>'),
             ])

    def check_content_2(self):
        self._run_check("<p tal:content='text string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:content': 'text string:foo'}),
             ('startTag', ('p', [('tal:content', 'text string:foo', 3)])),
             ('insertText', ('$string:foo$', [rawtext('bar')])),
             ('endScope', ()),
             rawtext('</p>'),
             ])

    def check_content_3(self):
        self._run_check("<p tal:content='structure string:<br>'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:content': 'structure string:<br>'}),
             ('startTag', ('p',
              [('tal:content', 'structure string:<br>', 3)])),
             ('insertStructure',
              ('$string:<br>$', {}, [rawtext('bar')])),
             ('endScope', ()),
             rawtext('</p>'),
             ])

    def check_replace_1(self):
        self._run_check("<p tal:replace='string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:replace': 'string:foo'}),
             ('insertText', ('$string:foo$',
              [('startTag', ('p', [('tal:replace', 'string:foo', 3)])),
               rawtext('bar</p>')])),
             ('endScope', ()),
             ])

    def check_replace_2(self):
        self._run_check("<p tal:replace='text string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:replace': 'text string:foo'}),
             ('insertText', ('$string:foo$',
              [('startTag', ('p',
                             [('tal:replace', 'text string:foo', 3)])),
               rawtext('bar</p>')])),
             ('endScope', ()),
             ])

    def check_replace_3(self):
        self._run_check("<p tal:replace='structure string:<br>'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:replace': 'structure string:<br>'}),
             ('insertStructure', ('$string:<br>$', {},
              [('startTag', ('p',
                [('tal:replace', 'structure string:<br>', 3)])),
               rawtext('bar</p>')])),
             ('endScope', ()),
             ])

    def check_repeat(self):
        self._run_check("<p tal:repeat='x python:(1,2,3)'>"
                        "<span tal:replace='x'>dummy</span></p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:repeat': 'x python:(1,2,3)'}),
             ('loop', ('x', '$python:(1,2,3)$',
              [('startTag', ('p',
                             [('tal:repeat', 'x python:(1,2,3)', 3)])),
               ('setPosition', (1, 33)),
               ('beginScope', {'tal:replace': 'x'}),
               ('insertText', ('$x$',
                [('startTag', ('span', [('tal:replace', 'x', 3)])),
                 rawtext('dummy</span>')])),
               ('endScope', ()),
               rawtext('</p>')])),
             ('endScope', ()),
             ])

    def check_attributes_1(self):
        self._run_check("<a href='foo' name='bar' tal:attributes="
                        "'href string:http://www.zope.org; x string:y'>"
                        "link</a>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:attributes': 'href string:http://www.zope.org; x string:y',
              'name': 'bar', 'href': 'foo'}),
            ('startTag', ('a',
             [('href', 'foo', 0, '$string:http://www.zope.org$'),
              ('name', 'name="bar"'),
              ('tal:attributes',
               'href string:http://www.zope.org; x string:y', 3),
              ('x', None, 1, '$string:y$')])),
            ('endScope', ()),
            rawtext('link</a>'),
            ])

    def check_attributes_2(self):
        self._run_check("<p tal:replace='structure string:<img>' "
                        "tal:attributes='src string:foo.png'>duh</p>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:attributes': 'src string:foo.png',
              'tal:replace': 'structure string:<img>'}),
            ('insertStructure', ('$string:<img>$',
             {'src': '$string:foo.png$'},
             [('startTag', ('p',
               [('tal:replace', 'structure string:<img>', 3),
                ('tal:attributes', 'src string:foo.png', 3)])),
              rawtext('duh</p>')])),
            ('endScope', ()),
            ])

    def check_on_error_1(self):
        self._run_check("<p tal:on-error='string:error' "
                        "tal:content='notHere'>okay</p>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:content': 'notHere', 'tal:on-error': 'string:error'}),
            ('onError',
             ([('startTag', ('p',
                [('tal:on-error', 'string:error', 3),
                 ('tal:content', 'notHere', 3)])),
               ('insertText', ('$notHere$', [rawtext('okay')])),
               rawtext('</p>')],
              [('startTag', ('p',
                [('tal:on-error', 'string:error', 3),
                 ('tal:content', 'notHere', 3)])),
               ('insertText', ('$string:error$', [])),
               rawtext('</p>')])),
            ('endScope', ()),
            ])

    def check_on_error_2(self):
        self._run_check("<p tal:on-error='string:error' "
                        "tal:replace='notHere'>okay</p>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:replace': 'notHere', 'tal:on-error': 'string:error'}),
            ('onError',
             ([('insertText', ('$notHere$',
                [('startTag', ('p',
                  [('tal:on-error', 'string:error', 3),
                   ('tal:replace', 'notHere', 3)])),
                 rawtext('okay</p>')]))],
              [('startTag', ('p',
                [('tal:on-error', 'string:error', 3),
                 ('tal:replace', 'notHere', 3)])),
               ('insertText', ('$string:error$', [])),
               rawtext('</p>')])),
            ('endScope', ()),
            ])

    def check_dup_attr(self):
        self._should_error("<img tal:condition='x' tal:condition='x'>")
        self._should_error("<img metal:define-macro='x' "
                           "metal:define-macro='x'>", METALError)

    def check_tal_errors(self):
        self._should_error("<p tal:define='x' />")
        self._should_error("<p tal:repeat='x' />")
        self._should_error("<p tal:foobar='x' />")
        self._should_error("<p tal:replace='x' tal:content='x' />")
        self._should_error("<p tal:replace='x'>")

    def check_metal_errors(self):
        exc = METALError
        self._should_error(2*"<p metal:define-macro='x'>xxx</p>", exc)
        self._should_error("<html metal:use-macro='x'>" +
                           2*"<p metal:fill-slot='y' />" + "</html>", exc)
        self._should_error("<p metal:foobar='x' />", exc)
        self._should_error("<p metal:define-macro='x'>", exc)
        

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HTMLTALParserTestCases, "check_"))
    suite.addTest(unittest.makeSuite(METALGeneratorTestCases, "check_"))
    suite.addTest(unittest.makeSuite(TALGeneratorTestCases, "check_"))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
