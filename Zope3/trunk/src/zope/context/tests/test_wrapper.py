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
$Id: test_wrapper.py,v 1.23 2003/08/17 06:08:53 philikon Exp $
"""
import unittest
from types import MethodType, FunctionType
from zope.proxy import getProxiedObject
from zope.context import wrapper, ContextMethod, ContextProperty
from zope.proxy.tests.test_proxy import Thing, ProxyTestCase

_marker = object()

__metaclass__ = type

class WrapperProperty(object):
    def __init__(self, name, dictname, default=_marker):
        self.name = name
        self.dictname = dictname
        self.default = default

    def __get__(self, obj, tp=None):
        if obj is None:
            return self
        d = wrapper.getdict(obj)
        if d:
            try:
                return d[self.dictname]
            except KeyError:
                pass
        if self.default is not _marker:
            return self.default
        raise AttributeError, self.name

    def __set__(self, obj, value):
        self.default = _marker
        wrapper.getdictcreate(obj)[self.dictname] = value

    def __delete__(self, obj):
        self.default = _marker
        d = wrapper.getdict(obj)
        if d:
            try:
                del d[self.dictname]
                return
            except KeyError:
                pass
        raise AttributeError, self.name

class WrapperTestCase(ProxyTestCase):

    proxy_class = wrapper.Wrapper

    def new_proxy(self, o, c=None):
        return self.proxy_class(o, c)

    def test_constructor(self):
        o1 = object()
        o2 = object()
        o3 = object()
        w = self.new_proxy((o1, o2), o3)
        self.assertEquals(getProxiedObject(w), (o1, o2))
        self.assert_(wrapper.getcontext(w) is o3)

    def test_subclass_constructor(self):
        class MyWrapper(self.proxy_class):
            def __init__(self, *args, **kwds):
                super(MyWrapper, self).__init__('foo', **kwds)

        w = MyWrapper(1, 2, key='value')
        self.assertEquals(getProxiedObject(w), 'foo')
        self.assertEquals(wrapper.getdict(w), {'key': 'value'})

        # __new__ catches too many positional args:
        self.assertRaises(TypeError, MyWrapper, 1, 2, 3)

    def test_wrapper_basics(self):
        o1 = 1
        o2 = 12
        w = self.new_proxy(o1)
        self.assert_(o1 is getProxiedObject(w))
        self.assert_(wrapper.getdict(w) is None)
        d = wrapper.getdictcreate(w)
        self.assert_(wrapper.getdictcreate(w) is d)

        c = 'context'
        wrapper.setcontext(w, c)
        self.assert_(wrapper.getcontext(w) is c)
        wrapper.setcontext(w, None)
        self.assert_(wrapper.getcontext(w) is None)

        wrapper.setobject(w, o2)
        self.assert_(getProxiedObject(w) is o2)

        # test 2-argument version of constructor
        o = object()
        w = self.new_proxy(o, c)
        self.assert_(getProxiedObject(w) is o)
        self.assert_(wrapper.getcontext(w) is c)

    def test_wrapper_subclass_attributes(self):
        class MyWrapper(self.proxy_class):
            def __init__(self, ob):
                super(MyWrapper, self).__init__(ob)
                self.foo = 1

        o = Thing()
        o.foo = 'not 1'
        o.bar = 2
        w = MyWrapper(o)
        self.assert_(w.foo == 1)
        self.assert_(w.bar == 2)

    def make_proxies(self, slot, fixed_retval=_marker):
        context = object()

        def doit(self, *args):
            self.retval = wrapper.getcontext(self), args
            if fixed_retval is _marker:
                return self.retval
            else:
                return fixed_retval

        class ContextUnawareObj(object):
            pass
        setattr(ContextUnawareObj, slot, doit)
        proxy1 = self.new_proxy(ContextUnawareObj(), context)

        class ContextMethodObj(object):
            pass
        setattr(ContextMethodObj, slot, ContextMethod(doit))
        proxy2 = self.new_proxy(ContextMethodObj(), context)

        return proxy1, proxy2, context

    def test_normal_getattr(self):
        class X(object):
            def __init__(self, retval):
                self.args = None
                self.retval = retval
            def __getattr__(self, name):
                if name == '__del__':
                    # We don't want Python's gc to think that we have a
                    # __del__, otherwise cycles will not be collected.
                    raise AttributeError, name
                self.__dict__['args'] = self, name
                return self.__dict__['retval']
            def getArgs(self):
                return self.__dict__['args']

        context = object()

        x = X(23)
        p = self.new_proxy(x, context)
        self.assertEquals(p.foo, 23)
        # Nothing special happens; we don't rebind the self of __getattr__
        self.assertEquals(p.getArgs(), (x, 'foo'))
        self.assert_(p.getArgs()[0] is x)

    def test_ContextMethod_getattr(self):
        class Z(object):
            def __getattr__(self, name):
                return 23
            __getattr__ = ContextMethod(__getattr__)

        z = Z()
        self.assertRaises(TypeError, getattr, z, 'foo')
        p = self.new_proxy(z, 23)
        self.assertRaises(TypeError, getattr, p, 'foo')

        # This is the same behaviour that you get if you try to make
        # __getattr__ a classmethod.
        class ZZ(object):
            def __getattr__(self, name):
                return 23
            __getattr__ = classmethod(__getattr__)

        zz = ZZ()
        self.assertRaises(TypeError, getattr, zz, 'foo')

    def test_property(self):
        class X(object):
            def getFoo(self):
                self.called_with = self
                return 42
            def setFoo(self, value):
                self.called_with = self, value
            foo = property(getFoo, setFoo)
            context_foo = ContextProperty(getFoo, setFoo)
        x = X()
        p = self.new_proxy(x)
        self.assertEquals(p.foo, 42)
        self.assert_(x.called_with is x)
        self.assertEquals(p.context_foo, 42)
        self.assert_(x.called_with is p)
        p.foo = 24
        self.assertEquals(x.called_with, (x, 24))
        self.assert_(x.called_with[0] is x)
        p.context_foo = 24
        self.assertEquals(x.called_with, (p, 24))
        self.assert_(x.called_with[0] is p)

    def test_setattr(self):
        class X(object):
            def __setattr__(self, name, value):
                self.__dict__['value_called'] = self, name, value

        x = X()
        p = self.new_proxy(x)
        p.foo = 'bar'
        self.assertEqual(x.value_called, (p, 'foo', 'bar'))
        self.assert_(x.value_called[0] is x)

        X.__setattr__ = ContextMethod(X.__setattr__)
        x = X()
        p = self.new_proxy(x)
        p.foo = 'bar'
        self.assertEqual(x.value_called, (p, 'foo', 'bar'))
        self.assert_(x.value_called[0] is x)

    def test_UnicodeAttrNames(self):
        class SomeObject(object):
            foo = 42
        obj = SomeObject()
        p = self.new_proxy(obj)
        self.assertEquals(getattr(p, u'foo'), 42)
        self.assertRaises(AttributeError, getattr, p, u'bar')
        self.assertRaises(UnicodeError, getattr, p, u'baz\u1234')
        setattr(p, u'bar', 23)
        self.assertEquals(p.bar, 23)
        self.assertRaises(UnicodeError, setattr, p, u'baz\u1234', 23)

    def test_getitem(self):
        p1, p2, context = self.make_proxies('__getitem__')
        self.assertEquals(p1[42], (None, (42, )))
        self.assertEquals(p2[42], (context, (42, )))
        # builtin
        p = self.new_proxy((1, 2), context)
        self.assertEquals(p[0], 1)
        self.assertEquals(p[1], 2)
        self.assertRaises(IndexError, p.__getitem__, 2)

    def test_setitem(self):
        p1, p2, context = self.make_proxies('__setitem__')
        p1[24] = 42
        p2[24] = 42
        self.assertEquals(p1.retval, (None, (24, 42)))
        self.assertEquals(p2.retval, (context, (24, 42)))
        # builtin
        p = self.new_proxy([1, 2], context)
        p[1] = 3
        self.assertEquals(p[1], 3)
        self.assertRaises(IndexError, p.__setitem__, 2, 4)

    def test_delitem(self):
        p1, p2, context = self.make_proxies('__delitem__')
        del p1[42]
        del p2[42]
        self.assertEquals(p1.retval, (None, (42, )))
        self.assertEquals(p2.retval, (context, (42, )))
        # builtin
        p = self.new_proxy([1, 2], context)
        del p[1]
        self.assertEquals(p, [1])
        self.assertRaises(IndexError, p.__delitem__, 2)

    def test_iter(self):
        p1, p2, context = self.make_proxies('__iter__', iter(()))
        iter(p1)
        iter(p2)
        self.assertEquals(p1.retval, (None, ()))
        self.assertEquals(p2.retval, (context, ()))

    def test_call(self):
        p1, p2, context = self.make_proxies('__call__')
        self.assertEquals(p1('foo', 'bar'), (None, ('foo', 'bar')))
        self.assertEquals(p2('foo', 'bar'), (context, ('foo', 'bar')))

    def test_str(self):
        p1, p2, context = self.make_proxies('__str__', 'foo')
        self.assertEquals(str(p1), 'foo')
        self.assertEquals(str(p2), 'foo')
        self.assertEquals(p1.retval, (None, ()))
        self.assertEquals(p2.retval, (context, ()))

    def test_contains(self):
        p1, p2, context = self.make_proxies('__contains__', 1)
        self.assert_(42 in p1)
        self.assert_(42 in p2)
        self.assertEquals(p1.retval, (None, (42, )))
        self.assertEquals(p2.retval, (context, (42, )))

    def test_len(self):
        p1, p2, context = self.make_proxies('__len__', 5)
        self.assertEquals(len(p1), 5)
        self.assertEquals(len(p2), 5)
        self.assertEquals(p1.retval, (None, ()))
        self.assertEquals(p2.retval, (context, ()))

        p1, p2, context = self.make_proxies('__len__', 5)
        self.assertEquals(bool(p1), True)
        self.assertEquals(bool(p2), True)
        self.assertEquals(p1.retval, (None, ()))
        self.assertEquals(p2.retval, (context, ()))

        p1, p2, context = self.make_proxies('__len__', 0)
        self.assertEquals(bool(p1), False)
        self.assertEquals(bool(p2), False)
        self.assertEquals(p1.retval, (None, ()))
        self.assertEquals(p2.retval, (context, ()))

    def test_nonzero(self):
        p1, p2, context = self.make_proxies('__nonzero__', True)
        self.assertEquals(bool(p1), True)
        self.assertEquals(bool(p2), True)
        self.assertEquals(p1.retval, (None, ()))
        self.assertEquals(p2.retval, (context, ()))

        p1, p2, context = self.make_proxies('__nonzero__', False)
        self.assertEquals(bool(p1), False)
        self.assertEquals(bool(p2), False)
        self.assertEquals(p1.retval, (None, ()))
        self.assertEquals(p2.retval, (context, ()))

    def test_nonzero_with_len(self):
        class ThingWithLenAndNonzero(object):
            len_called = False
            nonzero_called = False
            retval = None

            def __len__(self):
                self.len_called = True
                self.retval = self
                return 0

            def __nonzero__(self):
                self.nonzero_called = True
                self.retval = self
                return False

        obj = ThingWithLenAndNonzero()
        w = self.new_proxy(obj)
        self.assertEquals(bool(w), False)
        self.assertEquals(obj.nonzero_called, True)
        self.assertEquals(obj.len_called, False)
        self.assert_(obj.retval is obj)

        ThingWithLenAndNonzero.__nonzero__ = ContextMethod(
            ThingWithLenAndNonzero.__nonzero__.im_func)

        obj = ThingWithLenAndNonzero()
        w = self.new_proxy(obj)
        self.assertEquals(bool(w), False)
        self.assertEquals(obj.nonzero_called, True)
        self.assertEquals(obj.len_called, False)
        self.assert_(obj.retval is w)

    # Tests for wrapper module globals

    def test_getcontext(self):
        context = object()
        w = self.new_proxy(None, context)
        self.assert_(wrapper.getcontext(w) is context)
        self.assert_(wrapper.getcontext(self.new_proxy(None)) is None)
        self.assert_(wrapper.getcontext(object()) is None)

    def check_getinnercontext(self, context):
        obj = object()
        self.assert_(wrapper.getinnercontext(obj) is None)
        w1 = self.new_proxy(obj, context)
        self.assert_(wrapper.getinnercontext(w1) is context)
        w = self.new_proxy(w1, object())
        w = self.new_proxy(w)
        w = self.new_proxy(w, object())
        w = self.new_proxy(w)
        w = self.new_proxy(w, object())
        self.assert_(wrapper.getinnercontext(w) is context)
        wrapper.setcontext(w1, None)
        self.assert_(wrapper.getinnercontext(w) is None)
        context = object()
        wrapper.setcontext(w1, context)
        self.assert_(wrapper.getinnercontext(w) is context)

    def test_getinnercontext(self):
        self.check_getinnercontext(None)
        self.check_getinnercontext(object())

    def test_getinnerwrapper(self):
        context = object()
        o = object()
        w1 = self.new_proxy(o)
        w2 = self.new_proxy(w1, context)
        x = wrapper.getinnerwrapper(w2)
        self.assert_(x is w1)
        self.assert_(wrapper.getinnerwrapper(o) is o)

    def test_getdict(self):
        w = self.new_proxy(None)
        self.assert_(wrapper.getdict(w) is None)
        d = wrapper.getdictcreate(w)
        self.assert_(wrapper.getdict(w) is d)
        self.assert_(wrapper.getdictcreate(w) is d)
        self.assert_(wrapper.getdict(w) is d)

        w = self.proxy_class(None, name="myobject")
        d = wrapper.getdict(w)
        self.assert_(d is not None)
        self.assert_(wrapper.getdictcreate(w) is d)
        self.assert_(wrapper.getdictcreate(w) is d)
        self.assert_(len(d) == 1)

    def test_setobject(self):
        obj1 = object()
        obj2 = object()
        w = self.new_proxy(obj1)
        self.assert_(getProxiedObject(w) is obj1)
        wrapper.setobject(w, obj2)
        self.assert_(getProxiedObject(w) is obj2)

    def test_setcontext(self):
        w = self.new_proxy(None)
        context = object()
        wrapper.setcontext(w, context)
        self.assert_(wrapper.getcontext(w) is context)

    def test_simple_subclass(self):

        class Foo(self.proxy_class):
            def bar(self, *args):
                inner = getProxiedObject(self)
                inner += args
                return len(args)

            baz = 23
            spoo = WrapperProperty('spoo', 'spooprop', default=23)

        self.assert_(self.proxy_class in Foo.__mro__)

        l = []
        w = Foo(l)

        self.assert_(w.__class__ is l.__class__)
        self.assert_(type(w) is Foo)

        self.assertEquals(w.bar(1, 2, 3), 3)
        self.assertEquals(l, [1, 2, 3])
        w.append('x')
        self.assertEquals(l, [1, 2, 3, 'x'])

        self.assertEquals(w.spoo, 23)
        w.spoo = 24
        self.assertEquals(w.spoo, 24)

        self.assertEquals(w.baz, 23)
        self.assertRaises(TypeError, setattr, w, 'baz', 24)

    def test_subclass_with_slots(self):
        obj = object()

        names = ('__len__', '__getitem__', '__setitem__', '__str__',
                 '__contains__', '__call__', '__nonzero__', '__iter__',
                 'next')

        dummy_iter = iter(range(5))
        proxy_class = self.proxy_class
        class WrapperWithSlots(proxy_class):
            def __init__(self, *args, **kw):
                super(WrapperWithSlots, self).__init__(*args, **kw)
                d = wrapper.getdictcreate(self)
                d['initargs'] = args
                d['initkw'] = kw

            count = WrapperProperty('count', 'wrapper_count', default=0)
            called = WrapperProperty('called', 'wrapper_called')
            def __len__(self):
                self.called = 'len'
                return 5
            def __nonzero__(self):
                self.called = 'nonzero'
                return False
            def __getitem__(self, key):
                self.called = 'getitem'
                return 5
            def __setitem__(self, key, value):
                self.called = 'setitem'
            def __str__(self):
                self.called = 'str'
                return '5'
            def __contains__(self, key):
                self.called = 'contains'
                return True
            def __call__(self):
                self.called = 'call'
                return 'skidoo'
            def __iter__(self):
                self.called = 'iter'
                return self
            def next(self):
                self.called = 'next'
                self.count += 1
                if self.count == 5:
                    self.count = 0
                    raise StopIteration
                return self.count

        w = WrapperWithSlots(obj, None)

        self.assertEquals(len(w), 5)
        self.assertEquals(w.called, 'len')
        del w.called

        self.assertEquals(w[3], 5)
        self.assertEquals(w.called, 'getitem')
        del w.called

        w[3] = 5
        self.assertEquals(w.called, 'setitem')
        del w.called

        self.assertEquals(str(w), '5')
        self.assertEquals(w.called, 'str')
        del w.called

        self.assert_(5 in w)
        self.assertEquals(w.called, 'contains')
        del w.called

        self.assertEquals(w(), 'skidoo')
        self.assertEquals(w.called, 'call')
        del w.called

        self.assertEquals(bool(w), False)
        self.assertEquals(w.called, 'nonzero')
        del w.called

        # Test case where w doesn't provide a __nonzero__ but does
        # provide a __len__.
        del WrapperWithSlots.__nonzero__
        self.assertEquals(bool(w), True)
        self.assertEquals(w.called, 'len')
        del w.called

        self.assertEquals(iter(w), w)
        self.assertEquals(w.called, 'iter')
        del w.called

        self.assertEquals(w.next(), 1)
        self.assertEquals(w.called, 'next')
        self.assertEquals([i for i in iter(w)], [2, 3, 4])
        del w.called

    def test_decorated_iterable(self):
        obj = object()
        a = [1, 2, 3]
        b = []
        class IterableDecorator(self.proxy_class):
            def __iter__(self):
                return iter(a)
        for x in IterableDecorator(obj):
            b.append(x)
        self.assertEquals(a, b)

    def test_iteration_using_decorator(self):
        # Wrap an iterator within the iteration protocol, expecting it
        # still to work.  PyObject_GetIter() will not be called on the
        # proxy, so the tp_iter slot won't unwrap it.

        class Iterable:
            def __init__(self, test, data):
                self.test = test
                self.data = data
            def __iter__(self):
                obj = object()
                it = iter(self.data)
                class IterableDecorator(self.test.proxy_class):
                    def __iter__(self):
                        return it.__iter__()
                    def next(self):
                        return it.next()
                return IterableDecorator(obj)

        a = [1, 2, 3]
        b = []
        for x in Iterable(self, a):
            b.append(x)
        self.assertEquals(a, b)

    def test_descr_abuse(self):
        def abuse():
            def foo(): pass
            ContextMethod(ContextMethod(foo)).__get__(1)
	self.assertRaises(TypeError, abuse)


class WrapperSubclass(wrapper.Wrapper):

    def someMethodOrOther(self):
        pass

class WrapperSubclassTestCase(WrapperTestCase):

    proxy_class = WrapperSubclass

    def new_proxy(self, o, c=None):
        return self.proxy_class(o, c)


class Foo:
    __metaclass__ = type
    def foo(self):
        pass
    s = staticmethod(foo)
    c = classmethod(foo)

class TestGetDescriptor(unittest.TestCase):

    def test_getdescriptor(self):
        from zope.context.wrapper import getdescriptor
        f = Foo()

        self.assertEquals(type(f.foo), MethodType)
        self.assertEquals(type(f.c), MethodType)
        self.assertEquals(type(f.s), FunctionType)

        self.assertEquals(type(getdescriptor(f, 'c')), classmethod)
        self.assertEquals(type(getdescriptor(f, 's')), staticmethod)
        self.assertEquals(type(getdescriptor(f, 'foo')), FunctionType)

        self.assertEquals(getdescriptor(f, 'foo').__get__(f, Foo), f.foo)
        self.assertEquals(getdescriptor(f, 's').__get__(f, Foo), f.s)
        self.assertEquals(getdescriptor(f, 'c').__get__(f, Foo), f.c)

def test_suite():
    return unittest.TestSuite((
            unittest.makeSuite(WrapperTestCase),
            unittest.makeSuite(WrapperSubclassTestCase),
            unittest.makeSuite(TestGetDescriptor),
            ))


if __name__ == "__main__":
    import sys
    runner = unittest.TextTestRunner(sys.stdout)
    result = runner.run(test_suite())
    newerrs = len(result.errors) + len(result.failures)
    sys.exit(newerrs and 1 or 0)
