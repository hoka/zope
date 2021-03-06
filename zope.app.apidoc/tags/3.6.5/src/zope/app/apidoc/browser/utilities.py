##############################################################################
#
# Copyright (c) 2009 Zope Corporation and Contributors.
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
"""Common Utilities for Browser View

$Id$
"""
from zope.app.apidoc.apidoc import APIDocumentation
from zope.traversing.browser import absoluteURL
from zope.traversing.api import getParent
from zope.security.proxy import isinstance

def findAPIDocumentationRootURL(context, request):
    if isinstance(context, APIDocumentation):
        return absoluteURL(context, request)
    else:
        return findAPIDocumentationRootURL(getParent(context), request)
