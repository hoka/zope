##############################################################################
#
# Copyright (c) 2002, 2003 Zope Corporation and Contributors.
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

$Id: queryfield.py,v 1.5 2003/06/30 17:20:13 stevea Exp $
"""
from zope.schema import Tuple
from zope.schema.interfaces import ValidationError
from zope.component import getAdapter
from zope.interface import classImplements
# See end of file for further imports

# XXX This code does not work. I'm on the hook for updating it, providing
#     a test and fixing it.
#     SteveA.

class QueryProcessorsField(Tuple):

    def __init__(self, default=(), *args, **kw):
        super(QueryProcessorsField, self).__init__(default=default,
                                                   *args, **kw)

    def _validate(self, value):
        super(QueryProcessorsField, self)._validate(value)
        context = self.context
        for location, adaptername in value:
            # XXX locateComponent has been removed
            component = locateComponent(location, context, IQueryProcessable)
            processor = getAdapter(component, IQueryProcessor,
                                   context=context, name=adaptername)
            if processor is None:
                if name:
                    message = 'No IQueryProcessor adapter named "%s" found'
                else:
                    message = 'No IQueryProcessor adapter found'
                raise ValidationError(message, location)



# Imported here to avoid circular imports
from zope.app.interfaces.services.query import IQueryProcessorsField
from zope.app.interfaces.services.query import IQueryProcessable
from zope.app.interfaces.services.query import IQueryProcessor
classImplements(QueryProcessorsField, IQueryProcessorsField)

