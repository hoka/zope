##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""
$Id$
"""

from unittest import TestCase, main, makeSuite, TestSuite
from transaction import get_transaction
from transaction.tests.abstestIDataManager import IDataManagerTests
from zope.app.rdb import ZopeDBTransactionManager
from zope.app.rdb import ZopeConnection
from zope.app.rdb.tests.stubs import ConnectionStub, TypeInfoStub

class TxnMgrTest(IDataManagerTests, TestCase):

    def setUp(self):
        self.conn = ConnectionStub()
        zc = ZopeConnection(self.conn, TypeInfoStub())
        self.datamgr = ZopeDBTransactionManager(zc)
        zc.registerForTxn()
        self.txn_factory = get_transaction

    def tearDown(self):
        """ make sure the global env is clean"""
        get_transaction().abort()

    def test_abort(self):
        get_transaction().abort()
        self.assertEqual(self.conn._called.get('rollback'), 1)

    def test_commit(self):
        get_transaction().commit()
        self.assertEqual(self.conn._called.get('commit'), 1)


class TwoTxnMgrSortKeyTest(TestCase):

    # We test two transaction managers here so that when calling
    # commit or abort it triggers the code that calls sortKey()

    def setUp(self):
        self.conn1 = ConnectionStub()
        self.conn2 = ConnectionStub()
        zc1 = ZopeConnection(self.conn1, TypeInfoStub())
        self.datamgr1 = ZopeDBTransactionManager(zc1)
        zc2 = ZopeConnection(self.conn2, TypeInfoStub())
        self.datamgr1 = ZopeDBTransactionManager(zc2)
        zc1.registerForTxn()
        zc2.registerForTxn()
        self.txn_factory = get_transaction

    def tearDown(self):
        """ make sure the global env is clean"""
        get_transaction().abort()

    def test_abort(self):
        get_transaction().abort()
        self.assertEqual(self.conn1._called.get('rollback'), 1)
        self.assertEqual(self.conn2._called.get('rollback'), 1)

    def test_commit(self):
        get_transaction().commit()
        self.assertEqual(self.conn1._called.get('commit'), 1)
        self.assertEqual(self.conn2._called.get('commit'), 1)


def test_suite():
    from doctest import DocTestSuite
    return TestSuite((
        DocTestSuite('zope.app.rdb'),
        makeSuite(TxnMgrTest),
        makeSuite(TwoTxnMgrSortKeyTest),
        ))

if __name__=='__main__':
    main(defaultTest='test_suite')
