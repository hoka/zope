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

$Id: IntegerField.py,v 1.2 2002/06/10 23:27:47 jim Exp $
"""

from Zope.App.Formulator.Field import Field
from Zope.App.Formulator.Validators import IntegerValidator


class IntegerField(Field):

    __implements__ = Field.__implements__

    id = None
    default = ''
    title = 'Integer Field'
    description = 'Integer Field'
    validator = IntegerValidator.IntegerValidator()
