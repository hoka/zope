##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""Folder object

Folders are the basic container objects and are analogous to directories.

$Id: Folder.py,v 1.82 1999/07/05 14:44:49 jim Exp $"""

__version__='$Revision: 1.82 $'[11:-2]

import Globals, SimpleItem
from ObjectManager import ObjectManager
from PropertyManager import PropertyManager
from AccessControl.Role import RoleManager
from webdav.Collection import Collection
from FindSupport import FindSupport
from Globals import HTMLFile



manage_addFolderForm=HTMLFile('folderAdd', globals())

def manage_addFolder(self, id, title='',
                     createPublic=0,
                     createUserF=0,
                     REQUEST=None):
    """Add a new Folder object with id *id*.

    If the 'createPublic' and 'createUserF' parameters are set to any true
    value, an 'index_html' and a 'UserFolder' objects are created respectively
    in the new folder.
    """
    ob=Folder()
    ob.id=id
    ob.title=title
    self._setObject(id, ob)
    try: user=REQUEST['AUTHENTICATED_USER']
    except: user=None
    if createUserF:
        if (user is not None) and not (
            user.has_permission('Add User Folders', self)):
            raise 'Unauthorized', (
                  'You are not authorized to add User Folders.'
                  )
        ob.manage_addUserFolder()
    if createPublic:
        if (user is not None) and not (
            user.has_permission('Add Documents, Images, and Files', self)):
            raise 'Unauthorized', (
                  'You are not authorized to add DTML Documents.'
                  )
        ob.manage_addDTMLDocument(id='index_html', title='')
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)



class Folder(ObjectManager, PropertyManager, RoleManager, Collection,
             SimpleItem.Item, FindSupport):
    """
    The basic container object in Principia.  Folders can hold almost all
    other Principia objects.
    """
    meta_type='Folder'

    _properties=({'id':'title', 'type': 'string'},)

    manage_options=(
        {'label':'Contents', 'action':'manage_main'},
        {'label':'View', 'action':'index_html'},
        {'label':'Properties', 'action':'manage_propertiesForm'},
        {'label':'Import/Export', 'action':'manage_importExportForm'},
        {'label':'Security', 'action':'manage_access'},
        {'label':'Undo', 'action':'manage_UndoForm'},
        {'label':'Find', 'action':'manage_findFrame', 'target':'manage_main'},
    )

    __ac_permissions__=()


Globals.default__class_init__(Folder)
