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
"""API Documentation macros

$Id: macros.py,v 1.2 2004/03/02 17:11:10 philikon Exp $
"""
from zope.app.basicskin.standardmacros import StandardMacros

BaseMacros = StandardMacros

class APIDocumentationMacros(BaseMacros):
    """Page Template METAL macros for API Documentation"""
    macro_pages = ('menu_macros', 'details_macros')
