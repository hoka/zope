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
$Id: testField.py,v 1.5 2002/07/14 18:51:27 faassen Exp $
"""
from unittest import TestCase, TestSuite, main, makeSuite
from Schema import Field, IField, ErrorNames
from Schema.Exceptions import StopValidation, ValidationError


class FieldTest(TestCase):
    """Test generic Field."""

    def assertRaisesErrorNames(self, error_name, f, *args, **kw):
        try:
            f(*args, **kw)
        except ValidationError, e:
            self.assertEquals(error_name, e.error_name)
            return
        self.fail('Expected ValidationError')

    def unexpectedValidationError(self, e):
        self.fail("Expected no ValidationError, but we got %s" % e.error_name)
        
    def testValidate(self):
        field = Field(id="field", title='Not required field', description='',
                      readonly=0, required=0)
        try:
            field.validate(None)
            field.validate('foo')
            field.validate(1)
            field.validate(0)
            field.validate('')
        except ValidationError, e:
            self.unexpectedValidationError(e)
    
    def testValidateRequired(self):
        field = Field(id="field", title='Required field', description='',
                      readonly=0, required=1)
        try:
            field.validate('foo')
            field.validate(1)
            field.validate(0)
            field.validate('')
        except ValidationError, e:
            self.unexpectedValidationError(e)
            
        self.assertRaisesErrorNames(ErrorNames.RequiredMissing,
                                    field.validate, None)


def test_suite():
    return TestSuite((
        makeSuite(FieldTest),
        ))

if __name__ == '__main__':
    main(defaultTest='test_suite')
