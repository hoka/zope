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
"""Inserting optional tests with 'sqlgroup'
  
    It is sometimes useful to make inputs to an SQL statement
    optinal.  Doing so can be difficult, because not only must the
    test be inserted conditionally, but SQL boolean operators may or
    may not need to be inserted depending on whether other, possibly
    optional, comparisons have been done.  The 'sqlgroup' tag
    automates the conditional insertion of boolean operators.  

    The 'sqlgroup' tag is a block tag that has no attributes. It can
    have any number of 'and' and 'or' continuation tags.

    Suppose we want to find all people with a given first or nick name
    and optionally constrain the search by city and minimum and
    maximum age.  Suppose we want all inputs to be optional.  We can
    use DTML source like the following::

      <dtml-sqlgroup>
        <dtml-sqlgroup>
          <dtml-sqltest name column=nick_name type=nb multiple optional>
        <dtml-or>
          <dtml-sqltest name column=first_name type=nb multiple optional>
        </dtml-sqlgroup>
      <dtml-and>
        <dtml-sqltest home_town type=nb optional>
      <dtml-and>
        <dtml-if minimum_age>
           age >= <dtml-sqlvar minimum_age type=int>
        </dtml-if>
      <dtml-and>
        <dtml-if maximum_age>
           age <= <dtml-sqlvar maximum_age type=int>
        </dtml-if>
      </dtml-sqlgroup>

    This example illustrates how groups can be nested to control
    boolean evaluation order.  It also illustrates that the grouping
    facility can also be used with other DTML tags like 'if' tags.

    The 'sqlgroup' tag checks to see if text to be inserted contains
    other than whitespace characters.  If it does, then it is inserted
    with the appropriate boolean operator, as indicated by use of an
    'and' or 'or' tag, otherwise, no text is inserted.

$Id: DT_SQLTest.py,v 1.3 2002/09/18 15:04:47 jim Exp $
"""
import sys
from Zope.DocumentTemplate.DT_Util import ParseError, parse_params, name_param
from types import ListType, TupleType, StringTypes, StringType


class SQLTest: 
    name = 'sqltest'
    optional = multiple = None

    # Some defaults
    sql_delimiter = '\0'

    def sql_quote__(self, v):
        if v.find("\'") >= 0:
            v = "''".join(v.split("\'"))
        return "'%s'" %v

    def __init__(self, args):
        args = parse_params(args, name='', type=None, column=None,
                            multiple=1, optional=1, op=None)
        self.__name__ = name_param(args, 'sqlvar')
        has_key=args.has_key
        if not has_key('type'):
            raise ParseError, ('the type attribute is required', 'sqltest')
        self.type = t = args['type']
        if not valid_type(t):
            raise ParseError, ('invalid type, %s' % t, 'sqltest')
        if has_key('optional'):
            self.optional = args['optional']
        if has_key('multiple'):
            self.multiple = args['multiple']
        if has_key('column'):
            self.column = args['column']
        else: self.column=self.__name__

        # Deal with optional operator specification
        op = '='                        # Default
        if has_key('op'):
            op = args['op']
            # Try to get it from the chart, otherwise use the one provided
            op = comparison_operators.get(op, op)
        self.op = op


    def render(self, md):
        name = self.__name__
        t = self.type
        try:
            v = md[name]
        except KeyError, key:
            if key[0] == name and self.optional:
                return ''
            raise KeyError, key, sys.exc_info()[2]
            
        if isinstance(v, (ListType, TupleType)):
            if len(v) > 1 and not self.multiple:
                raise 'Multiple Values', (
                    'multiple values are not allowed for <em>%s</em>'
                    % name)
        else:
            v = [v]
        
        vs = []
        for v in v:
            if not v and isinstance(v, StringTypes) and t != 'string':
                continue
            # XXX Ahh, the code from DT_SQLVar is duplicated here!!! 
            if t == 'int':
                try:
                    if isinstance(v, StringTypes):
                        int(v)
                    else:
                        v = str(int(v))
                except:
                    raise ValueError, (
                        'Invalid integer value for **%s**' % name)

            elif t == 'float':
                if not v and type(v) is StringType:
                    continue
                try:
                    if isinstance(v, StringTypes):
                        float(v)
                    else:
                        v = str(float(v))
                except:
                    raise ValueError, (
                        'Invalid floating-point value for **%s**' % name)
            else:
                v = str(v)
                v = self.sql_quote__(v)
    
            vs.append(v)

        if not vs:
            if self.optional:
                return ''
            raise 'Missing Input', (
                'No input was provided for **%s**' % name)

        if len(vs) > 1:
            vs = ', '.join(map(str, vs))
            return "%s in (%s)" % (self.column,vs)
        return "%s %s %s" % (self.column, self.op, vs[0])

    __call__ = render

valid_type = {'int':1, 'float':1, 'string':1, 'nb': 1}.has_key

# SQL compliant comparison operators
comparison_operators = { 'eq': '=', 'ne': '<>',
                         'lt': '<', 'le': '<=', 'lte': '<=',
                         'gt': '>', 'ge': '>=', 'gte': '>=' }
