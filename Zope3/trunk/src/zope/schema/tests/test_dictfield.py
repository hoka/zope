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
$Id: test_dictfield.py,v 1.4 2003/07/12 02:47:26 richard Exp $
"""
from unittest import main, makeSuite
from zope.schema import Dict, Int, Float
from zope.schema import errornames
from zope.schema.tests.test_field import FieldTestBase

class DictTest(FieldTestBase):
    """Test the Dict Field."""

    _Field_Factory = Dict

    def testValidate(self):
        field = Dict(title=u'Dict field',
                     description=u'', readonly=False, required=False)
        field.validate(None)
        field.validate({})
        field.validate({1: 'foo'})
        field.validate({'a': 1})

    def testValidateRequired(self):
        field = Dict(title=u'Dict field',
                     description=u'', readonly=False, required=True)
        field.validate({})
        field.validate({1: 'foo'})
        field.validate({'a': 1})

        self.assertRaisesErrorNames(errornames.RequiredMissing,
                                    field.validate, None)

    def testValidateMinValues(self):
        field = Dict(title=u'Dict field',
                     description=u'', readonly=False, required=False,
                     min_length=1)
        field.validate(None)
        field.validate({1: 'a'})
        field.validate({1: 'a', 2: 'b'})

        self.assertRaisesErrorNames(errornames.TooShort,
                                    field.validate, {})

    def testValidateMaxValues(self):
        field = Dict(title=u'Dict field',
                     description=u'', readonly=False, required=False,
                     max_length=1)
        field.validate(None)
        field.validate({})
        field.validate({1: 'a'})

        self.assertRaisesErrorNames(errornames.TooLong,
                                    field.validate, {1: 'a', 2: 'b'})
        self.assertRaisesErrorNames(errornames.TooLong,
                                    field.validate, {1: 'a', 2: 'b', 3: 'c'})

    def testValidateMinValuesAndMaxValues(self):
        field = Dict(title=u'Dict field',
                     description=u'', readonly=False, required=False,
                     min_length=1, max_length=2)
        field.validate(None)
        field.validate({1: 'a'})
        field.validate({1: 'a', 2: 'b'})

        self.assertRaisesErrorNames(errornames.TooShort,
                                    field.validate, {})
        self.assertRaisesErrorNames(errornames.TooLong,
                                    field.validate, {1: 'a', 2: 'b', 3: 'c'})

    def testValidateValueType(self):
        field = Dict(title=u'Dict field',
                     description=u'', readonly=False, required=False,
                     value_type=Int())
        field.validate(None)
        field.validate({'a': 5})
        field.validate({'a': 2, 'b': 3})

        self.assertRaisesErrorNames(errornames.WrongContainedType,
                                    field.validate, {1: ''} )
        self.assertRaisesErrorNames(errornames.WrongContainedType,
                                    field.validate, {1: 3.14159} )
        self.assertRaisesErrorNames(errornames.WrongContainedType,
                                    field.validate, {'a': ()} )

    def testValidateKeyTypes(self):
        field = Dict(title=u'Dict field',
                     description=u'', readonly=False, required=False,
                     key_type=Int())
        field.validate(None)
        field.validate({5: 'a'})
        field.validate({2: 'a', 2: 'b'})

        self.assertRaisesErrorNames(errornames.WrongContainedType,
                                    field.validate, {'': 1} )
        self.assertRaisesErrorNames(errornames.WrongContainedType,
                                    field.validate, {3.14159: 1} )
        self.assertRaisesErrorNames(errornames.WrongContainedType,
                                    field.validate, {(): 'a'} )


def test_suite():
    return makeSuite(DictTest)

if __name__ == '__main__':
    main(defaultTest='test_suite')
