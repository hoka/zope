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

$Id: test_add.py,v 1.24 2004/01/16 13:38:19 philikon Exp $
"""

import unittest

from zope.app.tests import ztapi
from zope.interface import Interface, implements
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import TestRequest
from zope.schema import TextLine, accessors
from zope.component import getView

from zope.app.browser.form.add import AddViewFactory, AddView
from zope.app.browser.form.metaconfigure import AddFormDirective
from zope.app.interfaces.container import IAdding
from zope.app.form.widget import CustomWidgetFactory
from zope.app.browser.form.widget import TextWidget as Text
from zope.app.tests.placelesssetup import PlacelessSetup
from zope.app.browser.form.submit import Update
# Foo needs to be imported as globals() are checked
from zope.app.browser.form.tests.test_editview import IFoo, IBar, Foo
from zope.app.browser.form.tests.test_editview import FooBarAdapter

class Context:

    def action(self, discriminator, callable, args=(), kw={}):
        self.last_action = (discriminator, callable, args, kw)

class I(Interface):

    name = TextLine()
    first = TextLine()
    last = TextLine()
    email = TextLine()
    address = TextLine()
    getfoo, setfoo = accessors(TextLine())
    extra1 = TextLine()
    extra2 = TextLine(required=False)

class C:

    implements(I)

    def __init__(self, *args, **kw):
        self.args = args
        self.kw = kw

    def getfoo(self): return self._foo
    def setfoo(self, v): self._foo = v

class V:
    name_widget = CustomWidgetFactory(Text)
    first_widget = CustomWidgetFactory(Text)
    last_widget = CustomWidgetFactory(Text)
    email_widget = CustomWidgetFactory(Text)
    address_widget = CustomWidgetFactory(Text)
    getfoo_widget = CustomWidgetFactory(Text)
    extra1_widget = CustomWidgetFactory(Text)
    extra2_widget = CustomWidgetFactory(Text)

class FooV:
    bar_widget = CustomWidgetFactory(Text)


class SampleData:

    name = u"foo"
    first = u"bar"
    last = u"baz"
    email = u"baz@dot.com"
    address = u"aa"
    getfoo = u"foo"
    extra1 = u"extra1"
    extra2 = u"extra2"

class Test(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        self._context = Context()
        super(Test, self).setUp()
        ztapi.provideAdapter(IFoo, IBar, FooBarAdapter)

    def _invoke_add(self, schema=I, name="addthis", permission="zope.Public",
                    label="Add this", content_factory=C, class_=V,
                    arguments=['first', 'last'], keyword_arguments=['email'],
                    set_before_add=['getfoo'], set_after_add=['extra1'],
                    fields=None):
        """ Call the 'add' factory to process arguments into 'args'."""
        AddFormDirective(self._context,
                         schema=schema,
                         name=name,
                         permission=permission,
                         label=label,
                         content_factory=content_factory,
                         class_=class_,
                         arguments=arguments,
                         keyword_arguments=keyword_arguments,
                         set_before_add=set_before_add,
                         set_after_add=set_after_add,
                         fields=fields
                         )()

    def test_add_no_fields(self):
        _context = self._context
        self._invoke_add()
        result1 = _context.last_action
        self._invoke_add(
            fields="name first last email address getfoo extra1 extra2".split(),
            )
        result2 = _context.last_action

        self.assertEqual(result1, result2)

    def test_add_error_handling(self):
        # cannot use a field in arguments if it is not mentioned in fields
        self.assertRaises(ValueError, self._invoke_add, fields="first email getfoo extra1".split())
        # cannot use a field in keyword_arguments if it is not mentioned in fields
        self.assertRaises(ValueError, self._invoke_add, fields="first last getfoo extra1".split())
        # cannot use a field in set_before_add if it is not mentioned in fields
        self.assertRaises(ValueError, self._invoke_add, fields="first last email extra1".split())
        # cannot use a field in set_after_add if it is not mentioned in fields
        self.assertRaises(ValueError, self._invoke_add, fields="first last email getfoo".split())
        # cannot use an optional field in arguments
        self.assertRaises(ValueError, self._invoke_add, arguments=["extra2"])

    def test_add(self, args=None):
        self._invoke_add()
        (descriminator, callable, args, kw) = self._context.last_action

        self.assertEqual(descriminator,
                         ('view', IAdding, "addthis", IBrowserRequest,
                          "default"))
        self.assertEqual(callable, AddViewFactory)

        (name, schema, label, permission, layer, template,
         default_template, bases, for_, fields, content_factory,
         arguments, keyword_arguments, set_before_add,
         set_after_add)  = args

        self.assertEqual(name, 'addthis')
        self.assertEqual(schema, I)
        self.assertEqual(label, 'Add this')
        self.assertEqual(permission, 'zope.Public')
        self.assertEqual(layer, 'default')
        self.assertEqual(template, 'add.pt')
        self.assertEqual(default_template, 'add.pt')
        self.assertEqual(bases, (V, AddView, ))
        self.assertEqual(for_, IAdding)
        self.assertEqual(" ".join(fields),
                         "name first last email address getfoo extra1 extra2")
        self.assertEqual(content_factory, C)
        self.assertEqual(" ".join(arguments),
                         "first last")
        self.assertEqual(" ".join(keyword_arguments),
                         "email")
        self.assertEqual(" ".join(set_before_add),
                         "getfoo")
        self.assertEqual(" ".join(set_after_add),
                         "extra1 name address extra2")

        return args

    def test_create(self):

        class Adding:

            implements(IAdding)

            def __init__(self, test):
                self.test = test

            def add(self, ob):
                self.ob = ob
                self.test.assertEqual(
                    ob.__dict__,
                    {'args': ("bar", "baz"),
                     'kw': {'email': 'baz@dot.com'},
                     '_foo': 'foo',
                    })
                return ob
            def nextURL(self):
                return "."

        adding = Adding(self)
        self._invoke_add()
        (descriminator, callable, args, kw) = self._context.last_action
        factory = AddViewFactory(*args)
        request = TestRequest()
        view = getView(adding, 'addthis', request)
        content = view.create('a',0,abc='def')

        self.failUnless(isinstance(content, C))
        self.assertEqual(content.args, ('a', 0))
        self.assertEqual(content.kw, {'abc':'def'})

    def test_createAndAdd(self):

        class Adding:

            implements(IAdding)

            def __init__(self, test):
                self.test = test

            def add(self, ob):
                self.ob = ob
                self.test.assertEqual(
                    ob.__dict__,
                    {'args': ("bar", "baz"),
                     'kw': {'email': 'baz@dot.com'},
                     '_foo': 'foo',
                    })
                return ob
            def nextURL(self):
                return "."

        adding = Adding(self)
        self._invoke_add()
        (descriminator, callable, args, kw) = self._context.last_action
        factory = AddViewFactory(*args)
        request = TestRequest()
        view = getView(adding, 'addthis', request)

        view.createAndAdd(SampleData.__dict__)

        self.assertEqual(adding.ob.extra1, "extra1")
        self.assertEqual(adding.ob.extra2, "extra2")
        self.assertEqual(adding.ob.name, "foo")
        self.assertEqual(adding.ob.address, "aa")

    def test_createAndAdd_w_adapter(self):

        class Adding:

            implements(IAdding)

            def __init__(self, test):
                self.test = test

            def add(self, ob):
                self.ob = ob
                self.test.assertEqual(ob.__dict__, {'foo': 'bar'})
                return ob
            def nextURL(self):
                return "."

        adding = Adding(self)
        self._invoke_add(
            schema=IBar, name="addthis", permission="zope.Public",
            label="Add this", content_factory=Foo, class_=FooV,
            arguments=None, keyword_arguments=None,
            set_before_add=["bar"], set_after_add=None,
            fields=None
            )
        (descriminator, callable, args, kw) = self._context.last_action
        factory = AddViewFactory(*args)
        request = TestRequest()
        view = getView(adding, 'addthis', request)

        view.createAndAdd({'bar': 'bar'})

    def test_hooks(self):

        class Adding:
            implements(IAdding)

        adding = Adding()
        self._invoke_add()
        (descriminator, callable, args, kw) = self._context.last_action
        factory = AddViewFactory(*args)
        request = TestRequest()

        request.form.update(dict([
            ("field.%s" % k, v)
            for (k, v) in dict(SampleData.__dict__).items()
            ]))
        request.form[Update] = ''
        view = getView(adding, 'addthis', request)

        # Add hooks to V

        l=[None]

        def add(aself, ob):
            l[0] = ob
            self.assertEqual(
                ob.__dict__,
                {'args': ("bar", "baz"),
                 'kw': {'email': 'baz@dot.com'},
                 '_foo': 'foo',
                 })
            return ob

        V.add = add

        V.nextURL = lambda self: 'next'

        try:
            self.assertEqual(view.update(), '')

            self.assertEqual(view.errors, ())

            self.assertEqual(l[0].extra1, "extra1")
            self.assertEqual(l[0].extra2, "extra2")
            self.assertEqual(l[0].name, "foo")
            self.assertEqual(l[0].address, "aa")

            self.assertEqual(request.response.getHeader("Location"), "next")

            # Verify that calling update again doesn't do anything.
            l[0] = None
            self.assertEqual(view.update(), '')
            self.assertEqual(l[0], None)

        finally:
            # Uninstall hooks
            del V.add
            del V.nextURL


def test_suite():
    return unittest.makeSuite(Test)

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
