##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""Standard macros for page templates in the ZMI

The macros are drawn from various different page templates.

$Id: StandardMacros.py,v 1.3 2002/10/28 11:21:13 stevea Exp $
"""
from ZMIViewUtility import ZMIViewUtility, IZMIViewUtility
from Zope.ComponentArchitecture import getView

class Macros:

    macro_pages = ()

    def __getitem__(self, key):
        context = self.context
        request = self.request
        for name in self.macro_pages:
            page = getView(context, name, request)
            try:
                v = page[key]
            except KeyError:
                pass
            else:
                return v
        raise KeyError, key
    

class IStandardMacros(IZMIViewUtility):

    def __getitem__(key):
        """Return the macro named 'key'"""


class StandardMacros(ZMIViewUtility, Macros):

    __implements__ = IStandardMacros

    macro_pages = ('view_macros', 'dialog_macros')

