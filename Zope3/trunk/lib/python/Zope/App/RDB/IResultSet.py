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
$Id: IResultSet.py,v 1.4 2002/07/10 23:37:26 srichter Exp $
"""
from Interface import Interface
from Interface.Attribute import Attribute


class IResultSet(Interface):
    """Holds results, and allows iteration."""

    names = Attribute("""A list of the column names of the returned result
                      set.""")

    def __getitem__(index):
        """Return a brain row for index."""





    
