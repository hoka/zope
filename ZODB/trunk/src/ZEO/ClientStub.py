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
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""Stub for interface exported by ClientStorage"""

class ClientStorage:
    def __init__(self, rpc):
        self.rpc = rpc

    def beginVerify(self):
        self.rpc.callAsync('begin')

    # XXX must rename the two invalidate messages.  I can never
    # remember which is which

    def invalidate(self, args):
        self.rpc.callAsync('invalidate', args)

    def Invalidate(self, args):
        self.rpc.callAsync('Invalidate', args)

    def endVerify(self):
        self.rpc.callAsync('end')

    def serialnos(self, arg):
        self.rpc.callAsync('serialnos', arg)

    def info(self, arg):
        self.rpc.callAsync('info', arg)
