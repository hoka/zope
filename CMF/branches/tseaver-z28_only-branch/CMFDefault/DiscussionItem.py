##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Discussion item portal type.

$Id$
"""

from AccessControl import ClassSecurityInfo
from Acquisition import Implicit, aq_base, aq_inner, aq_parent
from DateTime import DateTime
from Globals import InitializeClass
from Globals import Persistent
from Globals import PersistentMapping
from OFS.Traversable import Traversable

from Products.CMFCore.interfaces.Discussions import Discussable
from Products.CMFCore.interfaces.Discussions import DiscussionResponse
from Products.CMFCore.utils import getToolByName

from Document import Document
from permissions import AccessContentsInformation
from permissions import ManagePortal
from permissions import ReplyToItem
from permissions import View
from utils import scrubHTML


factory_type_information = (
  { 'id'             : 'Discussion Item'
  , 'meta_type'      : 'Discussion Item'
  , 'description'    : """\
Discussion Items are documents which reply to other content.
They should *not* be addable through the standard 'folder_factories' interface.
"""
  , 'icon'           : 'discussionitem_icon.gif'
  , 'product'        : '' # leave blank to suppress
  , 'factory'        : ''
  , 'immediate_view' : ''
  , 'aliases'        : {'(Default)':'discussionitem_view',
                        'view':'discussionitem_view'}
  , 'actions'        : ( { 'id'            : 'view'
                         , 'name'          : 'View'
                         , 'action': 'string:${object_url}/discussionitem_view'
                         , 'permissions'   : (View,)
                         }
                       ,
                       )
  }
,
)


def addDiscussionItem(self, id, title, description, text_format, text,
                      reply_to, RESPONSE=None):
    """
    Add a discussion item

    'title' is also used as the subject header
    if 'description' is blank, it is filled with the contents of 'title'
    'reply_to' is the object (or path to the object) which this is a reply to

    Otherwise, same as addDocument
    """

    if not description: description = title
    text = scrubHTML(text)
    item = DiscussionItem( id )
    item.title = title
    item.description = description
    item.text_format = text_format
    item.text = text
    item.setReplyTo(reply_to)

    item._parse()
    self._setObject(id, item)

    if RESPONSE is not None:
        RESPONSE.redirect(self.absolute_url())


class DiscussionItem(Document):
    """
        Class for content which is a response to other content.
    """

    __implements__ = (DiscussionResponse, Document.__implements__)

    meta_type           = 'Discussion Item'
    portal_type         = 'Discussion Item'
    allow_discussion    = 1
    in_reply_to         = None
    # XXX this is wrong, it precludes the use of a normal workflow.
    review_state        ='published'

    security = ClassSecurityInfo()

    security.declareProtected(View, 'listCreators')
    def listCreators(self):
        """ List Dublin Core Creator elements - resource authors.
        """
        if not hasattr(aq_base(self), 'creators'):
            # for content created with CMF versions before 1.5
            if hasattr(aq_base(self), 'creator') and self.creator != 'unknown':
                self.creators = ( self.creator, )
            else:
                self.creators = ()
        return self.creators

    #
    #   DiscussionResponse interface
    #
    security.declareProtected(View, 'inReplyTo')
    def inReplyTo( self, REQUEST=None ):
        """
            Return the Discussable object to which we are a reply.

            Two cases obtain:

              - We are a "top-level" reply to a non-DiscussionItem piece
                of content;  in this case, our 'in_reply_to' field will
                be None.

              - We are a nested reply;  in this case, our 'in_reply_to'
                field will be the ID of the parent DiscussionItem.
        """
        tool = getToolByName( self, 'portal_discussion' )
        talkback = tool.getDiscussionFor( self )
        return talkback._getReplyParent( self.in_reply_to )

    security.declarePrivate(View, 'setReplyTo')
    def setReplyTo( self, reply_to ):
        """
            Make this object a response to the passed object.
        """
        if getattr( reply_to, 'meta_type', None ) == self.meta_type:
            self.in_reply_to = reply_to.getId()
        else:
            self.in_reply_to = None

    security.declareProtected(View, 'parentsInThread')
    def parentsInThread( self, size=0 ):
        """
            Return the list of items which are "above" this item in
            the discussion thread.

            If 'size' is not zero, only the closest 'size' parents
            will be returned.
        """
        parents = []
        current = self
        while not size or len( parents ) < size:
            parent = current.inReplyTo()
            assert not parent in parents  # sanity check
            parents.insert( 0, parent )
            if parent.meta_type != self.meta_type:
                break
            current = parent
        return parents

InitializeClass( DiscussionItem )


class DiscussionItemContainer( Persistent, Implicit, Traversable ):
    """
        Store DiscussionItem objects. Discussable content that
        has DiscussionItems associated with it will have an
        instance of DiscussionItemContainer injected into it to
        hold the discussion threads.
    """

    __implements__ = Discussable

    # for the security machinery to allow traversal
    #__roles__ = None

    security = ClassSecurityInfo()

    def __init__(self):
        self.id = 'talkback'
        self._container = PersistentMapping()

    security.declareProtected(View, 'getId')
    def getId( self ):
        return self.id

    security.declareProtected(View, 'getReply')
    def getReply( self, reply_id ):
        """
            Return a discussion item, given its ID;  raise KeyError
            if not found.
        """
        return self._container.get( reply_id ).__of__(self)

    # Is this right?
    security.declareProtected(View, '__bobo_traverse__')
    def __bobo_traverse__(self, REQUEST, name):
        """
        This will make this container traversable
        """
        target = getattr(self, name, None)
        if target is not None:
            return target

        else:
            try:
                return self.getReply(name)
            except:
                parent = aq_parent( aq_inner( self ) )
                if parent.getId() == name:
                    return parent
                else:
                    REQUEST.RESPONSE.notFoundError("%s\n%s" % (name, ''))

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        """
            We have juste been added or moved.
            Add the contained items to the catalog.
        """
        if aq_base(container) is not aq_base(self):
            for obj in self.objectValues():
                obj.__of__(self).manage_afterAdd(item, container)

    security.declarePrivate('manage_afterClone')
    def manage_afterClone(self, item):
        """
            We have just been cloned.
            Notify the workflow about the contained items.
        """
        for obj in self.objectValues():
            obj.__of__(self).manage_afterClone(item)

    security.declarePrivate( 'manage_beforeDelete' )
    def manage_beforeDelete(self, item, container):
        """
            Remove the contained items from the catalog.
        """
        if aq_base(container) is not aq_base(self):
            for obj in self.objectValues():
                obj.__of__( self ).manage_beforeDelete( item, container )

    #
    #   OFS.ObjectManager query interface.
    #
    security.declareProtected(AccessContentsInformation, 'objectIds')
    def objectIds( self, spec=None ):
        """
            Return a list of the ids of our DiscussionItems.
        """
        if spec and spec is not DiscussionItem.meta_type:
            return []
        return self._container.keys()


    security.declareProtected(AccessContentsInformation, 'objectItems')
    def objectItems(self, spec=None):
        """
            Return a list of (id, subobject) tuples for our DiscussionItems.
        """
        r=[]
        a=r.append
        g=self._container.get
        for id in self.objectIds(spec):
            a( (id, g( id ) ) )
        return r


    security.declareProtected(AccessContentsInformation, 'objectValues')
    def objectValues(self):
        """
            Return a list of our DiscussionItems.
        """
        return self._container.values()

    #
    #   Discussable interface
    #
    security.declareProtected(ReplyToItem, 'createReply')
    def createReply( self, title, text, Creator=None, text_format='structured-text' ):
        """
            Create a reply in the proper place
        """
        container = self._container

        id = int(DateTime().timeTime())
        while self._container.get( str(id), None ) is not None:
            id = id + 1
        id = str( id )

        item = DiscussionItem( id, title=title, description=title )
        item._edit( text_format=text_format, text=text )
        item.__of__(self).addCreator(Creator)
        item.__of__(self).indexObject()

        item.setReplyTo( self._getDiscussable() )
        item.__of__(self).notifyWorkflowCreated()

        self._container[ id ] = item

        return id

    security.declareProtected(ManagePortal, 'deleteReply')
    def deleteReply( self, reply_id ):
        """ Remove a reply from this container """
        if self._container.has_key( reply_id ):
            reply = self._container.get( reply_id ).__of__( self )
            my_replies = reply.talkback.getReplies()
            for my_reply in my_replies:
                my_reply_id = my_reply.getId()
                if hasattr( my_reply, 'unindexObject' ):
                    my_reply.unindexObject()

                del self._container[my_reply_id]

            if hasattr( reply, 'unindexObject' ):
                reply.unindexObject()

            del self._container[reply_id]


    security.declareProtected(View, 'hasReplies')
    def hasReplies( self, content_obj ):
        """
            Test to see if there are any dicussion items
        """
        outer = self._getDiscussable( outer=1 )
        if content_obj == outer:
            return bool( len(self._container) )
        else:
            return bool( len( content_obj.talkback._getReplyResults() ) )

    security.declareProtected(View, 'replyCount')
    def replyCount( self, content_obj ):
        """ How many replies do i have? """
        outer = self._getDiscussable( outer=1 )
        if content_obj == outer:
            return len( self._container )
        else:
            replies = content_obj.talkback.getReplies()
            return self._repcount( replies )

    security.declarePrivate('_repcount')
    def _repcount( self, replies ):
        """  counts the total number of replies by recursing thru the various levels
        """
        count = 0

        for reply in replies:
            count = count + 1

            #if there is at least one reply to this reply
            replies = reply.talkback.getReplies()
            if replies:
                count = count + self._repcount( replies )

        return count

    security.declareProtected(View, 'getReplies')
    def getReplies( self ):
        """
            Return a sequence of the DiscussionResponse objects which are
            associated with this Discussable
        """
        objects = []
        a = objects.append
        result_ids = self._getReplyResults()

        for id in result_ids:
            a( self._container.get( id ).__of__( self ) )

        return objects

    security.declareProtected(View, 'quotedContents')
    def quotedContents(self):
        """
            Return this object's contents in a form suitable for inclusion
            as a quote in a response.
        """

        return ""

    #
    #   Utility methods
    #
    security.declarePrivate( '_getReplyParent' )
    def _getReplyParent( self, in_reply_to ):
        """
            Return the object indicated by the 'in_reply_to', where
            'None' represents the "outer" content object.
        """
        outer = self._getDiscussable( outer=1 )
        if in_reply_to is None:
            return outer
        parent = self._container[ in_reply_to ].__of__( aq_inner( self ) )
        return parent.__of__( outer )

    security.declarePrivate( '_getDiscussable' )
    def _getDiscussable( self, outer=0 ):
        """
        """
        tb = outer and aq_inner( self ) or self
        return getattr( tb, 'aq_parent', None )

    security.declarePrivate( '_getReplyResults' )
    def _getReplyResults( self ):
        """
           Get a list of ids of DiscussionItems which are replies to
           our Discussable.
        """
        discussable = self._getDiscussable()
        outer = self._getDiscussable( outer=1 )

        if discussable == outer:
            in_reply_to = None
        else:
            in_reply_to = discussable.getId()

        result = []
        a = result.append
        for key, value in self._container.items():
            if value.in_reply_to == in_reply_to:
                a( ( key, value ) )

        result.sort( lambda a, b: cmp(a[1].creation_date, b[1].creation_date) )

        return [ x[0] for x in result ]

InitializeClass( DiscussionItemContainer )
