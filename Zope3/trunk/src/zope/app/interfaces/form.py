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
"""Validation Exceptions

$Id: form.py,v 1.6 2003/08/07 21:34:49 jim Exp $
"""

import cgi
from zope.schema.interfaces import ValidationError
from zope.component.interfaces import IView
from zope.interface import Attribute, Interface, implements
from zope.app.interfaces.exceptions import UserError

class IWidgetInputError(Interface):
    'Placeholder for a snippet View'
    pass

class WidgetInputError(UserError):
    """There were one or more user input errors
    """
    implements(IWidgetInputError)

    def __init__(self, field_name, widget_title, errors):
        ''' errors is a ValidationError '''
        UserError.__init__(self, field_name, widget_title, errors)
        self.field_name = field_name
        self.widget_title = widget_title
        self.errors = errors

class MissingInputError(WidgetInputError):
    """Required data was not supplied
    """

class ConversionError(WidgetInputError):
    """If some conversion fails, this exception is raised.
    """

    def __init__(self, error_name, original_exception=None):
        Exception.__init__(self, error_name, original_exception)
        self.error_name = error_name
        self.original_exception = original_exception


InputErrors = WidgetInputError, ValidationError


class ErrorContainer(Exception):
    """A base error class for collecting multiple errors
    """

    def append(self, error):
        self.args += (error, )

    def __len__(self):
        return len(self.args)

    def __iter__(self):
        return iter(self.args)

    def __getitem__(self, i):
        return self.args[i]

    def __str__(self):
        return "\n".join(
            ["%s: %s" % (error.__class__.__name__, error)
             for error in self.args]
            )

    __repr__ = __str__

class WidgetsError(ErrorContainer):
    """A collection of errors from widget processing.
    """

class IWidget(IView):
    """Generically describes the behavior of a widget.

    The widget defines a list of propertyNames, which describes
    what properties of the widget are available to use for
    constructing the widget render output.

    Note that this level must be still presentation independent.
    """

    propertyNames = Attribute("""This is a list of attributes that are
                                 defined for the widget.""")

    def getValue(name):
        """Look up a Widget configuration setting by name."""

    def validate():
        """Validate the widget data.

        If there is no user input and the field is required, then a
        MissingInputError will be raised.

        If there is no user input and the field is not required, then
        the field default value will be returned.

        A WidgetInputError is returned in the case of one or more
        errors encountered, inputting, converting, or validating the data.
        """

    def getData():
        """Return converted and validated widget data.

        See validate() for validation performed.
        """

    def applyChanges(content):
        """Validate the widget data and apply it to the content.

        See validate() for validation performed.
        """


    def haveData():
        """Is there input data for the field

        Return True if there is data and False otherwise.
        """

    name = Attribute("""The uniquewidget name

        This must be unique within a set of widgets.
        """)

    title = Attribute("The widget title")

    required = Attribute("Flag indicating whether the field is required")

    def setData(value):
        """Set the default data for the widget.

        The given value should be used even if the user has entered
        data.
        """

    def setPrefix(prefix):
        """Set the name prefix used for the widget

        The widget name is used to identify the widget's data within
        input data. For example, for HTTP forms, the widget name is
        used for the form key.
        """
