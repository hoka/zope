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
""" Allow the "view" of a folder to be skinned by type.

$Id$
"""

from Products.CMFCore.PortalFolder import PortalFolder
from Products.CMFCore.CMFCorePermissions import View
from Products.CMFCore.CMFCorePermissions import ManageProperties
from Products.CMFCore.CMFCorePermissions import ListFolderContents
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from Products.CMFCore.utils import _getViewFor
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Acquisition import aq_base

factory_type_information = (
  { 'id'             : 'Skinned Folder'
  , 'meta_type'      : 'Skinned Folder'
  , 'description'    : """\
Skinned folders can define custom 'view' actions.
"""
  , 'icon'           : 'folder_icon.gif'
  , 'product'        : 'CMFDefault'
  , 'factory'        : 'addSkinnedFolder'
  , 'filter_content_types' : 0
  , 'immediate_view' : 'folder_edit_form'
  , 'actions'        : ( { 'id'            : 'view'
                         , 'name'          : 'View'
                         , 'action': 'string:${object_url}/folder_view'
                         , 'permissions'   : (View,)
                         , 'category'      : 'folder'
                         }
                       , { 'id'            : 'edit'
                         , 'name'          : 'Edit'
                         , 'action': 'string:${object_url}/folder_edit_form'
                         , 'permissions'   : (ManageProperties,)
                         , 'category'      : 'folder'
                         }
                       , { 'id'            : 'foldercontents'
                         , 'name'          : 'Folder contents'
                         , 'action': 'string:${object_url}/folder_contents'
                         , 'permissions'   : (ListFolderContents,)
                         , 'category'      : 'folder'
                         }
                       )
  }
,
)


class SkinnedFolder(CMFCatalogAware, PortalFolder):
    """
    """
    meta_type = 'Skinned Folder'

    security = ClassSecurityInfo()

    manage_options = PortalFolder.manage_options

    def __call__(self):
        '''
        Invokes the default view.
        '''
        view = _getViewFor(self)
        if getattr(aq_base(view), 'isDocTemp', 0):
            return view(self, self.REQUEST)
        else:
            return view()

    security.declareProtected(View, 'view')
    view = __call__

    index_html = None  # This special value informs ZPublisher to use __call__

    security.declareProtected(View, 'Creator')
    def Creator( self ):
        """
            Return the ID of our owner.
        """
        owner = self.getOwner()
        if hasattr( owner, 'getId' ):
            return owner.getId()
        return 'No owner'

    # We derive from CMFCatalogAware first, so we are cataloged too.

InitializeClass( SkinnedFolder )

def addSkinnedFolder( self, id, title='', description='', REQUEST=None ):
    """
    """
    sf = SkinnedFolder( id, title )
    sf.description = description
    self._setObject( id, sf )
    sf = self._getOb( id )
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect( sf.absolute_url() + '/manage_main' )
