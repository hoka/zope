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
$Id: _Field.py,v 1.6 2002/07/14 18:51:27 faassen Exp $
"""
from Interface.Attribute import Attribute
from Interface.Implements import objectImplements

from Exceptions import StopValidation, ValidationError
import ErrorNames


class Field(Attribute):
    # we don't implement the same interface Attribute
    __implements__ = ()
    type = None
    default = None
    required = 0

    def __init__(self, **kw):
        """Pass in field values as keyword parameters."""
        for key, value in kw.items():
            setattr(self, key, value)
        super(Field, self).__init__(self.title or 'no title')

    def validate(self, value):
        try:
            return self.validator(self).validate(value)
        except StopValidation:
            return value

class SingleValueField(Field):
    """A field that contains only one value."""
    allowed_values = []

class Str(SingleValueField):
    """A field representing a Str."""
    type = str
    min_length = None
    max_length = None

class Bool(SingleValueField):
    """A field representing a Bool."""
    type = type(not 1) 

class Int(SingleValueField):
    """A field representing a Integer."""
    type = int
    min = max = None

class Float(SingleValueField):
    """A field representing a Floating Point."""
    type = float, int
    min = max = None
    decimals = None

class Tuple(Field):
    """A field representing a Tuple."""
    type = tuple
    value_types = None
    min_values = max_values = None

class List(Field):
    """A field representing a List."""
    type = list
    value_types = None
    min_values = max_values = None

class Dict(Field):
    """A field representing a Dict."""
    type = dict
    min_values = max_values = None
    key_types = value_types = None


