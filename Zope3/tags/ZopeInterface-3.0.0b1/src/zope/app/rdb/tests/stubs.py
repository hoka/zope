##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Stubs for Zope RDB unit tests.

$Id$
"""

class ConnectionStub:

    def __init__(self):
        self._called={}

    def cursor(self):
        return CursorStub()

    def answer(self):
        return 42

    def commit(self, *ignored):
        v = self._called.setdefault('commit',0)
        v+=1
        self._called['commit']=v
    def rollback(self, *ignored):
        v = self._called.setdefault('rollback',0)
        v+=1
        self._called['rollback']=v

class CursorStub:
    def execute(*args, **kw):
        pass

class TypeInfoStub:
    paramstyle = 'pyformat'
    threadsafety = 0
    def getConverter(self, type):
        return lambda x: x
