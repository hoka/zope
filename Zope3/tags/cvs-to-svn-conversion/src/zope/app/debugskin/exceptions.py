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
"""View that renders a traceback for exceptions.

$Id: exceptions.py,v 1.1 2004/03/02 17:11:29 philikon Exp $
"""
import sys
import traceback

from zope.interface.common.interfaces import IException

__metaclass__ = type


class ExceptionDebugView:
    """ Render exceptions for debugging."""
    __used_for__ = IException

    def __init__(self, context, request):

        self.context = context
        self.request = request

        self.error_type, self.error_object, tb = sys.exc_info()
        try:
            self.traceback_lines = traceback.format_tb(tb)
        finally:
            del tb
