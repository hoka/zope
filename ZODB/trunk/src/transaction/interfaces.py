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
from zope.interface import Interface

class TransactionError(StandardError):
    """An error occured due to normal transaction processing."""

class ConflictError(TransactionError):
    """Two transactions tried to modify the same object at once

    This transaction should be resubmitted.
    """

class RollbackError(TransactionError):
    """An error occurred rolling back a savepoint."""

class IDataManager(Interface):
    """Data management interface for storing objects transactionally

    This is currently implemented by ZODB database connections.
    """

    def prepare(transaction):
        """Begin two-phase commit of a transaction.

        DataManager should return True or False.
        """

    def abort(transaction):
        """Abort changes made by transaction."""

    def commit(transaction):
        """Commit changes made by transaction."""

    def savepoint(transaction):
        """Do tentative commit of changes to this point.

        Should return an object implementing IRollback
        """

class IRollback(Interface):

    def rollback():
        """Rollback changes since savepoint."""

class ITransaction(Interface):
    """Transaction objects

    Application code typically gets these by calling
    get_transaction().
    """

    def abort():
        """Abort the current transaction."""

    def begin():
        """Begin a transaction."""

    def commit():
        """Commit a transaction."""

    def join(resource):
        """Join a resource manager to the current transaction."""

    def status():
        """Return status of the current transaction."""
