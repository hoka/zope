#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  
#
############################################################################## 
__doc__='''Application support


$Id: Application.py,v 1.14 1997/09/25 14:04:56 brian Exp $'''
__version__='$Revision: 1.14 $'[11:-2]


import Globals,Folder,regex
from string import lower, find
from AccessControl.User import UserFolder


class Application(Folder.Folder):
    title    ='Principia'
    id       =title
    __roles__=None
    web__form__method='GET'

    manage_options=(
    {'icon':'OFS/Folder_icon.gif', 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'AccessControl/AccessControl_icon.gif', 'label':'Access Control',
     'action':'manage_rolesForm',   'target':'manage_main'},
    {'icon':'OFS/ControlPanel_icon.gif', 'label':'Control Panel',
     'action':'app/manage',   'target':'_top'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm',   'target':'manage_main'},
#    {'icon':'OFS/Help_icon.gif', 'label':'Help',
#     'action':'manage_help',   'target':'_new'},
    )

    manage_rolesForm=Globals.HTMLFile('OFS/rolesForm')

    _reserved_names=('standard_html_header',
		     'standard_html_footer',
		     'acl_users')

    __allow_groups__=UserFolder()

    def _init(self):
        self.manage_addDocument('standard_html_header',
	                        'Standard Html Header',
				'<HTML><HEAD><TITLE><!--#var title_or_id-->' \
				'</TITLE></HEAD><BODY BGCOLOR="#FFFFFF">')
        self.manage_addDocument('standard_html_footer',
				'Standard Html Footer',
				'</BODY></HTML>')
	self._setObject('acl_users', self.__allow_groups__)

    def folderClass(self): return Folder.Folder

    def __class_init__(self): pass

    def Redirect(self,destination,PARENT_URL):
	"""Utility function to allow user-controlled redirects"""
	if find(destination,'//') >= 0: raise 'Redirect', destination
	raise 'Redirect', ("%s/%s" % (PARENT_URL, destination))


	

def open_bobobase():
    # Open the application database
    Bobobase=Globals.Bobobase=Globals.PickleDictionary(Globals.BobobaseName)
    
    if not Bobobase.has_key('products'):
	import initial_products
	initial_products.install(Bobobase)
	get_transaction().commit()

    if not Bobobase.has_key('roles'):
	Bobobase['roles']=('manage',)
	get_transaction().commit()

    products=Bobobase['products']
    
    install_products(products)

    return Bobobase

def install_products(products):
    # Install a list of products into the basic folder class, so
    # that all folders know about top-level objects, aka products

    meta_types=list(Folder.Folder.dynamic_meta_types)
    role_names=list(Globals.Bobobase['roles'])

    for product in products:
	product=__import__(product)
	for meta_type in product.meta_types:
	    meta_types.append(meta_type)
	    name=meta_type['name']

	    if (not meta_type.has_key('prefix') and 
		not regex.match('[^a-zA-Z0-9_]', name)):
	        meta_type['prefix']=lower(name)

	    if meta_type.has_key('prefix'):
		prefix=meta_type['prefix']

		def productNames(self, name=name):
		    t=[]
		    for i in self.objectMap():
			if i['meta_type']==name: t.append(i['name'])
		    return t

		setattr(Folder.Folder, "%sNames" % prefix , productNames)

		def productValues(self, name=name):
		    t=[]
		    for i in self.objectMap():
			if i['meta_type']==name:
			    t.append(getattr(self,i['name']))
		    return t

		setattr(Folder.Folder, "%sValues" % prefix , productValues)

		def productItems(self, name=name):
		    t=[]
		    for i in self.objectMap():
			if i['meta_type']=='Image':
			    n=i['name']
			    t.append((n,getattr(self,n)))
		    return t

		setattr(Folder.Folder, "%sItems" % prefix , productItems)

	for name,method in product.methods.items():
	    setattr(Folder.Folder, name, method)

	# Try to install role names
	try:
	    for n in product.role_names:
		if n not in role_names: role_names.append(n)
	except: pass

    Folder.Folder.dynamic_meta_types=tuple(meta_types)
    Globals.Bobobase['roles']=tuple(role_names)



############################################################################## 
# Test functions:
#

def main():
    # The "main" program for this module
    import sys
    print sys.argv[0]+" is a pure module and doesn't do anything by itself."


if __name__ == "__main__": main()

############################################################################## 
#
# $Log: Application.py,v $
# Revision 1.14  1997/09/25 14:04:56  brian
# Added default __roles__ of None, custom roles form
#
# Revision 1.13  1997/09/24 22:16:43  brian
# Style update
#
# Revision 1.12  1997/09/23 10:30:44  jim
# added undo to menu
#
# Revision 1.11  1997/09/19 18:22:29  brian
# Nicified Application
#
# Revision 1.10  1997/09/10 18:42:35  jim
# Added SimpleItem mix-in and new title/id methods.
#
# Revision 1.9  1997/09/09 14:21:07  brian
# Fixed Image editing
#
# Revision 1.8  1997/09/08 23:38:58  brian
# Style mods
#
# Revision 1.7  1997/08/29 18:39:30  brian
# Added role management and fixed a few bugs:
#   o images/manage went nowhere
#   o text on document add form talked about adding images...
#   o added role mgmgt to add forms for Folder,Document,Image
#
# Revision 1.6  1997/08/27 13:30:19  brian
# Changes for UserFolder support:
#   o Added support for role registration to Application.py
#     Products may define a __.role_names in their __init__.py
#     which may be a tuple of role names which will be added to
#     the global list of role names which appears in the role
#     assignment select box when defining/editing a user.
#
#   o Application.Application now has a default __allow_groups__
#     attribute which is a UserFolder with no members defined.
#     This default top-level UF is not visible in the UI, and
#     the user can create a new UF at the top level (in the
#     Application object) at a later time which will simply
#     override the default and be visible in the UI. Since the
#     default UF has no users, an out-of-the-box application's
#     management interfaces will effectively be available to the
#     superuser alone.
#
#   o Removed the __init__ in Folder which created a default ACL.
#     This is no longer needed.
#
#   o Made some minor (but controversial!) style consistency fixes
#     to some of the OFS templates.
#
# Revision 1.5  1997/08/15 22:24:12  jim
# Added Redirect
#
# Revision 1.4  1997/08/08 15:51:27  jim
# Added access control support
#
# Revision 1.3  1997/08/06 18:26:12  jim
# Renamed description->title and name->id and other changes
#
# Revision 1.2  1997/07/28 21:33:08  jim
# Changed top name.
#
# Revision 1.1  1997/07/25 20:03:22  jim
# initial
#
#
