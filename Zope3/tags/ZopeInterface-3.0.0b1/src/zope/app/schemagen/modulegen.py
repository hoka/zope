##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""
$Id$
"""
from zope.app.schemagen.typereg import fieldRegistry

def generateModuleSource(schema_name, fields, class_name,
                         schema_version=0, extra_imports='', extra_methods=''):
    """Generate module source from schema information.

    extra_methods if supplied needs to be a string with a four space indent.
    """
    if extra_methods:
        extra_methods = '\n%s' % extra_methods
    if extra_imports:
        extra_imports = '%s\n' % extra_imports

    import_list = []
    field_text_list = []
    property_text_list = []
    for field_name, field in fields:
        r = fieldRegistry.represent(field)
        field_text_list.append('    %s = %s' % (field_name, r.text))
        property_text_list.append(
            "    %s = "
            "FieldProperty(%s['%s'])" % (
            field_name, schema_name, field_name))
        for import_entry in r.importList:
            import_list.append("from %s import %s" % import_entry)

    import_text = '\n'.join(import_list)
    field_text = '\n'.join(field_text_list)
    property_text = '\n'.join(property_text_list)

    text = '''\
from zope.interface import Interface, implements
from persistent import Persistent
from zope.schema.fieldproperty import FieldProperty

# field imports
%(import_text)s
%(extra_imports)s
class %(schema_name)s(Interface):
    """Autogenerated schema."""
%(field_text)s

class %(class_name)s(Persistent):
    """Autogenerated class for %(schema_name)s."""
    implements(%(schema_name)s)

    def __init__(self):
        self.__schema_version__ = %(schema_version)s

%(property_text)s
%(extra_methods)s
''' % vars()

    # Normalize to one trailing newline.  This helps exact-match tests pass.
    # Since the loop is unlikely to go around more than once, don't bother
    # with a fancy algorithm.
    while text.endswith('\n\n'):
        text = text[:-1]
    return text
