
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
"""Filesystem synchroniation support for `zope.app.module`.

$Id$
"""
__docformat__ = 'restructuredtext'

from zope.interface import implements

from zope.fssync.server.entryadapter import ObjectEntryAdapter, AttrMapping
from zope.fssync.server.interfaces import IObjectFile


class ModuleAdapter(ObjectEntryAdapter):

    implements(IObjectFile)

    def getBody(self):
        return self.context.source

    def setBody(self, source):
        self.context.update(source)

    def extra(self):
        return AttrMapping(self.context, ("name",))
