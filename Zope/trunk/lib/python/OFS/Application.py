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


$Id: Application.py,v 1.33 1997/12/19 19:11:15 jim Exp $'''
__version__='$Revision: 1.33 $'[11:-2]


import Globals,Folder,os,regex,sys
from string import lower, find
from DateTime import DateTime
from AccessControl.User import UserFolder
from App.ApplicationManager import ApplicationManager

from ImageFile import ImageFile

class Application(Folder.Folder):
    title    ='Principia'
#    id       =title
    __roles__=None
    __defined_roles__=('manage',)
    web__form__method='GET'

    class misc_:
	"Miscellaneous product information"
	__roles__=None

    class p_:
	"Shared Principia information"
	__roles__=None

	folder=ImageFile('www/Folder_icon.gif', globals())
	image =ImageFile('www/Image_icon.gif', globals())
	file  =ImageFile('www/File_icon.gif', globals())
	doc   =ImageFile('www/Document_icon.gif', globals())

	UserFolder=ImageFile('AccessControl/www/UserFolder_icon.gif')
	User_icon =ImageFile('AccessControl/www/User_icon.gif')

	locked=ImageFile('www/modified.gif', globals())

	pl=ImageFile('TreeDisplay/www/Plus_icon.gif')
	mi=ImageFile('TreeDisplay/www/Minus_icon.gif')
	rtab=ImageFile('App/www/rtab.gif')
	ltab=ImageFile('App/www/ltab.gif')
	ControlPanel_icon=ImageFile('OFS/www/ControlPanel_icon.gif')
	PyPoweredSmall_Gif=ImageFile('App/www/PythonPoweredSmall.gif')

	#up=ImageFile('www/UpFolder_icon.gif', globals())
	#help=ImageFile('www/Help_icon.gif', globals())

    manage_options=(
    {'icon':'OFS/Folder_icon.gif', 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'AccessControl/AccessControl_icon.gif', 'label':'Security',
     'action':'manage_rolesForm',   'target':'manage_main'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm',   'target':'manage_main'},
#    {'icon':'OFS/Help_icon.gif', 'label':'Help',
#     'action':'manage_help',   'target':'_new'},
    )

    manage_rolesForm=Globals.HTMLFile('rolesForm', globals())

    _reserved_names=('standard_html_header',
		     'standard_html_footer',
		     'acl_users',
		     'Control_Panel')

    def _init(self):
	# Initialize users
	self.__allow_groups__=UserFolder()
	self.__allow_groups__._init()
	self._setObject('acl_users', self.__allow_groups__)

	# Initialize control panel
	cpl=ApplicationManager()
        cpl._init()
	self._setObject('Control_Panel', cpl)

        self.manage_addDocument('standard_html_header',
	                        'Standard Html Header',
				'<HTML><HEAD><TITLE><!--#var title_or_id-->' \
				'</TITLE></HEAD><BODY BGCOLOR="#FFFFFF">')
        self.manage_addDocument('standard_html_footer',
				'Standard Html Footer',
				'</BODY></HTML>')


    def id(self):
	try:    return self.REQUEST['SCRIPT_NAME'][1:]
	except: return self.title

    def folderClass(self): return Folder.Folder

    def __class_init__(self): pass

    def PrincipiaRedirect(self,destination,URL1):
	"""Utility function to allow user-controlled redirects"""
	if find(destination,'//') >= 0: raise 'Redirect', destination
	raise 'Redirect', ("%s/%s" % (URL1, destination))
    Redirect=PrincipiaRedirect

    def __bobo_traverse__(self, REQUEST, name=None):
	if name is None and REQUEST.has_key(Globals.SessionNameName):
	    pd=Globals.SessionBase[REQUEST[Globals.SessionNameName]]
	    alternate_self=pd.jar[self._p_oid]
	    if hasattr(self, 'aq_parent'):
		alternate_self=alternate_self.__of__(self.aq_parent)
	    return alternate_self

	try: return getattr(self, name)
	except AttributeError:
	    try: return self[name]
	    except KeyError:
		raise 'NotFound',(
		    "Sorry, the requested document does not exist.<p>"
		    "\n<!--\n%s\n%s\n-->" % (name,REQUEST['REQUEST_METHOD']))

    def PrincipiaTime(self):
	"""Utility function to return current date/time"""
	return DateTime()


    def manage_addRole(self,REQUEST,role):
	""" """
        roles=list(self.__defined_roles__)
	if role not in roles:
	    roles.append(role)
            roles.sort()
	    self.__defined_roles__=tuple(roles)
	try:    roles=self.__roles__
	except: roles=[]
	if roles is None: roles=[]
        roles.append(role)
	self.__roles__=roles
	return self.manage_rolesForm(self, REQUEST)

    def manage_deleteRole(self,REQUEST,role):
	""" """
	roles=list(self.__defined_roles__)
	if role in roles:
	    del roles[roles.index(role)]
	    self.__defined_roles__=tuple(roles)

    def validRoles(self):
	return self.__defined_roles__




def open_bobobase():
    # Open the application database
    Bobobase=Globals.Bobobase=Globals.PickleDictionary(Globals.BobobaseName)

    product_dir=os.path.join(SOFTWARE_HOME,'lib/python/Products')
    
    install_products()

    __traceback_info__=sys.path
    
    try: app=Bobobase['Application']
    except KeyError:
	app=Application()
	app._init()
	Bobobase['Application']=app
	get_transaction().commit()

    if not Bobobase.has_key('roles'):
	Bobobase['roles']=('manage',)
	get_transaction().commit()

    # Backward compatibility
    if not hasattr(app, 'Control_Panel'):
	cpl=ApplicationManager()
        cpl._init()
	app._setObject('Control_Panel', cpl)
	get_transaction().commit()

    return Bobobase

def install_products():
    # Install a list of products into the basic folder class, so
    # that all folders know about top-level objects, aka products

    path_join=os.path.join
    product_dir=path_join(SOFTWARE_HOME,'lib/python/Products')
    isdir=os.path.isdir
    exists=os.path.exists
    DictType=type({})

    meta_types=list(Folder.Folder.dynamic_meta_types)

    product_names=os.listdir(product_dir)
    product_names.sort()

    for product_name in product_names:
	package_dir=path_join(product_dir, product_name)
	if not isdir(package_dir): continue
	if not exists(path_join(package_dir, '__init__.py')): continue
	product=getattr(__import__("Products.%s" % product_name), product_name)

	for meta_type in pgetattr(product, 'meta_types', ()):
	    if product_name=='OFSP': meta_types.insert(0,meta_type)
	    else: meta_types.append(meta_type)
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

	for name,method in pgetattr(product, 'methods', {}).items():
	    setattr(Folder.Folder, name, method)

	misc_=pgetattr(product, 'misc_', {})
	if type(misc_) is DictType: misc_=Misc_(product_name, misc_)
	Application.misc_.__dict__[product_name]=misc_

    Folder.Folder.dynamic_meta_types=tuple(meta_types)

def pgetattr(product, name, default=install_products):
    if hasattr(product, name): return getattr(product, name)
    if hasattr(product, '__init__'):
	product=product.__init__
	if hasattr(product, name): return getattr(product, name)

    if default is not install_products: return default

    raise AttributeError, name

class Misc_:
    "Miscellaneous product information"

    __roles__=None

    def __init__(self, name, dict):
	self._d=dict
	self.__name__=name

    def __str__(self): return self.__name__
    def __getitem__(self, name): return self._d[name]

############################################################################## 
#
# $Log: Application.py,v $
# Revision 1.33  1997/12/19 19:11:15  jim
# updated icon management strategy
#
# Revision 1.32  1997/12/19 17:04:21  jim
# Make Products a Package.
#
# Revision 1.31  1997/12/19 15:37:34  jim
# Now product __init__s can omit __ foolishness.
# Now products can define misc objects.
#
# Revision 1.30  1997/12/18 18:42:07  jim
# Rearranged things to make fixup "products" work.
#
# Revision 1.29  1997/12/18 17:17:46  jim
# Added rule: only treat a directory in Products as a product if it
# has __init__.py
#
# Revision 1.28  1997/12/18 17:10:40  jim
# Added check for CVS directory.
#
# Revision 1.27  1997/12/18 16:45:38  jeffrey
# changeover to new ImageFile and HTMLFile handling
#
# Revision 1.26  1997/12/17 16:45:26  jim
# initial_products is dead!
#
# Revision 1.25  1997/12/12 21:53:05  brian
# ui support
#
# Revision 1.24  1997/12/12 21:49:41  brian
# ui update
#
# Revision 1.23  1997/12/05 20:33:02  brian
# *** empty log message ***
#
# Revision 1.22  1997/12/05 17:13:48  brian
# New UI
#
# Revision 1.21  1997/11/20 13:40:28  jim
# Added logic to make sure that the top-level user folder gets
# initialized correctly.
#
# Revision 1.20  1997/11/07 17:33:09  jim
# Added code to add Application key to Bobobase if necessary.
#
# Revision 1.19  1997/11/07 17:11:48  brian
# Added role mgmt to Application object
#
# Revision 1.18  1997/11/07 16:09:59  jim
# Added __bobo_traverse__ machinery in support of sessions.
# Updated product installation logic to give OFS special treatment.
#
# Revision 1.17  1997/11/06 22:43:39  brian
# Added global roles to app
#
# Revision 1.16  1997/11/05 15:06:56  paul
# Renamed Redirect to PrincipiaRedirect, leaving Redirect for
# compatibility.  Added PrincipiaTime which returns a DateTime object.
#
# Revision 1.15  1997/10/27 15:21:22  jim
# Fixed bug in assigning role names that caused roles record to be
# rewritten on every start up.
#
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
