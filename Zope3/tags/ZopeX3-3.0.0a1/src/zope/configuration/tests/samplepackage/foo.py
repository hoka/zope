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
"""Sample module used for testing

$Id$
"""
from zope.interface import Interface
from zope import schema

data = []

class S1(Interface):
    x = schema.BytesLine()
    y = schema.Int()

class stuff:
    def __init__(self, args, info, basepath, package, includepath):
        (self.args, self.info, self.basepath, self.package, self.includepath
         ) = args, info, basepath, package, includepath

def handler(_context, **kw):
    args = kw.items()
    args.sort()
    args = tuple(args)
    discriminator = args
    args = (stuff(args, _context.info, _context.basepath, _context.package,
                  _context.includepath), )
    _context.action(discriminator, data.append, args)
