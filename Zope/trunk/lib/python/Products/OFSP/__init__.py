############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''OFS
$Id: __init__.py,v 1.2 1997/12/19 17:06:22 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

import Session, DraftFolder
from ImageFile import ImageFile

meta_types=(
    {'name':'Draft Folder', 'action':'manage_addDraftFolderForm'},
    {'name':'Session', 'action':'manage_addSessionForm'},
    {'name':'File', 'action':'manage_addFileForm'},
    {'name':'Image', 'action':'manage_addImageForm'},
    {'name':'Folder', 'action':'manage_addFolderForm'},
    {'name':'Document', 'action':'manage_addDocumentForm'},
    )

methods={
    'manage_addSessionForm': Session.addForm,
    'manage_addSession': Session.add,
    'manage_addDraftFolderForm': DraftFolder.addForm,
    'manage_addDraftFolder': DraftFolder.add,
    }

misc_={
    'image': ImageFile('images/Image_icon.gif', globals()),
    'file': ImageFile('images/File_icon.gif', globals()),
    'doc': ImageFile('images/Document_icon.gif', globals()),
    'draft': ImageFile('images/DraftFolder.gif', globals()),
    'sup': ImageFile('images/DraftFolderControl.gif', globals()),
    'session': ImageFile('images/session.gif', globals()),
    'folder': ImageFile('images/folder.gif', globals()),
    }

############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.2  1997/12/19 17:06:22  jim
# moved Sessions and Daft folders here.
#
# Revision 1.1  1997/12/18 17:05:54  jim
# *** empty log message ***
#
# Revision 1.3  1997/11/11 19:26:37  jim
# Added DraftFolder.
#
# Revision 1.2  1997/11/10 16:32:54  jim
# Changed to support separate Image and File objects.
#
# Revision 1.1  1997/11/07 19:31:42  jim
# *** empty log message ***
#
# Revision 1.1  1997/10/09 17:34:53  jim
# first cut, no testing
#
# Revision 1.1  1997/07/25 18:14:28  jim
# initial
#
#
