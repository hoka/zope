##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" List Criterion: A criterion that is a list

$Id$
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from zope.interface import implements

from Products.CMFTopic.AbstractCriterion import AbstractCriterion
from Products.CMFTopic.interfaces import ICriterion
from Products.CMFTopic.permissions import ChangeTopics
from Products.CMFTopic.permissions import View
from Products.CMFTopic.Topic import Topic


class ListCriterion( AbstractCriterion ):

    """
        Represent a criterion which is a list of values (for an
        'OR' search).
    """

    implements(ICriterion)

    meta_type = 'List Criterion'
    operator = None
    value = ( '', )

    security = ClassSecurityInfo()

    _editableAttributes = ( 'value', 'operator' )

    def __init__( self, id, field ):
        self.id = id
        self.field = field
        self._clear()

    security.declarePrivate( '_clear' )
    def _clear( self ):
        """
            Restore to original value.
        """
        self.value = ( '', )    # *Not* '()', which won't do at all!
        self.operator = None

    security.declareProtected( ChangeTopics, 'getEditForm' )
    def getEditForm( self ):
        """
            Return the name of skin method which renders the form
            used to edit this kind of criterion.
        """
        return "listc_edit"

    security.declareProtected( ChangeTopics, 'edit' )
    def edit( self, value=None, operator=None ):
        """
            Update the value we match against.
        """
        if value is None:
            self._clear()
        else:
            if type( value ) == type( '' ):
                value = value.split('\n')
            self.value = tuple( value )

        if not operator:
            operator = None

        self.operator = operator

    security.declareProtected(View, 'getCriteriaItems')
    def getCriteriaItems( self ):
        """
            Return a tuple of query elements to be passed to the catalog
            (used by 'Topic.buildQuery()').
        """
        # filter out empty strings
        result = []

        value = tuple( filter( None, self.value ) )
        if not value:
            return ()
        result.append( ( self.field, self.value ), )

        if self.operator is not None:
            result.append( ( '%s_operator' % self.field, self.operator ) )

        return tuple( result )

InitializeClass( ListCriterion )

# Register as a criteria type with the Topic class
Topic._criteriaTypes.append( ListCriterion )
