##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
__version__='$Revision: 1.15 $'[11:-2]

import re
from types import ListType, TupleType, UnicodeType

def field2string(v):
    if hasattr(v,'read'): return v.read()
    elif isinstance(v,UnicodeType) :
        return v
    else:  
        return str(v)

def field2text(v, nl=re.compile('\r\n|\n\r').search):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    mo = nl(v)
    if mo is None: return v
    l = mo.start(0)
    r=[]
    s=0
    while l >= s:
        r.append(v[s:l])
        s=l+2
        mo=nl(v,s)
        if mo is None: l=-1
        else:          l=mo.start(0)

    r.append(v[s:])
        
    return '\n'.join(r)

def field2required(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    if v.strip(): return v
    raise ValueError, 'No input for required field<p>'

def field2int(v):
    if type(v) in (ListType, TupleType):
        return map(field2int, v)
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    if v:
        try: return int(v)
        except ValueError:
            raise ValueError, (
                "An integer was expected in the value '%s'" % v
                )
    raise ValueError, 'Empty entry when <strong>integer</strong> expected'

def field2float(v):
    if type(v) in (ListType, TupleType):
        return map(field2float, v)
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    if v:
        try: return float(v)
        except ValueError:
            raise ValueError, (
                "A floating-point number was expected in the value '%s'" % v
                )
    raise ValueError, (
        'Empty entry when <strong>floating-point number</strong> expected')

def field2long(v):
    if type(v) in (ListType, TupleType):
        return map(field2long, v)
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)

    # handle trailing 'L' if present.
    if v[-1:] in ('L', 'l'):
        v = v[:-1]
    if v:
        try: return long(v)
        except ValueError:
            raise ValueError, (
                "A long integer was expected in the value '%s'" % v
                )
    raise ValueError, 'Empty entry when <strong>integer</strong> expected'

def field2tokens(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return v.split()

def field2lines(v):
    if type(v) in (ListType, TupleType):
        result=[]
        for item in v:
            result.append(str(item))
        return result
    return field2text(v).split('\n')

def field2date(v):
    from DateTime import DateTime
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return DateTime(v)

def field2boolean(v):
    return v

class _unicode_converter:
    def __call__(self,v):
        # Convert a regular python string. This probably doesnt do what you want,
        # whatever that might be. If you are getting exceptions below, you
        # probably missed the encoding tag from a form field name. Use:
        #       <input name="description:utf8:ustring" .....
        # rather than
        #       <input name="description:ustring" .....
        if hasattr(v,'read'): v=v.read()
        v = unicode(v)
        return self.convert_unicode(v)

    def convert_unicode(self,v):
        raise NotImplementedError('convert_unicode')

class field2ustring(_unicode_converter):
    def convert_unicode(self,v):
        return v
field2ustring = field2ustring()

class field2utokens(_unicode_converter):
    def convert_unicode(self,v):
        return v.split()
field2utokens = field2utokens()

class field2utext(_unicode_converter):
    def convert_unicode(self,v):
        return unicode(field2text(v.encode('utf8')),'utf8')
field2utext = field2utext()

class field2ulines(_unicode_converter):
    def convert_unicode(self,v):
        return field2utext.convert_unicode(v).split('\n')
field2ulines = field2ulines()

type_converters = {
    'float':    field2float,
    'int':      field2int,
    'long':     field2long,
    'string':   field2string,
    'date':     field2date,
    'required': field2required,
    'tokens':   field2tokens,
    'lines':    field2lines,
    'text':     field2text,
    'boolean':  field2boolean,
    'ustring':  field2ustring,
    'utokens':  field2utokens,
    'ulines':   field2ulines,
    'utext':    field2utext,
    }

get_converter=type_converters.get
