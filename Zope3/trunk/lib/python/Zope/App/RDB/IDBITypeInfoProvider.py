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
"""

$Id: IDBITypeInfoProvider.py,v 1.2 2002/07/10 23:37:26 srichter Exp $
"""
from Interface import Interface

class IDBITypeInfoProvider(Interface):
    """This object can get the Type Info for a particular DBI
    implementation."""

    def getTypeInfo():
        """Return an IDBITypeInfo object."""
