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
"""Interface Service Tests

$Id$
"""
import unittest

from transaction import get_transaction

from ZODB.tests.util import DB
from zodbcode.module import ManagedRegistry

from zope.interface import Interface, implements
from zope.app.interface import PersistentInterface

# XXX for some reason changing this code to use implements() does not work
code = """\
from zope.interface import Interface

class IFoo(Interface):
    pass

class Foo:
    __implemented__ = IFoo

aFoo = Foo()
"""

class PersistentInterfaceTest(unittest.TestCase):

    def setUp(self):
        self.db = DB()
        self.root = self.db.open().root()
        self.registry = ManagedRegistry()
        self.root["registry"] = self.registry
        get_transaction().commit()

    def tearDown(self):
        get_transaction().abort() # just in case

    def test_creation(self):
        class IFoo(PersistentInterface):
            pass

        class Foo:
            implements(IFoo)

        self.assert_(IFoo.providedBy(Foo()))
        self.assertEqual(IFoo._p_oid, None)

    def test_patch(self):
        self.registry.newModule("imodule", code)
        get_transaction().commit()
        imodule = self.registry.findModule("imodule")

        # test for a pickling bug
        self.assertEqual(imodule.Foo.__implemented__, imodule.IFoo)

        self.assert_(imodule.IFoo.providedBy(imodule.aFoo))
        # the conversion should not affect Interface
        self.assert_(imodule.Interface is Interface)


def test_suite():
    return unittest.makeSuite(PersistentInterfaceTest)
