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
"""

$Id: AttrItemNamespaces.py,v 1.3 2002/07/12 19:28:32 jim Exp $
"""

from Namespaces import provideNamespaceHandler
from Exceptions import UnexpectedParameters

def attr(name, parameters, pname, ob, request):
    if parameters:
        raise UnexpectedParameters(parameters)
    return getattr(ob, name)

def item(name, parameters, pname, ob, request):
    if parameters:
        raise UnexpectedParameters(parameters)
    return ob[name]
